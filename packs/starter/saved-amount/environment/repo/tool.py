import json, sys
from service import handle
print(json.dumps(handle(json.load(sys.stdin)),ensure_ascii=False))
