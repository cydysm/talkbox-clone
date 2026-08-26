from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase
from config.settings.production import validate_production_security


class ProductionSecurityTests(SimpleTestCase):
    def test_weak_secret_key_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            validate_production_security("short", ["example.com"])

    def test_default_secret_key_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            validate_production_security("insecure-change-me", ["example.com"])

    def test_wildcard_allowed_hosts_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            validate_production_security("a" * 50, ["*"])

    def test_empty_allowed_hosts_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            validate_production_security("a" * 50, [])

    def test_valid_config_passes(self):
        validate_production_security("a" * 50, ["example.com"])
