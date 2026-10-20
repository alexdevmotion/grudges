from panel import Panel

def handle(data):
    p=Panel(data['mode'],data['storage_available'])
    return [p.apply(e) for e in data['events']]
