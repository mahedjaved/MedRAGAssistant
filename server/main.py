from fastapi import FastAPI

from .routes.upload_pdfs import router as upload_router
from .routes.ask_question import router as ask_router
from .routes.health import router as health_router
from .routes.langsmith_health import router as langsmith_router
from .routes.metrics import router as metrics_router

from .modules.rate_limiter import limiter

from fastapi.middleware.cors import CORSMiddleware
from .middlewares.exceptionHandlers import catch_exception_from_middleware
from .modules.db_logger import init_db

app = FastAPI(
    title="Medical Assistant API",
    version="1.0",
    description="API for Medical Assistant ChatBot Application",
)

app.state.limiter = limiter


@app.on_event("startup")
async def startup_event():
    await init_db()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_credentials=["*"],
    allow_headers=["*"],
)

# add middleware exception handlers
app.middleware("http")(catch_exception_from_middleware)

# add routers - 1) upload PDF documents 2) asking query
app.include_router(upload_router)
app.include_router(ask_router)
app.include_router(health_router)
app.include_router(langsmith_router)
app.include_router(metrics_router)
