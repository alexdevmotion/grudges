from catalogs import translation
from locales import LOCALES
import desktop, mobile

def handle(data):
    locale=data['locale']; current=next(r for r in LOCALES if r['id']==locale)
    return dict(trigger=dict(code=current['code'],label=translation(locale,'switch')),options=(desktop if data['surface']=='desktop' else mobile).options(locale))
