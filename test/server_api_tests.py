import unittest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import io

from main import app, task_list, manager, INDEX_FILE

class MockPrinter:
    def start(self):
        pass
    def stop(self):
        pass
    def get_status(self):
        return {
            'running': True,
            'current_task': None,
            'is_printing': False
        }


@patch('main.Printer', new=MockPrinter)
class TestMainApp(unittest.TestCase):

    def setUp(self):
        """
        Method for preparation before every test.
        """
        self.client = TestClient(app)

        app.state.printer = MockPrinter()

        task_list.clear()
        manager.active_connections.clear()

    def tearDown(self):
        """
        Method for cleaning after every test.
        """
        with task_list.not_empty:
            task_list.not_empty.notify_all()

        if hasattr(app.state, 'printer'):
            del app.state.printer

    def test_get_root(self):
        """
        Testing if main page returns HTML.
        """
        with patch('main.resource_path', return_value=INDEX_FILE):
            response = self.client.get("/")
            self.assertEqual(response.status_code, 200)
            self.assertIn('text/html', response.headers['content-type'])

    def test_get_system_state_endpoint(self):
        """
        Testing /system-state/ endpoint.
        """
        response = self.client.get("/system-state/")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["queue_length"], 0)
        self.assertEqual(data["printer_status"], "idle")
        self.assertIsNone(data["current_task"])
        self.assertEqual(data["queue_tasks"], [])

    @patch('main.manager.broadcast_json', new_callable=AsyncMock)
    @patch('main.manager.broadcast', new_callable=AsyncMock)
    @patch('main.get_page_count', return_value=5)
    def test_create_task_endpoint(self, mock_get_pages, mock_broadcast, mock_broadcast_json):
        """
        Testing /tasks/ endpoint.
        """

        fake_file = ("test.pdf", io.BytesIO(b"obsah"), "application/pdf")
        form_data = {"username": "test_user", "priority": 3}

        response = self.client.post(
            "/tasks/",
            data=form_data,
            files={"file": fake_file}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["task_id"], "test.pdf")

        mock_get_pages.assert_called_once()
        self.assertEqual(len(task_list), 1)

        mock_broadcast.assert_called_once()
        mock_broadcast_json.assert_called_once()


    @patch('main.get_page_count', return_value=1)
    def test_websocket_broadcast_on_new_task(self, mock_get_pages):
        """
        Testing if WebSocket client gets a message after adding a task.
        """

        with self.client.websocket_connect("/ws/status") as websocket:
            greeting = websocket.receive_text()
            self.assertIn("Successfully connected", greeting)

            self.assertEqual(len(manager.active_connections), 1)

            self.client.post(
                "/tasks/",
                data={"username": "ws_user", "priority": 1},
                files={"file": ("report.txt", io.BytesIO(b"abc"), "text/plain")}
            )

            text_message = websocket.receive_text()
            self.assertIn("NEW: New task added report.txt", text_message)

            json_state = websocket.receive_json()
            self.assertEqual(json_state["type"], "system_state")
            self.assertEqual(json_state["data"]["queue_length"], 1)

        self.assertEqual(len(manager.active_connections), 0)

if __name__ == '__main__':
    unittest.main()