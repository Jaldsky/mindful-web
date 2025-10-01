from typing import Generator
from sqlalchemy.orm import Session

ExceptionMessage = str
DatabaseURL = str
DatabaseSession = Generator[Session, None, None]
