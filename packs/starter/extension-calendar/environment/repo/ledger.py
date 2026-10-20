from datetime import date
from calendar_rules import boundaries
from accrual import amounts

def schedule(data):
    dates=boundaries(data)
    if data.get('extended'):
        dates=sorted(set(dates+[date.fromisoformat(data['expiry'])]))
    left=date.fromisoformat(data['start']); rows=[]
    for right in dates:
        base,extra=amounts(data,left,right)
        rows.append(dict(date=right.isoformat(),base=base,extra=extra,principal=data['balance'] if right==dates[-1] else 0))
        left=right
    return rows
