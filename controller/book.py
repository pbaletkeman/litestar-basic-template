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

from model.book import Book, BookDTO, BookCreate, BookDTOWithTotalCount

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
    async def list_books(
            self,
            book_repo: BookRepository,
            limit_offset: LimitOffset,
    ) -> OffsetPagination[BookDTO]:
        """List book records (paginated)."""
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

    @get('/all', tags=book_controller_tag)
    async def list_all_books(
            self,
            book_repo: BookRepository,
    ) -> BookDTOWithTotalCount:
        """List all book records."""
        try:
            order_by1 = OrderBy(field_name=Book.sort_order)
            order_by2 = OrderBy(field_name=Book.name)
            results, total = await book_repo.list_and_count(order_by1, order_by2)
            type_adapter = TypeAdapter(list[BookDTO])
            return BookDTOWithTotalCount(books=type_adapter.validate_python(results), total=total)

        except Exception as ex:
            raise HTTPException(detail=str(ex), status_code=status_codes.HTTP_404_NOT_FOUND)

    @get('/details/{book_id: int}', tags=book_controller_tag)
    async def get_book_details(self,
                               book_repo: BookRepository,
                               book_id: int = Parameter(title='Book Id',
                                                        description='The book to update.', ),
                               ) -> BookDTO:
        """Get all the details for a single book record."""
        try:
            obj = await book_repo.get_one(id=book_id)
            return BookDTO.model_validate(obj)
        except Exception as ex:
            raise HTTPException(detail=str(ex), status_code=status_codes.HTTP_404_NOT_FOUND)

    @post(tags=book_controller_tag)
    async def create_book(self, book_repo: BookRepository,
                          data: BookCreate, ) -> BookDTO:
        """Create a new book record."""
        try:
            _data = data.model_dump(exclude_unset=True, by_alias=False, exclude_none=True)
            # _data["slug"] = await book_repo.get_available_slug(_data["name"])
            obj = await book_repo.add(Book(**_data))
            await book_repo.session.commit()
            return BookDTO.model_validate(obj)
        except Exception as ex:
            raise HTTPException(detail=str(ex), status_code=status_codes.HTTP_404_NOT_FOUND)

    @post('/bulk-add', tags=book_controller_tag)
    async def bulk_create_book(self, book_repo: BookRepository,
                               data: list[BookCreate], ) -> list[BookDTO]:
        """Create many book records."""
        try:
            _data = [b.model_dump(exclude_unset=True, by_alias=False, exclude_none=True) for b in data]
            obj = await book_repo.add_many([Book(**b) for b in _data])
            await book_repo.session.commit()
            return [BookDTO.model_validate(b) for b in obj]
        except Exception as ex:
            raise HTTPException(detail=str(ex), status_code=status_codes.HTTP_404_NOT_FOUND)

    @route('/{book_id:int}',
           http_method=[HttpMethod.PUT, HttpMethod.PATCH],
           tags=book_controller_tag)
    async def update_book(
            self,
            book_repo: BookRepository,
            data: BookCreate,
            book_id: int = Parameter(title='Book Id', description='The book to update.', ),
    ) -> BookDTO:
        """Update a book record"""
        try:
            _data = data.model_dump(exclude_unset=True, exclude_none=True)
            _data.update({'id': book_id})
            obj = await book_repo.update(Book(**_data))
            await book_repo.session.commit()
            return BookDTO.model_validate(obj)
        except Exception as ex:
            raise HTTPException(detail=str(ex), status_code=status_codes.HTTP_404_NOT_FOUND)

    @delete('/{book_ids:str}', tags=book_controller_tag)
    async def delete_books(
            self,
            book_repo: BookRepository,
            book_ids: str = Parameter(title='List Of Book Ids',
                                      description='Comma Separated Of The Ids For Books To Delete.', ),
    ) -> None:
        """Delete book records from the system."""
        try:
            _ = await book_repo.delete_many([int(i) for i in book_ids.split(',')])
            await book_repo.session.commit()
        except Exception as ex:
            raise HTTPException(detail=str(ex), status_code=status_codes.HTTP_404_NOT_FOUND)
