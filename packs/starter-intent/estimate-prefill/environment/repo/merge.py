from schema import FIELDS, FINANCE

def opening(data):
    fields={k:(data.get('saved') or {}).get(k) for k in FIELDS}
    estimate=data.get('estimate') or {}
    conflict=any(k in estimate and estimate[k]!=fields[k] for k in FINANCE)
    if not conflict:
        fields.update({k:v for k,v in estimate.items() if k in FINANCE})
    fields.update({k:v for k,v in (data.get('session') or {}).items() if k in FIELDS})
    return fields,['choose-estimate'] if conflict else []
