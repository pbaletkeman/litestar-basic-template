from __future__ import annotations

from typing import Optional, Any

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from model.base import BaseModel, Base
# from model.publisher import Publisher


class BookDTO(BaseModel):
    id: Optional[int]
    sort_order: Optional[int] = 0
    publisher_id: int
    name: str


class BookCreate(BaseModel):
    name: str
    sort_order: Optional[int] = 0


class NewBook(BaseModel):
    name: str
    publisher_id: int
    sort_order: Optional[int] = 0


class Book(Base):
    """
    """
    __tablename__ = 'book'
    id: Mapped[int] = mapped_column(primary_key=True, name='book_id', sort_order=-10)
    publisher_id: Mapped[int] = mapped_column(ForeignKey('publisher.publisher_id'))
    sort_order: Mapped[int] = mapped_column(nullable=False, default=0, sort_order=1)
    name: Mapped[str] = mapped_column(String(length=30), nullable=False, sort_order=2)

    publisher: Mapped["Publisher"] = relationship(back_populates="books",
                                                  # order_by="desc(publisher.name)",
                                                  primaryjoin="Publisher.id == Book.publisher_id",
                                                  # lazy="joined"
                                                  )

    def __init__(self, **kw: Any):
        super().__init__(**kw)
        if self.sort_order is None:
            self.sort_order = 0
