def save(expected,current):
    if expected!=current: return 'conflict',['stale-save']
    return 'accepted',[]
