def confirmation(refund):
    if refund['state'] not in ('queued','screened'): return None
    message=dict(template='refund-received',id=refund['id'],gross=refund['gross'],fee=refund['fee'],net=refund['gross']-refund['fee'])
    if refund['state']=='screened':
        message.update(screening=True,reason=refund['reason'])
    return message
