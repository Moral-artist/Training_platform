from fastapi import FastAPI
from Router.auth.auth import router as auth_router
from Router.user.user import router as user_router
from Router.lessons.lessons import router as lessons_router
from Router.lessons.lesson_video import router as lesson_video
from Router.plan.plan_action import router as plan_action
from fastapi.middleware.cors import CORSMiddleware
from Router.Exams.exams import router as exams_router

app = FastAPI(title="Training ERP", description="企业培训考试管理系统", version="1.0.0")


@app.get("/")
def home():
    return {"message": "Training ERP API is running"}


app.include_router(auth_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(lessons_router, prefix="/api")
from Router.lessons.catalog import router as catalog_router
from Router.lessons.uploads import router as uploads_router

app.include_router(catalog_router, prefix="/api")
app.include_router(uploads_router, prefix="/api")

app.include_router(lesson_video, prefix="/api")

app.include_router(plan_action, prefix="/api")

app.include_router(exams_router, prefix="/api")

from data_model.config import settings

origins = [
    origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging
from uuid import uuid4


@app.exception_handler(HTTPException)
async def http_error(request: Request, error: HTTPException):
    return JSONResponse(
        status_code=error.status_code,
        content={"detail": error.detail, "code": f"HTTP_{error.status_code}"},
        headers=error.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, error: RequestValidationError):
    # 仅返回字段路径，不回显密码、Token 或用户输入。
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Invalid request fields",
            "code": "HTTP_422",
            "fields": [".".join(map(str, item["loc"])) for item in error.errors()],
        },
    )


@app.exception_handler(Exception)
async def unexpected_error(request: Request, error: Exception):
    reference = uuid4().hex[:12]
    logging.getLogger("api.error").error(
        "request_id=%s error_type=%s", reference, type(error).__name__
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Service temporarily unavailable",
            "code": "HTTP_500",
            "request_id": reference,
        },
    )


from Router.user.admin import router as admin_router

app.include_router(admin_router, prefix="/api")
