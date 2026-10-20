from datetime import date
from calendar_rules import boundaries
from accrual import amounts

def schedule(data):
    cuts=boundaries(data)
    if data.get('extended'):
        cuts=sorted(set(cuts+[date.fromisoformat(data['expiry'])]))
    prior=date.fromisoformat(data['start']); result=[]
    for cut in cuts:
        base,extra=amounts(data,prior,cut)
        result.append(dict(date=str(cut),base=base,extra=extra,principal=data['balance'] if cut==cuts[-1] else 0))
        prior=cut
    return result
