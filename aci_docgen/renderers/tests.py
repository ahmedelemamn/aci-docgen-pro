import os
from jinja2 import Environment, FileSystemLoader

class TestsRenderer:
    def __init__(self, outdir):
        self.outdir = outdir
        self.env = Environment(loader=FileSystemLoader('templates'), trim_blocks=True, lstrip_blocks=True)

    def render(self, data):
        tdir = os.path.join(self.outdir, 'tests')
        os.makedirs(tdir, exist_ok=True)
        tpl = self.env.get_template('tests.md.j2')
        with open(os.path.join(tdir, 'README.md'), 'w') as f:
            f.write(tpl.render(data=data))
