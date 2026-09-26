import logging

from fastapi import APIRouter, Request

from services.review_flow import run_code_review

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/webhooks/github")
async def github_webhook(request: Request):
    event = request.headers.get("X-GitHub-Event")
    data = await request.json()

    logger.info("GitHub event: %s", event)

    if event != "pull_request":
        return {"status": "ignored"}

    action = data.get("action")

    logger.info("Action: %s", action)

    if action not in ["opened", "synchronize", "reopened"]:
        return {
            "status": "ignored",
            "action": action,
        }

    pr_number = data.get("number")

    repository = data.get("repository")
    full_name = repository.get("full_name")

    owner, repo = full_name.split("/")

    logger.info("Repository: %s, PR: %s", full_name, pr_number)

    review = await run_code_review(owner, repo, pr_number)

    return {
        "status": "reviewed",
        "repository": full_name,
        "pr_number": pr_number,
        "issues": len(review.issues),
    }
