"""One encrypted file per event: the current book, saved versions and a change log.

File layout: b'TBK1' + 16-byte salt + 12-byte nonce + AES-256-GCM(JSON). The key comes from the
password via scrypt and is kept only in memory while the file is open. Nothing is sent anywhere.
"""
from __future__ import annotations

import json
import os
import secrets
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .model import BookError, new_book, normalize

MAGIC = b'TBK1'
SUFFIX = '.ticketbook'


class WrongPassword(BookError):
    pass


def _key(password: str, salt: bytes) -> bytes:
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    if not password:
        raise BookError('请输入密码')
    return Scrypt(salt=salt, length=32, n=2 ** 15, r=8, p=1).derive(password.encode('utf-8'))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


class BookFile:
    """An open event file. Every change is written to disk at once (atomic replace)."""

    def __init__(self, path: Path, key: bytes, salt: bytes, data: dict):
        self.path, self._key, self._salt, self.data = Path(path), key, salt, data

    # --- opening and saving -------------------------------------------------
    @classmethod
    def create(cls, path, password: str, book: dict | None = None) -> 'BookFile':
        path = Path(path)
        if path.suffix != SUFFIX:
            path = path.with_name(path.name + SUFFIX)
        if path.exists():
            raise BookError(f'文件已存在：{path.name}')
        salt = secrets.token_bytes(16)
        data = {'book': normalize(book or new_book()), 'versions': [], 'log': []}
        f = cls(path, _key(password, salt), salt, data)
        f.log('创建文件')
        return f

    @classmethod
    def open(cls, path, password: str) -> 'BookFile':
        from cryptography.exceptions import InvalidTag
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        raw = Path(path).read_bytes()
        if raw[:4] != MAGIC:
            raise BookError('不是票务总表文件')
        salt, nonce, body = raw[4:20], raw[20:32], raw[32:]
        key = _key(password, salt)
        try:
            plain = AESGCM(key).decrypt(nonce, body, MAGIC)
        except InvalidTag as exc:
            raise WrongPassword('密码不正确，或文件已损坏') from exc
        data = json.loads(plain.decode('utf-8'))
        data['book'] = normalize(data['book'])
        data.setdefault('versions', [])
        data.setdefault('log', [])
        return cls(Path(path), key, salt, data)

    def save(self):
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        nonce = secrets.token_bytes(12)
        body = AESGCM(self._key).encrypt(nonce, json.dumps(self.data, ensure_ascii=False).encode('utf-8'), MAGIC)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix='.' + self.path.name, suffix='.tmp')
        try:
            with os.fdopen(fd, 'wb') as out:
                out.write(MAGIC + self._salt + nonce + body)
                out.flush()
                os.fsync(out.fileno())
            os.replace(tmp, self.path)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise

    # --- content --------------------------------------------------------------
    @property
    def book(self) -> dict:
        return self.data['book']

    def log(self, action: str, detail: str = ''):
        self.data['log'].append({'at': _now(), 'action': action, 'detail': detail})
        self.save()

    def replace_book(self, book: dict, action: str, detail: str = ''):
        self.data['book'] = normalize(book)
        self.log(action, detail)

    def save_version(self, label: str) -> dict:
        version = {'id': uuid.uuid4().hex[:12], 'label': label or '未命名版本', 'created_at': _now(), 'book': json.loads(json.dumps(self.book))}
        self.data['versions'].append(version)
        self.log('保存版本', version['label'])
        return {k: v for k, v in version.items() if k != 'book'}

    def version(self, version_id: str) -> dict:
        for v in self.data['versions']:
            if v['id'] == version_id:
                return v
        raise BookError('找不到版本：' + version_id)

    def versions(self) -> list[dict]:
        return [{k: v for k, v in item.items() if k != 'book'} for item in self.data['versions']]

    def restore(self, version_id: str) -> dict:
        target = self.version(version_id)
        self.save_version('恢复前自动保存')
        self.replace_book(json.loads(json.dumps(target['book'])), '恢复版本', target['label'])
        return self.book

    def change_password(self, old: str, new: str):
        if _key(old, self._salt) != self._key:
            raise WrongPassword('原密码不正确')
        self._salt = secrets.token_bytes(16)
        self._key = _key(new, self._salt)
        self.log('修改密码')
