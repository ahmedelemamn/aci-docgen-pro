from ..utils.normalize import simple_attr
from .epgs import _parse_path_tdn


def _contract_name_from_tdn(tdn: str) -> str:
    """Render a friendly contract name from a target DN."""

    if not tdn:
        return ""
    if "/brc-" in tdn:
        return tdn.split("/brc-")[-1]
    return tdn.split("uni/")[-1]

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
    instp_by_dn = {}
    for item in subtree.get('imdata', []):
        if 'l2extInstP' in item:
            a = simple_attr(item, 'l2extInstP')
            parent = a.get('dn', '').split('/instP-')[0]
            for dn, out in dn_to_out.items():
                if parent.startswith(dn):
                    instp = {
                        'name': a.get('name'),
                        'subnets': [],
                        'path_attachments': [],
                        'provided_contracts': [],
                        'consumed_contracts': [],
                        'protected_by_contracts': []
                    }
                    out['instps'].append(instp)
                    instp_by_dn[a.get('dn')] = instp

    # enrich InstPs with subnets, paths, and contracts
    for item in subtree.get('imdata', []):
        if 'l2extSubnet' in item:
            a = simple_attr(item, 'l2extSubnet')
            parent = a.get('dn', '').split('/subnet-')[0]
            instp = instp_by_dn.get(parent)
            if instp:
                subnet_info = {
                    'ip': a.get('ip') or a.get('prefix'),
                    'scope': a.get('scope'),
                    'aggregate': a.get('aggregate'),
                    'name': a.get('name')
                }
                if subnet_info not in instp['subnets']:
                    instp['subnets'].append(subnet_info)
        if 'l2extRsPathL2OutAtt' in item:
            a = simple_attr(item, 'l2extRsPathL2OutAtt')
            parent = a.get('dn', '').split('/rsPathL2OutAtt')[0]
            instp = instp_by_dn.get(parent)
            if instp:
                parsed = _parse_path_tdn(a.get('tDn', ''), a.get('encap', ''))
                if not any(
                    p.get('raw_tdn') == parsed.get('raw_tdn') and p.get('vlan') == parsed.get('vlan')
                    for p in instp['path_attachments']
                ):
                    instp['path_attachments'].append(parsed)
        if 'fvRsProv' in item:
            a = simple_attr(item, 'fvRsProv')
            parent = a.get('dn', '').split('/rsprov-')[0]
            instp = instp_by_dn.get(parent)
            if instp:
                name = _contract_name_from_tdn(a.get('tDn', ''))
                if name and name not in instp['provided_contracts']:
                    instp['provided_contracts'].append(name)
        if 'fvRsCons' in item:
            a = simple_attr(item, 'fvRsCons')
            parent = a.get('dn', '').split('/rscons-')[0]
            instp = instp_by_dn.get(parent)
            if instp:
                name = _contract_name_from_tdn(a.get('tDn', ''))
                if name and name not in instp['consumed_contracts']:
                    instp['consumed_contracts'].append(name)
        if 'fvRsProtBy' in item:
            a = simple_attr(item, 'fvRsProtBy')
            parent = a.get('dn', '').split('/rsprotBy-')[0]
            instp = instp_by_dn.get(parent)
            if instp:
                name = _contract_name_from_tdn(a.get('tDn', ''))
                if name and name not in instp['protected_by_contracts']:
                    instp['protected_by_contracts'].append(name)

    # sort for stable output
    for out in dn_to_out.values():
        out['domains'] = sorted({d for d in out['domains'] if d})
        for instp in out['instps']:
            instp['subnets'].sort(key=lambda s: (s.get('ip') or '', s.get('scope') or ''))
            instp['path_attachments'].sort(
                key=lambda p: (p.get('kind'), ','.join(p.get('leafs', [])), p.get('iface_or_pc'), p.get('vlan') or 0)
            )
            instp['provided_contracts'].sort()
            instp['consumed_contracts'].sort()
            instp['protected_by_contracts'].sort()

    return list(dn_to_out.values())
