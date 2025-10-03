from ..utils.normalize import simple_attr

def _l3out_dn_from(child_dn: str) -> str:
    """
    Given any DN under an L3Out, return the L3Out DN:
      uni/tn-T/out-MyOut/instP-EXT/..   -> uni/tn-T/out-MyOut
      uni/tn-T/out-MyOut/lnodep-...     -> uni/tn-T/out-MyOut
    """
    if not child_dn or "/out-" not in child_dn:
        return ""
    head, tail = child_dn.split("/out-", 1)
    out_name = tail.split("/")[0]
    return f"{head}/out-{out_name}"

def _vrf_name_from_tdn(tdn: str) -> str:
    # e.g. uni/tn-DC1/ctx-DC1  -> DC1
    if not tdn or "/ctx-" not in tdn:
        return ""
    return tdn.split("/ctx-")[-1]

def harvest_l3out_for_tenant(api, tenant):
    """
    Harvest per-tenant L3Outs with:
      - name, DN
      - VRF name via l3extRsEctx.tDn
      - protocol hints (BGP/OSPF) if present in subtree
      - external subnet count (l3extSubnet under instPs)
    """
    subtree = api.mo_subtree(tenant['dn'])
    lo_by_dn = {}

    # Base L3Outs
    for item in subtree.get('imdata', []):
        if 'l3extOut' in item:
            a = simple_attr(item, 'l3extOut')
            dn = a.get('dn')
            lo_by_dn[dn] = {
                'name': a.get('name'),
                'dn': dn,
                'vrf': "",           # filled by l3extRsEctx
                'protocols': set(),  # 'BGP', 'OSPF'
                'external_subnets': 0
            }

    if not lo_by_dn:
        return []

    # Resolve VRF via l3extRsEctx.tDn
    for item in subtree.get('imdata', []):
        if 'l3extRsEctx' in item:
            a = simple_attr(item, 'l3extRsEctx')
            parent_out = a.get('dn', '').split('/rsectx-')[0]  # parent is the l3extOut DN
            if parent_out in lo_by_dn:
                lo_by_dn[parent_out]['vrf'] = _vrf_name_from_tdn(a.get('tDn', ''))

    # External subnets count (under instP)
    for item in subtree.get('imdata', []):
        if 'l3extSubnet' in item:
            a = simple_attr(item, 'l3extSubnet')
            l3out_dn = _l3out_dn_from(a.get('dn', ''))
            if l3out_dn in lo_by_dn:
                lo_by_dn[l3out_dn]['external_subnets'] += 1

    # Protocol hints: mark BGP/OSPF if any matching policy exists under this L3Out
    for item in subtree.get('imdata', []):
        for cls in ('bgpExtP', 'bgpPeerP', 'bgpProtP', 'bgpRsPeerPfxPol', 'bgpAsP',
                    'ospfExtP', 'ospfIfP', 'ospfCtxPol', 'ospfRsIfPol'):
            if cls in item:
                a = simple_attr(item, cls)
                l3out_dn = _l3out_dn_from(a.get('dn', ''))
                if l3out_dn in lo_by_dn:
                    if cls.startswith('bgp'):
                        lo_by_dn[l3out_dn]['protocols'].add('BGP')
                    if cls.startswith('ospf'):
                        lo_by_dn[l3out_dn]['protocols'].add('OSPF')

    # Normalize sets
    los = []
    for lo in lo_by_dn.values():
        lo['protocols'] = sorted(lo['protocols'])
        los.append(lo)

    # Sort for stable output
    los.sort(key=lambda x: x['name'])
    return los
