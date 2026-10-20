from datetime import date, timedelta

def boundaries(data):
    start=date.fromisoformat(data['start']); old=date.fromisoformat(data['expiry'])
    end=date.fromisoformat(data.get('extended') or data['expiry'])
    dates={end}; cursor=start+timedelta(days=1)
    while cursor<end:
        if cursor.day==1 and (data['frequency']=='monthly' or cursor.month in (1,4,7,10)):
            dates.add(cursor)
        cursor+=timedelta(days=1)
    return sorted(dates)
