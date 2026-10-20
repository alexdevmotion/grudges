from catalogs import translation
from locales import LOCALES

def options(locale):
    return [dict(code=r['code'],text=translation(locale,'names')[r['id']],lang=locale,accessible=translation(locale,'names')[r['id']]+' '+r['code'],selected=r['id']==locale) for r in LOCALES]
