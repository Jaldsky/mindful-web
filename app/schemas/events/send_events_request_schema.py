from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator


class SendEventData(BaseModel):
    event: str = Field(
        ...,
        examples=["active", "inactive"],
        description="Тип события внимания: active - пользователь перешёл на вкладку, inactive - покинул вкладку",
    )
    domain: str = Field(
        ..., min_length=1, max_length=255, examples=["instagram.com", "youtube.com"], description="Домен"
    )
    timestamp: datetime = Field(
        ..., examples=["2025-04-05T18:30:00Z"], description="Временная метка события в формате ISO 8601 UTC."
    )

    @staticmethod
    @field_validator("event")
    def validate_event_type(v: str) -> str:
        if v not in ("active", "inactive"):
            raise ValueError("Event must be either active or inactive")
        return v

    @staticmethod
    @field_validator("domain")
    def validate_and_normalize_domain(v: str) -> str:
        v = v.strip().lower()
        if not v or "." not in v:
            raise ValueError("Invalid domain format: must contain at least one dot")
        if v.startswith("http://"):
            v = v[7:]
        elif v.startswith("https://"):
            v = v[8:]
        v = v.split("/")[0].split(":")[0]
        if v.startswith("www."):
            v = v[4:]
        if not v or len(v) > 255:
            raise ValueError("Domain is invalid or too long after normalization")
        return v

    @staticmethod
    @field_validator("timestamp")
    def validate_timestamp_not_in_future(v: datetime) -> datetime:
        now = datetime.now(timezone.utc)
        if v > now:
            raise ValueError("Timestamp cannot be in the future")
        return v


class SendEventsRequestSchema(BaseModel):
    data: list[SendEventData] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Список событий внимания",
        examples=[
            [
                {"event": "active", "domain": "reddit.com", "timestamp": "2025-04-05T09:00:00Z"},
                {"event": "inactive", "domain": "reddit.com", "timestamp": "2025-04-05T09:05:22Z"},
            ]
        ],
    )
