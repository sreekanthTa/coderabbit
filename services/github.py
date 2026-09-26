import httpx

from config import GITHUB_TOKEN

REVIEW_HEADING = "## CodeGuard AI Review"


def _github_headers():
    headers = {"Accept": "application/vnd.github+json"}

    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    return headers


def parse_github_pr_url(url: str):
    parts = url.rstrip("/").split("/")

    if len(parts) < 7 or parts[5] != "pull" or not parts[6].isdigit():
        raise ValueError(
            f"Not a GitHub pull request URL: {url}. "
            "Expected https://github.com/<owner>/<repo>/pull/<number>"
        )

    owner = parts[3]
    repo = parts[4]
    pr_number = int(parts[6])

    return owner, repo, pr_number


async def get_pull_request_files(owner, repo, pr_number):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=_github_headers())

    response.raise_for_status()

    return response.json()


async def get_pr_comments(owner, repo, pr_number):
    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/issues/{pr_number}/comments"
    )

    params = {"per_page": 100}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=_github_headers(),
            params=params,
        )

    response.raise_for_status()

    return response.json()


def build_review_input(files):
    review_text = ""

    for file in files:
        filename = file["filename"]
        status = file["status"]
        patch = file.get("patch")

        if not patch:
            continue

        review_text += f"""
File: {filename}
Status: {status}

Diff:
{patch}

-------------------------
"""

    return review_text


def build_github_comment(review):

    if not review.issues:
        return f"{REVIEW_HEADING}\n\n✅ No issues found."

    comment = f"{REVIEW_HEADING}\n\n"

    for issue in review.issues:

        comment += f"""
### {issue.severity.upper()}

**File:** `{issue.file}`  
**Line:** `{issue.line}`

**Issue:** {issue.issue}

**Why:** {issue.why}

**Suggested fix:** {issue.suggestion}

---
"""

    return comment


async def post_pr_comment(
    owner,
    repo,
    pr_number,
    comment
):
    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/issues/{pr_number}/comments"
    )

    payload = {
        "body": comment
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=_github_headers(),
            json=payload
        )

    response.raise_for_status()

    return response.json()


async def update_pr_comment(owner, repo, comment_id, comment):
    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/issues/comments/{comment_id}"
    )

    payload = {
        "body": comment
    }

    async with httpx.AsyncClient() as client:
        response = await client.patch(
            url,
            headers=_github_headers(),
            json=payload
        )

    response.raise_for_status()

    return response.json()


async def delete_pr_comment(owner, repo, comment_id):
    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/issues/comments/{comment_id}"
    )

    async with httpx.AsyncClient() as client:
        response = await client.delete(
            url,
            headers=_github_headers()
        )

    response.raise_for_status()


async def upsert_pr_comment(owner, repo, pr_number, comment):
    existing_comments = await get_pr_comments(owner, repo, pr_number)

    bot_comments = [
        existing
        for existing in existing_comments
        if REVIEW_HEADING in (existing.get("body") or "")
    ]

    if not bot_comments:
        await post_pr_comment(owner, repo, pr_number, comment)
        return False

    primary, *duplicates = bot_comments

    await update_pr_comment(owner, repo, primary["id"], comment)

    for duplicate in duplicates:
        await delete_pr_comment(owner, repo, duplicate["id"])

    return True
