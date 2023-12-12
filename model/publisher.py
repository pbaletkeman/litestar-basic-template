from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from model.book import BookDTO, BookCreate, BookUpdate

if TYPE_CHECKING:
    pass

from model.base import BaseModel, Base


class Publisher(Base):
    """
    """
    __tablename__ = 'publisher'
    id: Mapped[int] = mapped_column(primary_key=True, name='publisher_id', sort_order=-10)

    sort_order: Mapped[int] = mapped_column(nullable=False, default=0, sort_order=1)
    name: Mapped[str] = mapped_column(String(length=30), nullable=False, sort_order=2)

    books: Mapped[List['Book']] = relationship(back_populates='publisher',
                                               order_by='asc(Book.sort_order), asc(Book.name)',
                                               primaryjoin='Publisher.id == Book.publisher_id',
                                               lazy='selectin',
                                               cascade='all, delete',
                                               )

    def __init__(self, **kw: Any):
        super().__init__(**kw)
        if self.sort_order is None:
            self.sort_order = 0


class PublisherDTOWithTotalCount(BaseModel):
    publishers: Optional[list[PublisherDTO]] = None
    total: int = 0


class PublisherDTO(BaseModel):
    id: int | None
    books: Optional[List[BookDTO]] = None
    sort_order: Optional[int] = 0
    name: str


class PublisherCreate(BaseModel):
    name: str
    sort_order: Optional[int] = 0


class PublisherCreateWithBooks(BaseModel):
    name: str
    books: Optional[List[BookCreate]] = None
    sort_order: Optional[int] = 0


class PublisherUpdateWithBooks(BaseModel):
    name: str
    books: Optional[List[BookUpdate]] = None
    sort_order: Optional[int] = 0


class PublisherUpdate(BaseModel):
    name: str
    sort_order: Optional[int] = 0
