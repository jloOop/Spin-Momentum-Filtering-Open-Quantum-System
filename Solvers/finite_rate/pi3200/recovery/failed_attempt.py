"""Read-only check that the superseded v1 attempt failed before the driver.

The v1 runtime is failure provenance only, never the numerical parent.
No file in that attempt is created, deleted, unlocked, renamed, or rewritten.
"""
from __future__ import annotations
from pathlib import Path
from archive_tools import require, digest_file, plain_json
from common import PACKAGE_DIR

FAILED_JOB = '3464089'
OLD_PACKAGE = 'Task09_Pi3200_11845_To12000_PC2_H100_2026-09-27_v1'
OLD_RUNTIME = 'Task09_Pi3200_11845_To12000_v1_Run_' + FAILED_JOB
OLD_PREFIX = 'Task09_Pi3200_11845_To12000_v1_Result_' + FAILED_JOB


def verify_failed_attempt(root: Path, *, package: Path = PACKAGE_DIR) -> dict:
    root = Path(root)
    old = root / OLD_PACKAGE
    runtime = root / OLD_RUNTIME
    hashes = {}

    def load(path: Path):
        require(path.is_file() and not path.is_symlink(), 'Failed-attempt evidence missing/unsafe: ' + str(path))
        require(path.resolve().is_relative_to(root.resolve()), 'Failed-attempt evidence escapes project root')
        hashes[path.relative_to(root).as_posix()] = digest_file(path)
        return plain_json(path.read_bytes())

    cfg = load(old / 'CONFIG.json')
    require(hashes[(old / 'CONFIG.json').relative_to(root).as_posix()] ==
            digest_file(package / 'RECOVERY_V1_PROVENANCE/CONFIG.json'), 'Failed-attempt v1 config changed')
    receipt = load(old / 'PREPARED/submission_recovery_receipt.json')
    require(str(receipt.get('job_id')) == FAILED_JOB and receipt.get('package_name') == OLD_PACKAGE
            and receipt.get('stage') == 'recovery', 'Wrong v1 failure receipt')
    status = load(runtime / 'pipeline_status.json')
    codes = load(runtime / 'recovery/return_codes.json')
    expected = {'device': 0, 'preflight': 0, 'smoke': 1}
    require(str(status.get('job_id')) == FAILED_JOB and status.get('return_code') == 1
            and status.get('phase_codes', {}).get('recovery') == expected and codes == expected,
            'V1 attempt not the recorded pre-driver smoke failure')
    smoke = load(runtime / 'recovery/platform_bridge_report.json')
    require(smoke.get('passed') is False and smoke.get('authoritative_steps_advanced') == 0
            and 'CONFIGS/recovery.json' in smoke.get('message', '')
            and 'FileNotFoundError' in smoke.get('traceback', ''), 'Unexpected v1 smoke failure')
    ready = load(root / (OLD_PREFIX + '_READY.json'))
    require(str(ready.get('job_id')) == FAILED_JOB and ready.get('stage') == 'recovery'
            and ready.get('return_code') == 1 and ready.get('last_persisted_steps') == {},
            'V1 failure finalization is not the recorded no-output case')
    output = root / cfg['output_relative']
    require(not output.exists() and not output.is_symlink(), 'V1 recovery output exists; review before making another branch')
    solver_log = runtime / 'recovery/solver.txt'
    require(not solver_log.exists() and not solver_log.is_symlink(), 'V1 solver log exists; no blind retry authorized')
    return {'passed': True, 'failed_job_id': FAILED_JOB, 'authoritative_steps_advanced': 0,
            'not_a_restart_parent': True, 'failed_attempt_files_unchanged': True, 'file_sha256': hashes}
