from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, List

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from model.base import BaseModel, Base


class Publisher(Base):
    """
    """
    __tablename__ = 'publisher'
    id: Mapped[int] = mapped_column(primary_key=True, name='publisher_id', sort_order=-10)

    sort_order: Mapped[int] = mapped_column(nullable=False, default=0, sort_order=1)
    name: Mapped[str] = mapped_column(String(length=30), nullable=False, sort_order=2)

    def __init__(self, **kw: Any):
        super().__init__(**kw)
        if self.sort_order is None:
            self.sort_order = 0


class PublisherDTO(BaseModel):
    id: Optional[int]
    sort_order: Optional[int] = 0
    name: str


class PublisherCreate(BaseModel):
    name: str
    sort_order: Optional[int] = 0
