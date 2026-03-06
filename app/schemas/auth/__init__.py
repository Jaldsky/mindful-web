from .auth_error_code import AuthErrorCode
from .anonymous import (
    AnonymousResponseSchema,
    AnonymousMethodNotAllowedSchema,
    AnonymousInternalServerErrorSchema,
)
from .register import (
    RegisterRequestSchema,
    RegisterResponseSchema,
    RegisterBadRequestSchema,
    RegisterUnprocessableEntitySchema,
    RegisterConflictSchema,
    RegisterMethodNotAllowedSchema,
    RegisterInternalServerErrorSchema,
)
from .verify import (
    VerifyRequestSchema,
    VerifyResponseSchema,
    VerifyBadRequestSchema,
    VerifyUnprocessableEntitySchema,
    VerifyUnauthorizedSchema,
    VerifyMethodNotAllowedSchema,
    VerifyInternalServerErrorSchema,
)
from .login import (
    LoginRequestSchema,
    LoginResponseSchema,
    LoginBadRequestSchema,
    LoginUnauthorizedSchema,
    LoginForbiddenSchema,
    LoginMethodNotAllowedSchema,
    LoginInternalServerErrorSchema,
)
from .refresh import (
    RefreshRequestSchema,
    RefreshResponseSchema,
    RefreshBadRequestSchema,
    RefreshUnauthorizedSchema,
    RefreshMethodNotAllowedSchema,
    RefreshInternalServerErrorSchema,
)
from .resend_code import (
    ResendCodeRequestSchema,
    ResendCodeResponseSchema,
    ResendCodeBadRequestSchema,
    ResendCodeUnprocessableEntitySchema,
    ResendCodeUnauthorizedSchema,
    ResendCodeMethodNotAllowedSchema,
    ResendCodeInternalServerErrorSchema,
)
from .logout import (
    LogoutResponseSchema,
    LogoutMethodNotAllowedSchema,
    LogoutInternalServerErrorSchema,
)
from .session import (
    SessionResponseSchema,
    SessionMethodNotAllowedSchema,
    SessionInternalServerErrorSchema,
)
from .oauth_callback import (
    OAuthCallbackRequestSchema,
    OAuthCallbackResponseSchema,
    OAuthCallbackBadRequestSchema,
    OAuthCallbackUnauthorizedSchema,
    OAuthCallbackUnprocessableEntitySchema,
    OAuthCallbackMethodNotAllowedSchema,
    OAuthCallbackInternalServerErrorSchema,
)

__all__ = (
    # Common
    "AuthErrorCode",
    # Anonymous
    "AnonymousResponseSchema",
    "AnonymousMethodNotAllowedSchema",
    "AnonymousInternalServerErrorSchema",
    # Register
    "RegisterRequestSchema",
    "RegisterResponseSchema",
    "RegisterBadRequestSchema",
    "RegisterUnprocessableEntitySchema",
    "RegisterConflictSchema",
    "RegisterMethodNotAllowedSchema",
    "RegisterInternalServerErrorSchema",
    # Verify
    "VerifyRequestSchema",
    "VerifyResponseSchema",
    "VerifyBadRequestSchema",
    "VerifyUnprocessableEntitySchema",
    "VerifyUnauthorizedSchema",
    "VerifyMethodNotAllowedSchema",
    "VerifyInternalServerErrorSchema",
    # Login
    "LoginRequestSchema",
    "LoginResponseSchema",
    "LoginBadRequestSchema",
    "LoginUnauthorizedSchema",
    "LoginForbiddenSchema",
    "LoginMethodNotAllowedSchema",
    "LoginInternalServerErrorSchema",
    # Refresh
    "RefreshRequestSchema",
    "RefreshResponseSchema",
    "RefreshBadRequestSchema",
    "RefreshUnauthorizedSchema",
    "RefreshMethodNotAllowedSchema",
    "RefreshInternalServerErrorSchema",
    # Resend code
    "ResendCodeRequestSchema",
    "ResendCodeResponseSchema",
    "ResendCodeBadRequestSchema",
    "ResendCodeUnprocessableEntitySchema",
    "ResendCodeUnauthorizedSchema",
    "ResendCodeMethodNotAllowedSchema",
    "ResendCodeInternalServerErrorSchema",
    # Logout
    "LogoutResponseSchema",
    "LogoutMethodNotAllowedSchema",
    "LogoutInternalServerErrorSchema",
    # Session
    "SessionResponseSchema",
    "SessionMethodNotAllowedSchema",
    "SessionInternalServerErrorSchema",
    # OAuth callback
    "OAuthCallbackRequestSchema",
    "OAuthCallbackResponseSchema",
    "OAuthCallbackBadRequestSchema",
    "OAuthCallbackUnauthorizedSchema",
    "OAuthCallbackUnprocessableEntitySchema",
    "OAuthCallbackMethodNotAllowedSchema",
    "OAuthCallbackInternalServerErrorSchema",
)
