import asyncio
import os

import httpx
import websockets
from fastapi import APIRouter, Request, WebSocket
from fastapi.responses import JSONResponse, Response

CHROME_URL = os.environ.get("CHROME_DEBUG_URL", "http://127.0.0.1:9222").rstrip("/")

router = APIRouter(tags=["proxy"])


def _chrome_websocket_base(chrome_http_url: str) -> str:
    return chrome_http_url.replace("http://", "ws://").replace("https://", "wss://")


def _rewrite_cdp_host_references(content: bytes, netloc: bytes) -> bytes:
    return content.replace(b"localhost:9222", netloc).replace(b"127.0.0.1:9222", netloc)


def _public_origin_bytes(request: Request) -> bytes:
    forwarded_host = request.headers.get("x-forwarded-host")
    if forwarded_host:
        scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        return f"{scheme}://{forwarded_host}".encode()
    return f"{request.url.scheme}://{request.url.netloc}".encode()


@router.api_route("/{path:path}", methods=["GET", "POST"])
async def proxy_http(request: Request, path: str) -> Response:
    url = f"{CHROME_URL}/{path}" if path else f"{CHROME_URL}"
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                    k: v
                    for k, v in request.headers.items()
                    if k.lower() != "host"
                }
            rp_resp = await client.request(
                method=request.method,
                url=url,
                params=request.query_params,
                headers=headers,
            )
    except httpx.RequestError as e:
        return JSONResponse(
            status_code=502,
            content={"detail": f"Cannot connect to CDP ({CHROME_URL}): {e!s}"},
        )
    public = _public_origin_bytes(request)
    netloc = public.split(b"://", 1)[1]
    content = _rewrite_cdp_host_references(rp_resp.content, netloc)
    return Response(content=content, status_code=rp_resp.status_code)


@router.websocket("/devtools/{path:path}")
async def proxy_ws(websocket: WebSocket, path: str) -> None:
    await websocket.accept()
    target_url = f"{_chrome_websocket_base(CHROME_URL)}/devtools/{path}"

    async with websockets.connect(target_url) as target_ws:

        async def forward_to_chrome() -> None:
            async for message in websocket.iter_text():
                await target_ws.send(message)

        async def forward_to_client() -> None:
            async for message in target_ws:
                await websocket.send_text(message)

        await asyncio.gather(forward_to_chrome(), forward_to_client())
