def simple_attr(mo, cls):
    return mo.get(cls, {}).get('attributes', {})

def collect_children(mo, cls):
    return [c[cls] for c in [x for x in mo.get('children', []) if cls in x]]
