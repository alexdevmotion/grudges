def nodes(mode,id,notice):
    base=[dict(key=id,kind='form',id=id)]
    if notice:
            base.append(dict(key=id,kind='notice',id=notice))
    return base
