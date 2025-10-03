from ..utils.normalize import simple_attr

def harvest_bds_for_tenant(api, tenant):
    subtree = api.mo_subtree(tenant['dn'])
    bds = []
    dn_to_bd = {}

    # Collect BDs and key attributes
    for item in subtree.get('imdata', []):
        if 'fvBD' in item:
            a = simple_attr(item, 'fvBD')
            dn_to_bd[a.get('dn')] = {
                'name': a.get('name'),
                # Key features you asked for:
                'unicastRoute': a.get('unicastRoute'),        # enabled/disabled (L3 GW)
                'arpFlood': a.get('arpFlood'),                # true/false
                'unkMacUcastAct': a.get('unkMacUcastAct'),    # proxy/flood
                'limitIpLearnToSubnets': a.get('limitIpLearnToSubnets'),
                # Keep other commonly useful flags if present (graceful if missing):
                'ipLearning': a.get('ipLearning'),
                'multiDstPktAct': a.get('multiDstPktAct'),
                'subnets': []
            }

    # Attach subnets with IP and scope (e.g., private/shared/public)
    for item in subtree.get('imdata', []):
        if 'fvSubnet' in item:
            a = simple_attr(item, 'fvSubnet')
            parent_dn = a.get('dn', '').split('/subnet-')[0]
            if parent_dn in dn_to_bd:
                dn_to_bd[parent_dn]['subnets'].append({
                    'ip': a.get('ip'),
                    'scope': a.get('scope')  # may be "", "public", "shared", etc.
                })

    return list(dn_to_bd.values())
