from collections import defaultdict

from ..utils.normalize import simple_attr

def harvest_service_graphs_for_tenant(api, tenant):
    subtree = api.mo_subtree(tenant['dn'])
    dn_to_graph = {}
    node_lookup = {}
    graph_name_to_dn = {}
    graph_bindings = defaultdict(list)
    # abstract graphs
    for item in subtree.get('imdata', []):
        if 'vnsAbsGraph' in item:
            a = simple_attr(item, 'vnsAbsGraph')
            dn = a.get('dn')
            if not dn:
                continue
            graph = {
                'name': a.get('name'),
                'dn': dn,
                'nodes': [],
                'connections': [],
                'redirect_policies': [],
                'bound_contract_subjects': [],
            }
            dn_to_graph[dn] = graph
            if a.get('name'):
                graph_name_to_dn[a.get('name')] = dn
    # nodes
    for item in subtree.get('imdata', []):
        if 'vnsAbsNode' in item:
            a = simple_attr(item, 'vnsAbsNode')
            parent = a.get('dn', '').split('/AbsNode-')[0]
            if parent in dn_to_graph:
                node = {
                    'name': a.get('name'),
                    'funcType': a.get('funcType'),
                    'dn': a.get('dn'),
                    'connectors': [],
                }
                dn_to_graph[parent]['nodes'].append(node)
                if node['dn']:
                    node_lookup[node['dn']] = node
    # node connectors
    for item in subtree.get('imdata', []):
        if 'vnsAbsFuncConn' in item:
            a = simple_attr(item, 'vnsAbsFuncConn')
            node_dn = a.get('dn', '').split('/AbsFuncConn-')[0]
            node = node_lookup.get(node_dn)
            if not node:
                continue
            connector_attrs = _clean_attributes(a)
            connector = {
                'name': a.get('name'),
                'attributes': connector_attrs,
                'summary': _build_connector_summary(a),
            }
            node['connectors'].append(connector)
    # redirect policies (if any)
    for item in subtree.get('imdata', []):
        if 'vnsRedirectPol' in item:
            a = simple_attr(item, 'vnsRedirectPol')
            # try to associate to nearest graph by dn prefix
            parent = a.get('dn', '').split('/redirectPol-')[0]
            for dn in dn_to_graph:
                if parent.startswith(dn):
                    name = a.get('name')
                    if name and name not in dn_to_graph[dn]['redirect_policies']:
                        dn_to_graph[dn]['redirect_policies'].append(name)
    # graph connections
    for item in subtree.get('imdata', []):
        if 'vnsAbsConnection' in item:
            a = simple_attr(item, 'vnsAbsConnection')
            parent = a.get('dn', '').split('/AbsConnection-')[0]
            if parent in dn_to_graph:
                connection_attrs = _clean_attributes(a)
                connection = {
                    'name': a.get('name'),
                    'attributes': connection_attrs,
                    'summary': _build_connection_summary(a),
                }
                dn_to_graph[parent]['connections'].append(connection)
    # contract bindings (graph references)
    for item in subtree.get('imdata', []):
        if 'vzRsSubjGraphAtt' in item:
            _record_binding(
                item,
                'vzRsSubjGraphAtt',
                dn_to_graph,
                graph_name_to_dn,
                graph_bindings,
            )
        elif 'vzRsGraphAtt' in item:
            _record_binding(
                item,
                'vzRsGraphAtt',
                dn_to_graph,
                graph_name_to_dn,
                graph_bindings,
            )
    # finalise graphs
    graphs = []
    for dn, graph in dn_to_graph.items():
        graph['bound_contract_subjects'] = graph_bindings.get(dn, [])
        # strip helper fields not needed by templates
        cleaned_nodes = []
        for node in graph['nodes']:
            cleaned_connectors = [
                {k: v for k, v in connector.items() if k != 'attributes' or v}
                for connector in node.get('connectors', [])
            ]
            cleaned_node = {k: v for k, v in node.items() if k != 'dn'}
            cleaned_node['connectors'] = cleaned_connectors
            cleaned_nodes.append(cleaned_node)
        graph['nodes'] = cleaned_nodes
        graph['connections'] = [
            {k: v for k, v in connection.items() if k != 'attributes' or v}
            for connection in graph['connections']
        ]
        graph.pop('dn', None)
        graphs.append(graph)
    return graphs


def _clean_attributes(attrs):
    """Remove noisy keys from an attribute dictionary."""

    ignored = {'childAction', 'dn', 'lcOwn', 'modTs', 'rn', 'status', 'uid'}
    cleaned = {}
    for key, value in attrs.items():
        if key in ignored:
            continue
        if value in (None, '', 'unspecified'):
            continue
        cleaned[key] = value
    return cleaned


def _build_connector_summary(attrs):
    name = attrs.get('name') or 'connector'
    parts = []
    if attrs.get('connType'):
        parts.append(f"connType: {attrs['connType']}")
    if attrs.get('type'):
        parts.append(f"type: {attrs['type']}")
    if attrs.get('order'):
        parts.append(f"order: {attrs['order']}")
    if attrs.get('adjType'):
        parts.append(f"adjType: {attrs['adjType']}")
    if attrs.get('directConnectPort'):
        parts.append(f"directPort: {attrs['directConnectPort']}")
    return f"{name} ({', '.join(parts)})" if parts else name


def _build_connection_summary(attrs):
    name = attrs.get('name') or 'connection'
    parts = []
    if attrs.get('connDir'):
        parts.append(f"dir: {attrs['connDir']}")
    if attrs.get('connType'):
        parts.append(f"type: {attrs['connType']}")
    if attrs.get('adjType'):
        parts.append(f"adj: {attrs['adjType']}")
    if attrs.get('directed'):
        parts.append(f"directed: {attrs['directed']}")
    if attrs.get('targetName'):
        parts.append(f"target: {attrs['targetName']}")
    if attrs.get('sourceName'):
        parts.append(f"source: {attrs['sourceName']}")
    return f"{name} ({', '.join(parts)})" if parts else name


def _record_binding(item, cls, dn_to_graph, graph_name_to_dn, graph_bindings):
    attrs = simple_attr(item, cls)
    dn = attrs.get('dn', '')
    contract = None
    subject = None
    for part in dn.split('/'):
        if part.startswith('brc-'):
            contract = part[4:]
        elif part.startswith('subj-'):
            subject = part[5:]
    graph_dn = attrs.get('tDn')
    if not graph_dn:
        graph_name = attrs.get('tnVnsAbsGraphName') or attrs.get('graphName')
        if graph_name:
            graph_dn = graph_name_to_dn.get(graph_name)
    if graph_dn and graph_dn not in dn_to_graph:
        # Sometimes tDn references the graph's AbsGraph child directly
        for candidate in dn_to_graph:
            if graph_dn.startswith(candidate):
                graph_dn = candidate
                break
    if not graph_dn or graph_dn not in dn_to_graph:
        return
    contract_name = contract or attrs.get('tnVzBrCPName')
    if not contract_name:
        return
    subject_name = subject or attrs.get('tnVzSubjName')
    binding = {
        'contract': contract_name,
        'subject': subject_name or '—',
    }
    existing = graph_bindings[graph_dn]
    if binding not in existing:
        existing.append(binding)
