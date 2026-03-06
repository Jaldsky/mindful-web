"""Тесты для core.localizer (load_translations, LocalizerStore, Localizer, localize_key)."""

from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import MagicMock

from app.config import DEFAULT_LOCALE
from app.core.localizer import (
    load_translations,
    LocalizerStore,
    Localizer,
    localize_key,
)


class TestLoadTranslations(TestCase):
    """Тесты для load_translations()."""

    def test_returns_dict(self):
        """Возвращается словарь."""
        result = load_translations()
        self.assertIsInstance(result, dict)

    def test_contains_supported_locales(self):
        """Словарь содержит ключи en и ru."""
        result = load_translations()
        self.assertIn("en", result)
        self.assertIn("ru", result)

    def test_locale_value_is_nested_dict(self):
        """Значение по локали — вложенный словарь."""
        result = load_translations()
        for locale in ("en", "ru"):
            self.assertIsInstance(result[locale], dict, msg=locale)

    def test_known_key_exists(self):
        """Известный ключ general.method_not_allowed присутствует в en и ru."""
        result = load_translations()
        self.assertIn("general", result["en"])
        self.assertIn("method_not_allowed", result["en"]["general"])
        self.assertIn("general", result["ru"])
        self.assertIn("method_not_allowed", result["ru"]["general"])


class TestLocalizerStore(TestCase):
    """Тесты для LocalizerStore."""

    def setUp(self):
        self.translations: dict[str, dict] = {
            "en": {"general": {"method_not_allowed": "Method not allowed", "with_param": "Hello {name}"}},
            "ru": {"general": {"method_not_allowed": "Метод не разрешён", "with_param": "Привет, {name}"}},
        }
        self.store = LocalizerStore(self.translations)

    def test_get_returns_translation_for_locale(self):
        """get() возвращает перевод для указанной локали."""
        self.assertEqual(self.store.get("general.method_not_allowed", locale="en"), "Method not allowed")
        self.assertEqual(self.store.get("general.method_not_allowed", locale="ru"), "Метод не разрешён")

    def test_get_default_locale_when_locale_none(self):
        """При locale=None используется DEFAULT_LOCALE."""
        self.assertEqual(self.store.get("general.method_not_allowed"), "Method not allowed")

    def test_get_fallback_to_default_when_locale_unknown(self):
        """При неизвестной локали используется fallback на DEFAULT_LOCALE."""
        self.assertEqual(self.store.get("general.method_not_allowed", locale="de"), "Method not allowed")
        self.assertEqual(self.store.get("general.method_not_allowed", locale="fr"), "Method not allowed")

    def test_get_returns_key_when_key_missing(self):
        """При отсутствующем ключе возвращается сам ключ."""
        self.assertEqual(self.store.get("missing.key"), "missing.key")
        self.assertEqual(self.store.get("general.unknown"), "general.unknown")

    def test_get_returns_key_when_translations_empty(self):
        """При пустом хранилище возвращается ключ."""
        empty_store = LocalizerStore({})
        self.assertEqual(empty_store.get("any.key"), "any.key")

    def test_get_formats_with_params(self):
        """Параметры подставляются в строку перевода."""
        self.assertEqual(
            self.store.get("general.with_param", locale="en", name="World"),
            "Hello World",
        )
        self.assertEqual(
            self.store.get("general.with_param", locale="ru", name="Мир"),
            "Привет, Мир",
        )

    def test_get_with_invalid_param_key_returns_unformatted(self):
        """При неверном ключе в params возвращается строка без форматирования."""
        result = self.store.get("general.with_param", locale="en", wrong_key="x")
        self.assertEqual(result, "Hello {name}")


class TestLocalizer(TestCase):
    """Тесты для Localizer."""

    def test_get_with_custom_translations(self):
        """get() с переданным словарём возвращает перевод."""
        translations = {"en": {"foo": {"bar": "Baz"}}}
        localizer = Localizer(translations=translations)
        self.assertEqual(localizer.get("foo.bar", locale="en"), "Baz")

    def test_get_without_translations_loads_from_disk(self):
        """При translations=None загружаются переводы из app/locales."""
        localizer = Localizer()
        self.assertEqual(localizer.get("general.method_not_allowed", locale="en"), "Method not allowed")
        self.assertEqual(localizer.get("general.method_not_allowed", locale="ru"), "Метод не разрешён")

    def test_get_returns_key_when_missing(self):
        """При отсутствующем ключе возвращается ключ."""
        localizer = Localizer({"en": {}})
        self.assertEqual(localizer.get("missing.key"), "missing.key")

    def test_get_passes_params_to_store(self):
        """Параметры передаются в store.get()."""
        translations = {"en": {"a": {"b": "Value: {x}"}}}
        localizer = Localizer(translations)
        self.assertEqual(localizer.get("a.b", locale="en", x=42), "Value: 42")


class TestGetMessage(TestCase):
    """Тесты для localize_key()."""

    def test_returns_fallback_when_no_localizer(self):
        """При отсутствии localizer в app.state возвращается fallback."""
        request = MagicMock()
        request.app.state = SimpleNamespace()
        result = localize_key(request, "any.key", "Fallback text")
        self.assertEqual(result, "Fallback text")

    def test_returns_fallback_when_localizer_is_none(self):
        """При request.app.state.localizer is None возвращается fallback."""
        request = MagicMock()
        request.app.state = SimpleNamespace(localizer=None)
        request.state = SimpleNamespace(locale="en")
        result = localize_key(request, "any.key", "Fallback text")
        self.assertEqual(result, "Fallback text")

    def test_returns_translated_message_when_localizer_present(self):
        """При наличии localizer возвращается перевод по ключу и locale."""
        request = MagicMock()
        localizer = Localizer()
        request.app.state = SimpleNamespace(localizer=localizer)
        request.state = SimpleNamespace(locale="en")
        result = localize_key(request, "general.method_not_allowed", "Fallback")
        self.assertEqual(result, "Method not allowed")

    def test_uses_request_state_locale(self):
        """Используется request.state.locale для перевода."""
        request = MagicMock()
        request.app.state = SimpleNamespace(localizer=Localizer())
        request.state = SimpleNamespace(locale="ru")
        result = localize_key(request, "general.method_not_allowed", "Fallback")
        self.assertEqual(result, "Метод не разрешён")

    def test_returns_fallback_when_translation_equals_key(self):
        """Когда перевод не найден (localizer возвращает ключ), возвращается fallback."""
        request = MagicMock()
        request.app.state = SimpleNamespace(localizer=Localizer({"en": {}}))
        request.state = SimpleNamespace(locale="en")
        result = localize_key(request, "missing.key", "Fallback")
        self.assertEqual(result, "Fallback")

    def test_uses_default_locale_when_state_locale_missing(self):
        """При отсутствии request.state.locale getattr подставляет 'en', возвращается перевод."""
        request = MagicMock()
        request.app.state = SimpleNamespace(localizer=Localizer())
        request.state = SimpleNamespace()
        result = localize_key(request, "general.method_not_allowed", "Fallback")
        self.assertEqual(result, "Method not allowed")
