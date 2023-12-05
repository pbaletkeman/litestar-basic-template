from __future__ import annotations

import random
import re
import string
from typing import TYPE_CHECKING, Any

import unicodedata
from litestar.contrib.sqlalchemy.repository import (
    ModelT,
    SQLAlchemyAsyncRepository,
)
from litestar.params import Parameter
from litestar.repository.filters import LimitOffset

if TYPE_CHECKING:
    pass


def provide_limit_offset_pagination(
    current_page: int = Parameter(ge=1, query='currentPage', default=1, required=False),
    page_size: int = Parameter(
        query='pageSize',
        ge=1,
        default=10,
        required=False,
    ),
) -> LimitOffset:
    """Add offset/limit pagination.

    Return type consumed by `Repository.apply_limit_offset_pagination()`.

    Parameters
    ----------
    current_page : int
        LIMIT to apply to select.
    page_size : int
        OFFSET to apply to select.
    """
    return LimitOffset(page_size, page_size * (current_page - 1))


# this class can be re-used with any model that has the `SlugKey` Mixin
class SQLAlchemyAsyncSlugRepository(SQLAlchemyAsyncRepository[ModelT]):
    """Extends the repository to include slug model features."""

    async def get_available_slug(self, value_to_slugify: str, **kwargs: Any, ) -> str:
        """Get a unique slug for the supplied value.

        If the value is found to exist, a random 4 digit character is appended to the end.
        There may be a better way to do this, but I wanted to limit the number of
        additional database calls.

        Args:
            value_to_slugify (str): A string that should be converted to a unique slug.
            **kwargs: stuff

        Returns:
            str: a unique slug for the supplied value. This is safe for URLs and other
            unique identifiers.
        """
        slug = self._slugify(value_to_slugify)
        if await self._is_slug_unique(slug):
            return slug
        # generate a random 4 digit alphanumeric string to make the slug unique and
        # avoid another DB lookup.
        random_string = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
        return f"{slug}-{random_string}"

    @staticmethod
    def _slugify(value: str) -> str:
        """slugify.

        Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
        dashes to single dashes. Remove characters that aren't alphanumerics,
        underscores, or hyphens. Convert to lowercase. Also strip leading and
        trailing whitespace, dashes, and underscores.

        Args:
            value (str): the string to slugify

        Returns:
            str: a slugified string of the value parameter
        """
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
        value = re.sub(r'[^\w\s-]', '', value.lower())
        return re.sub(r'[-\s]+', '-', value).strip('-_')

    async def _is_slug_unique(self, slug: str, **kwargs: Any, ) -> bool:
        return await self.get_one_or_none(slug=slug) is None
