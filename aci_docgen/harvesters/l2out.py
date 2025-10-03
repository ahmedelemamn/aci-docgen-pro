from ..utils.normalize import simple_attr

def harvest_l2out_for_tenant(api, tenant):
    subtree = api.mo_subtree(tenant['dn'])
    outs = []
    dn_to_out = {}
    for item in subtree.get('imdata', []):
        if 'l2extOut' in item:
            a = simple_attr(item, 'l2extOut')
            dn_to_out[a.get('dn')] = {
                'name': a.get('name'),
                'domains': [],
                'bd': '',
                'instps': []
            }
    # domain attachments
    for item in subtree.get('imdata', []):
        if 'l2extRsEBd' in item:
            a = simple_attr(item, 'l2extRsEBd')
            parent = a.get('dn', '').split('/rsEBd')[0]
            if parent in dn_to_out:
                dn_to_out[parent]['bd'] = a.get('tDn', '').split('/BD-')[-1]
        if 'l2extRsL2DomAtt' in item:
            a = simple_attr(item, 'l2extRsL2DomAtt')
            parent = a.get('dn', '').split('/rsL2DomAtt')[0]
            if parent in dn_to_out and a.get('tDn'):
                dn_to_out[parent]['domains'].append(a.get('tDn').split('uni/')[1])
    # instance profiles
    for item in subtree.get('imdata', []):
        if 'l2extInstP' in item:
            a = simple_attr(item, 'l2extInstP')
            parent = a.get('dn', '').split('/instP-')[0]
            for dn, out in dn_to_out.items():
                if parent.startswith(dn):
                    out['instps'].append({'name': a.get('name')})
    return list(dn_to_out.values())
