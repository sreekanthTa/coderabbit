import hashlib
import hmac
import logging
import os

from dotenv import load_dotenv
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response

from services.review_flow import run_code_review

load_dotenv()

GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

if not GITHUB_WEBHOOK_SECRET:
    raise RuntimeError("GITHUB_WEBHOOK_SECRET is not configured")


logger = logging.getLogger(__name__)

router = APIRouter()

REVIEW_ACTIONS = {"opened", "synchronize", "reopened"}


def verify_github_signature(
    payload: bytes,
    signature: str | None,
) -> bool:
    if not signature:
        return False

    expected_signature = "sha256=" + hmac.new(
        GITHUB_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(
        expected_signature,
        signature
    )


async def _review_pull_request(owner: str, repo: str, pr_number: int) -> None:
    try:
        review = await run_code_review(owner, repo, pr_number)
    except Exception:
        logger.exception(
            "Review failed for %s/%s PR #%s", owner, repo, pr_number
        )
        return

    logger.info(
        "Reviewed %s/%s PR #%s: %s issue(s)",
        owner,
        repo,
        pr_number,
        len(review.issues),
    )


@router.post("/webhooks/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    response: Response,
):

    payload = await request.body()

    signature = request.headers.get(
        "X-Hub-Signature-256"
    )

    if not verify_github_signature(
        payload,
        signature
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid GitHub webhook signature"
        )

    event = request.headers.get("X-GitHub-Event")

    data = await request.json()

    if event != "pull_request":
        return {
            "status": "ignored",
            "reason": "not a pull_request event"
        }

    action = data.get("action")

    if action not in REVIEW_ACTIONS:
        return {
            "status": "ignored",
            "action": action
        }

    pr_number = data.get("number")

    repository = data.get("repository") or {}
    full_name = repository.get("full_name")

    parts = full_name.split("/") if full_name else []

    if len(parts) != 2 or not pr_number:
        raise HTTPException(
            status_code=400,
            detail="Webhook payload is missing the repository or PR number",
        )

    owner, repo = parts

    background_tasks.add_task(
        _review_pull_request,
        owner,
        repo,
        pr_number,
    )

    response.status_code = 202

    return {
        "status": "accepted",
        "repository": full_name,
        "pr_number": pr_number,
    }