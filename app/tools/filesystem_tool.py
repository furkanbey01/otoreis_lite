from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class FilesystemTool:
    def __init__(self, workspace_dir: str):
        self.root = Path(workspace_dir).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _safe(self, rel_path: str) -> Path:
        p = (self.root / rel_path).resolve()
        if not str(p).startswith(str(self.root)):
            raise ValueError("path escapes workspace")
        return p

    def write_file(self, path: str, content: str) -> dict[str, Any]:
        target = self._safe(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {"path": str(target), "bytes": len(content.encode("utf-8"))}

    def read_file(self, path: str) -> dict[str, Any]:
        target = self._safe(path)
        content = target.read_text(encoding="utf-8")
        return {"path": str(target), "content": content[:5000]}

    def save_json(self, path: str, payload: Any) -> dict[str, Any]:
        data = json.dumps(payload, ensure_ascii=False, indent=2)
        return self.write_file(path, data)

    def delete_file(self, path: str) -> dict[str, Any]:
        target = self._safe(path)
        target.unlink(missing_ok=False)
        return {"deleted": str(target)}
