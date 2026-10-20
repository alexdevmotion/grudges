SEPARATORS={'en':',','de':'.','pl':' '}

def pretty(raw,locale):
    if not raw: return raw
    chunks=[]
    while raw:
        chunks.append(raw[-3:]); raw=raw[:-3]
    return SEPARATORS[locale].join(reversed(chunks))
