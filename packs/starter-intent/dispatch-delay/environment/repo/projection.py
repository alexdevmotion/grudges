def summary(row):
    return {'group': row['group'], 'id': row['id'], 'state': row['state'],
            'due': row['due'], 'arrival': row['planned'], 'revised': row['revised']}
