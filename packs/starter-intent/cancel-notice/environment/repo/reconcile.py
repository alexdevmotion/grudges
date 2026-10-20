class Children:
    def __init__(self): self.previous=[]
    def update(self,desired):
        # Duplicate keys make ownership ambiguous; retain old ambiguous siblings.
        keys=[n['key'] for n in desired]
        result=list(desired)
        for node in self.previous:
            if [n['key'] for n in self.previous].count(node['key'])>1 and node not in result:
                result.append(node)
        self.previous=result
        return [dict(kind=n['kind'],id=n['id']) for n in result]
