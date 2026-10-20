from datetime import date
from decimal import Decimal, ROUND_HALF_UP

def amounts(data,left,right):
    cut=date.fromisoformat(data['expiry'])
    days=(right-left).days
    extra_days=max(0,(right-max(left,cut)).days)
    denominator=Decimal(3650000)
    def cents(rate,n):
        return int((Decimal(data['balance'])*rate*n/denominator).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
    return cents(data['rate'],days),cents(data['extra_rate'],extra_days)
