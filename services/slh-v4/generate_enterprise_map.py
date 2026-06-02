import yaml
import json
import os
from collections import defaultdict

SPEC_FILE = "slh_v4_spec.yaml"
OUTPUT_DIR = "enterprise_map"


# ---------------------------
# LOAD SPEC
# ---------------------------
def load_spec():
    with open(SPEC_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------
# ROI CLASSIFIER (simple rules engine)
# ---------------------------
def classify_roi(endpoint: str) -> str:
    e = endpoint.lower()

    if "wallet" in e or "payment" in e or "buy" in e or "sell" in e:
        return "HIGH"

    if "admin" in e or "deploy" in e or "logs" in e:
        return "STRATEGIC"

    if "roi" in e or "analytics" in e or "report" in e:
        return "MED"

    if "game" in e or "airdrop" in e or "meme" in e:
        return "ENGAGEMENT"

    return "LOW"


# ---------------------------
# BOT MAPPER (from your SLH ecosystem)
# ---------------------------
def bot_owner(domain):
    mapping = {
        "users": "SLH Core Bot",
        "wallet": "Wallet Bot",
        "payments": "SLH Core Bot",
        "roi": "Crazy Panel",
        "marketplace": "BotShop",
        "crm": "Campaign Bot",
        "ai": "SLH Claude AI",
        "admin": "MY_SUPER_ADMIN"
    }
    return mapping.get(domain, "UNKNOWN BOT")


# ---------------------------
# MAIN MAPPER
# ---------------------------
def build_map(spec):
    domains = spec.get("domains", {})

    system_map = {
        "services": {},
        "endpoints": {},
        "db": {},
        "bots": defaultdict(list),
        "roi": {},
        "graph": defaultdict(list)
    }

    for domain, data in domains.items():
        service = data.get("service", f"slh-{domain}-service")
        endpoints = data.get("endpoints", [])

        system_map["services"][domain] = service
        system_map["db"][domain] = f"{domain}_db"

        for ep in endpoints:
            entry = {
                "endpoint": ep,
                "domain": domain,
                "service": service,
                "db": f"{domain}_db",
                "bot": bot_owner(domain),
                "roi": classify_roi(ep)
            }

            system_map["endpoints"][ep] = entry

            system_map["bots"][entry["bot"]].append(ep)

            system_map["roi"].setdefault(entry["roi"], []).append(ep)

            system_map["graph"][domain].append(service)

    return system_map


# ---------------------------
# EXPORT
# ---------------------------
def export_map(system_map):
    ensure_dir(OUTPUT_DIR)

    with open(f"{OUTPUT_DIR}/full_map.json", "w", encoding="utf-8") as f:
        json.dump(system_map, f, indent=2)

    # readable summary
    with open(f"{OUTPUT_DIR}/summary.txt", "w", encoding="utf-8") as f:
        f.write("SLH ENTERPRISE v4 MAP\n\n")

        for domain, service in system_map["services"].items():
            f.write(f"{domain} â†’ {service}\n")

        f.write("\nROI DISTRIBUTION:\n")
        for k, v in system_map["roi"].items():
            f.write(f"{k}: {len(v)} endpoints\n")


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def main():
    spec = load_spec()
    system_map = build_map(spec)
    export_map(system_map)

    print("\n========================")
    print("SLH ENTERPRISE MAP DONE")
    print("========================")
    print(f"Output: {OUTPUT_DIR}/full_map.json")


if __name__ == "__main__":
    main()
