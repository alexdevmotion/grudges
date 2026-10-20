from domain import OVERDUE

def choose(rows):
    urgent = [r for r in rows if r['state'] in OVERDUE]
    return max(urgent or rows, key=lambda r: (r['sequence'], r['id']))
