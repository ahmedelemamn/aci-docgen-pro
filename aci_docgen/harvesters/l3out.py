from ..utils.normalize import simple_attr

def harvest_l3out_for_tenant(api, tenant):
    subtree = api.mo_subtree(tenant['dn'])
    outs = []
    dn_to_out = {}
    for item in subtree.get('imdata', []):
        if 'l3extOut' in item:
            a = simple_attr(item, 'l3extOut')
            dn_to_out[a.get('dn')] = {'name': a.get('name'), 'vrf': '', 'protocols': set(), 'external_subnets': []}

    # protocols and VRF
    for item in subtree.get('imdata', []):
        if 'l3extRsEctx' in item:
            a = simple_attr(item, 'l3extRsEctx')
            parent = a.get('dn', '').split('/out-')[0] + '/out-' + a.get('tDn', '').split('/ctx-')[-1] if False else a.get('dn', '').split('/rsEctx')[0]
            for dn in list(dn_to_out.keys()):
                if dn.startswith(parent.split('/rsEctx')[0]):
                    dn_to_out[dn]['vrf'] = a.get('tDn', '').split('/ctx-')[-1]

        if 'ospfExtP' in item:  # presence means OSPF used
            parent = simple_attr(item, 'ospfExtP').get('dn', '').split('/ospfExtP')[0]
            if parent in dn_to_out:
                dn_to_out[parent]['protocols'].add('OSPF')

        if 'bgpExtP' in item:
            parent = simple_attr(item, 'bgpExtP').get('dn', '').split('/bgpExtP')[0]
            if parent in dn_to_out:
                dn_to_out[parent]['protocols'].add('BGP')

    # external subnets
    for item in subtree.get('imdata', []):
        if 'l3extSubnet' in item:
            a = simple_attr(item, 'l3extSubnet')
            parent = a.get('dn', '').split('/extsubnet-')[0]
            for dn in dn_to_out:
                if dn and parent.startswith(dn):
                    dn_to_out[dn]['external_subnets'].append({'ip': a.get('ip')})

    # finalize protocols
    for dn in dn_to_out:
        dn_to_out[dn]['protocols'] = sorted(list(dn_to_out[dn]['protocols']))

    return list(dn_to_out.values())
