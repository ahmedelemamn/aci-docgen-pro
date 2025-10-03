from ..utils.normalize import simple_attr, sorted_unique


def _extract_name_from_tdn(tdn: str, marker: str) -> str:
    if not tdn:
        return ''

    for part in reversed(tdn.split('/')):
        if part.startswith(f"{marker}-"):
            return part.split(f"{marker}-", 1)[1]

    return tdn.split('/')[-1]


def _binding_display(dn: str) -> str:
    if not dn:
        return ''

    if '/ap-' in dn and '/epg-' in dn:
        ap = dn.split('/ap-')[1].split('/')[0]
        epg = dn.split('/epg-')[1].split('/')[0]
        return f"AP {ap}/{epg}"

    if '/out-' in dn and '/instP-' in dn:
        l3out = dn.split('/out-')[1].split('/')[0]
        instp = dn.split('/instP-')[1].split('/')[0]
        return f"L3Out {l3out}/{instp}"

    if '/l2out-' in dn and '/instP-' in dn:
        l2out = dn.split('/l2out-')[1].split('/')[0]
        instp = dn.split('/instP-')[1].split('/')[0]
        return f"L2Out {l2out}/{instp}"

    if '/grp-' in dn:
        return dn.split('/grp-')[1].split('/')[0]

    if 'uni/tn-' in dn:
        return dn.split('uni/tn-')[-1]

    return dn


def _subject_flags(attrs: dict) -> list:
    flags = []
    if attrs.get('revFltPorts') == 'yes':
        flags.append('revFltPorts')
    if attrs.get('applyToFrag') == 'yes':
        flags.append('applyToFrag')

    if attrs.get('prio') and attrs.get('prio') not in ('unspecified', 'level1'):
        flags.append(f"prio:{attrs.get('prio')}")

    if attrs.get('targetDscp') and attrs.get('targetDscp') not in ('unspecified', 'CS0'):
        flags.append(f"targetDscp:{attrs.get('targetDscp')}")

    if attrs.get('consMatchT') and attrs.get('consMatchT') not in ('AtleastOne',):
        flags.append(f"consMatch:{attrs.get('consMatchT')}")

    if attrs.get('provMatchT') and attrs.get('provMatchT') not in ('AtleastOne',):
        flags.append(f"provMatch:{attrs.get('provMatchT')}")

    return sorted_unique(flags)


def harvest_contracts_for_tenant(api, tenant):
    subtree = api.mo_subtree(tenant['dn'])
    cps = []
    dn_to_cp = {}
    subj_dn_to_subject = {}

    for item in subtree.get('imdata', []):
        if 'vzBrCP' in item:
            a = simple_attr(item, 'vzBrCP')
            dn_to_cp[a.get('dn')] = {
                'name': a.get('name'),
                'scope': a.get('scope'),
                'subjects': [],
                'providers': [],
                'consumers': []
            }

    for item in subtree.get('imdata', []):
        if 'vzSubj' in item:
            a = simple_attr(item, 'vzSubj')
            parent = a.get('dn', '').split('/subj-')[0]
            if parent in dn_to_cp:
                subject = {
                    'name': a.get('name'),
                    'flags': _subject_flags(a),
                    'filters': [],
                    'graphs': []
                }
                dn_to_cp[parent]['subjects'].append(subject)
                subj_dn_to_subject[a.get('dn')] = subject

    for item in subtree.get('imdata', []):
        if 'vzRsSubjFiltAtt' in item:
            a = simple_attr(item, 'vzRsSubjFiltAtt')
            parent = a.get('dn', '').rsplit('/', 1)[0]
            if parent in subj_dn_to_subject:
                name = _extract_name_from_tdn(a.get('tDn', ''), 'flt')
                if not name:
                    name = a.get('tDn', '')
                subj_dn_to_subject[parent]['filters'].append(name)

        if 'vzRsSubjGraphAtt' in item:
            a = simple_attr(item, 'vzRsSubjGraphAtt')
            parent = a.get('dn', '').rsplit('/', 1)[0]
            if parent in subj_dn_to_subject:
                name = _extract_name_from_tdn(a.get('tDn', ''), 'graph')
                if not name:
                    name = a.get('tDn', '')
                subj_dn_to_subject[parent]['graphs'].append(name)

        if 'fvRsProv' in item:
            a = simple_attr(item, 'fvRsProv')
            contract_dn = a.get('tDn')
            if contract_dn in dn_to_cp:
                dn_to_cp[contract_dn]['providers'].append(_binding_display(a.get('dn', '')))

        if 'fvRsCons' in item:
            a = simple_attr(item, 'fvRsCons')
            contract_dn = a.get('tDn')
            if contract_dn in dn_to_cp:
                dn_to_cp[contract_dn]['consumers'].append(_binding_display(a.get('dn', '')))

    for cp in dn_to_cp.values():
        for subject in cp['subjects']:
            subject['filters'] = sorted_unique(subject['filters'])
            subject['graphs'] = sorted_unique(subject['graphs'])
            subject['flags'] = sorted_unique(subject['flags'])
        cp['subjects'].sort(key=lambda s: s['name'] or '')
        cp['providers'] = sorted_unique(cp['providers'])
        cp['consumers'] = sorted_unique(cp['consumers'])

    cps.extend(dn_to_cp.values())
    return cps
