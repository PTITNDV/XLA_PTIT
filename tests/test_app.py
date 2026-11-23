"""Exercise the real Streamlit app and widgets without a browser."""
from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest


class AppTests(unittest.TestCase):
    def test_fixed_pipeline_and_evaluation(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value, "2")
        self.assertEqual([tab.label for tab in app.tabs], ["Đếm đồng xu", "Đánh giá bộ dữ liệu", "Giải thích các bước"])
        self.assertEqual([select.label for select in app.selectbox], ["Chọn ảnh demo"])
        self.assertEqual(len(app.slider), 0)
        self.assertEqual(len(app.select_slider), 0)
        next(b for b in app.button if b.label == "Đánh giá bộ ảnh").click().run()
        self.assertFalse(app.exception)
        self.assertIn("fixed_evaluation", app.session_state)
        details, _ = app.session_state["fixed_evaluation"]
        self.assertEqual(len(details), 11)
        self.assertNotIn("method", details.columns)


if __name__ == "__main__":
    unittest.main()
