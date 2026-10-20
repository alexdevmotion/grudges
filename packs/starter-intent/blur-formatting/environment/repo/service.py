from editor import Editor
from presentation import display
from payload import submission

def handle(data):
    editor=Editor(data['initial'],data['locale']); result=[]
    for e in data['events']:
        editor.apply(e)
        result.append(dict(display=display(editor),submission=submission(editor) if e['type']=='submit' else None))
    return result
