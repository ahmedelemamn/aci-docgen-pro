import requests
from .utils.log import debug
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
class AciApi:
    def __init__(self, apic, user, pw, insecure=False, debug_enabled=False):
        self.apic = apic.rstrip('/')
        self.s = requests.Session()
        self.s.verify = not insecure
        self.debug_enabled = debug_enabled
        self.login(user, pw)

    def login(self, user, pw):
        url = f"{self.apic}/api/aaaLogin.json"
        r = self.s.post(url, json={'aaaUser': {'attributes': {'name': user, 'pwd': pw}}})
        r.raise_for_status()

    def mo_subtree(self, dn, extra=""):
        url = f"{self.apic}/api/node/mo/{dn}.json?query-target=subtree&rsp-subtree=full{extra}"
        debug(f"GET {url}", self.debug_enabled)
        r = self.s.get(url)
        r.raise_for_status()
        return r.json()

    def class_query(self, cls, extra=""):
        url = f"{self.apic}/api/class/{cls}.json{extra}"
        debug(f"GET {url}", self.debug_enabled)
        r = self.s.get(url)
        r.raise_for_status()
        return r.json()
