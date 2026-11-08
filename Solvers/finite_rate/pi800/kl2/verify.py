from pathlib import Path
import hashlib
P=Path(__file__).resolve().parent
def verify(root=P):
 root=Path(root);seen=set()
 for line in (root/'SHA256SUMS.txt').read_text().splitlines():
  want,name=line.split('  ',1);rel=Path(name)
  if rel.is_absolute() or '..' in rel.parts or name in seen or len(want)!=64:raise RuntimeError('Invalid release manifest')
  seen.add(name);f=root/name
  if f.is_symlink() or not f.is_file():raise RuntimeError('Missing/unsafe file: '+name)
  with f.open('rb') as h:got=hashlib.file_digest(h,'sha256').hexdigest()
  if got!=want:raise RuntimeError('Release hash mismatch: '+name)
 actual={str(f.relative_to(root)) for f in root.rglob('*') if f.is_file() and f.relative_to(root).parts[0] not in ('work','__pycache__') and '__pycache__' not in f.parts and f.suffix!='.pyc'}
 if actual!=seen|{'SHA256SUMS.txt'}:raise RuntimeError('Unexpected or missing static file: '+str(actual^(seen|{'SHA256SUMS.txt'})))
 print('PASS_PI800_KL2_RELEASE files='+str(len(seen)));return len(seen)
if __name__=='__main__':verify()
