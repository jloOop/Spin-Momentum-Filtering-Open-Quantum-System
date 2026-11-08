#!/usr/bin/env python3
"""Bounded CPU reconstruction from bundled scientific arrays; never runs a solver."""
from pathlib import Path
import argparse, importlib, json, os
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--group',choices=['canonical','finite-rate','extensions','foundations','all'],required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    repo=Path(__file__).resolve().parents[1]
    output=args.output.resolve()
    build=(repo/'build').resolve()
    if output!=build and build not in output.parents:
        parser.error('Outputs must be inside this checkout build/ directory.')
    output.mkdir(parents=True,exist_ok=True)
    os.environ.setdefault('MPLBACKEND','Agg')
    os.environ.setdefault('MPLCONFIGDIR',str(output/'.matplotlib'))
    names=['canonical','finite-rate','extensions','foundations'] if args.group=='all' else [args.group]
    results={}
    for name in names:
        module=importlib.import_module(name.replace('-','_'))
        results[name]=module.run(repo,output/name if args.group=='all' else output)
    print(json.dumps({'groups':names,'output':str(args.output),'completed':True},indent=2))
if __name__=='__main__':
    main()
