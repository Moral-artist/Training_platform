from fastapi import FastAPI
from Router.auth.auth import router as auth_router
from Router.user.user import router as user_router
from Router.lessons.lessons import router as lessons_router
from Router.lessons.lesson_video import router as lesson_video
from Router.plan.plan_action import router as plan_action
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(
    title="Training ERP",
    description="企业培训考试管理系统",
    version="1.0.0"
)

@app.get("/")
def home():
    return {
        "message": "Training ERP API is running"
    }

app.include_router(auth_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(lessons_router, prefix="/api")

app.include_router(lesson_video, prefix="/api")

app.include_router(plan_action, prefix="/api")

from data_model.config import settings
origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)