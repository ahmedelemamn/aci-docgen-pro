from ..utils.normalize import simple_attr

def harvest_vrfs_for_tenant(api, tenant):
    # subtree of tenant contains fvCtx
    subtree = api.mo_subtree(tenant['dn'])
    vrfs = []
    for item in subtree.get('imdata', []):
        if 'fvCtx' in item:
            a = simple_attr(item, 'fvCtx')
            vrfs.append({'name': a.get('name'),
                         'pcEnfPref': a.get('pcEnfPref'),
                         'pcEnfDir': a.get('pcEnfDir'),
                         'dn': a.get('dn')})
    return vrfs
