import yaml
import os

SPEC_FILE = "slh_v4_spec.yaml"
OUTPUT_DIR = "generated_v4"


def load_spec():
    with open(SPEC_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def generate_service(domain_name, domain_data):
    service_name = domain_data.get("service") or f"slh-{domain_name}-service"
    endpoints = domain_data.get("endpoints", [])

    base_path = os.path.join(OUTPUT_DIR, service_name)
    ensure_dir(base_path)

    # app.py
    app_file = os.path.join(base_path, "app.py")

    with open(app_file, "w", encoding="utf-8") as f:
        f.write("from fastapi import FastAPI\n\n")
        f.write("app = FastAPI()\n\n")

        for ep in endpoints:
            try:
                method, path = ep.split(" ", 1)
            except:
                continue

            func_name = (
                path.replace("/", "_")
                .replace("{", "")
                .replace("}", "")
                .strip("_")
            )

            f.write(f"@app.{method.lower()}('{path}')\n")
            f.write(f"def {func_name}():\n")
            f.write("    return {'status': 'ok', 'endpoint': '" + path + "'}\n\n")

    # db.py
    db_file = os.path.join(base_path, "db.py")
    with open(db_file, "w", encoding="utf-8") as f:
        f.write(f"# DB layer for {service_name}\n")
        f.write("class DB:\n")
        f.write("    def connect(self):\n")
        f.write("        pass\n")

    print(f"[OK] Generated service: {service_name}")


def main():
    spec = load_spec()
    domains = spec.get("domains", {})

    ensure_dir(OUTPUT_DIR)

    for domain_name, domain_data in domains.items():
        generate_service(domain_name, domain_data)

    print("\nDONE: V4 ecosystem generated")


if __name__ == "__main__":
    main()
