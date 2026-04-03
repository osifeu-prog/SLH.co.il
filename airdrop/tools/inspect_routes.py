from app.main import app

def show(path: str):
    hits = []
    for r in app.routes:
        if getattr(r, "path", None) == path:
            ep = getattr(r, "endpoint", None)
            hits.append((
                getattr(r, "name", None),
                sorted(list(getattr(r, "methods", []) or [])),
                getattr(ep, "__module__", None),
                getattr(ep, "__qualname__", None),
            ))
    print(path, "count=", len(hits))
    for i,(name,methods,mod,qual) in enumerate(hits, 1):
        print(f" {i}. name={name} methods={methods} endpoint={mod}.{qual}")

show("/public/progress")
show("/api/v1/public/progress")
