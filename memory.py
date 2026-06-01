import json
import os
from datetime import datetime


class MemoryStore:
    """本地 JSON 文件持久化的知识点掌握度记忆库。"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.data: dict = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def get_weak_points(self) -> list[tuple[str, int]]:
        """返回评分 <= 2 的知识点列表，按评分升序排列。"""
        weak = [
            (topic, info.get("score", 3))
            for topic, info in self.data.items()
            if info.get("score", 3) <= 2
        ]
        weak.sort(key=lambda x: x[1])
        return weak

    def update(self, topic: str, correct: bool):
        """根据回答正误调整掌握度评分（1-5）。"""
        if topic not in self.data:
            self.data[topic] = {"ask_count": 0, "last_wrong": None, "score": 3}

        entry = self.data[topic]
        entry["ask_count"] = entry.get("ask_count", 0) + 1

        if correct:
            entry["score"] = min(5, entry.get("score", 3) + 1)
        else:
            entry["score"] = max(1, entry.get("score", 3) - 1)
            entry["last_wrong"] = datetime.now().isoformat()

        self._save()

    def get_topic(self, topic: str) -> dict | None:
        """获取某个知识点的完整记录。"""
        return self.data.get(topic)
