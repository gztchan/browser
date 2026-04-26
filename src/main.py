import os
import signal
import httpx
import logging
import uvicorn
from fastapi import FastAPI

from .proxy import router as proxy_router

logging.basicConfig(level=logging.INFO)

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
BROWSER_ID = os.getenv("BROWSER_ID")
JOB_ID = os.getenv("JOB_ID")

logger = logging.getLogger("browser")

app = FastAPI(title="Browser")
app.include_router(proxy_router)

def handle_sigterm(signum, _):
    logger.debug(f"Signum: {signum}")
    if WEBHOOK_URL is not None:
        try:
            with httpx.Client() as client:
                client.post(WEBHOOK_URL, json={
                    "browser_id": BROWSER_ID,
                    "job_id": JOB_ID,
                    "status": "terminated",
                }, headers={ "Content-Type": "application/json" })
        except Exception as e:
            logger.error(f"Failed to update webhook status: {e}")
    exit(0)

def main() -> None:
    logger.info(f"BROWSER_ID: {BROWSER_ID}")
    logger.info(f"JOB_ID: {JOB_ID}")
    logger.info(f"WEBHOOK_URL: {WEBHOOK_URL}")

    if WEBHOOK_URL is not None:
        try:
            with httpx.Client() as client:
                client.post(WEBHOOK_URL, json={
                    "browser_id": BROWSER_ID,
                    "job_id": JOB_ID,
                    "status": "running",
                }, headers={ "Content-Type": "application/json" })
        except Exception as e:
            logger.error(f"Failed to update webhook status: {e}")
    uvicorn.run(app, host="0.0.0.0", port=8002)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigterm)
    main()
