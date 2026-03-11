from datetime import date, datetime
from typing import NoReturn

from .constants import MIN_PAGE, MIN_PER_PAGE, MAX_PER_PAGE
from .exceptions import (
    InvalidDateFormatException,
    InvalidPageException,
    InvalidTimeRangeException,
)
from .types import Date, DateStr, Page, PageSize
from ...config import DATE_FORMATS


class AnalyticsServiceValidators:
    """Валидаторы для analytics-сервиса."""

    @classmethod
    def validate_date(cls, date_: Date | DateStr) -> Date | NoReturn:
        """Метод бизнес-валидации и парсинга даты.

        Args:
            date_: Дата (date) или строка даты.

        Returns:
            Объект date.

        Raises:
            InvalidDateFormatException: Если формат даты не распознан.
        """
        if isinstance(date_, date):
            return date_
        if not isinstance(date_, str):
            raise InvalidDateFormatException(
                key="analytics.errors.invalid_date_format",
                fallback="Invalid date format",
            )

        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(date_, fmt).date()
            except ValueError:
                continue

        raise InvalidDateFormatException(
            key="analytics.errors.invalid_date_format",
            fallback="Invalid date format",
        )

    @classmethod
    def validate_time_range(cls, from_date: Date, to_date: Date) -> None | NoReturn:
        """Метод валидации временного диапазона.

        Args:
            from_date: Дата начала диапозона.
            to_date: Дата конца диапозона.

        Raises:
            InvalidTimeRangeException: Диапазон не корректен.
        """
        if to_date < from_date:
            raise InvalidTimeRangeException(
                key="analytics.errors.invalid_time_range",
                fallback="End date must be after start date",
            )

    @classmethod
    def validate_page(cls, page: Page) -> None | NoReturn:
        """Метод валидации номера страницы.

        Args:
            page: Номер страницы.

        Raises:
            InvalidPageException: Номер страницы не корректен.
        """

        if not isinstance(page, int):
            raise InvalidPageException(
                key="analytics.errors.invalid_page_type",
                fallback="Page must be a valid integer",
            )

        if page < MIN_PAGE:
            raise InvalidPageException(
                key="analytics.errors.invalid_page",
                fallback="Page must be greater than or equal to 1",
            )

    @classmethod
    def validate_per_page(cls, per_page: PageSize) -> None | NoReturn:
        """Метод валидации размера страницы.

        Args:
            per_page: Размер страницы.

        Raises:
            InvalidPageException: Размер страницы не корректен.
        """
        if not isinstance(per_page, int):
            raise InvalidPageException(
                key="analytics.errors.invalid_page_type",
                fallback="Per page must be a valid integer",
            )
        if per_page < MIN_PER_PAGE or per_page > MAX_PER_PAGE:
            raise InvalidPageException(
                key="analytics.errors.invalid_page",
                fallback=f"Per page must be between {MIN_PER_PAGE} and {MAX_PER_PAGE}",
            )
