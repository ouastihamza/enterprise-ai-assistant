from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
from app.api.assistant_routes import router as assistant_router
from app.api.conversation_routes import (
    router as conversation_router,
)
from app.api.document_routes import (
    router as document_router,
)
from app.auth.auth_routes import router as auth_router
from app.configuration.workspace_settings_routes import (
    router as workspace_settings_router,
)
from app.customers.customer_routes import router as customer_router
from app.workspaces.workspace_routes import (
    router as workspace_router,
)


app = FastAPI(
    title="AI Solutions Platform API",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(workspace_router)
app.include_router(workspace_settings_router)
app.include_router(assistant_router)
app.include_router(conversation_router)
app.include_router(document_router)
app.include_router(customer_router)


@app.get("/")
def root():
    return {
        "message": "AI Solutions Platform API is running",
        "status": "ok",
    }
