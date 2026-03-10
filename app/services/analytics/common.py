import os

from ...core.common import read_text_file


def load_sql(filename: str) -> str:
    """Функция загрузки SQL файла из директории analytics/sql.

    Returns:
        SQL текст запроса.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sql_path = os.path.join(base_dir, "sql", filename)
    return read_text_file(sql_path, encoding="utf-8")
