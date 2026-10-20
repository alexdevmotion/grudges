class Memory:
    def __init__(self,available):
        self.available=available; self.ids=set()
    def has(self,id): return id in self.ids if self.available else False
    def add(self,id):
        if self.available: self.ids.add(id)
