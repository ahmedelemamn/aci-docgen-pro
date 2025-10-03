# ACI DocGen Pro

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Status](https://img.shields.io/badge/status-active-success)
![License](https://img.shields.io/badge/license-MIT-green)

Automated documentation generator for Cisco ACI fabrics.  
Harvests APIC configuration via REST API and produces Markdown documentation, test plans, and structured JSON for audits.

---

## Features

- Tenant Documentation
  - VRFs, Bridge Domains (with attributes & subnets)
  - EPGs (domains, static bindings, ports)
  - Contracts (provided/consumed, filters)
  - L2Outs, L3Outs (protocols, subnets)
  - Service Graphs (nodes, redirect policies)
  - Endpoint Security Groups (ESGs: contracts, selectors)

- Fabric-Wide Output
  - Markdown docs (per tenant + index)
  - Auto-generated test plan (`testing.md`)
  - JSON snapshot (`reports/summary.json`) for further automation
  - Excel/CSV export support (coming soon)

- Extensible
  - Modular harvesters (`aci_docgen/harvesters/`)
  - Toggle sections in `sections.yml`
  - Jinja2 templates for Markdown/PDF/Confluence

---

## Installation

```bash
git clone https://github.com/<youruser>/aci-docgen-pro.git
cd aci-docgen-pro
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
````

---

## Usage

```bash
python cli.py \
  --apic https://<APIC_HOST> \
  --user <USERNAME> \
  --password '<PASSWORD>' \
  --insecure \
  --out out \
  --debug
```

Options:

* `--insecure` : skip SSL verification (APIC with self-signed certs)
* `--debug` : print API URLs & payloads for troubleshooting
* `--sections` : specify a custom sections file (default: `sections.yml`)

Docs will be written to `out/`:

```
out/
├── index.md             # Fabric overview
├── tenants/<tenant>.md  # Per-tenant documentation
├── testing.md           # Auto test plan
└── reports/summary.json # Raw harvested data
```

---

## Configuration

`sections.yml` lets you toggle what to include:

```yaml
tenants: true
vrfs: true
bds: true
epgs: true
contracts: true
l3out: true
l2out: true
service_graphs: true
esg: true
vmm: true
include_system_tenants: false
testing: true
```

---

## Example Output

### Tenants

| Tenant | VRFs | BDs | EPGs | Contracts |
| ------ | ---- | --- | ---- | --------- |
| DC1    | 3    | 12  | 24   | 8         |

### Bridge Domains

| Name         | Unicast Routing | ARP Flood | L2 Ucast | Limit IP Learn | Subnets                  |
| ------------ | --------------- | --------- | -------- | -------------- | ------------------------ |
| WEB_VLAN_107 | yes             | no        | proxy    | yes            | 10.100.107.1/24 (public) |
| BD_ESXI_DB   | yes             | yes       | proxy    | yes            | 10.100.120.1/24 (public) |

### ESGs

| ESG         | Isolation  | pcTag | Provided | Consumed | EPG Selectors                        | IP Selectors    | Tag Selectors |
| ----------- | ---------- | ----- | -------- | -------- | ------------------------------------ | --------------- | ------------- |
| WEB_APP_ESG | unenforced | 5474  | —        | —        | EPG_WEB_EXT_107,<br/>EPG_WEB_EXT_108 | 10.100.109.0/24 | None          |

---

## Roadmap

* [ ] Export to CSV/Excel cutsheets
* [ ] Confluence integration (Markdown → Pages)
* [ ] More BD/EPG/Contract attributes (DHCP relay, QoS, etc.)
* [ ] Automated topology diagrams (Graphviz/Diagrams Python)
* [ ] Unit tests & CI pipeline

---

## Contributing

1. Fork this repo
2. Create a feature branch (`git checkout -b feature/foo`)
3. Commit changes (`git commit -m "Add foo"`)
4. Push to branch (`git push origin feature/foo`)
5. Open a Pull Request

---

## License

MIT License — feel free to use, modify, and share.

---

## Acknowledgements

* Cisco APIC API & Cobra SDK documentation
* Community ACI automation tooling for inspiration