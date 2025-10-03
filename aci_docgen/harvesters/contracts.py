from ..utils.normalize import simple_attr

def harvest_contracts_for_tenant(api, tenant):
    subtree = api.mo_subtree(tenant['dn'])
    cps = []
    dn_to_cp = {}
    for item in subtree.get('imdata', []):
        if 'vzBrCP' in item:
            a = simple_attr(item, 'vzBrCP')
            dn_to_cp[a.get('dn')] = {'name': a.get('name'), 'scope': a.get('scope'), 'subjects': []}
    for item in subtree.get('imdata', []):
        if 'vzSubj' in item:
            a = simple_attr(item, 'vzSubj')
            parent = a.get('dn', '').split('/subj-')[0]
            if parent in dn_to_cp:
                dn_to_cp[parent]['subjects'].append({'name': a.get('name')})
    return list(dn_to_cp.values())
