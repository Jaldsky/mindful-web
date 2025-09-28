from enum import Enum


class StringEnum(str, Enum):
    """Базовая форма для энумерации."""

    def __str__(self) -> str:
        """Магический метод возвращения строкового представления.

        Returns:
            Строковое представление.
        """
        return str.__str__(self)

    def __iter__(self):
        """Магический метод возвращения итерационного представления.

        Returns:
            Итерационное представление.
        """
        return iter((value.value for value in self))
