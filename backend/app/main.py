from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(
    title="EchoFinder API",
    description="Initial backend API for the EchoFinder prototype.",
    version="0.2.0",
)


@app.exception_handler(Exception)
async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
    """Return a consistent response shape for unexpected server errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected error occurred.",
            }
        },
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
