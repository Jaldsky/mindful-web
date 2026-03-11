from datetime import date
from typing import Any, Literal, TypeAlias

DateStr: TypeAlias = str
Date: TypeAlias = date
Page: TypeAlias = int
PageSize: TypeAlias = int
SortBy: TypeAlias = Literal["total_seconds", "domain", "category"]
SortOrder: TypeAlias = Literal["asc", "desc"]
DomainUsageRow: TypeAlias = dict[str, Any]
UsageSummaryRow: TypeAlias = dict[str, Any]
