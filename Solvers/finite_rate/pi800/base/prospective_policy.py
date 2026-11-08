"""An explicit horizon extension, not retroactive credit or a ledger reset."""
from decimal import Decimal
from archive_tools import require

def validate_policy(cfg):
    p=cfg['policy'];old=p['historical_policy']
    require(old=={'end_call':14400,'event_sectors':6,'final_ceiling_decimal':'2.25e-7',
      'future_borrowing':False,'name':'Pi800_FromZero_LinearReserve_J6_v1','start_call':1,
      'start_ledger_decimal':'0','trace_restoration':False},'Historical reserve contract changed')
    require(p['name']=='Pi800_Post7200_SamePerCallReserveTo600_J6_v1','Unknown prospective policy')
    require(p['start_call']==14401 and p['end_call']==24000 and p['frozen_past_last_call']==14400,'Policy span')
    require(p['start_ledger_decimal']=='2.25e-7' and p['final_ceiling_decimal']=='3.75e-7','Horizon ceiling changed')
    require(p['future_borrowing'] is False and p['trace_restoration'] is False and p['retroactive_rebudgeting'] is False,'Forbidden policy operation')
    increment=(Decimal(p['final_ceiling_decimal'])-Decimal(p['start_ledger_decimal']))/9600
    require(increment==Decimal('1.5625e-11')==Decimal(old['final_ceiling_decimal'])/14400,'Per-call allowance changed')
    return {'passed':True,'past_calls_unchanged':14400,'first_new_call':14401,'last_call':24000,
      'per_new_call_allowance':str(increment),'old_ceiling':'2.25e-7','new_t6_ceiling':'3.75e-7',
      'additional_horizon_allowance':'1.5e-7','full_horizon_feasibility_certified':False}
