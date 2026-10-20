CATALOGS={
'nl':dict(switch='Taal kiezen',names=dict(nl='Nederlands',da='Deens',el='Grieks')),
'da':dict(switch='Vælg sprog',names=dict(nl='Nederlandsk',da='Dansk',el='Græsk')),
'el':dict(switch='Επιλογή γλώσσας',names=dict(nl='Ολλανδικά',da='Δανικά',el='Ελληνικά'))}

def translation(locale,key): return CATALOGS[locale][key]
