from ..utils.normalize import simple_attr
from ..utils.log import debug

def harvest_tenants(api, debug_enabled=False):
    data = api.class_query('fvTenant')
    tenants = []
    for mo in data.get('imdata', []):
        a = simple_attr(mo, 'fvTenant')
        tenants.append({'name': a.get('name'), 'dn': a.get('dn')})
    debug(f"Found tenants: {[t['name'] for t in tenants]}", debug_enabled)
    return tenants
