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

from controller.book import provide_book_repo, BookRepository
from model.book import Book, BookDTO
from model.publisher import Publisher, PublisherDTO, PublisherCreateWithBooks, PublisherUpdateWithBooks, \
    PublisherDTOWithTotalCount, PublisherCreate, PublisherUpdate
from sqlalchemy import delete as sqlalchemy_delete

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
        'book_repo': Provide(provide_book_repo)
    }
    publisher_controller_tag = ['Publisher - CRUD']

    @get(tags=publisher_controller_tag)
    async def list_publishers(
            self,
            publisher_repo: PublisherRepository,
            limit_offset: LimitOffset,
    ) -> OffsetPagination[PublisherDTO]:
        """List items."""
        try:
            order_by1 = OrderBy(field_name=Publisher.sort_order)
            order_by2 = OrderBy(field_name=Publisher.name)
            results, total = await publisher_repo.list_and_count(limit_offset, order_by1, order_by2, )
            type_adapter = TypeAdapter(list[PublisherDTO])
            return OffsetPagination[PublisherDTO](
                items=type_adapter.validate_python(results),
                total=total,
                limit=limit_offset.limit,
                offset=limit_offset.offset,
            )
        except Exception as ex:
            raise HTTPException(detail=str(ex), status_code=status_codes.HTTP_404_NOT_FOUND)

    @get('/all', tags=publisher_controller_tag)
    async def list_all_publishers(
            self,
            publisher_repo: PublisherRepository,
    ) -> PublisherDTOWithTotalCount:
        """List items."""
        try:
            order_by1 = OrderBy(field_name=Publisher.sort_order)
            order_by2 = OrderBy(field_name=Publisher.name)
            results, total = await publisher_repo.list_and_count(order_by1, order_by2, )
            type_adapter = TypeAdapter(list[PublisherDTO])
            return PublisherDTOWithTotalCount(publishers=type_adapter.validate_python(results), total=total)

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
    async def create_publisher(self,
                               publisher_repo: PublisherRepository,
                               book_repo: BookRepository,
                               data: PublisherCreate, ) -> PublisherDTO:
        try:
            return await self.create_publisher_helper(book_repo, data, publisher_repo)

        except Exception as ex:
            raise HTTPException(detail=str(ex), status_code=status_codes.HTTP_404_NOT_FOUND)

    @post('/with-books', tags=publisher_controller_tag)
    async def create_publisher_with_books(self,
                                          publisher_repo: PublisherRepository,
                                          book_repo: BookRepository,
                                          data: PublisherCreateWithBooks, ) -> PublisherDTO:
        """Create a new ."""
        """
        {
          "name": "pubName",
          "sort_order": 5,
          "books": [
              {"name": "bookName1", "sort_order": 70},
              {"name": "bookName2", "sort_order": 50},
              {"name": "bookName3", "sort_order": 100},
              {"name": "bookName4", "sort_order": 10}
          ]
        }
        """
        try:
            return await self.create_publisher_helper(book_repo, data, publisher_repo)

        except Exception as ex:
            raise HTTPException(detail=str(ex), status_code=status_codes.HTTP_404_NOT_FOUND)

    async def create_publisher_helper(self, book_repo, data, publisher_repo):
        _data = data.model_dump(exclude_unset=True, by_alias=False, exclude_none=True)
        books: list[BookDTO] = []
        if 'books' in _data:
            books = _data.pop('books')
        publisher_data = Publisher(**_data)
        publisher_repo.session.add(publisher_data)
        await publisher_repo.session.commit()
        return_entity = publisher_data.to_dict()
        if books:
            for b in books:
                b['publisher_id'] = publisher_data.id
            book_items = await book_repo.add_many([Book(**b) for b in books])
            await book_repo.session.commit()
            return_entity['books'] = [b.to_dict() for b in book_items]
        return PublisherDTO.model_validate(return_entity)

    @route('/{publisher_id:int}',
           http_method=[HttpMethod.PUT, HttpMethod.PATCH],
           tags=publisher_controller_tag)
    async def update_publisher(
            self,
            publisher_repo: PublisherRepository,
            data: PublisherUpdate,
            publisher_id: int = Parameter(title='Publisher Id', description='Publisher Primary Key', ),
    ) -> PublisherDTO:
        try:
            _data = data.model_dump(exclude_unset=True, exclude_none=True)
            _data.update({'id': publisher_id})
            obj = await publisher_repo.update(Publisher(**_data))
            await publisher_repo.session.commit()
            return PublisherDTO.model_validate(obj)
        except Exception as ex:
            raise HTTPException(detail=str(ex), status_code=status_codes.HTTP_404_NOT_FOUND)

    @route('/pub-and-book/{publisher_id:int}',
           http_method=[HttpMethod.PUT, HttpMethod.PATCH],
           tags=publisher_controller_tag)
    async def update_publisher_and_books(
            self,
            publisher_repo: PublisherRepository,
            book_repo: BookRepository,
            data: PublisherUpdateWithBooks,
            publisher_id: int = Parameter(title='Publisher Id', description='Publisher Primary Key', ),
    ) -> PublisherDTO:
        """### Update a publisher and their books.

        Handle with care.

        If the books are not listed then they are deleted.
```
Examples:
==============================
{
    "sort_order": 3,
    "books": [
        {
            "id": 12,
            "sort_order": 10,
            "name": "bookName4"
        },
        {
            "id": 10,
            "sort_order": 50,
            "name": "bookName2"
        },
        {
            "sort_order": 5,
            "name": "new_bookName"
        }
    ],
    "name": "new_pub_name"
}
==============================
{
    "sort_order": 3,
    "books": [],
    "name": "new_pub_name"
}
```
        """
        try:
            _data = data.model_dump(exclude_unset=True, exclude_none=True)
            _data.update({'id': publisher_id})
            return_entity: dict[str, dict[str, list[str]]] = {}
            book_entity: dict[str, list[str]] = {}
            books: list[BookDTO] = []
            keep_books: list[int] = []
            if 'books' in _data:
                books = _data.pop('books')
                new_books: list[BookDTO] = []
                update_books: list[BookDTO] = []
                for b in books:
                    b.update({'publisher_id': publisher_id})
                    book_id = b.get('id')
                    if book_id:
                        keep_books.append(book_id)
                        update_books.append(b)
                    else:
                        new_books.append(b)
                books = []
                if update_books:
                    book_items = await book_repo.update_many([Book(**b) for b in update_books])
                    books = book_items
                if new_books:
                    book_items = await book_repo.add_many([Book(**b) for b in new_books])
                    for b in book_items:
                        keep_books.append(b.id)
                    books = books + book_items
                await book_repo.session.commit()

                book_entity['books'] = [b.to_dict() for b in books]

            delete_sql: sqlalchemy_delete
            if keep_books:
                delete_sql = (
                    sqlalchemy_delete(Book)
                    .where(Book.publisher_id == publisher_id)
                    .where(Book.id.notin_(keep_books))
                )
            else:
                delete_sql = (
                    sqlalchemy_delete(Book)
                    .where(Book.publisher_id == publisher_id)
                )
            await book_repo.session.execute(delete_sql)
            await book_repo.session.commit()

            pub = Publisher(**_data)
            await publisher_repo.update(pub)
            await publisher_repo.session.commit()
            return_entity = pub.to_dict()
            return_entity['books'] = book_entity.get('books')

            return PublisherDTO.model_validate(return_entity)
        except Exception as ex:
            raise HTTPException(detail=str(ex), status_code=status_codes.HTTP_404_NOT_FOUND)

    @delete('/{publisher_ids:str}', tags=publisher_controller_tag)
    async def delete_publishers(
            self,
            publisher_repo: PublisherRepository,
            publisher_ids: str = Parameter(title='List Of Publisher Ids',
                                           description='Comma Separated Of The Ids The Publishers To Delete.', ),
    ) -> None:
        """Delete publishers and their books from the system."""
        try:
            _ = await publisher_repo.delete([int(i) for i in publisher_ids.split(',')])
            await publisher_repo.session.commit()
        except Exception as ex:
            raise HTTPException(detail=str(ex), status_code=status_codes.HTTP_404_NOT_FOUND)
