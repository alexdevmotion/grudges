from merge import opening
from revision import save

def handle(data):
    fields,alerts=opening(data)
    state,save_alerts=save(data['expected_revision'],data['current_revision'])
    return dict(fields=fields,alerts=alerts+save_alerts,save=state)
