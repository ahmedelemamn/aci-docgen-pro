from ..utils.normalize import simple_attr

def harvest_vmm_for_tenant(api, tenant):
    # There isn't a strict per-tenant VMM, but EPG -> fvRsDomAtt -> vmmDomP references.
    subtree = api.mo_subtree(tenant['dn'])
    vmm_refs = {}
    for item in subtree.get('imdata', []):
        if 'fvRsDomAtt' in item:
            a = simple_attr(item, 'fvRsDomAtt')
            tdn = a.get('tDn', '')
            if '/vmmp-VMware/dom-' in tdn or '/vmmp-OpenStack/dom-' in tdn:
                vmm_refs[tdn.split('uni/')[1]] = {'name': tdn.split('/dom-')[-1], 'type': tdn.split('/vmmp-')[1].split('/')[0], 'vcenter': ''}
    return list(vmm_refs.values())
