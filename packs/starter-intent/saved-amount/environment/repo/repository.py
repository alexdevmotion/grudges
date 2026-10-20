def known(row):
    return bool(row and row.get('amount') is not None and row['amount']>0)

def saved(data):
    return data.get('draft') if known(data.get('draft')) else data.get('submitted') if known(data.get('submitted')) else None
