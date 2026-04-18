"""HTTP GET tool — for API health checks, version endpoints, etc."""
import httpx


async def get(url: str, timeout: int = 15) -> str:
    timeout = min(max(timeout, 1), 60)
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            r = await client.get(url)
    except Exception as e:
        return f"[http error] {type(e).__name__}: {e}"
    body = r.text
    if len(body) > 4096:
        body = body[:4096] + f"\n... [truncated, total {len(body)} chars]"
    return f"[{r.status_code}] {url}\n{body}"
