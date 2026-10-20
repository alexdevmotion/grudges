class Editor:
    def __init__(self,initial,locale):
        self.values=dict(initial); self.locale=locale; self.focused=None
    def apply(self,e):
        kind=e['type']
        if kind=='focus': self.focused=e['field']
        elif kind=='blur':
            if self.focused==e['field']: self.focused=None
        elif kind=='input': self.values[e['field']]=e['value']
        elif kind=='locale': self.locale=e['value']
