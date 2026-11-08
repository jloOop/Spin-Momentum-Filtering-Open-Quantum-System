"""Private, hash-pinned NumPy overlay. Never modify the shared PC2 environment."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, shutil, subprocess, sys, tempfile
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent

def cfg():
    return json.loads((PACKAGE/'CONFIG.json').read_text())

def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

def need(value, message):
    if not value: raise RuntimeError(message)

def file_hashes(root: Path):
    out={}
    for p in sorted(root.rglob('*')):
        need(not p.is_symlink(),f'Symlink in runtime overlay: {p}')
        if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':
            out[p.relative_to(root).as_posix()]=sha(p)
    return out

def manifest_path():return PACKAGE/'PREPARED/numpy_overlay_manifest.json'

def verify_overlay():
    c=cfg();overlay=PACKAGE/c['port']['numpy_overlay_relative'];mp=manifest_path()
    need(overlay.is_dir() and not overlay.is_symlink() and mp.is_file() and not mp.is_symlink(),
         'Private NumPy runtime is not installed; run the release installer first.')
    report=json.loads(mp.read_text())
    need(report['wheel_sha256']==c['port']['numpy_wheel_sha256'], 'Runtime wheel identity changed')
    need(report['files']==file_hashes(overlay), 'Installed private NumPy files changed')
    need(platform.python_version()==c['port']['base_python_version'], 'Unexpected PC2 Python interpreter version')
    return report

def cpu_probe(overlay: Path):
    c=cfg();env=os.environ.copy()
    env.update(PYTHONPATH=str(overlay),PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1')
    code=r'''
import json, pathlib, platform, numpy as np, scipy, scipy.linalg
expected=pathlib.Path(__import__('sys').argv[1]).resolve()
assert pathlib.Path(np.__file__).resolve().is_relative_to(expected), np.__file__
assert np.__version__=='2.4.2', np.__version__
assert scipy.__version__=='1.17.1', scipy.__version__
assert platform.python_version()=='3.11.5', platform.python_version()
a=np.array([[3.+0j,1.-.25j],[1.+.25j,4.+0j]],np.complex128)
x=np.array([1.+.2j,-.3+.4j]); b=a@x; y=scipy.linalg.solve(a,b)
r=float(np.linalg.norm(a@y-b)/np.linalg.norm(b)); assert r<1e-13
print(json.dumps({'passed':True,'python':platform.python_version(),'numpy':np.__version__,
 'numpy_file':np.__file__,'scipy':scipy.__version__,'cpu_linear_solve_relative_residual':r},sort_keys=True))
'''
    result=subprocess.run([c['python'],'-B','-c',code,str(overlay)],env=env,text=True,capture_output=True,timeout=180)
    need(result.returncode==0, 'Private-runtime CPU import/solve failed:\n'+result.stdout+result.stderr)
    return json.loads(result.stdout.strip().splitlines()[-1])

def install():
    c=cfg();need(platform.system()=='Linux' and platform.machine()=='x86_64','Install this runtime only on PC2 Linux x86_64')
    need(platform.python_version()==c['port']['base_python_version'],'Use the recorded PC2 Python 3.11.5 environment')
    need(PACKAGE==Path(c['project_root'])/c['package_name'],'Unexpected runtime installation directory')
    prepared=PACKAGE/'PREPARED';prepared.mkdir(exist_ok=True)
    need(not prepared.is_symlink(),'PREPARED cannot be a symlink')
    import fcntl
    with (prepared/'.runtime_install.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        overlay=PACKAGE/c['port']['numpy_overlay_relative']
        if overlay.exists() or overlay.is_symlink():
            verify_overlay();cpu_probe(overlay)
            print('PASS_TASK09_PC2_NUMPY_242_PRIVATE_RUNTIME_ALREADY_VERIFIED');return
        need(not manifest_path().exists(), 'Manifest exists without its runtime; inspect instead of overwriting')
        wheel=PACKAGE/'WHEELS'/c['port']['numpy_wheel_name']
        need(wheel.is_file() and not wheel.is_symlink(),'Pinned Linux NumPy wheel missing; run Mac_01_Verify_and_Upload.sh')
        need(sha(wheel)==c['port']['numpy_wheel_sha256'],'NumPy wheel SHA mismatch')
        stage=Path(tempfile.mkdtemp(prefix='.numpy_install_',dir=prepared))
        command=[c['python'],'-B','-m','pip','--isolated','install','--disable-pip-version-check',
                 '--no-index','--no-deps','--no-compile','--target',str(stage),str(wheel)]
        env=os.environ.copy();env.pop('PYTHONPATH',None)
        env.update(PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1')
        p=subprocess.run(command,env=env,text=True,capture_output=True,timeout=600)
        (prepared/'numpy_install.log').write_text(p.stdout+p.stderr)
        need(p.returncode==0,'Private NumPy installation failed; see PREPARED/numpy_install.log')
        test=cpu_probe(stage)
        need(not overlay.exists(),'Runtime destination appeared during installation')
        stage.rename(overlay)
        test=cpu_probe(overlay)
        report={'schema':'task09-pc2-private-numpy-runtime-v1','passed':True,
          'base_environment_modified':False,'wheel_name':wheel.name,'wheel_sha256':sha(wheel),
          'overlay_path':str(overlay),'python':c['python'],'cpu_probe':test,
          'files':file_hashes(overlay)}
        tmp=manifest_path().with_suffix('.tmp');tmp.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
        tmp.replace(manifest_path());verify_overlay()
        print('PASS_TASK09_PC2_NUMPY_242_PRIVATE_RUNTIME')

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['install','verify']);a=p.parse_args()
    if a.action=='install':install()
    else:
        verify_overlay();print('PASS_TASK09_PC2_NUMPY_242_PRIVATE_RUNTIME_HASHES')
if __name__=='__main__':main()
