"""Local filesystem storage backend."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any


class LocalStorage:
    """Store generated assets and uploads on the local filesystem.

    Args:
        generated_dir: Directory for generated assets (images/videos).
        upload_dir: Directory for user uploads (logos, product photos).
    """

    def __init__(
        self,
        generated_dir: str | Path = "./generated",
        upload_dir: str | Path = "./uploads",
    ) -> None:
        self.generated_dir = Path(generated_dir)
        self.upload_dir = Path(upload_dir)
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save_generated(
        self,
        content: bytes,
        filename: str,
        session_id: str = "",
    ) -> str:
        """Save a generated asset.

        Returns the file path.
        """
        if session_id:
            dest_dir = self.generated_dir / session_id
            dest_dir.mkdir(parents=True, exist_ok=True)
        else:
            dest_dir = self.generated_dir

        path = dest_dir / filename
        path.write_bytes(content)
        return str(path)

    def save_upload(
        self,
        content: bytes,
        filename: str,
        subfolder: str = "",
    ) -> str:
        """Save an uploaded file.

        Returns the file path.
        """
        if subfolder:
            dest_dir = self.upload_dir / subfolder
            dest_dir.mkdir(parents=True, exist_ok=True)
        else:
            dest_dir = self.upload_dir

        path = dest_dir / filename
        path.write_bytes(content)
        return str(path)

    def get_url(self, path: str) -> str:
        """Get the serving URL for a file path."""
        p = Path(path)
        if self.generated_dir in p.parents or p.parent == self.generated_dir:
            rel = p.relative_to(self.generated_dir)
            return f"/generated/{rel}"
        if self.upload_dir in p.parents or p.parent == self.upload_dir:
            rel = p.relative_to(self.upload_dir)
            return f"/uploads/{rel}"
        return f"/{p.name}"

    def delete(self, path: str) -> bool:
        """Delete a file. Returns True if deleted."""
        p = Path(path)
        if p.exists():
            p.unlink()
            return True
        return False

    def list_generated(
        self,
        session_id: str = "",
        file_types: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".mp4"),
    ) -> list[dict[str, Any]]:
        """List generated files."""
        search_dir = self.generated_dir / session_id if session_id else self.generated_dir
        if not search_dir.exists():
            return []

        files = []
        for f in search_dir.iterdir():
            if f.suffix.lower() in file_types:
                files.append({
                    "filename": f.name,
                    "path": str(f),
                    "url": self.get_url(str(f)),
                    "created": f.stat().st_mtime,
                    "size": f.stat().st_size,
                    "type": "video" if f.suffix.lower() == ".mp4" else "image",
                })
        files.sort(key=lambda x: x["created"], reverse=True)
        return files
