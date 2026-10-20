def inspect(refund):
    return dict(state=refund['state'],executable=refund['state']=='queued',team=dict(id=refund['id'],reason=refund['reason']) if refund['state']=='screened' else None)
