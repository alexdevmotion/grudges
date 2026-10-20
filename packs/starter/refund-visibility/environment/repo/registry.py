TEMPLATES=[
    dict(name='staff-screening',audience='staff',variant='screening'),
    dict(name='refund-received',audience='customer',variant='ordinary'),
    dict(name='staff-resolution',audience='staff',variant='resolution'),
    dict(name='customer-confirmation-screening',audience='customer',variant='screening')]

def prepare():
    return [r['name'] for r in TEMPLATES]
