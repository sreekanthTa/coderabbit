import logging

from fastapi import APIRouter, Request

from services.review_flow import run_code_review

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/webhooks/github")
async def github_webhook(request: Request):

    event = request.headers.get("X-GitHub-Event")
    data = await request.json()

    if event != "pull_request":
        return {
            "status": "ignored",
            "reason": "not a pull_request event"
        }

    action = data.get("action")

    if action not in ["opened", "synchronize", "reopened"]:
        return {
            "status": "ignored",
            "action": action
        }

    pr_number = data.get("number")

    repository = data.get("repository")
    full_name = repository.get("full_name")

    owner, repo = full_name.split("/")

    # Run our existing V1 review pipeline
    review = await run_code_review(
        owner,
        repo,
        pr_number
    )

    return {
        "status": "reviewed",
        "action": action,
        "repository": full_name,
        "pr_number": pr_number,
        "issues": len(review.issues)
    }