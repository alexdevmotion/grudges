from selection import choose
from projection import summary

def handle(data):
    buckets = {}
    for row in data['rows']:
        buckets.setdefault(row['group'], []).append(row)
    return [summary(choose(buckets[k])) for k in sorted(buckets)]
