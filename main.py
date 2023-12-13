from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Type

from litestar import Litestar, get
from litestar.config.compression import CompressionConfig
from litestar.contrib.mako import MakoTemplateEngine
from litestar.contrib.sqlalchemy.plugins import AsyncSessionConfig, SQLAlchemyAsyncConfig, SQLAlchemyInitPlugin
from litestar.di import Provide
from litestar.openapi import OpenAPIConfig, OpenAPIController
from litestar.static_files import StaticFilesConfig
from litestar.template.config import TemplateConfig
from litestar.response import Template

from controller.book import BookController
from controller.publisher import PublisherController
from model.base import Base

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from logger import logger

from shared import provide_limit_offset_pagination

session_config = AsyncSessionConfig(expire_on_commit=False)
sqlalchemy_config = SQLAlchemyAsyncConfig(
    connection_string="sqlite+aiosqlite:///test.sqlite", session_config=session_config,
    # connection_string='postgresql+asyncpg://pete:pete@host.docker.internal:5432/sample_project',
    # session_config=session_config

)  # Create 'async_session' dependency.
sqlalchemy_plugin = SQLAlchemyInitPlugin(config=sqlalchemy_config)

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


async def on_startup() -> None:
    """Initializes the database."""
    try:
        async with sqlalchemy_config.get_engine().begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as ex:
        logger.error('db connection issue ' + str(ex))
        sys.exit(1)


@get(path='/', sync_to_thread=False)
def index(name: str) -> Template:
    return Template(template_name='hello.mako.html', context={"name": name})


@get(path='/test', sync_to_thread=False)
def index_test() -> Template:
    return Template(template_name='test.mako.html')


class OpenAPIControllerExtra(OpenAPIController):
    favicon_url = 'static-files/favicon.ico'


app = Litestar(
    route_handlers=[
        PublisherController,
        BookController,
        index, index_test
    ],
    openapi_config=OpenAPIConfig(
        title='My API', version='1.0.0',
        root_schema_site='elements',  # swagger, elements, redoc, rapidoc
        path='/docs',
        create_examples=False,
        openapi_controller=OpenAPIControllerExtra,
        use_handler_docstrings=True,
    ),
    static_files_config=[StaticFilesConfig(
        path='static-files',
        directories=['static-files']
    )],
    template_config=TemplateConfig(
        directory=Path('templates'),
        engine=MakoTemplateEngine,
    ),
    on_startup=[on_startup],
    plugins=[SQLAlchemyInitPlugin(config=sqlalchemy_config)],
    dependencies={'limit_offset': Provide(provide_limit_offset_pagination, sync_to_thread=False)},
    compression_config=CompressionConfig(backend='gzip', gzip_compress_level=9),
)
