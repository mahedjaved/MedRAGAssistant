from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.middlewares.exceptionHandlers import catch_exception_from_middleware

app = FastAPI(
    title="Medical Assistant API",
    version="1.0",
    description="API for Medical Assistant ChatBot Application",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_credentials=["*"],
    allow_headers=["*"],
)

# add middleware exception handlers
app.middleware("http")(catch_exception_from_middleware)

# add routers - 1) upload PDF documents 2) asing query 