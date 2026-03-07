from unittest import TestCase

from starlette.responses import Response

from app.config import (
    AUTH_COOKIE_HTTPONLY,
    AUTH_COOKIE_SECURE,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS,
    AUTH_COOKIE_SAMESITE,
    OAUTH_STATE_COOKIE_EXPIRE_MINUTES,
)
from app.services.auth.cookies import (
    clear_auth_cookies,
    set_auth_cookies,
    set_anon_cookie,
    clear_anon_cookie,
    set_oauth_state_cookie,
    clear_oauth_state_cookie,
)
from app.services.auth.constants import (
    AUTH_ACCESS_COOKIE_NAME,
    AUTH_REFRESH_COOKIE_NAME,
    AUTH_ANON_COOKIE_NAME,
)


class TestSetAuthCookies(TestCase):
    def test_sets_access_and_refresh_cookies(self):
        response = Response()

        set_auth_cookies(response, "access-token", "refresh-token")

        set_cookie_headers = response.headers.getlist("set-cookie")
        self.assertEqual(len(set_cookie_headers), 2)

        access_cookie = next(
            header for header in set_cookie_headers if header.startswith(f"{AUTH_ACCESS_COOKIE_NAME}=")
        )
        refresh_cookie = next(
            header for header in set_cookie_headers if header.startswith(f"{AUTH_REFRESH_COOKIE_NAME}=")
        )

        self.assertIn("access-token", access_cookie)
        self.assertIn("Path=/", access_cookie)
        self.assertIn(f"SameSite={AUTH_COOKIE_SAMESITE}", access_cookie)
        self.assertIn(f"Max-Age={JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60}", access_cookie)
        if AUTH_COOKIE_HTTPONLY:
            self.assertIn("HttpOnly", access_cookie)
        if AUTH_COOKIE_SECURE:
            self.assertIn("Secure", access_cookie)

        self.assertIn("refresh-token", refresh_cookie)
        self.assertIn("Path=/", refresh_cookie)
        self.assertIn(f"SameSite={AUTH_COOKIE_SAMESITE}", refresh_cookie)
        self.assertIn(f"Max-Age={JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60}", refresh_cookie)
        if AUTH_COOKIE_HTTPONLY:
            self.assertIn("HttpOnly", refresh_cookie)
        if AUTH_COOKIE_SECURE:
            self.assertIn("Secure", refresh_cookie)


class TestClearAuthCookies(TestCase):
    def test_clears_access_and_refresh_cookies(self):
        response = Response()

        clear_auth_cookies(response)

        set_cookie_headers = response.headers.getlist("set-cookie")
        self.assertEqual(len(set_cookie_headers), 2)

        access_cookie = next(
            header for header in set_cookie_headers if header.startswith(f"{AUTH_ACCESS_COOKIE_NAME}=")
        )
        refresh_cookie = next(
            header for header in set_cookie_headers if header.startswith(f"{AUTH_REFRESH_COOKIE_NAME}=")
        )

        self.assertIn("Max-Age=0", access_cookie)
        self.assertIn("Max-Age=0", refresh_cookie)


class TestSetAnonCookie(TestCase):
    def test_sets_anon_cookie(self):
        response = Response()

        set_anon_cookie(response, "anon-token")

        set_cookie_headers = response.headers.getlist("set-cookie")
        self.assertEqual(len(set_cookie_headers), 1)

        anon_cookie = set_cookie_headers[0]
        self.assertTrue(anon_cookie.startswith(f"{AUTH_ANON_COOKIE_NAME}="))
        self.assertIn("anon-token", anon_cookie)
        self.assertIn("Path=/", anon_cookie)
        self.assertIn(f"SameSite={AUTH_COOKIE_SAMESITE}", anon_cookie)
        if AUTH_COOKIE_HTTPONLY:
            self.assertIn("HttpOnly", anon_cookie)
        if AUTH_COOKIE_SECURE:
            self.assertIn("Secure", anon_cookie)


class TestClearAnonCookie(TestCase):
    def test_clears_anon_cookie(self):
        response = Response()

        clear_anon_cookie(response)

        set_cookie_headers = response.headers.getlist("set-cookie")
        self.assertEqual(len(set_cookie_headers), 1)

        anon_cookie = set_cookie_headers[0]
        self.assertTrue(anon_cookie.startswith(f"{AUTH_ANON_COOKIE_NAME}="))
        self.assertIn("Max-Age=0", anon_cookie)


class TestSetOAuthStateCookie(TestCase):
    """Тесты для set_oauth_state_cookie."""

    def test_sets_oauth_state_cookie_with_given_key(self):
        response = Response()
        cookie_key = "oauth_state_google"
        state = "random-state-value"

        set_oauth_state_cookie(response, cookie_key, state)

        set_cookie_headers = response.headers.getlist("set-cookie")
        self.assertEqual(len(set_cookie_headers), 1)
        cookie_header = set_cookie_headers[0]
        self.assertTrue(cookie_header.startswith(f"{cookie_key}="))
        self.assertIn(state, cookie_header)
        self.assertIn("Path=/", cookie_header)
        self.assertIn(f"SameSite={AUTH_COOKIE_SAMESITE}", cookie_header)
        self.assertIn(f"Max-Age={OAUTH_STATE_COOKIE_EXPIRE_MINUTES * 60}", cookie_header)
        if AUTH_COOKIE_HTTPONLY:
            self.assertIn("HttpOnly", cookie_header)
        if AUTH_COOKIE_SECURE:
            self.assertIn("Secure", cookie_header)


class TestClearOAuthStateCookie(TestCase):
    """Тесты для clear_oauth_state_cookie."""

    def test_clears_oauth_state_cookie_by_key(self):
        response = Response()
        cookie_key = "oauth_state_google"

        clear_oauth_state_cookie(response, cookie_key)

        set_cookie_headers = response.headers.getlist("set-cookie")
        self.assertEqual(len(set_cookie_headers), 1)
        cookie_header = set_cookie_headers[0]
        self.assertTrue(cookie_header.startswith(f"{cookie_key}="))
        self.assertIn("Max-Age=0", cookie_header)
