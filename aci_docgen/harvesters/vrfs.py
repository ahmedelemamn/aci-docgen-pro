from ..utils.normalize import simple_attr

def harvest_vrfs_for_tenant(api, tenant):
    """
    Harvest VRFs (fvCtx) under a tenant, including:
      - enforcement prefs (pcEnfPref/pcEnfDir)
      - multicast/learning flags (knwMcastAct, ipDataPlaneLearning)
      - vzAny provided/consumed contracts (vzRsAnyToProv/vzRsAnyToCons)
      - health score (healthInst.cur)
      - number of BDs bound to the VRF (via fvRtCtx entries)
    """
    subtree = api.mo_subtree(tenant['dn'])

    dn_to_vrf = {}

    # Base VRF objects (fvCtx)
    for item in subtree.get('imdata', []):
        if 'fvCtx' in item:
            a = simple_attr(item, 'fvCtx')
            dn = a.get('dn')
            dn_to_vrf[dn] = {
                'name': a.get('name'),
                'dn': dn,
                'pcEnfPref': a.get('pcEnfPref'),                  # enforced/unenforced
                'pcEnfDir': a.get('pcEnfDir'),                    # ingress/egress/both (if set)
                'knwMcastAct': a.get('knwMcastAct'),              # permit/deny
                'ipDataPlaneLearning': a.get('ipDataPlaneLearning'),
                'bdEnforcedEnable': a.get('bdEnforcedEnable'),    # yes/no (legacy toggle)
                'pcTag': a.get('pcTag'),
                'health': None,
                'bd_count': 0,
                'vzAny': {
                    'prov_contracts': [],
                    'cons_contracts': []
                }
            }

    if not dn_to_vrf:
        return []

    # Health under VRF
    for item in subtree.get('imdata', []):
        if 'fvCtx' in item and 'children' in item['fvCtx']:
            ctx_dn = item['fvCtx']['attributes'].get('dn')
            for ch in item['fvCtx']['children']:
                if 'healthInst' in ch:
                    cur = ch['healthInst']['attributes'].get('cur')
                    if ctx_dn in dn_to_vrf:
                        dn_to_vrf[ctx_dn]['health'] = cur

    # vzAny relations (correct classes are vzRsAnyToProv / vzRsAnyToCons)
    for item in subtree.get('imdata', []):
        if 'vzRsAnyToProv' in item:
            a = simple_attr(item, 'vzRsAnyToProv')
            parent_any_dn = a.get('dn', '')               # .../ctx-<VRF>/any/rsanyToProv-<brc-name>
            ctx_dn = parent_any_dn.split('/any')[0]
            if ctx_dn in dn_to_vrf:
                tdn = a.get('tDn', '')
                name = tdn.split('/brc-')[-1] if '/brc-' in tdn else tdn
                if name:
                    dn_to_vrf[ctx_dn]['vzAny']['prov_contracts'].append(name)

        if 'vzRsAnyToCons' in item:
            a = simple_attr(item, 'vzRsAnyToCons')
            parent_any_dn = a.get('dn', '')
            ctx_dn = parent_any_dn.split('/any')[0]
            if ctx_dn in dn_to_vrf:
                tdn = a.get('tDn', '')
                name = tdn.split('/brc-')[-1] if '/brc-' in tdn else tdn
                if name:
                    dn_to_vrf[ctx_dn]['vzAny']['cons_contracts'].append(name)

    # Count BDs attached to VRF via reverse reference fvRtCtx (tDn points to BD)
    bd_by_ctx = {}
    for item in subtree.get('imdata', []):
        if 'fvRtCtx' in item:
            a = simple_attr(item, 'fvRtCtx')
            # Parent VRF DN is before /rtctx-...
            parent_ctx_dn = a.get('dn', '').split('/rtctx-')[0]
            if parent_ctx_dn:
                bd_by_ctx.setdefault(parent_ctx_dn, set()).add(a.get('tDn'))

    for ctx_dn, bds in bd_by_ctx.items():
        if ctx_dn in dn_to_vrf:
            dn_to_vrf[ctx_dn]['bd_count'] = len([x for x in bds if x])

    # Dedup/sort vzAny lists
    for v in dn_to_vrf.values():
        v['vzAny']['prov_contracts'] = sorted(set(v['vzAny']['prov_contracts']))
        v['vzAny']['cons_contracts'] = sorted(set(v['vzAny']['cons_contracts']))

    return list(dn_to_vrf.values())
