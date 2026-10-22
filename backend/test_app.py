import unittest

from plan_core import DemoProvider, validate_plan_data


class PlanTests(unittest.TestCase):
    def test_demo_is_deterministic_and_labeled(self):
        provider = DemoProvider()
        first = provider.generate("prepare for a flood")
        second = provider.generate("prepare for a flood")
        self.assertEqual(first, second)
        self.assertEqual(first["provider"], "demo")
        self.assertIn("flood", first["title"].lower())

    def test_rejects_malformed_output(self):
        with self.assertRaises(Exception):
            validate_plan_data({"title": "x", "summary": "x", "steps": ["one"], "provider": "bedrock"})

    def test_rejects_unknown_provider(self):
        with self.assertRaises(ValueError):
            validate_plan_data({"title": "Useful plan", "summary": "A useful summary", "steps": ["one", "two"], "provider": "pretend"})

    def test_rejects_extra_fields(self):
        with self.assertRaises(ValueError):
            validate_plan_data({"title": "Useful plan", "summary": "A useful summary", "steps": ["one", "two"], "provider": "demo", "command": "run"})


if __name__ == "__main__":
    unittest.main()
