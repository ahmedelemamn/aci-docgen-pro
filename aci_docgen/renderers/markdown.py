import os, json
from jinja2 import Environment, FileSystemLoader
from ..utils.log import info
from .tests import TestsRenderer

class MarkdownRenderer:
    def __init__(self, outdir):
        self.outdir = outdir
        self.env = Environment(loader=FileSystemLoader('templates'), trim_blocks=True, lstrip_blocks=True)

    def write_reports(self, data):
        repdir = os.path.join(self.outdir, 'reports')
        os.makedirs(repdir, exist_ok=True)
        with open(os.path.join(repdir, 'summary.json'), 'w') as f:
            json.dump(data, f, indent=2)

    def render(self, data):
        os.makedirs(self.outdir, exist_ok=True)
        os.makedirs(os.path.join(self.outdir, 'tenants'), exist_ok=True)

        # index
        idx = self.env.get_template('index.md.j2').render(data=data)
        with open(os.path.join(self.outdir, 'index.md'), 'w') as f:
            f.write(idx)

        # per-tenant
        ttpl = self.env.get_template('tenant.md.j2')
        for t in data.get('tenants', []):
            body = ttpl.render(tenant=t)
            with open(os.path.join(self.outdir, 'tenants', f"{t['name']}.md"), 'w') as f:
                f.write(body)

        self.write_reports(data)
        info(f"Wrote Markdown to {self.outdir}")

        # testing plan
        if data.get('tenants') is not None:
            if os.path.exists(os.path.join('templates','testing.md.j2')):
                ttpl = self.env.get_template('testing.md.j2')
                body = ttpl.render(data=data)
                with open(os.path.join(self.outdir, 'testing.md'), 'w') as f:
                    f.write(body)
