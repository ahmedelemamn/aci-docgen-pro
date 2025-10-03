from .harvesters.tenants import harvest_tenants
from .harvesters.vrfs import harvest_vrfs_for_tenant
from .harvesters.bds import harvest_bds_for_tenant
from .harvesters.epgs import harvest_epgs_for_tenant
from .harvesters.contracts import harvest_contracts_for_tenant
from .harvesters.l3out import harvest_l3out_for_tenant
from .harvesters.l2out import harvest_l2out_for_tenant
from .harvesters.service_graphs import harvest_service_graphs_for_tenant
from .harvesters.esg import harvest_esg_for_tenant

SYSTEM_TENANTS = {"mgmt", "common", "infra"}

def run_harvest(api, sections, debug_enabled=False):
    fabric = {'tenants': []}

    tenants = harvest_tenants(api, debug_enabled=debug_enabled) if sections.get('tenants') else []
    # filter if requested
    if not sections.get('include_system_tenants', False):
        tenants = [t for t in tenants if t['name'] not in SYSTEM_TENANTS]

    for tn in tenants:
        entry = {'name': tn['name']}
        if sections.get('tenants'):
            entry['vrfs'] = harvest_vrfs_for_tenant(api, tn)
            entry['bds'] = harvest_bds_for_tenant(api, tn)
            entry['epgs'] = harvest_epgs_for_tenant(api, tn)
        if sections.get('contracts'):
            entry['contracts'] = harvest_contracts_for_tenant(api, tn)
        if sections.get('l3out'):
            entry['l3outs'] = harvest_l3out_for_tenant(api, tn)
        if sections.get('l2out'):
            entry['l2outs'] = harvest_l2out_for_tenant(api, tn)
        if sections.get('service_graphs'):
            entry['service_graphs'] = harvest_service_graphs_for_tenant(api, tn)
        if sections.get('vmm'):
            from .harvesters.vmm import harvest_vmm_for_tenant
            entry['vmm'] = harvest_vmm_for_tenant(api, tn)
        if sections.get('esg'):
            entry['esgs'] = harvest_esg_for_tenant(api, tn)

        fabric['tenants'].append(entry)

    return fabric
