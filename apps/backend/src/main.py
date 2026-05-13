from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference

from src.routes.repositories import router as repositories_router
from src.routes.tasks import tasks_router
from src.routes.agent_runs import agent_runs_router
from src.routes.feedback import feedback_router
from src.routes.dashboard import dashboard_router
from src.routes.ws import ws_router

app = FastAPI(
    title="P.A.T.C.H.",
    description="AI Coding Agent MVP",
    version="0.1.0",
    docs_url=None,
)

app.include_router(repositories_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks_router)
app.include_router(agent_runs_router)
app.include_router(feedback_router)
app.include_router(dashboard_router)
app.include_router(ws_router)


@app.get("/")
def read_root():
    return {"message": "Halo kids"}


@app.get("/scalar")
def get_scalar():
    return get_scalar_api_reference(openapi_url=app.openapi_url, title=app.title)


@app.get("/health")
def health_check():
    return {"status": "ok"}
