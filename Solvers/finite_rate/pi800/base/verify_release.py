"""Standard-library integrity checks. Safe on login nodes; no GPU imports."""
from pathlib import Path
import hashlib,json,sys,stat
P=Path(__file__).resolve().parent

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
    return h.hexdigest()

def verify(p=P):
    p=Path(p);lines=(p/'SHA256SUMS.txt').read_text().splitlines();seen=set()
    for line in lines:
        want,name=line.split('  ',1);rel=Path(name)
        if len(want)!=64 or rel.is_absolute() or '..' in rel.parts or name in seen:raise RuntimeError('Unsafe manifest')
        seen.add(name);f=p/rel
        if f.is_symlink() or not f.is_file() or digest(f)!=want:raise RuntimeError('Release hash mismatch: '+name)
    if not {'CONFIG.json','pi800_run.py','fresh_inputs.py','checkpoints.py','audit_pi800.py','run_gpu.sh','submit.py'}<=seen:raise RuntimeError('Missing required release files')
    actual={str(f.relative_to(p)) for f in p.rglob('*') if f.is_file() and f.relative_to(p).parts[0] not in ('work','PREPARED','__pycache__') and '__pycache__' not in f.parts and f.suffix!='.pyc'}
    if actual != seen|{'SHA256SUMS.txt'}:raise RuntimeError('Unmanifested or missing static release payload: '+repr(sorted(actual ^ (seen|{'SHA256SUMS.txt'}))))
    print(f'PASS_PI800_RELEASE_HASHES files={len(seen)}');return len(seen)
if __name__=='__main__':verify(Path(sys.argv[1]) if len(sys.argv)>1 else P)
