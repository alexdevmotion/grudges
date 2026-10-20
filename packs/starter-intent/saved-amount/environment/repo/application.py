from repository import known

def open_application(data,seed=None):
    if seed is not None:
        row=seed
    elif known(data.get('draft')):
        row=data['draft']
    elif known(data.get('submitted')):
        return dict(route='submitted',id=data['submitted']['id'])
    else:
        row=dict(amount=None,term=None,income=None)
    return dict(route='form',fields={k:row[k] for k in ('amount','term','income')} | {k:data['profile'].get(k) for k in ('phone','region')})
