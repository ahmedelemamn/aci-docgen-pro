from ..utils.normalize import simple_attr


def _walk_imdata(nodes):
    """Yield (class_name, attributes) pairs from an imdata-style list."""

    for node in nodes or []:
        for cls, body in node.items():
            attributes = body.get('attributes', {})
            yield cls, attributes
            # Children are already in the same {cls: {...}} format.
            yield from _walk_imdata(body.get('children', []))


def _extract_vlan_pool_name(tdn):
    if not tdn:
        return ""

    if 'vlanns-[' in tdn:
        return tdn.split('vlanns-[')[1].split(']')[0]

    # Fall back to the last segment of the DN.
    return tdn.split('/')[-1]


def harvest_vmm_for_tenant(api, tenant):
    # There isn't a strict per-tenant VMM, but EPG -> fvRsDomAtt -> vmmDomP references.
    subtree = api.mo_subtree(tenant['dn'])
    vmm_refs = {}
    for item in subtree.get('imdata', []):
        if 'fvRsDomAtt' in item:
            a = simple_attr(item, 'fvRsDomAtt')
            tdn = a.get('tDn', '')
            if '/vmmp-' in tdn and '/dom-' in tdn:
                key = tdn.split('uni/')[1] if 'uni/' in tdn else tdn
                domain_name = tdn.split('/dom-')[-1]
                if '/' in domain_name:
                    domain_name = domain_name.split('/')[0]

                vmm_refs[key] = {
                    'name': domain_name,
                    'type': tdn.split('/vmmp-')[1].split('/')[0],
                    'vcenter': [],
                    'vlan_pools': [],
                    'mode': '',
                }

    for tdn, info in vmm_refs.items():
        domain_data = api.mo_subtree(f"uni/{tdn}")
        controllers = []
        vlan_pools = []
        mode = info.get('mode', '')

        for cls, attributes in _walk_imdata(domain_data.get('imdata', [])):
            if cls == 'vmmDomP':
                mode = attributes.get('mode') or mode
            elif cls == 'vmmCtrlrP':
                controller_name = attributes.get('name') or attributes.get('hostOrIp')
                if controller_name and controller_name not in controllers:
                    controllers.append(controller_name)
            elif cls in ('infraRsVlanNs', 'vmmRsVlanNs'):
                pool_name = _extract_vlan_pool_name(attributes.get('tDn'))
                if pool_name and pool_name not in vlan_pools:
                    vlan_pools.append(pool_name)

        info['mode'] = mode or ''
        info['vcenter'] = controllers
        info['vlan_pools'] = vlan_pools

    return list(vmm_refs.values())
