#!/usr/bin/env python3
import argparse, os, yaml
from aci_docgen.aci_api import AciApi
from aci_docgen.pipeline import run_harvest
from aci_docgen.renderers.markdown import MarkdownRenderer
from aci_docgen.utils.log import info, debug

def main():
    p = argparse.ArgumentParser(description='ACI DocGen Pro')
    p.add_argument('--apic', required=True)
    p.add_argument('--user', required=True)
    p.add_argument('--password', required=True)
    p.add_argument('--out', default='out')
    p.add_argument('--insecure', action='store_true')
    p.add_argument('--debug', action='store_true')
    p.add_argument('--sections', default='sections.yml')
    args = p.parse_args()

    with open(args.sections) as f:
        sections = yaml.safe_load(f) or {}

    api = AciApi(args.apic, args.user, args.password, insecure=args.insecure, debug_enabled=args.debug)
    data = run_harvest(api, sections, debug_enabled=args.debug)

    os.makedirs(args.out, exist_ok=True)
    md = MarkdownRenderer(args.out)
    md.render(data)

    info(f"Documentation written to: {args.out}")

if __name__ == '__main__':
    main()
