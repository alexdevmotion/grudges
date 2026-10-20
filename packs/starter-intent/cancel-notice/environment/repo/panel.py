from storage import Memory
from reconcile import Children
from widgets import nodes

class Panel:
    def __init__(self,mode,available):
        self.mode=mode; self.memory=Memory(available); self.children=Children()
        self.opened=False; self.id='draft'; self.notice=None
    def apply(self,e):
        kind=e['type']
        if kind=='open':
            self.opened=True; row=e.get('latest')
            self.id=row['id'] if row else 'draft'
            self.notice=row['id'] if row and row['state']=='cancelled' and not self.memory.has(row['id']) else None
        elif kind=='cancel':
            self.id=e['inspection']['id']; self.notice=self.id
        elif kind in ('dismiss','action','close'):
            if self.notice: self.memory.add(self.notice)
            self.notice=None
            if kind=='close': self.opened=False
        desired=nodes(self.mode,self.id,self.notice) if self.opened else []
        return dict(open=self.opened,children=self.children.update(desired))
