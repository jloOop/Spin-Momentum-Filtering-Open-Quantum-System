"""Same Kraus/trace/concatenation order; release consumed lists between concatenations.
No rank selection, array value, reduction order, or environmental event is changed.
GPU improvement is unvalidated until the full-size paired qualification passes.
"""
def install(engine, sample_and_flush):
 original=engine.bath_half_truncated
 def shorter_lifetime(family,kraus,*,config,h_z,backend):
  k0,kx,ky=kraus;pieces={};event_omitted=0.0
  trace_before=engine.family_trace(family,h_z,backend)
  for sector,factor in sorted(family.items()):
   mapped0=engine.apply_kraus(k0,factor,config.d_channels,config.n_z,backend)
   if engine.physical_trace(mapped0,h_z,backend)>0.0:pieces.setdefault(int(sector),[]).append(mapped0)
   for operator in (kx,ky):
    mapped=engine.apply_kraus(operator,factor,config.d_channels,config.n_z,backend)
    mapped_trace=engine.physical_trace(mapped,h_z,backend)
    if sector+1<=config.max_event_sector:
     if mapped_trace>0.0:pieces.setdefault(int(sector+1),[]).append(mapped)
    else:event_omitted+=mapped_trace
  # All numerical mapping/reductions above are in the original order.
  # These names only alias completed mapped outputs; pieces owns retained ones.
  if family:del mapped0,mapped
  raw={}
  for sector in list(pieces):
   sample_and_flush('before_concat_'+str(sector),backend,False)
   blocks=pieces.pop(sector)
   raw[sector]=backend.xp.ascontiguousarray(backend.xp.concatenate(blocks,axis=1))
   sample_and_flush('after_concat_'+str(sector),backend,False)
   del blocks
   # Keep the pre-release high-water sample, then release only unused pool blocks.
   sample_and_flush('released_pieces_'+str(sector),backend,True)
  trace_raw=engine.family_trace(raw,h_z,backend)
  closure=trace_before-trace_raw-event_omitted
  return raw,float(event_omitted),{'trace_before':trace_before,'trace_raw_retained':trace_raw,'event_first_crossing_increment':float(event_omitted),'trace_closure_before_compression':float(closure),'rank_raw':engine.family_rank(raw)}
 engine.bath_half_truncated=shorter_lifetime
 return original
