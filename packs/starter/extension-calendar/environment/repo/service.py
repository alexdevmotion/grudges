import ledger, preview

def handle(data):
    rows=ledger.schedule(data)
    return dict(ledger=rows,preview=preview.schedule(data),next=next((r['date'] for r in rows if r['date']>data.get('as_of',data['start'])),None))
