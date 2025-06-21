# analytics.py
import json
import os
from datetime import datetime

class Analytics:
    def __init__(self, log_file="analytics.json"):
        self.log_file = log_file
        self.logs = self._load_logs()

    def _load_logs(self):
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r") as f:
                    # Handle empty file case
                    content = f.read()
                    if not content:
                        return {"visits": 0, "clicks": {}, "slider_positions": []}
                    return json.loads(content)
            except json.JSONDecodeError:
                # If the file is corrupted, start fresh
                return {"visits": 0, "clicks": {}, "slider_positions": []}
        return {"visits": 0, "clicks": {}, "slider_positions": []}

    def _save_logs(self):
        try:
            with open(self.log_file, "w") as f:
                json.dump(self.logs, f, indent=2)
        except IOError as e:
            st.error(f"Error saving analytics: {e}") # In a real app, you'd handle this better

    def log_visit(self):
        self.logs["visits"] += 1
        self._save_logs()

    def log_click(self, article_url):
        if article_url not in self.logs["clicks"]:
            self.logs["clicks"][article_url] = 0
        self.logs["clicks"][article_url] += 1
        self._save_logs()

    def log_slider_position(self, position):
        self.logs["slider_positions"].append({"position": position, "timestamp": str(datetime.now())})
        self._save_logs()

    def get_summary(self):
        total_slider_positions = len(self.logs["slider_positions"])
        avg_slider = sum(p["position"] for p in self.logs["slider_positions"]) / max(1, total_slider_positions)
        return {
            "total_visits": self.logs["visits"],
            "total_clicks": sum(self.logs["clicks"].values()),
            "avg_slider_position": avg_slider,
            "clicks_by_url": self.logs["clicks"]
        }