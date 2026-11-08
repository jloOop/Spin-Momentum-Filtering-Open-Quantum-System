"""Read-only, bounded archive utilities. No archived Python is imported or run."""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile
import numpy as np

class IntegrityError(RuntimeError):
    pass

class MissingInput(RuntimeError):
    pass

def require(condition: bool, message: str) -> None:
    if not condition:
        raise IntegrityError(message)

def relative_name(name: str) -> str:
    require(isinstance(name, str) and bool(name), 'Empty/non-string relative path')
    p = PurePosixPath(name)
    require(not p.is_absolute() and '..' not in p.parts and '\\' not in name
            and '\x00' not in name and ':' not in p.parts[0], f'Unsafe path: {name}')
    return str(p)

def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def plain_json(data: bytes):
    def pairs(items):
        out = {}
        for k, v in items:
            require(k not in out, f'Duplicate JSON key: {k}')
            out[k] = v
        return out
    def bad_constant(s):
        raise IntegrityError(f'Nonfinite JSON constant: {s}')
    return json.loads(data, object_pairs_hook=pairs, parse_constant=bad_constant)

def sha_value(value) -> str:
    if isinstance(value, dict):
        value = value.get('sha256')
    require(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None,
            'Malformed SHA-256')
    return value

class Archive:
    """All names are relative to one verified archive root; reads are bounded."""
    def __init__(self, path: Path, expected_sha: str | None = None):
        self.path = Path(path)
        if not self.path.is_file():
            raise MissingInput(f'Archive absent: {self.path}')
        self.sha256 = digest_file(self.path)
        if expected_sha is not None:
            require(self.sha256 == sha_value(expected_sha), f'Outer SHA mismatch: {self.path}')
        self.z = zipfile.ZipFile(self.path)
        self._cache = {}
        try:
            infos = self.z.infolist()
            names = [x.filename for x in infos]
            require(len(names) == len(set(names)), 'Duplicate ZIP members')
            require(len(names) <= 100000, 'Archive member-count limit exceeded')
            require(sum(i.file_size for i in infos) <= 16 * 1024**3,
                    'Archive uncompressed size exceeds 16 GiB audit limit')
            roots = {relative_name(x).split('/')[0] for x in names}
            require(len(roots) == 1, f'Expected one ZIP root: {roots}')
            self.root = next(iter(roots))
            for info in infos:
                relative_name(info.filename)
                require(not stat.S_ISLNK(info.external_attr >> 16), 'ZIP symlink prohibited')
                require(not info.flag_bits & 1, 'Encrypted ZIP member prohibited')
            require(self.z.testzip() is None, 'ZIP CRC failed')
            prefix = self.root + '/'
            self.members = {i.filename[len(prefix):]: i for i in infos
                            if i.filename.startswith(prefix) and not i.is_dir()}
            require(self.members, 'Empty result archive')
        except Exception:
            self.z.close()
            raise

    def close(self):
        self.z.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def has(self, name):
        return relative_name(name) in self.members

    def read(self, name: str, limit: int = 256 * 1024**2) -> bytes:
        name = relative_name(name)
        require(name in self.members, f'Archive member missing: {name}')
        require(self.members[name].file_size <= limit, f'Member exceeds read limit: {name}')
        return self.z.read(self.root + '/' + name)

    def json(self, name):
        return plain_json(self.read(name))

    def npz(self, name):
        data = self.read(name)
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            require(sum(i.file_size for i in z.infolist()) <= 512 * 1024**2,
                    f'NPZ expanded size limit: {name}')
            require(len(z.namelist()) == len(set(z.namelist())), f'Duplicate NPZ fields: {name}')
        with np.load(io.BytesIO(data), allow_pickle=False) as a:
            return {k: np.asarray(a[k]) for k in a.files}

    def digest(self, name):
        name = relative_name(name)
        require(name in self.members, f'Hash target absent: {name}')
        if name not in self._cache:
            h = hashlib.sha256()
            with self.z.open(self.root + '/' + name) as f:
                for b in iter(lambda: f.read(8 * 1024 * 1024), b''):
                    h.update(b)
            self._cache[name] = h.hexdigest()
        return self._cache[name]

    def manifest(self, name, base=''):
        obj = self.json(name)
        files = obj.get('files')
        require(isinstance(files, dict) and bool(files), f'Malformed/empty manifest: {name}')
        for rel, sha in files.items():
            rel = relative_name(rel)
            require(self.digest(base + rel) == sha_value(sha), f'Manifest mismatch: {base}{rel}')
        return len(files)

    def sums(self, name, base=''):
        seen = set()
        for line in self.read(name).decode('utf-8').splitlines():
            if not line.strip():
                continue
            expected, rel = line.split(maxsplit=1)
            rel = relative_name(rel.lstrip('*'))
            require(rel not in seen, f'Duplicate SHA256SUMS entry: {rel}')
            seen.add(rel)
            require(self.digest(base + rel) == sha_value(expected), f'SHA256SUMS mismatch: {rel}')
        require(seen, 'Empty SHA256SUMS')
        return len(seen)

    def unique_suffix(self, suffix: str, required=True):
        names = [n for n in self.members if n == suffix or n.endswith('/' + suffix)]
        if not names and not required:
            return None
        require(len(names) == 1, f'Expected one {suffix}: {names}')
        return names[0]

    def export(self, names, dest: Path):
        dest.mkdir(parents=True, exist_ok=False)
        for name in sorted(set(names)):
            name = relative_name(name)
            path = dest / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as f:
                f.write(self.read(name))

def verify_local_package(package: Path) -> int:
    seen = set()
    for line in (package / 'SHA256SUMS.txt').read_text().splitlines():
        if not line.strip():
            continue
        expected, name = line.split(maxsplit=1)
        name = relative_name(name.lstrip('*'))
        require(name not in seen, f'Duplicate package checksum: {name}')
        seen.add(name)
        target = package / name
        require(target.resolve().is_relative_to(package.resolve()) and not target.is_symlink(),
                f'Package path escape/symlink: {name}')
        require(target.is_file() and digest_file(target) == sha_value(expected),
                f'Local package checksum mismatch: {name}')
    require(bool(seen), 'Empty local package manifest')
    return len(seen)
