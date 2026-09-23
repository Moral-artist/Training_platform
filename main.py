from fastapi import FastAPI
from Router.auth.auth import router as auth_router
from Router.user.user import router as user_router
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

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)