from .request_schema import OAuthLoginRequestSchema
from .response_schema import OAuthLoginResponseSchema
from .bad_request_schema import OAuthLoginBadRequestSchema
from .unauthorized_schema import OAuthLoginUnauthorizedSchema
from .unprocessable_entity_schema import OAuthLoginUnprocessableEntitySchema
from .method_not_allowed_schema import OAuthLoginMethodNotAllowedSchema
from .internal_server_error_schema import OAuthLoginInternalServerErrorSchema

__all__ = (
    "OAuthLoginRequestSchema",
    "OAuthLoginResponseSchema",
    "OAuthLoginBadRequestSchema",
    "OAuthLoginUnauthorizedSchema",
    "OAuthLoginUnprocessableEntitySchema",
    "OAuthLoginMethodNotAllowedSchema",
    "OAuthLoginInternalServerErrorSchema",
)
