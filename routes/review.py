import logging

import httpx
from fastapi import APIRouter, HTTPException

from schemas import ReviewRequest
from services.github import parse_github_pr_url
from services.review_flow import run_code_review

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/review")
async def review_pr(request: ReviewRequest):
    try:
        owner, repo, pr_number = parse_github_pr_url(request.url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    logger.info("Reviewing %s/%s PR #%s", owner, repo, pr_number)

    try:
        review = await run_code_review(owner, repo, pr_number)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"GitHub API returned {exc.response.status_code}",
        ) from exc

    return {
        "repository": f"{owner}/{repo}",
        "pr_number": pr_number,
        "issues": [
            issue.model_dump()
            for issue in review.issues
        ],
    }
