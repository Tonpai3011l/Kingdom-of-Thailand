import json
import logging
import os
from typing import Any

from keep_alive import get_database


class HybridJsonStorage:
    """Store JSON-shaped data in MongoDB with a local JSON fallback."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.mongo_path = file_path.replace("\\", "/")
        self.collection_name = os.getenv("MONGODB_COLLECTION", "json_files")

    def _read_json(self) -> Any:
        if not os.path.exists(self.file_path):
            return None
        with open(self.file_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def _write_json(self, data: Any) -> None:
        directory = os.path.dirname(self.file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    def load(self, default: Any = None) -> Any:
        database = get_database()
        if database is not None:
            try:
                document = database[self.collection_name].find_one({"_id": self.mongo_path})
                if document is not None:
                    return document["data"]
            except Exception:
                logging.exception("MongoDB read failed for %s; using JSON fallback", self.file_path)

        data = self._read_json()
        if data is not None:
            if database is not None:
                try:
                    database[self.collection_name].replace_one(
                        {"_id": self.mongo_path},
                        {"_id": self.mongo_path, "data": data},
                        upsert=True,
                    )
                except Exception:
                    logging.exception("Could not migrate %s to MongoDB", self.file_path)
            return data
        return default

    def save(self, data: Any) -> None:
        database = get_database()
        if database is not None:
            try:
                database[self.collection_name].replace_one(
                    {"_id": self.mongo_path},
                    {"_id": self.mongo_path, "data": data},
                    upsert=True,
                )
                return
            except Exception:
                logging.exception("MongoDB write failed for %s; using JSON fallback", self.file_path)

        self._write_json(data)
