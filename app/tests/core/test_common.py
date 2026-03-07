from unittest import TestCase

from app.core.common import path_matches


class TestPathMatches(TestCase):
    """Тесты для path_matches()."""

    def test_exact_match_without_placeholders(self) -> None:
        """При совпадении path и шаблона без плейсхолдеров возвращается True."""
        path = "/api/v1/auth/login"
        template = "/api/v1/auth/login"
        self.assertTrue(path_matches(path, template))

    def test_match_with_provider_placeholder(self) -> None:
        """Шаблон с {provider} совпадает с любым сегментом на этой позиции."""
        path = "/api/v1/auth/oauth/google/callback"
        template = "/api/v1/auth/oauth/{provider}/callback"
        self.assertTrue(path_matches(path, template))

    def test_match_with_any_placeholder_name(self) -> None:
        """Любой плейсхолдер {name} сопоставляется с сегментом."""
        path = "/api/v1/user/42/profile"
        template = "/api/v1/user/{id}/profile"
        self.assertTrue(path_matches(path, template))

    def test_match_multiple_placeholders(self) -> None:
        """В шаблоне может быть несколько плейсхолдеров."""
        path = "/api/v1/org/acme/project/backend"
        template = "/api/v1/org/{org}/project/{project}"
        self.assertTrue(path_matches(path, template))

    def test_no_match_different_segment(self) -> None:
        """При различии сегмента без плейсхолдера возвращается False."""
        path = "/api/v1/auth/oauth/google/callback"
        template = "/api/v1/auth/oauth/yandex/callback"
        self.assertFalse(path_matches(path, template))

    def test_no_match_different_number_of_segments(self) -> None:
        """При разном количестве сегментов возвращается False."""
        path = "/api/v1/auth/login"
        template = "/api/v1/auth/oauth/{provider}/callback"
        self.assertFalse(path_matches(path, template))

    def test_no_match_extra_segment_in_path(self) -> None:
        """Path длиннее шаблона — False."""
        path = "/api/v1/auth/oauth/google/callback/extra"
        template = "/api/v1/auth/oauth/{provider}/callback"
        self.assertFalse(path_matches(path, template))

    def test_strips_leading_trailing_slashes(self) -> None:
        """Ведущие и завершающие слэши не влияют на разбиение."""
        path = "/api/v1/auth/oauth/google/callback/"
        template = "/api/v1/auth/oauth/{provider}/callback"
        self.assertTrue(path_matches(path, template))
        self.assertTrue(path_matches("api/v1/auth/oauth/google/callback", template))

    def test_empty_path_empty_template_match(self) -> None:
        """Пустой path и пустой шаблон совпадают."""
        self.assertTrue(path_matches("", ""))
        self.assertTrue(path_matches("/", "/"))

    def test_empty_path_non_empty_template_no_match(self) -> None:
        """Пустой path и непустой шаблон — False."""
        self.assertFalse(path_matches("", "/api/v1"))
        self.assertFalse(path_matches("/", "/api/v1"))

    def test_placeholder_at_first_segment(self) -> None:
        """Плейсхолдер в первом сегменте сопоставляется."""
        path = "foo/bar/baz"
        template = "{first}/bar/baz"
        self.assertTrue(path_matches(path, template))

    def test_placeholder_at_last_segment(self) -> None:
        """Плейсхолдер в последнем сегменте сопоставляется."""
        path = "api/v1/resource/123"
        template = "api/v1/resource/{id}"
        self.assertTrue(path_matches(path, template))

    def test_segment_with_curly_braces_but_not_placeholder_no_match(self) -> None:
        """Сегмент шаблона «{» не плейсхолдер (длина <= 2), сопоставляется только с «{»."""
        path = "/api/v1/auth/oauth/xxx/callback"
        template = "/api/v1/auth/oauth/{/callback"
        self.assertFalse(path_matches(path, template))
