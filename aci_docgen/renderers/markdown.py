import os, json
from jinja2 import Environment, FileSystemLoader
from ..utils.log import info

class MarkdownRenderer:
    def __init__(self, outdir):
        self.outdir = outdir
        self.env = Environment(loader=FileSystemLoader('templates'), trim_blocks=True, lstrip_blocks=True)

    def write_reports(self, data):
        repdir = os.path.join(self.outdir, 'reports')
        os.makedirs(repdir, exist_ok=True)
        with open(os.path.join(repdir, 'summary.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def render(self, data):
        os.makedirs(self.outdir, exist_ok=True)
        os.makedirs(os.path.join(self.outdir, 'tenants'), exist_ok=True)

        # index
        idx = self.env.get_template('index.md.j2').render(data=data)
        with open(os.path.join(self.outdir, 'index.md'), 'w', encoding='utf-8') as f:
            f.write(idx)

        # per-tenant
        ttpl = self.env.get_template('tenant.md.j2')
        for t in data.get('tenants', []):
            body = ttpl.render(tenant=t)
            with open(os.path.join(self.outdir, 'tenants', f"{t['name']}.md"), 'w', encoding='utf-8') as f:
                f.write(body)

        # testing plan (if template exists)
        if data.get('tenants') is not None and os.path.exists(os.path.join('templates','testing.md.j2')):
            tplan = self.env.get_template('testing.md.j2').render(data=data)
            with open(os.path.join(self.outdir, 'testing.md'), 'w', encoding='utf-8') as f:
                f.write(tplan)

        self.write_reports(data)
        info(f"Wrote Markdown to {self.outdir}")
