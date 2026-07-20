import unittest

from app import app


class FlaskDay08Tests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()
        with self.client.session_transaction() as session_data:
            session_data["username"] = "student"

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"ok": True, "service": "day08-flask-upgrade"})

    def test_metrics_endpoint_returns_metric_cards(self):
        response = self.client.get("/api/metrics")
        payload = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["ok"])
        self.assertIsInstance(payload["metrics"], list)
        self.assertEqual(len(payload["metrics"]), 4)
        self.assertTrue({"label", "value", "note"}.issubset(payload["metrics"][0].keys()))

    def test_categories_endpoint_supports_filtering(self):
        response = self.client.get("/api/categories?category=Fashion")
        payload = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["category"], "Fashion")
        self.assertTrue(all(row["偏好品类"] == "Fashion" for row in payload["rows"]))

    def test_bad_request_returns_json_error(self):
        response = self.client.post("/api/ask", data="not-json", content_type="application/json")
        payload = response.get_json()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(payload["ok"])
        self.assertIn("error", payload)


if __name__ == "__main__":
    unittest.main()
