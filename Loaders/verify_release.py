#!/usr/bin/env python3
"""Verify release packaging and saved-array schemas. This is not physics certification."""
import argparse,ast,csv,hashlib,io,json,re,sys,zipfile
from pathlib import Path
import numpy as np
REPO=Path(__file__).resolve().parents[1]
PRIVATE=re.compile(r'/(?:Users/[^/\s\'"\x60<>]+|home/[^/\s\'"\x60<>]+|scratch|gpfs|lustre|work|projects|pfs|mnt/data)(?:/[^\s\'"\x60<>|,;)\]}]+)*')
PC2=re.compile(r'(?<![\w.-])/\x70c2/')
SECRET=[re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{35,})'),re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),re.compile(rb'\bAKIA[A-Z0-9]{16}\b'),re.compile(rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{30,}'),re.compile(rb'\bxox[baprs]-[A-Za-z0-9-]{20,}')]
TEXT={'.py','.json','.md','.txt','.csv','.tsv','.sh','.patch','.diff','.cff','.tex','.yaml','.yml'}
def files():
    for base in ['Solvers','Loaders','data','paper']:
        for p in (REPO/base).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:
                yield p
    for p in REPO.iterdir():
        if p.is_file():yield p
def sha(data):return hashlib.sha256(data).hexdigest()
def payload(path):
    if '!/' in path:
        outer,member=path.split('!/',1)
        with zipfile.ZipFile(REPO/outer) as z:return z.read(member)
    return (REPO/path).read_bytes()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--write-schemas',type=Path)
    args=parser.parse_args()
    errors=[];schemas={};seen=set();archive_count=0
    manifest=list(csv.DictReader((REPO/'data/provenance/release_manifest.csv').open()))
    destinations={}
    for row in manifest:
        p=row['distributed_path'];h=row['distributed_sha256']
        if p in destinations and destinations[p]!=h:errors.append('conflicting manifest identity: '+p)
        destinations[p]=h
    for p,h in destinations.items():
        try:
            b=payload(p)
            if sha(b)!=h:errors.append('payload hash mismatch: '+p)
        except (OSError,KeyError,zipfile.BadZipFile):errors.append('missing/unreadable manifest payload: '+p)
    def inspect(b,path):
        nonlocal archive_count
        if any(rx.search(b) for rx in SECRET):
            errors.append('potential secret pattern (value suppressed): '+path)
        suffix=Path(path).suffix.lower()
        if suffix in TEXT or Path(path).name in ('SHA256SUMS','LICENSE','COPYING'):
            try:
                t=b.decode()
                if PRIVATE.search(t) or PC2.search(t):errors.append('private absolute path: '+path)
                if suffix=='.py':ast.parse(t,filename=path)
                if suffix=='.json':json.loads(t)
            except (UnicodeDecodeError,SyntaxError,json.JSONDecodeError) as ex:errors.append('text parse failure: '+path+' ('+type(ex).__name__+')')
        if suffix=='.zip':
            archive_count+=1
            try:
                with zipfile.ZipFile(io.BytesIO(b)) as z:
                    if z.testzip():errors.append('ZIP CRC failure: '+path)
                    for info in z.infolist():
                        if info.is_dir():continue
                        if info.filename.startswith('/') or '..' in Path(info.filename).parts:errors.append('unsafe archive member: '+path)
                        inspect(z.read(info),path+'!/'+info.filename)
            except zipfile.BadZipFile:errors.append('invalid ZIP: '+path)
        elif suffix in ('.npy','.npz'):
            try:
                with io.BytesIO(b) as buf:
                    loaded=np.load(buf,allow_pickle=False)
                    data={k:loaded[k] for k in loaded.files} if suffix=='.npz' else {'array':loaded}
                    schemas[path]={}
                    for name,a in data.items():
                        if a.dtype.hasobject:raise ValueError('object dtype')
                        schemas[path][name]={'shape':list(a.shape),'dtype':str(a.dtype)}
                        if a.dtype.kind in 'US':
                            if any(PRIVATE.search(str(v)) or PC2.search(str(v)) for v in a.flat):errors.append('private path in string array: '+path+'/'+name)
                    if suffix=='.npz':loaded.close()
            except Exception as ex:errors.append('unsafe/unreadable numerical container: '+path+' ('+type(ex).__name__+')')
    listed=list(files())
    for p in listed:
        rel=p.relative_to(REPO).as_posix()
        if rel in seen:continue
        seen.add(rel)
        inspect(p.read_bytes(),rel)
        # Self-referential release manifest is authenticated by the Git commit, not itself.
        if rel!='data/provenance/release_manifest.csv' and rel not in destinations:
            errors.append('unmanifested release file: '+rel)
    for row in manifest:
        if row['distributed_path'].endswith(('.npz','.npy')) and row['source_sha256']!=row['distributed_sha256']:
            errors.append('numerical source bytes changed: '+row['distributed_path'])
    index=list(csv.DictReader((REPO/'data/canonical_response/case_index.csv').open()))
    expected={x+str(i) for x in 'DUP' for i in range(1,6)}|{'D2-I','U2-I','P2-I'}
    if {r['matrix_id'] for r in index}!=expected or len(index)!=18:errors.append('canonical role coverage')
    register={r['matrix_id']:r for r in csv.DictReader((REPO/'data/canonical_response/CANONICAL_CASE_MASTER_TABLE.csv').open())}
    for row in index:
        if row['original_sha256']!=register[row['matrix_id']]['case_zip_sha256']:errors.append('canonical source identity '+row['matrix_id'])
        if sha(payload(row['distributed_path']))!=row['distributed_sha256']:errors.append('canonical distributed identity '+row['matrix_id'])
    det=list(csv.DictReader((REPO/'data/detector_controls/case_index.csv').open()))
    if len(det)!=16:errors.append('detector cohort coverage')
    # Check portable primary documentation only; archived reports retain historical references.
    for name in ['README.md','PROJECT_SCOPE.md','REPRODUCING.md','paper/README.md','data/finite_rate/README.md','data/finite_rate/poster_provenance/README.md']:
        p=REPO/name
        if not p.exists():errors.append('missing documentation '+name);continue
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',p.read_text()):
            target=target.split('#')[0].split(' "')[0]
            if not target or '://' in target or target.startswith('mailto:'):continue
            if not (p.parent/target).exists():errors.append('broken primary-doc link: '+name+' -> '+target)
    if args.write_schemas:
        args.write_schemas.parent.mkdir(parents=True,exist_ok=True)
        args.write_schemas.write_text(json.dumps(schemas,indent=2,sort_keys=True)+'\n')
    result={'scope':'release integrity, privacy patterns, syntax, declared identities and safe saved-array schemas; not scientific acceptance',
            'passed':not errors,'failed':errors,'payload_files':len(listed),'payload_bytes':sum(p.stat().st_size for p in listed),
            'manifest_records':len(manifest),'archive_count':archive_count,'numerical_containers':len(schemas),
            'canonical_roles':len(index),'detector_controls':len(det),
            'not_run':['production simulations','original full Task06 aggregate re-audit','Task09 full spectral/factor re-audit','historical state restart']}
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return 0 if not errors else 1
if __name__=='__main__':sys.exit(main())
