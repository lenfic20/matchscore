"""Matchscore API gateway. SportAPI credentials stay on the server."""
import os, time, asyncio
from typing import Any
from urllib.parse import quote
import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

HOST = "sportapi7.p.rapidapi.com"
BASE = f"https://{HOST}"
API_KEY = os.getenv("RAPIDAPI_KEY", "").strip()
CACHE: dict[str, tuple[float, Any]] = {}
LOCK = asyncio.Lock()

app = FastAPI(title="Matchscore API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","), allow_methods=["GET", "OPTIONS"], allow_headers=["*"])


def ttl_for(path: str) -> int:
    p = path.lower()
    if "/events/live" in p: return 12
    if "/scheduled-events/" in p: return 45
    if "/standings/" in p or "/winners/" in p: return 3600
    if "/statistics" in p or "/lineups" in p or "/incidents" in p: return 25
    return 180


async def fetch_sportapi(path: str, params: dict | None = None):
    if not API_KEY:
        raise HTTPException(503, "Sports API is not configured. Add RAPIDAPI_KEY to the backend environment.")
    clean = "/" + "/".join(quote(part, safe="-_.~") for part in path.strip("/").split("/"))
    if ".." in clean or not clean.startswith("/api/v1/"):
        raise HTTPException(400, "Invalid API route")
    query = tuple(sorted((params or {}).items()))
    cache_key = clean + repr(query)
    now = time.time()
    cached = CACHE.get(cache_key)
    if cached and cached[0] > now:
        return cached[1]
    headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}
    timeout = httpx.Timeout(18.0, connect=8.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        last_error = None
        for attempt in range(2):
            try:
                response = await client.get(BASE + clean, headers=headers, params=params)
                if response.status_code == 429:
                    raise HTTPException(429, "SportAPI rate limit reached. Please wait and try again.")
                if response.status_code >= 500 and attempt == 0:
                    await asyncio.sleep(0.4)
                    continue
                if response.status_code >= 400:
                    detail = response.text[:300]
                    raise HTTPException(response.status_code, f"SportAPI returned {response.status_code}: {detail}")
                data = response.json()
                CACHE[cache_key] = (now + ttl_for(clean), data)
                return data
            except HTTPException:
                raise
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                if attempt == 0:
                    await asyncio.sleep(0.4)
        raise HTTPException(502, f"Could not reach SportAPI: {str(last_error)[:180]}")


@app.get("/api/health")
async def health():
    return {"ok": True, "configured": bool(API_KEY), "provider": HOST}


@app.get("/api/sports/{sport}/live")
async def live(sport: str):
    if sport not in {"football", "basketball", "tennis"}: raise HTTPException(400, "Unsupported sport")
    return await fetch_sportapi(f"/api/v1/sport/{sport}/events/live")


@app.get("/api/sports/{sport}/date/{match_date}")
async def by_date(sport: str, match_date: str, timezone_offset: int = Query(default=0, alias="timezoneOffset")):
    if sport not in {"football", "basketball", "tennis"}: raise HTTPException(400, "Unsupported sport")
    return await fetch_sportapi(f"/api/v1/sport/{sport}/scheduled-events/{match_date}", {"timezoneOffset": timezone_offset})


@app.get("/api/proxy/{path:path}")
async def proxy(path: str):
    return await fetch_sportapi("/" + path)


@app.get("/api/cache/clear")
async def clear_cache():
    CACHE.clear()
    return {"ok": True}

@app.get("/{path:path}")
async def frontend(path: str):
    root = os.path.join(os.path.dirname(__file__), "..", "frontend")
    target = os.path.join(root, path)
    if path and os.path.isfile(target): return FileResponse(target)
    return FileResponse(os.path.join(root, "index.html"))
