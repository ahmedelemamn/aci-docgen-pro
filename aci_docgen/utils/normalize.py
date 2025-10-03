def simple_attr(mo, cls):
    return mo.get(cls, {}).get('attributes', {})


def collect_children(mo, cls):
    return [c[cls] for c in [x for x in mo.get('children', []) if cls in x]]


def sorted_unique(values):
    """Return a sorted list of unique, truthy values."""

    if not values:
        return []

    seen = set()
    filtered = []
    for value in values:
        if not value:
            continue
        if value in seen:
            continue
        seen.add(value)
        filtered.append(value)

    return sorted(filtered, key=lambda v: str(v))
