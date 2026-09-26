import json

from langchain_groq import ChatGroq
from pydantic import BaseModel

from config import GROQ_MODEL, GROQ_TEMPERATURE


class ReviewIssue(BaseModel):
    severity: str
    file: str
    line: int
    issue: str
    why: str
    suggestion: str


class CodeReview(BaseModel):
    issues: list[ReviewIssue]


SYSTEM_PROMPT = f"""
You are a senior software engineer performing a code review.

Analyze the provided GitHub pull request diff carefully.

Look for:
- Bugs
- Security issues
- Performance problems
- Incorrect logic
- Maintainability problems

Only report issues that are actually supported by the code.

Respond with a JSON object matching this schema exactly. Use these exact
field names and do not add extra fields:

{json.dumps(CodeReview.model_json_schema(), indent=2)}
"""

llm = ChatGroq(
    model=GROQ_MODEL,
    temperature=GROQ_TEMPERATURE,
)

structured_llm = llm.with_structured_output(CodeReview, method="json_mode")


async def review_code(diff: str) -> CodeReview:
    user_prompt = f"""Review this pull request:

{diff}

Report one object per issue, using the schema's field names:

- severity: how serious the issue is
- file: the path of the file
- line: the line number in the new version of the file
- issue: what is wrong
- why: why it matters
- suggestion: how to fix it

If there are no issues, return an empty "issues" list.
"""

    response =  await structured_llm.ainvoke(
        [
            ("system", SYSTEM_PROMPT),
            ("human", user_prompt),
        ]
    )


    return response
