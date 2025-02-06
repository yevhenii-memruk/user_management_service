import uvicorn
from fastapi import FastAPI

from src.config import settings

app = FastAPI(title=settings.PROJECT_NAME)


@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
