"""Bind this batch allocation to its guarded submission, before any scientific import."""
import argparse,re
from pathlib import Path
import pcommon as q
from verify import verify

def bind(job):
    q.need(job.isdecimal(),'Invalid batch job ID')
    verify()
    work=q.P/'work';intent=q.read(work/'submission_intent.json')
    q.need(intent.get('command')==['sbatch','--parsable','--chdir='+str(q.P),str(q.P/'run_gpu.sh')],
           'Batch command does not match guarded intent')
    q.need(intent.get('release_manifest_sha256')==q.sha(q.P/'SHA256SUMS.txt'),'Intent release hash mismatch')
    q.need(intent.get('parent')==str(q.PARENT) and intent.get('parent_manifest_sha256')==q.Q['parent_pins']['checkpoint_manifest.json'],
           'Wrong intended parent')
    q.need(intent.get('accepted_bounded_continuation')==q.Q['acknowledgement'] and intent.get('bounded_continuation') is True and intent.get('bounded_target_step')==q.Q['end_step'],'Wrong bounded intent')
    qualification=q.qualification_evidence();q.need(intent.get('qualified_source')==qualification,'Qualification evidence changed')
    # This also closes the legitimate race where Slurm starts before sbatch returns the receipt.
    control=q.command(['scontrol','show','job',job,'-o'])
    values=dict(re.findall(r'(?:^|\s)([A-Za-z0-9_]+)=(\S+)',control))
    for key,expected in [('JobId',job),('JobName','T09P8KL2'),('Command',str(q.P/'run_gpu.sh')),('WorkDir',str(q.P))]:
        q.need(values.get(key)==expected,'Allocated '+key+' differs from submission')
    q.need(values.get('UserId','').split('(')[0]=='hpcaljo1' and values.get('JobState')=='RUNNING',
           'Unexpected allocated user or state')
    receipt=work/'receipt.json'
    if receipt.exists():
        r=q.read(receipt);q.need(r.get('job_id')==job and all(r.get(k)==v for k,v in intent.items()),'Wrong batch receipt')
    run=work/'runtime'/('job_'+job);dest=run/'SUBMISSION';dest.mkdir(exist_ok=True)
    for f in [work/'submission_intent.json']+([receipt] if receipt.exists() else []):
        q.need(not f.is_symlink(),'Linked submission record')
        (dest/f.name).write_bytes(f.read_bytes())
    (dest/'scontrol_job.txt').write_text(control)
    q.write(run/'startup_binding.json',{'passed':True,'job_id':job,'receipt_present':receipt.exists(),
             'live_job_identity_verified':True,'package':str(q.P),'production_authorized':False})
    print('PASS_KL2_BATCH_BINDING job='+job+' parent_step=7600 bounded_target=7650')
    return True

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--job',required=True);a=p.parse_args();bind(a.job)
