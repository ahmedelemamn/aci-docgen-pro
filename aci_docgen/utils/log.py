import sys

def info(msg):
    print(f"[+] {msg}")

def debug(msg, enabled=False):
    if enabled:
        print(f"[D] {msg}")

def warn(msg):
    print(f"[!] {msg}", file=sys.stderr)

def error(msg):
    print(f"[X] {msg}", file=sys.stderr)
