from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings


limiter = Limiter(key_func=get_remote_address)


def setup_middleware(app: FastAPI):
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
