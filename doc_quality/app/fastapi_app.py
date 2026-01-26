# fastapi_app.py
# /FastAPI app instantiation/
# adriana r.f.
# jan-2026

import logging
import socket
from fastapi import FastAPI
from contextlib import asynccontextmanager

from config.settings import Settings
from doc_quality.app.routers.doc_quality import router as ko_quality_router
from app.global_state import get_or_init_doc_quality_validator

logger = logging.getLogger(__name__)

def init_logger(settings: Settings):
    FORMAT = '%(asctime)s %(levelname)s (%(threadName)s) %(module)s: %(message)s'
    logging_levels_map = {
        'debug': logging.DEBUG, 'info': logging.INFO, 'warning': logging.WARNING, 'error': logging.ERROR, 'critical': logging.CRITICAL
    }
    logging.basicConfig(format=FORMAT, level=logging_levels_map.get(settings.api_log_level.lower(), logging.INFO))
    logging.getLogger('multipart').setLevel(logging.WARNING)
    logger.info(f'Logging configured with log level: {settings.api_log_level}')

def log_api_link(settings: Settings):
    hostname = socket.gethostname()
    protocol = 'http'
    api_doc_url = f'{protocol}://{hostname}:{settings.api_port}{settings.api_root_path}/docs'
    logger.info(f'OpenAPI documentation at: {api_doc_url}')

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    get_or_init_doc_quality_validator(settings)
    yield

def create_app(settings: Settings = None):
    if settings is None:
        settings = Settings()
        
    init_logger(settings=settings)
    log_api_link(settings=settings)
    
    logger.info(f'Creating FastAPI app for document quality assessment app...')
    
    app = FastAPI() 
    
    app2 = FastAPI(
        root_path=settings.api_root_path,
        title=settings.api_title,
        description=settings.api_description,
        version="0.1.0",
        lifespan=lifespan
    )
    
    app.mount(settings.api_root_path, app2) 
    app2.include_router(ko_quality_router, prefix=settings.api_prefix, tags=["KO Quality"])
    
    return app

app = create_app(Settings()) #app_fqn must match dir structure in "app.fastapi_app:app"