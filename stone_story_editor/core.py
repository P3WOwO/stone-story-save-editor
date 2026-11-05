"""Core logic: SJSON parsing/writing, save encryption, change tracking.

No GUI code lives here, so everything in this module is unit-testable.
"""
from __future__ import annotations

import base64
import copy
import datetime as _dt
import hashlib
import json
import math
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

SLOT_RE = re.compile(r"^save_file_\d+$")

# Constants match the encrypted save format of the current game version
# (and the public SSRPGS cryptor implementation).
_CIPHER_PASSWORD = b"peekabeyoufoundme"
_CIPHER_SALT_PREFIX = base64.b64decode("MADE/BY/CATALYST/42/")
_CIPHER_SALT = _CIPHER_SALT_PREFIX + bytes(32 - len(_CIPHER_SALT_PREFIX))
_CIPHER_IV = bytes(32)
_BLOCK_SIZE = 32


class SJSONError(ValueError):
    """The text is not valid save syntax."""


# --------------------------------------------------------------------------
# SJSON parser / writer
# --------------------------------------------------------------------------
class SJSONParser:
    """Small recursive-descent parser for the SJSON-like save syntax."""

    def __init__(self, text: str):
        self.text = text
        self.i = 0
        self.n = len(text)

    def _skip(self) -> None:
        while self.i < self.n and self.text[self.i].isspace():
            self.i += 1

    def _quoted(self) -> str:
        start = self.i
        self.i += 1
        escaped = False
        while self.i < self.n:
            ch = self.text[self.i]
            self.i += 1
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                raw = self.text[start:self.i]
                # The game may use backslash-escaped square brackets (\[ or \])
                # inside quoted text. They are not valid JSON escapes, so double
                # an odd run of backslashes before those brackets.
                repaired = []
                k = 0
                while k < len(raw):
                    if raw[k] == "\\":
                        j = k
                        while j < len(raw) and raw[j] == "\\":
                            j += 1
                        count = j - k
                        if j < len(raw) and raw[j] in "[]" and count % 2 == 1:
                            repaired.append("\\" * (count + 1) + raw[j])
                            k = j + 1
                        else:
                            repaired.append("\\" * count)
                            k = j
                    else:
                        repaired.append(raw[k])
                        k += 1
                raw = "".join(repaired)
                try:
                    return json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise SJSONError(f"Invalid string near position {start}: {exc}") from exc
        raise SJSONError(f"Unterminated string near position {start}")

    def _bare(self, stop_chars: str) -> str:
        start = self.i
        while self.i < self.n:
            ch = self.text[self.i]
            if ch in stop_chars:
                if ch in "]}" and self.i > start and self.text[self.i - 1] == "\\":
                    self.i += 1
                    continue
                break
            self.i += 1
        return self.text[start:self.i].strip()

    def _atom(self, token: str) -> Any:
        if token == "":
            return ""
        low = token.lower()
        if low == "true":
            return True
        if low == "false":
            return False
        if low in ("null", "none"):
            return None
        if re.fullmatch(r"[-+]?(?:0|[1-9]\d*)", token):
            try:
                return int(token)
            except ValueError:
                pass
        if (re.fullmatch(r"[-+]?(?:\d+\.\d*|\d*\.\d+)(?:[eE][-+]?\d+)?", token)
                or re.fullmatch(r"[-+]?\d+[eE][-+]?\d+", token)):
            try:
                val = float(token)
                return val if math.isfinite(val) else token
            except ValueError:
                pass
        return token

    def parse(self) -> Any:
        self._skip()
        value = self._value()
        self._skip()
        if self.i != self.n:
            raise SJSONError(f"Unexpected data at the end of the file (position {self.i})")
        return value

    def _value(self) -> Any:
        self._skip()
        if self.i >= self.n:
            raise SJSONError("Unexpected end of file")
        ch = self.text[self.i]
        if ch == "{":
            return self._object()
        if ch == "[":
            return self._array()
        if ch == '"':
            return self._quoted()
        token = self._bare(",}]")
        if not token:
            raise SJSONError(f"Empty value near position {self.i}")
        return self._atom(token)

    def _key(self) -> str:
        self._skip()
        if self.i >= self.n:
            raise SJSONError("Object key expected")
        if self.text[self.i] == '"':
            key = self._quoted()
        else:
            key = self._bare(":")
        if not isinstance(key, str) or key == "":
            raise SJSONError(f"Invalid object key near position {self.i}")
        self._skip()
        if self.i >= self.n or self.text[self.i] != ":":
            raise SJSONError(f"Expected ':' after key {key!r}")
        self.i += 1
        return key

    def _object(self) -> dict:
        self.i += 1
        result: dict = {}
        self._skip()
        while self.i < self.n and self.text[self.i] != "}":
            key = self._key()
            result[key] = self._value()
            self._skip()
            if self.i < self.n and self.text[self.i] == ",":
                self.i += 1
                self._skip()
                continue
            if self.i < self.n and self.text[self.i] == "}":
                break
            raise SJSONError(f"Expected ',' or '}}' near position {self.i}")
        if self.i >= self.n:
            raise SJSONError("Unterminated object")
        self.i += 1
        return result

    def _array(self) -> list:
        self.i += 1
        result: list = []
        self._skip()
        while self.i < self.n and self.text[self.i] != "]":
            result.append(self._value())
            self._skip()
            if self.i < self.n and self.text[self.i] == ",":
                self.i += 1
                self._skip()
                continue
            if self.i < self.n and self.text[self.i] == "]":
                break
            raise SJSONError(f"Expected ',' or ']' near position {self.i}")
        if self.i >= self.n:
            raise SJSONError("Unterminated array")
        self.i += 1
        return result


