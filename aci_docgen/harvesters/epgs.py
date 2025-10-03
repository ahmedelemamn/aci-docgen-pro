from ..utils.normalize import simple_attr

def _pretty_domain(tdn: str) -> str:
    """
    Examples:
      uni/vmmp-VMware/dom-DC1-CLUSTER   -> VMware:DC1-CLUSTER
      uni/phys-DC1-PHYS                 -> phys:DC1-PHYS
      uni/l2dom-LEGACY-L2               -> l2dom:LEGACY-L2
    """
    if not tdn:
        return ""
    if "/vmmp-" in tdn and "/dom-" in tdn:
        vmmp = tdn.split("/vmmp-")[1].split("/")[0]
        name = tdn.split("/dom-")[1]
        return f"{vmmp}:{name}"
    if "/phys-" in tdn:
        return f"phys:{tdn.split('/phys-')[1]}"
    if "/l2dom-" in tdn:
        return f"l2dom:{tdn.split('/l2dom-')[1]}"
    return tdn.split("uni/")[-1]

def _parse_path_tdn(tdn: str, encap: str) -> dict:
    """
    Convert tDn into a readable binding:
      topology/pod-1/paths-101/pathep-[eth1/1]             -> Leaf 101, eth1/1, single
      topology/pod-1/protpaths-101-102/pathep-[PC-ESX]     -> vPC 101-102, PC-ESX, vpc

    encap example: 'vlan-110' -> vlan_id: 110
    """
    info = {"kind": "unknown", "leafs": [], "iface_or_pc": "", "vlan": None, "raw_tdn": tdn}
    if not tdn:
        return info

    # VLAN
    if encap and encap.startswith("vlan-"):
        try:
            info["vlan"] = int(encap.split("-")[1])
        except Exception:
            pass

    # vPC path
    if "/protpaths-" in tdn and "/pathep-[" in tdn:
        leaf_pair = tdn.split("/protpaths-")[1].split("/")[0]  # e.g., 101-102
        pc = tdn.split("/pathep-[", 1)[1].split("]")[0]       # e.g., PC-ESX
        info.update({"kind": "vpc", "leafs": leaf_pair.split("-"), "iface_or_pc": pc})
        return info

    # single leaf path
    if "/paths-" in tdn and "/pathep-[" in tdn:
        leaf = tdn.split("/paths-")[1].split("/")[0]          # e.g., 101
        iface = tdn.split("/pathep-[", 1)[1].split("]")[0]    # e.g., eth1/1
        info.update({"kind": "single", "leafs": [leaf], "iface_or_pc": iface})
        return info

    return info

def harvest_epgs_for_tenant(api, tenant):
    subtree = api.mo_subtree(tenant['dn'])
    epgs = []

    # Build basic EPG list
    for item in subtree.get('imdata', []):
        if 'fvAEPg' in item:
            a = simple_attr(item, 'fvAEPg')
            epgs.append({
                'name': a.get('name'),
                'ap': a.get('dn').split('/ap-')[1].split('/')[0],
                'domains': [],
                'static_paths': []
            })

    # Domains bound to EPGs
    # fvRsDomAtt is a child under EPG; use its parent DN to identify the EPG cleanly
    for item in subtree.get('imdata', []):
        if 'fvRsDomAtt' in item:
            a = simple_attr(item, 'fvRsDomAtt')
            parent_dn = a.get('dn', '')
            # parent_dn like: uni/tn-<T>/ap-<AP>/epg-<EPG>/rsdomAtt-...
            epg_name = parent_dn.split('/epg-')[-1].split('/')[0] if '/epg-' in parent_dn else ''
            dom = _pretty_domain(a.get('tDn', ''))
            for e in epgs:
                if e['name'] == epg_name and dom:
                    if dom not in e['domains']:
                        e['domains'].append(dom)

    # Static path attachments (ports/PCs/vPCs) with VLAN
    for item in subtree.get('imdata', []):
        if 'fvRsPathAtt' in item:
            a = simple_attr(item, 'fvRsPathAtt')
            parent_dn = a.get('dn', '')
            if '/epg-' in parent_dn:
                epg_name = parent_dn.split('/epg-')[1].split('/')[0]
                parsed = _parse_path_tdn(a.get('tDn', ''), a.get('encap', ''))
                for e in epgs:
                    if e['name'] == epg_name:
                        e['static_paths'].append(parsed)

    # Sort for stable output
    for e in epgs:
        e['domains'].sort()
        e['static_paths'].sort(key=lambda x: (x['kind'], ",".join(x['leafs']), x['iface_or_pc']))

    return epgs
