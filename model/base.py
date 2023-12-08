from __future__ import annotations

import json
from datetime import datetime

from typing_extensions import Self

from advanced_alchemy.base import AuditColumns
from pydantic import BaseModel as _BaseModel
from sqlalchemy import String
from sqlalchemy.orm import declarative_mixin, Mapped, mapped_column, DeclarativeBase, InstanceState


def is_pydantic(obj: object):
    """Checks whether an object is pydantic."""
    return type(obj).__class__.__name__ == "ModelMetaclass"


class Base(DeclarativeBase, AuditColumns):
    """Base for SQLAlchemy declarative models in this project with int primary keys."""

    def to_dict(self):
        json_exclude = getattr(self, '__json_exclude__', set())
        class_dict = {key: value for key, value in self.__dict__.items() if not key.startswith('_')
                      and key not in json_exclude}

        for i in class_dict:
            if 'time' in str(type(class_dict[i])):
                class_dict[i] = str(class_dict.get(i).isoformat(' '))  # format time and make it a str

        return class_dict

    def __str__(self):
        return {key: value for key, value in self.__dict__.items()}

    def __repr__(self):
        return {key: value for key, value in self.__dict__.items()}


class BaseModel(_BaseModel):
    """Extend Pydantic's BaseModel to enable ORM mode"""

    model_config = {'from_attributes': True}


# we are going to add a simple "slug" to our model that is a URL safe surrogate key to
# our database record.
@declarative_mixin
class SlugKey:
    """Slug unique Field Model Mixin."""

    __abstract__ = True
    slug: Mapped[str] = mapped_column(String(length=100), nullable=False, unique=True, sort_order=99)