def _sjson_string(value: str) -> str:
    if (value and value == value.strip()
            and not re.search(r'[\\"{},\[\],:\n\r\t]', value)
            and not any(ch.isspace() for ch in value)
            and value.lower() not in {"true", "false", "null", "none"}
            and not re.fullmatch(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?", value)):
        return value
    return json.dumps(value, ensure_ascii=False)


def sjson_dumps(value: Any) -> str:
    if isinstance(value, dict):
        chunks = []
        for key, item in value.items():
            if not isinstance(key, str):
                key = str(key)
            key_out = key if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key) else json.dumps(key, ensure_ascii=False)
            chunks.append(f"{key_out}:{sjson_dumps(item)}")
        return "{" + ",".join(chunks) + "}"
    if isinstance(value, list):
        return "[" + ",".join(sjson_dumps(item) for item in value) + "]"
    if isinstance(value, bool):
        return "True" if value else "False"
    if value is None:
        return "null"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("NaN and Infinity cannot be saved")
        return repr(value)
    if isinstance(value, str):
        return _sjson_string(value)
    raise TypeError(f"Unsupported value type: {type(value).__name__}")


# --------------------------------------------------------------------------
# Encryption
# --------------------------------------------------------------------------
def _rijndael_class():
    try:
        from pprp.crypto_3 import rijndael
        return rijndael
    except Exception as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(
            "The 'pprp' library (version 0.2.6) is not installed. "
            "Run:  pip install pprp==0.2.6   (do not upgrade to 0.2.7)."
        ) from exc


def _derive_key(salt: bytes = _CIPHER_SALT) -> bytes:
    return hashlib.pbkdf2_hmac("sha1", _CIPHER_PASSWORD, salt, 1000, dklen=32)


def decrypt_progress(cipher_text: str) -> str:
    raw = base64.b64decode(cipher_text, validate=True)
    if len(raw) < 64 or (len(raw) - 64) % _BLOCK_SIZE != 0:
        raise ValueError("Encrypted block has an invalid length")
    salt, iv = raw[:32], raw[32:64]
    payload = raw[64:]
    rijndael = _rijndael_class()(_derive_key(salt), block_size=_BLOCK_SIZE)
    out = bytearray()
    prev = iv
    for offset in range(0, len(payload), _BLOCK_SIZE):
        block = payload[offset:offset + _BLOCK_SIZE]
        plain = rijndael.decrypt(block)
        out.extend(a ^ b for a, b in zip(plain, prev))
        prev = block
    if out:
        last = out[-1]
        j = len(out) - 1
        while j >= 0 and out[j] == last:
            j -= 1
        remove_count = len(out) - 1 - j
        if 1 <= last <= _BLOCK_SIZE and remove_count == last:
            del out[-last:]
        else:
            raise ValueError("Padding check failed - the game's encryption format has probably changed.")
    return bytes(out).decode("utf-8")


def encrypt_progress(plain_text: str) -> str:
    data = plain_text.encode("utf-8")
    if len(data) % _BLOCK_SIZE == 0:
        data += b"\n"
    rijndael = _rijndael_class()(_derive_key(), block_size=_BLOCK_SIZE)
    out = bytearray()
    prev = _CIPHER_IV
    for offset in range(0, len(data), _BLOCK_SIZE):
        block = data[offset:offset + _BLOCK_SIZE]
        if len(block) < _BLOCK_SIZE:
            pad = _BLOCK_SIZE - len(block)
            block += bytes([pad]) * pad
        xored = bytes(a ^ b for a, b in zip(block, prev))
        enc = bytes(rijndael.encrypt(xored))
        out.extend(enc)
        prev = enc
    return base64.b64encode(_CIPHER_SALT + _CIPHER_IV + bytes(out)).decode("ascii")


# --------------------------------------------------------------------------
# Loading / saving whole save files
# --------------------------------------------------------------------------
def profile_slots(root: dict) -> list[str]:
    return [key for key in root if SLOT_RE.fullmatch(str(key)) and isinstance(root[key], dict)]


def load_save_text(text: str) -> tuple[dict, list[str]]:
    root = SJSONParser(text.lstrip("\ufeff")).parse()
    if not isinstance(root, dict):
        raise ValueError("This does not look like a Stone Story save (root is not an object).")
    slots = profile_slots(root)
    if not slots:
        raise ValueError("No save_file_N profiles found. Is this really a Stone Story save file?")
    loaded = copy.deepcopy(root)
    for slot in slots:
        profile = loaded[slot]
        if "progress_data" not in profile:
            continue
        progress = profile["progress_data"]
        if bool(profile.get("encrypted", False)):
            if not isinstance(progress, str):
                raise ValueError(f"{slot}: encrypted=true but progress_data is not a string")
            parsed = SJSONParser(decrypt_progress(progress)).parse()
            if not isinstance(parsed, dict):
                raise ValueError(f"{slot}: decrypted progress_data is not an object")
            profile["progress_data"] = parsed
        elif isinstance(progress, str):
            parsed = SJSONParser(progress).parse()
            if isinstance(parsed, dict):
                profile["progress_data"] = parsed
    return loaded, slots


def load_save(path: Path) -> tuple[dict, list[str]]:
    return load_save_text(Path(path).read_text(encoding="utf-8-sig"))


def looks_like_save(path: Path) -> bool:
    """Cheap check used by the automatic save finder."""
    try:
        if path.stat().st_size > 200 * 1024 * 1024:
            return False
        with open(path, "rb") as fh:
            head = fh.read(4096)
        return b"save_file_" in head
    except OSError:
        return False


def make_game_text(root: dict, slots: list[str]) -> str:
    exported = copy.deepcopy(root)
    for slot in slots:
        profile = exported[slot]
        progress = profile.get("progress_data")
        if isinstance(progress, dict):
            profile["progress_data"] = encrypt_progress(sjson_dumps(progress))
            profile["encrypted"] = True
    return sjson_dumps(exported) + "\n"


def validate_game_text(text: str, original: dict, slots: list[str]) -> None:
    parsed = SJSONParser(text).parse()
    if not isinstance(parsed, dict):
        raise ValueError("Verification failed: the written root is not an object")
    if profile_slots(parsed) != slots:
        raise ValueError("Verification failed: the profile list changed")
    for slot in slots:
        p = parsed[slot]
        if p.get("encrypted") is not True or not isinstance(p.get("progress_data"), str):
            raise ValueError(f"Verification failed: {slot} was not encrypted")
        restored = SJSONParser(decrypt_progress(p["progress_data"])).parse()
        if restored != original[slot].get("progress_data"):
            raise ValueError(f"Verification failed: data of {slot} differs after encryption")


def make_backup(path: Path) -> Path:
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = path.with_name(f"{path.name}.{stamp}.bak")
    shutil.copy2(path, backup)
    return backup


def write_save(root: dict, slots: list[str], destination: Path, backup_existing: bool) -> Path | None:
    """Encrypt, verify, back up the old file and atomically write the new one.

    Returns the backup path (or None). Nothing is written if verification fails.
    """
    destination = Path(destination)
    text = make_game_text(root, slots)
    validate_game_text(text, root, slots)
    destination.parent.mkdir(parents=True, exist_ok=True)
    backup = make_backup(destination) if backup_existing and destination.exists() else None
    fd, tmp_name = tempfile.mkstemp(prefix=destination.name + ".", suffix=".tmp", dir=str(destination.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, destination)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    return backup


def list_backups(path: Path) -> list[Path]:
    path = Path(path)
    return sorted(path.parent.glob(path.name + ".*.bak"), reverse=True)


# --------------------------------------------------------------------------
# Data helpers (paths into nested dict/list data)
# --------------------------------------------------------------------------
def get_at(data: Any, path: tuple) -> Any:
    for part in path:
        data = data[part]
    return data


def exists_at(data: Any, path: tuple) -> bool:
    try:
        get_at(data, path)
        return True
    except (KeyError, IndexError, TypeError):
        return False


def path_str(path: tuple) -> str:
    out = ""
    for part in path:
        out += f"[{part}]" if isinstance(part, int) else (("." if out else "") + str(part))
    return out


def kind_of(value: Any) -> str:
    """Stable internal type name: object, array, bool, null, number, text."""
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, bool):
        return "bool"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return "number"
    return "text"


def is_leaf(value: Any) -> bool:
    return not isinstance(value, (dict, list))


def iter_leaves(data: Any, path: tuple = ()) -> Iterator[tuple[tuple, Any]]:
    if isinstance(data, dict):
        for k, v in data.items():
            yield from iter_leaves(v, path + (k,))
    elif isinstance(data, list):
        for i, v in enumerate(data):
            yield from iter_leaves(v, path + (i,))
    else:
        yield path, data


def humanize(key: Any) -> str:
    """Turn technical keys into readable names: 'maxHealth' -> 'Max health'."""
    if isinstance(key, int):
        return f"#{key + 1}"
    s = str(key)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", s)
    s = re.sub(r"[_\-]+", " ", s).strip()
    if not s:
        return str(key)
    words = s.split()
    words = [words[0][:1].upper() + words[0][1:]] + [
        w if (w.isupper() and len(w) > 1) else w.lower() for w in words[1:]
    ]
    return " ".join(words)


def diff(original: Any, current: Any, path: tuple = ()) -> list[tuple[str, tuple, Any, Any]]:
    """List differences as (change_type, path, old, new).

    change_type is one of: 'changed', 'added', 'removed'.
    """
    out: list[tuple[str, tuple, Any, Any]] = []
    if isinstance(original, dict) and isinstance(current, dict):
        for k in original:
            if k not in current:
                out.append(("removed", path + (k,), original[k], None))
            else:
                out.extend(diff(original[k], current[k], path + (k,)))
        for k in current:
            if k not in original:
                out.append(("added", path + (k,), None, current[k]))
    elif isinstance(original, list) and isinstance(current, list):
        for i in range(min(len(original), len(current))):
            out.extend(diff(original[i], current[i], path + (i,)))
        for i in range(len(current), len(original)):
            out.append(("removed", path + (i,), original[i], None))
        for i in range(len(original), len(current)):
            out.append(("added", path + (i,), None, current[i]))
    else:
        same = (type(original) is type(current) and original == current)
        if not same:
            out.append(("changed", path, original, current))
    return out


def parse_typed(kind: str, raw: str) -> Any:
    """Convert user text to a value of the given kind. Raises ValueError."""
    if kind == "text":
        return raw
    if kind == "number":
        s = raw.strip().replace(",", ".").replace(" ", "")
        if s == "":
            raise ValueError("empty")
        try:
            if re.fullmatch(r"[-+]?\d+", s):
                return int(s)
            val = float(s)
        except ValueError:
            raise ValueError("not a number") from None
        if not math.isfinite(val):
            raise ValueError("not finite")
        return val
    if kind == "bool":
        v = raw.strip().lower()
        if v in ("true", "yes", "1", "да"):
            return True
        if v in ("false", "no", "0", "нет"):
            return False
        raise ValueError("bool")
    if kind == "null":
        return None
    if kind in ("object", "array"):
        val = json.loads(raw)
        if kind == "object" and not isinstance(val, dict):
            raise ValueError("object")
        if kind == "array" and not isinstance(val, list):
            raise ValueError("array")
        return val
    raise ValueError("unknown kind")


# --------------------------------------------------------------------------
# Undo / redo
# --------------------------------------------------------------------------
@dataclass
class Op:
    """One reversible edit on a profile."""
    slot: str
    kind: str            # 'set' | 'add' | 'delete'
    path: tuple
    old: Any = None      # previous value (set / delete)
    new: Any = None      # new value (set / add)
    index: int = -1      # position inside parent (delete / add into dict)
    label: str = ""
    group: int | None = None   # ops sharing a group are undone/redone together


def _insert_at_position(parent: dict, key: str, value: Any, index: int) -> None:
    items = list(parent.items())
    if index < 0 or index > len(items):
        index = len(items)
    items.insert(index, (key, value))
    parent.clear()
    parent.update(items)


class History:
    """Undo/redo stack operating on a loaded save (root dict)."""

    MAX_STEPS = 2000

    def __init__(self, root: dict):
        self.root = root
        self.undo_stack: list[Op] = []
        self.redo_stack: list[Op] = []
        self._group_counter = 0

    def new_group(self) -> int:
        self._group_counter += 1
        return self._group_counter

    def reset(self, root: dict) -> None:
        self.root = root
        self.undo_stack.clear()
        self.redo_stack.clear()

    # --- doing ---
    def set_value(self, slot: str, path: tuple, new: Any, label: str = "", group: int | None = None) -> bool:
        parent = get_at(self.root[slot], path[:-1])
        old = parent[path[-1]]
        if type(old) is type(new) and old == new:
            return False
        parent[path[-1]] = copy.deepcopy(new)
        self._push(Op(slot, "set", path, old=copy.deepcopy(old), new=copy.deepcopy(new),
                      label=label, group=group))
        return True

    def add_item(self, slot: str, parent_path: tuple, key: Any, value: Any, label: str = "",
                 group: int | None = None) -> tuple:
        parent = get_at(self.root[slot], parent_path)
        if isinstance(parent, dict):
            if key in parent:
                raise KeyError(key)
            parent[key] = copy.deepcopy(value)
            path = parent_path + (key,)
        elif isinstance(parent, list):
            parent.append(copy.deepcopy(value))
            path = parent_path + (len(parent) - 1,)
        else:
            raise TypeError("Can only add into an object or array")
        self._push(Op(slot, "add", path, new=copy.deepcopy(value), index=len(parent) - 1, label=label, group=group))
        return path

    def delete_item(self, slot: str, path: tuple, label: str = "", group: int | None = None) -> None:
        parent = get_at(self.root[slot], path[:-1])
        key = path[-1]
        if isinstance(parent, dict):
            index = list(parent.keys()).index(key)
        elif isinstance(parent, list):
            index = key
        else:
            raise TypeError("Cannot delete here")
        old = parent.pop(key)
        self._push(Op(slot, "delete", path, old=copy.deepcopy(old), index=index, label=label, group=group))

    def _push(self, op: Op) -> None:
        self.undo_stack.append(op)
        self.redo_stack.clear()
        if len(self.undo_stack) > self.MAX_STEPS:
            del self.undo_stack[0]

    # --- undo / redo ---
    def undo(self) -> list[Op]:
        """Undo the last step (a whole group if it was a bulk edit)."""
        if not self.undo_stack:
            return []
        done = [self.undo_stack.pop()]
        while done[0].group is not None and self.undo_stack and self.undo_stack[-1].group == done[0].group:
            done.append(self.undo_stack.pop())
        for op in done:  # newest first
            self._reverse(op)
        self.redo_stack.extend(done)
        return done

    def redo(self) -> list[Op]:
        if not self.redo_stack:
            return []
        done = [self.redo_stack.pop()]
        while done[0].group is not None and self.redo_stack and self.redo_stack[-1].group == done[0].group:
            done.append(self.redo_stack.pop())
        for op in done:  # in the order they were originally applied
            self._forward(op)
        self.undo_stack.extend(reversed(done))
        return done

    def _reverse(self, op: Op) -> None:
        parent = get_at(self.root[op.slot], op.path[:-1])
        key = op.path[-1]
        if op.kind == "set":
            parent[key] = copy.deepcopy(op.old)
        elif op.kind == "add":
            if isinstance(parent, dict):
                parent.pop(key, None)
            else:
                parent.pop(key)
        elif op.kind == "delete":
            if isinstance(parent, dict):
                _insert_at_position(parent, key, copy.deepcopy(op.old), op.index)
            else:
                parent.insert(key, copy.deepcopy(op.old))

    def _forward(self, op: Op) -> None:
        parent = get_at(self.root[op.slot], op.path[:-1])
        key = op.path[-1]
        if op.kind == "set":
            parent[key] = copy.deepcopy(op.new)
        elif op.kind == "add":
            if isinstance(parent, dict):
                parent[key] = copy.deepcopy(op.new)
            else:
                parent.append(copy.deepcopy(op.new))
        elif op.kind == "delete":
            if isinstance(parent, dict):
                parent.pop(key, None)
            else:
                parent.pop(key)
