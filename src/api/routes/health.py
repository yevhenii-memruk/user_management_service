from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/healthcheck")
async def healthcheck() -> dict[str, str]:
    """
    Endpoint to check if the service is up and running.
    """
    return {"status": "ok"}
