from fastapi import FastAPI

from routes import health, review, webhooks

app = FastAPI(title="CodeGuard AI")

app.include_router(health.router)
app.include_router(review.router)
app.include_router(webhooks.router)
