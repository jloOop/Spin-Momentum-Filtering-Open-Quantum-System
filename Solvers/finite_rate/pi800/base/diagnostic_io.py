"""Persistence-only optimization. All GPU operations, checks and telemetry remain.

Completed per-step detector telemetry is still written in full before returning.
Only repeated in-progress snapshots are throttled. Pool-flush records are journaled
once and the legacy cumulative JSON is materialized at checkpoints/finalization.
No solver, trace, Kraus, Gram, eigensolver, rank tolerance or pool operation changes.
"""
from __future__ import annotations
import ast,json,os,time
from pathlib import Path
from common import write_json,json_value,PACKAGE_DIR
from archive_tools import require


def verify_rank_optimization():
    """Verify that the alternate function differs only by the reviewed conversion."""
    source=(PACKAGE_DIR/'spectral_components.py').read_text()
    node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='build_rank_ladder')
    original=ast.get_source_segment(source,node)
    before='''    cumulative = np.asarray(
        [math.fsum(float(value) for value in values[:count]) for count in range(1, support_rank + 1)],'''
    after='''    scalar_values = values.tolist()  # Same binary64-to-Python-float conversion, performed once.
    cumulative = np.asarray(
        [math.fsum(scalar_values[:count]) for count in range(1, support_rank + 1)],'''
    require(original.count(before)==1,'Frozen rank-ladder source changed')
    proposed=(PACKAGE_DIR/'fast_rank_ladder.py').read_text()
    function=next(n for n in ast.parse(proposed).body if isinstance(n,ast.FunctionDef) and n.name=='build_rank_ladder')
    expected=ast.parse(original.replace(before,after)).body[0]
    require(ast.dump(function,include_attributes=False)==ast.dump(expected,include_attributes=False),
            'Unreviewed change in optimized rank ladder')
    return {'passed':True,'same_ordered_fsum_inputs':True,'changed_rounding_or_rank_tolerance':False}


def verify_detector_optimization():
    source=(PACKAGE_DIR/'spectral_components.py').read_text()
    node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='run_bundled_detector_traceblockfix1')
    original=ast.get_source_segment(source,node)
    before="            batch = backend.xp.ascontiguousarray(bundle[:, start:stop])\n            backend.synchronize()\n"
    after=before+"            if batch_index == 0:\n                del positive\n"
    require(original.count(before)==1,'Frozen detector source changed')
    proposed=(PACKAGE_DIR/'optimized_detector.py').read_text()
    function=next(n for n in ast.parse(proposed).body if isinstance(n,ast.FunctionDef) and n.name=='run_bundled_detector_traceblockfix1')
    expected=ast.parse(original.replace(before,after)).body[0]
    require(ast.dump(function,include_attributes=False)==ast.dump(expected,include_attributes=False),
            'Unreviewed change in optimized detector')
    # The removed local is not read after the insertion point in the frozen body.
    # Exactly one read of the local 'positive': the concatenate that constructs bundle.
    reads=[n for n in ast.walk(node) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Load) and n.id=='positive']
    require(len(reads)==1,'Unexpected additional use of the concatenation temporary')
    return {'passed':True,'only_dead_local_lifetime_changed':True,'all_gpu_synchronizations_retained':True}


class DiagnosticIO:
    def __init__(self, output: Path, spec, mode='buffered', interval=15.0):
        require(mode in ('baseline','buffered'),'Unknown optimization mode')
        self.output=Path(output);self.spec=spec;self.mode=mode;self.interval=float(interval)
        self.original_writer=spec.atomic_write_json;self.original_ladder=spec.build_rank_ladder
        self.original_detector=spec.run_bundled_detector_traceblockfix1
        self.latest_pool=None;self.journal=None;self.pool_count=0;self.detector_times={}
        self.stats={'mode':mode,'detector_write_requests':0,'detector_full_writes':0,'detector_deferred_writes':0,
            'pool_cumulative_write_requests':0,'pool_full_writes':0,'pool_journal_records':0,
            'full_diagnostic_payloads_preserved':True,'gpu_syncs_removed':False,
            'pool_operations_changed':False,'rank_ladder':verify_rank_optimization(),'detector_lifetime':verify_detector_optimization()}
        if mode=='buffered':
            import fast_rank_ladder,optimized_detector,types
            spec.build_rank_ladder=fast_rank_ladder.build_rank_ladder
            spec.atomic_write_json=self.spec_writer
            self.journal=(self.output/'pool_flush_records.jsonl').open('x',encoding='utf-8')
        # BLF1: the frozen production lifetime is common to both test arms.
        # Baseline still uses the original rank ladder and unbuffered JSON writes.
        import optimized_detector,types
        f=optimized_detector.run_bundled_detector_traceblockfix1
        spec.run_bundled_detector_traceblockfix1=types.FunctionType(f.__code__,spec.__dict__,f.__name__,f.__defaults__)
        spec.run_bundled_detector_traceblockfix1.__kwdefaults__=f.__kwdefaults__
        self.stats['dead_temporary_lifetime_scope']='common frozen production lifetime in both bridge arms'

    def spec_writer(self,path,payload):
        path=Path(path)
        if path.name!='detector_traceblockfix1_telemetry.json':
            return self.original_writer(path,payload)
        self.stats['detector_write_requests']+=1
        now=time.monotonic();state=payload.get('status');last=self.detector_times.get(path)
        if last is None or state in ('completed','failed') or now-last>=self.interval:
            self.original_writer(path,payload);self.detector_times[path]=now
            self.stats['detector_full_writes']+=1
        else:self.stats['detector_deferred_writes']+=1
        # Callers finish/read one step at a time; don't retain completed telemetry objects.

    def pool_writer(self,path,payload):
        if self.mode=='baseline' or Path(path).name!='pool_flush.json':return write_json(Path(path),payload)
        self.stats['pool_cumulative_write_requests']+=1
        records=payload['flushes'];require(len(records)>=self.pool_count,'Pool log was reset')
        for row in records[self.pool_count:]:
            self.journal.write(json.dumps(row,sort_keys=True,separators=(',',':'),allow_nan=False,default=json_value)+'\n')
            self.stats['pool_journal_records']+=1
        self.journal.flush();self.pool_count=len(records);self.latest_pool=payload
        if self.pool_count==0:self.flush_full('initial')

    def flush_full(self,reason):
        if self.latest_pool is not None:
            write_json(self.output/'pool_flush.json',self.latest_pool);self.stats['pool_full_writes']+=1
        if self.journal is not None:
            self.journal.flush();os.fsync(self.journal.fileno())
        write_json(self.output/'io_optimization.json',{**self.stats,'last_flush_reason':reason})

    def restore(self):
        self.spec.atomic_write_json=self.original_writer
        self.spec.build_rank_ladder=self.original_ladder
        self.spec.run_bundled_detector_traceblockfix1=self.original_detector
        if self.journal is not None:self.journal.close();self.journal=None
