from .query_params_schema import OAuthAuthorizeQueryParamsSchema
from .method_not_allowed_schema import OAuthAuthorizeMethodNotAllowedSchema
from .internal_server_error_schema import OAuthAuthorizeInternalServerErrorSchema
from .bad_request_schema import OAuthAuthorizeBadRequestSchema

__all__ = (
    "OAuthAuthorizeQueryParamsSchema",
    "OAuthAuthorizeMethodNotAllowedSchema",
    "OAuthAuthorizeInternalServerErrorSchema",
    "OAuthAuthorizeBadRequestSchema",
)
