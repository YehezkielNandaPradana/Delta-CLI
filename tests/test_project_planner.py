import unittest
from delta.web.bridge import EngineBridge

class TestProjectPlanner(unittest.TestCase):
    def test_plan_generation_structure(self):
        bridge = EngineBridge(engine=None)
        payload = {
            "projectName": "Test E-Commerce",
            "description": "A secure marketplace with cart, checkout, and JWT auth",
            "techStack": "FastAPI, React, SQLite",
            "targetAudience": "Shoppers",
            "securityLevel": "High"
        }
        res = bridge.generate_project_plan(payload)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["projectName"], "Test E-Commerce")
        self.assertTrue("planMarkdown" in res)
        self.assertTrue("generatedAt" in res)

if __name__ == "__main__":
    unittest.main()
