from states import public_state
from customer import view
from mail import confirmation
from staff import inspect
from registry import prepare

def handle(data):
    if data['op']=='prepare': return prepare()
    if data['op']=='view': return view(data['state'],data['locale'])
    r=data['refund']; state=public_state(r['state'])
    return dict(api=dict(id=r['id'],state=state),view=view(state,data['locale']),email=confirmation(r),internal=inspect(r))
