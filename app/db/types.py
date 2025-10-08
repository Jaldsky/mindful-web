from typing import Generator
from sqlalchemy.ext.asyncio import AsyncSession

ExceptionMessage = str
DatabaseURL = str
DatabaseSession = Generator[AsyncSession, None, None]
