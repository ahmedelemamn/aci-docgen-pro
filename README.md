# ACI DocGen Pro (Starter)

A modular, debuggable documentation generator for Cisco ACI.
- Clear module split for easier troubleshooting
- Jinja templating for Markdown output
- Optional parsing of external device configs (NX-OS/IOS-XE)
- Simple, readable requests-based APIC client

## Quick Start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python cli.py --apic https://APIC_HOST --user USER --password PASS --insecure --out out
```

Artifacts go to `out/`:
- `index.md` (fabric overview and ToC)
- `tenants/<tenant>.md` (per-tenant pages)
- `reports/summary.json` (raw harvested data snapshot)

## Layout

```
aci-docgen-pro/
├── cli.py
├── requirements.txt
├── sections.yml
├── templates/
│   ├── index.md.j2
│   └── tenant.md.j2
└── aci_docgen/
    ├── __init__.py
    ├── aci_api.py
    ├── pipeline.py
    ├── utils/
    │   ├── log.py
    │   └── normalize.py
    ├── harvesters/
    │   ├── tenants.py
    │   ├── vrfs.py
    │   ├── bds.py
    │   ├── epgs.py
    │   ├── contracts.py
    │   ├── l3out.py
    │   └── vmm.py
    ├── renderers/
        ├── markdown.py
        └── tables.py
```

## Troubleshooting tips
- Run with `PYTHONWARNINGS=default` to see SSL warnings if not using `--insecure`.
- Use `--debug` to print API URLs and sample payload sizes.
- Check `reports/summary.json` for the exact harvested structure.

