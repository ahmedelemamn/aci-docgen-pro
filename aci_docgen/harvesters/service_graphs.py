from ..utils.normalize import simple_attr

def harvest_service_graphs_for_tenant(api, tenant):
    subtree = api.mo_subtree(tenant['dn'])
    graphs = []
    dn_to_graph = {}
    # abstract graphs
    for item in subtree.get('imdata', []):
        if 'vnsAbsGraph' in item:
            a = simple_attr(item, 'vnsAbsGraph')
            dn_to_graph[a.get('dn')] = {'name': a.get('name'), 'nodes': [], 'redirect_policies': []}
    # nodes
    for item in subtree.get('imdata', []):
        if 'vnsAbsNode' in item:
            a = simple_attr(item, 'vnsAbsNode')
            parent = a.get('dn', '').split('/AbsNode-')[0]
            if parent in dn_to_graph:
                dn_to_graph[parent]['nodes'].append({'name': a.get('name'), 'funcType': a.get('funcType')})
    # redirect policies (if any)
    for item in subtree.get('imdata', []):
        if 'vnsRedirectPol' in item:
            a = simple_attr(item, 'vnsRedirectPol')
            # try to associate to nearest graph by dn prefix
            parent = a.get('dn', '').split('/redirectPol-')[0]
            for dn in dn_to_graph:
                if parent.startswith(dn):
                    dn_to_graph[dn]['redirect_policies'].append({'name': a.get('name')})
    return list(dn_to_graph.values())
