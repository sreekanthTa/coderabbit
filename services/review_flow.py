from services.github import (
    build_github_comment,
    build_review_input,
    get_pull_request_files,
    upsert_pr_comment,
)
from services.reviewer import review_code


async def run_code_review(owner, repo, pr_number):
    files = await get_pull_request_files(owner, repo, pr_number)

    review_input = build_review_input(files)

    review = await review_code(review_input)

    comment = build_github_comment(review)

    await upsert_pr_comment(owner, repo, pr_number, comment)

    return review
