from ..utils.normalize import simple_attr

def _contract_name_from_tdn(tdn: str) -> str:
    if not tdn:
        return ""
    if "/brc-" in tdn:
        return tdn.split("/brc-")[-1]
    return tdn.split("uni/")[-1]

def _pretty_epg_from_selector_dn(dn: str) -> str:
    """
    ESG EPG selector DN example:
      uni/tn-T/ap-App/esg-Web/esgepgselector-[uni/tn-T/ap-App/epg-Frontend]
    Render as: T/App/Frontend (or App/Frontend if tenant missing)
    """
    try:
        inner = dn.split("/epgselector-[", 1)[1].split("]", 1)[0]
    except Exception:
        return dn
    tn = inner.split("/tn-")[1].split("/")[0] if "/tn-" in inner else ""
    ap = inner.split("/ap-")[1].split("/")[0] if "/ap-" in inner else ""
    epg = inner.split("/epg-")[1].split("/")[0] if "/epg-" in inner else inner
    return f"{tn}/{ap}/{epg}" if tn else f"{ap}/{epg}"

def _extract_ip_from_attrs(attrs: dict, fallback_dn: str) -> str:
    """
    Try common attribute names for ESG IP selectors:
      ip, subnet, prefix, fromIp/toIp (range), or matchExpression "ip=='CIDR'"
    """
    if not attrs:
        return fallback_dn

    # direct fields
    ip = attrs.get("ip") or attrs.get("subnet") or attrs.get("prefix")
    if ip:
        return ip

    # range form
    fip, tip = attrs.get("fromIp"), attrs.get("toIp")
    if fip and tip:
        return f"{fip}-{tip}"

    # matchExpression form e.g., "ip=='10.100.109.0/24'"
    expr = attrs.get("matchExpression", "")
    if "ip==" in expr:
        # try to pull content between single or double quotes
        for q in ("'", '"'):
            if q in expr:
                try:
                    return expr.split(q)[1]
                except Exception:
                    pass
        # fallback: strip prefix
        return expr.replace("ip==", "").strip("'\" ")

    return fallback_dn

def harvest_esg_for_tenant(api, tenant):
    """
    Harvest Endpoint Security Groups (ESGs) under the tenant.
    Captures: name, pcTag, pcEnfPref, prov/cons contracts, EPG/IP/Tag selectors.
    """
    subtree = api.mo_subtree(tenant['dn'])
    dn_to_esg = {}

    # Base ESGs
    for item in subtree.get('imdata', []):
        if 'fvESg' in item:
            a = simple_attr(item, 'fvESg')
            dn_to_esg[a.get('dn')] = {
                'name': a.get('name'),
                'pcTag': a.get('pcTag'),
                'pcEnfPref': a.get('pcEnfPref'),  # enforced/unenforced
                'prov_contracts': [],
                'cons_contracts': [],
                'epg_selectors': [],
                'ip_selectors': [],
                'tag_selectors': []
            }
    if not dn_to_esg:
        return []

    # Relations & selectors under ESGs
    for item in subtree.get('imdata', []):
        # Provided contracts
        if 'fvRsProv' in item:
            a = simple_attr(item, 'fvRsProv')
            parent = a.get('dn', '').split('/rsprov-')[0]
            if parent in dn_to_esg:
                dn_to_esg[parent]['prov_contracts'].append(_contract_name_from_tdn(a.get('tDn', '')))

        # Consumed contracts
        if 'fvRsCons' in item:
            a = simple_attr(item, 'fvRsCons')
            parent = a.get('dn', '').split('/rscons-')[0]
            if parent in dn_to_esg:
                dn_to_esg[parent]['cons_contracts'].append(_contract_name_from_tdn(a.get('tDn', '')))

        # EPG selectors (explicit class)
        if 'fvEPgSelector' in item:
            a = simple_attr(item, 'fvEPgSelector')
            parent = a.get('dn', '').split('/epgselector-')[0]
            if parent in dn_to_esg:
                dn_to_esg[parent]['epg_selectors'].append(_pretty_epg_from_selector_dn(a.get('dn', '')))

        # Tag selectors
        if 'fvTagSelector' in item:
            a = simple_attr(item, 'fvTagSelector')
            parent = a.get('dn', '').split('/tagselector-')[0]
            if parent in dn_to_esg:
                key = a.get('key'); op = a.get('operator'); val = a.get('value')
                if key or op or val:
                    dn_to_esg[parent]['tag_selectors'].append(" ".join([x for x in [key, op, val] if x]))
                else:
                    dn_to_esg[parent]['tag_selectors'].append(a.get('name') or a.get('dn', ''))

        # ---- ESG selectors that arrive as EP selectors (IP/EPG) ----
        # Observed classes: fvEPSelector, fvAEPSelector
        for cls in ('fvEPSelector', 'fvAEPSelector'):
            if cls in item:
                a = simple_attr(item, cls)
                dn = a.get('dn', '')
                parent = dn.split('/epselector-')[0]
                if parent not in dn_to_esg:
                    continue
                match_class = a.get('matchClass', '')
                if match_class == 'fvIp':
                    ip_val = _extract_ip_from_attrs(a, dn)
                    dn_to_esg[parent]['ip_selectors'].append(ip_val)
                elif match_class == 'fvEPg':
                    # Sometimes EPG comes via EP selector; use matchEpgDn if present
                    epg_dn = a.get('matchEpgDn') or dn
                    # Convert to pretty "T/App/EPG"
                    try:
                        inner = epg_dn if '/epg-' in epg_dn else dn
                        tn = inner.split("/tn-")[1].split("/")[0] if "/tn-" in inner else ""
                        ap = inner.split("/ap-")[1].split("/")[0] if "/ap-" in inner else ""
                        epg = inner.split("/epg-")[1].split("/")[0] if "/epg-" in inner else inner
                        pretty = f"{tn}/{ap}/{epg}" if tn else f"{ap}/{epg}"
                    except Exception:
                        pretty = epg_dn
                    dn_to_esg[parent]['epg_selectors'].append(pretty)

        # ---- Fallback: other IP selector variants (keep broad for compatibility) ----
        for cls_name, mo in item.items():
            if not isinstance(mo, dict) or 'attributes' not in mo:
                continue
            cls_lower = cls_name.lower()
            if cls_lower.endswith('ipselector') or cls_lower.endswith('subnetselector') or cls_lower in {'fvipselector', 'fvesgipselector', 'fvsubnetselector'}:
                attrs = mo.get('attributes', {})
                parent = attrs.get('dn', '')
                parent = parent.split('/ipsel-')[0] if '/ipsel-' in parent else parent
                parent = parent.split('/ipselector-')[0] if '/ipselector-' in parent else parent
                parent = parent.split('/subnetselector-')[0] if '/subnetselector-' in parent else parent
                if parent in dn_to_esg:
                    dn_to_esg[parent]['ip_selectors'].append(_extract_ip_from_attrs(attrs, attrs.get('dn', '')))

    # Stable, tidy output
    esgs = list(dn_to_esg.values())
    for e in esgs:
        e['prov_contracts'] = sorted(set(filter(None, e['prov_contracts'])))
        e['cons_contracts'] = sorted(set(filter(None, e['cons_contracts'])))
        e['epg_selectors'] = sorted(set(filter(None, e['epg_selectors'])))
        e['ip_selectors']  = sorted(set(filter(None, e['ip_selectors'])))
        e['tag_selectors'] = sorted(set(filter(None, e['tag_selectors'])))
    return esgs
