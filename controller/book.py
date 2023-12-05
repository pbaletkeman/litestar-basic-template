from __future__ import annotations

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

from model.book import Book, BookDTO, NewBook

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from logger import logger


class BookRepository(SQLAlchemyAsyncRepository[Book]):
    """MetaData Tag repository."""

    model_type = Book


# we can optionally override the default `select` used for the repository to pass in
# specific SQL options such as join details
async def provide_book_repo(db_session: AsyncSession) -> BookRepository:
    """This provides a simple example demonstrating how to override the join options
    for the repository."""
    return BookRepository(session=db_session)


class BookController(Controller):
    path = '/book'
    dependencies = {
        'book_repo': Provide(provide_book_repo),
    }
    book_controller_tag = ['Book - CRUD']

    @get(tags=book_controller_tag)
    async def list_book(
            self,
            book_repo: BookRepository,
            limit_offset: LimitOffset,
    ) -> OffsetPagination[BookDTO]:
        """List items."""
        try:
            order_by1 = OrderBy(field_name=Book.sort_order)
            order_by2 = OrderBy(field_name=Book.name)
            results, total = await book_repo.list_and_count(limit_offset, order_by1, order_by2)
            type_adapter = TypeAdapter(list[BookDTO])
            return OffsetPagination[BookDTO](
                items=type_adapter.validate_python(results),
                total=total,
                limit=limit_offset.limit,
                offset=limit_offset.offset,
            )
        except Exception as ex:
            raise HTTPException(detail=str(ex), status_code=status_codes.HTTP_404_NOT_FOUND)

    @get('/details/{book_id: int}', tags=book_controller_tag)
    async def get_book_details(self,
                               book_repo: BookRepository,
                               book_id: int = Parameter(title='Book Id',
                                                        description='The book to update.', ),
                               ) -> BookDTO:
        """Interact with SQLAlchemy engine and session."""
        try:
            obj = await book_repo.get_one(id=book_id)
            return BookDTO.model_validate(obj)
        except Exception as ex:
            raise HTTPException(detail=str(ex), status_code=status_codes.HTTP_404_NOT_FOUND)

    @post(tags=book_controller_tag)
    async def create_book(self, book_repo: BookRepository,
                          data: NewBook, ) -> BookDTO:
        """Create a new."""
        try:
            _data = data.model_dump(exclude_unset=True, by_alias=False, exclude_none=True)
            # _data["slug"] = await book_repo.get_available_slug(_data["name"])
            obj = await book_repo.add(Book(**_data))
            await book_repo.session.commit()
            return BookDTO.model_validate(obj)
        except Exception as ex:
            raise HTTPException(detail=str(ex), status_code=status_codes.HTTP_404_NOT_FOUND)

    @route('/{book_id:int}',
           http_method=[HttpMethod.PUT, HttpMethod.PATCH],
           tags=book_controller_tag)
    async def update_book(
            self,
            book_repo: BookRepository,
            data: NewBook,
            book_id: int = Parameter(title='Book Id', description='The book to update.', ),
    ) -> NewBook:
        """Update an"""
        try:
            _data = data.model_dump(exclude_unset=True, exclude_none=True)
            _data.update({'id': book_id})
            obj = await book_repo.update(Book(**_data))
            await book_repo.session.commit()
            return NewBook.model_validate(obj)
        except Exception as ex:
            raise HTTPException(detail=str(ex), status_code=status_codes.HTTP_404_NOT_FOUND)

    @delete('/{book_id:int}', tags=book_controller_tag)
    async def delete_book(
            self,
            book_repo: BookRepository,
            book_id: int = Parameter(title='Book Id',
                                     description='The id meta data tag to delete.', ),
    ) -> None:
        """## Delete
          from the system."""
        try:
            _ = await book_repo.delete(book_id)
            await book_repo.session.commit()
        except Exception as ex:
            raise HTTPException(detail=str(ex), status_code=status_codes.HTTP_404_NOT_FOUND)
