"""Identity of the sole immutable recovery CONFIG.json; no numerical operations."""
from __future__ import annotations
from pathlib import Path
from archive_tools import digest_file, plain_json, require
from common import PACKAGE_DIR


def configuration_identity(cfg: dict, *, package: Path = PACKAGE_DIR) -> dict:
    path = package / 'CONFIG.json'
    require(path.is_file() and not path.is_symlink(), 'Canonical recovery CONFIG.json missing or symlink')
    recorded = plain_json(path.read_bytes())
    require(recorded.get('phase') == 'recovery' and cfg == recorded,
            'Canonical recovery configuration differs from loaded configuration')
    identity = plain_json((package / 'PARENT_IDENTITY.json').read_bytes())
    actual = digest_file(path)
    require(actual == identity['new_configuration_sha256'], 'Canonical recovery config hash mismatch')
    return {'configuration_file': 'CONFIG.json', 'configuration_sha256': actual}


def verify_smoke_configuration(smoke: dict, cfg: dict, *, package: Path = PACKAGE_DIR) -> dict:
    identity = configuration_identity(cfg, package=package)
    require(smoke.get('phase') == 'recovery', 'Smoke report has wrong phase')
    for key, value in identity.items():
        require(smoke.get(key) == value, 'Smoke report configuration binding mismatch: ' + key)
    require(smoke.get('source_driver_sha256') == digest_file(package / 'half_rate_continue.py'),
            'Smoke report driver hash mismatch')
    return identity
