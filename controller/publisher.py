from __future__ import annotations

import json
from typing import TYPE_CHECKING
from litestar.exceptions import HTTPException
from litestar import status_codes
from advanced_alchemy import SQLAlchemyAsyncRepository
from litestar import Controller
from litestar import HttpMethod
from litestar import get, post, delete
from litestar import route
from litestar.di import Provide
from litestar.pagination import OffsetPagination
from litestar.params import Parameter
from litestar.repository.filters import LimitOffset, OrderBy
from pydantic import TypeAdapter

from model.base import is_pydantic
from model.publisher import Publisher, PublisherDTO, PublisherCreate

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from logger import logger


class PublisherRepository(SQLAlchemyAsyncRepository[Publisher]):
    """MetaData Tag repository."""

    model_type = Publisher


# we can optionally override the default `select` used for the repository to pass in
# specific SQL options such as join details
async def provide_publisher_repo(db_session: AsyncSession) -> PublisherRepository:
    """This provides a simple example demonstrating how to override the join options
    for the repository."""
    return PublisherRepository(session=db_session)


class PublisherController(Controller):
    path = '/publisher'
    dependencies = {
        'publisher_repo': Provide(provide_publisher_repo),
    }
    publisher_controller_tag = ['Publisher - CRUD']

    @get(tags=publisher_controller_tag)
    async def list_publisher(
            self,
            publisher_repo: PublisherRepository,
            limit_offset: LimitOffset,
    ) -> OffsetPagination[PublisherDTO]:
        """List items."""
        try:
            order_by1 = OrderBy(field_name=Publisher.sort_order)
            order_by2 = OrderBy(field_name=Publisher.name)
            results, total = await publisher_repo.list_and_count(limit_offset, order_by1, order_by2)
            type_adapter = TypeAdapter(list[PublisherDTO])
            return OffsetPagination[PublisherDTO](
                items=type_adapter.validate_python(results),
                total=total,
                limit=limit_offset.limit,
                offset=limit_offset.offset,
            )
        except Exception as ex:
            raise HTTPException(detail=str(ex), status_code=status_codes.HTTP_404_NOT_FOUND)

    @get('/details/{publisher_id: int}', tags=publisher_controller_tag)
    async def get_publisher_details(self,
                                    publisher_repo: PublisherRepository,
                                    publisher_id: int = Parameter(title='Publisher Id',
                                                                  description='The publisher to update.', ),
                                    ) -> PublisherDTO:
        """Interact with SQLAlchemy engine and session."""
        try:
            obj = await publisher_repo.get_one(id=publisher_id)
            return PublisherDTO.model_validate(obj)
        except Exception as ex:
            raise HTTPException(detail=str(ex), status_code=status_codes.HTTP_404_NOT_FOUND)

    @post(tags=publisher_controller_tag)
    async def create_publisher(self, publisher_repo: PublisherRepository,
                               data: PublisherCreate, ) -> PublisherDTO:
        """Create a new ."""
        try:
            _data = data.model_dump(exclude_unset=True, by_alias=False, exclude_none=True)
            # books = _data.pop('books')

            pub = Publisher(**_data)

            publisher_repo.session.add(pub)
            await publisher_repo.session.commit()

            return PublisherDTO.model_validate(pub.__json__())

        except Exception as ex:
            raise HTTPException(detail=str(ex), status_code=status_codes.HTTP_404_NOT_FOUND)

    @route('/{publisher_id:int}',
           http_method=[HttpMethod.PUT, HttpMethod.PATCH],
           tags=publisher_controller_tag)
    async def update_publisher(
            self,
            publisher_repo: PublisherRepository,
            data: PublisherCreate,
            publisher_id: int = Parameter(title='Publisher Id', description='The publisher to update.', ),
    ) -> PublisherCreate:
        """Update an."""
        try:
            _data = data.model_dump(exclude_unset=True, exclude_none=True)
            _data.update({'id': publisher_id})
            obj = await publisher_repo.update(Publisher(**_data))
            await publisher_repo.session.commit()
            return PublisherCreate.model_validate(obj)
        except Exception as ex:
            raise HTTPException(detail=str(ex), status_code=status_codes.HTTP_404_NOT_FOUND)

    @delete('/{publisher_id:int}', tags=publisher_controller_tag)
    async def delete_publisher(
            self,
            publisher_repo: PublisherRepository,
            publisher_id: int = Parameter(title='Publisher Id',
                                          description='The id meta data tag to delete.', ),
    ) -> None:
        """## Delete
          from the system."""
        try:
            _ = await publisher_repo.delete(publisher_id)
            await publisher_repo.session.commit()
        except Exception as ex:
            raise HTTPException(detail=str(ex), status_code=status_codes.HTTP_404_NOT_FOUND)
