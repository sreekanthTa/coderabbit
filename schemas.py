from pydantic import BaseModel, field_validator


class ReviewRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_github_url(cls, value):

        if not value.startswith(
            "https://github.com/"
        ):
            raise ValueError(
                "URL must be a GitHub URL"
            )

        if "/pull/" not in value:
            raise ValueError(
                "URL must be a GitHub Pull Request URL"
            )

        return value
