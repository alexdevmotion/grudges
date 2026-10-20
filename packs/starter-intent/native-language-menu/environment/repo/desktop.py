from catalogs import translation
from locales import LOCALES

def options(locale):
    names=translation(locale,'names')
    return [dict(code=r['code'],text=names[r['id']],lang=locale,accessible=names[r['id']]+' '+r['code'],selected=r['id']==locale) for r in LOCALES]
