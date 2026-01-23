import unittest
from configparser import ConfigParser
from toni.core import discover_providers


class TestDiscovery(unittest.TestCase):
    def test_discover_custom_provider(self):
        config = ConfigParser()
        config.read_string("""
[ollama]
url = http://localhost:11434/v1
key = ollama
model = llama3.2
priority = 100
        """)
        providers = discover_providers(config)
        self.assertEqual(len(providers["custom"]), 1)
        self.assertEqual(providers["custom"][0]["name"], "ollama")
        self.assertEqual(providers["custom"][0]["priority"], 100)

    def test_discover_multiple_custom_sorted(self):
        config = ConfigParser()
        config.read_string("""
[provider_a]
url = http://a.com/v1
priority = 50

[provider_b]
url = http://b.com/v1
priority = 100
        """)
        providers = discover_providers(config)
        self.assertEqual(len(providers["custom"]), 2)
        self.assertEqual(providers["custom"][0]["name"], "provider_b")
        self.assertEqual(providers["custom"][1]["name"], "provider_a")

    def test_builtin_classification(self):
        config = ConfigParser()
        config.read_string("""
[OPENAI]
key = sk-123

[GEMINI]
key = gem-123

[MISTRAL]
key = mis-123
        """)
        providers = discover_providers(config)
        # OPENAI with no URL is treated as custom (official endpoint)
        self.assertEqual(len(providers["custom"]), 1)
        self.assertEqual(providers["custom"][0]["name"], "OPENAI")
        # GEMINI and MISTRAL with no URL are native
        self.assertEqual(len(providers["native"]), 2)
        native_names = [p["name"] for p in providers["native"]]
        self.assertIn("GEMINI", native_names)
        self.assertIn("MISTRAL", native_names)

    def test_disabled_providers(self):
        config = ConfigParser()
        config.read_string("""
[ollama]
url = http://localhost:11434/v1
disabled = true
        """)
        providers = discover_providers(config)
        self.assertEqual(len(providers["custom"]), 0)


if __name__ == "__main__":
    unittest.main()
