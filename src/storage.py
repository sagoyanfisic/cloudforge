"""Diagram storage and retrieval module"""

import json
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from .models import StoredDiagram, DiagramMetadata
from .config import settings


class DiagramStorage:
    """Manages diagram storage and retrieval"""

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        self.storage_path = storage_path or settings.diagrams_storage_path
        self.diagrams_path = self.storage_path / "diagrams"
        self.metadata_path = self.storage_path / "metadata"
        self.index_path = self.storage_path / "index.json"

        # Create directories
        self.diagrams_path.mkdir(parents=True, exist_ok=True)
        self.metadata_path.mkdir(parents=True, exist_ok=True)

        # Load or create index
        self._index: dict[str, dict[str, str]] = self._load_index()

    def save_diagram(
        self,
        code: str,
        metadata: DiagramMetadata,
        output_files: dict[str, str],
    ) -> StoredDiagram:
        """Save a diagram and its outputs"""
        # Generate diagram ID
        diagram_id = str(uuid.uuid4())

        # Calculate checksum
        checksum = self._calculate_checksum(code)

        # Save code
        code_file = self.diagrams_path / f"{diagram_id}.py"
        code_file.write_text(code, encoding="utf-8")

        # Save outputs
        file_paths: dict[str, str] = {}
        total_size = 0

        for format_type, file_path in output_files.items():
            if Path(file_path).exists():
                output_file = self.diagrams_path / f"{diagram_id}.{format_type}"
                Path(file_path).rename(output_file)
                file_paths[format_type] = str(output_file)
                total_size += output_file.stat().st_size

        # Save metadata
        metadata.updated_at = datetime.utcnow()
        metadata_file = self.metadata_path / f"{diagram_id}.json"
        metadata_file.write_text(
            metadata.model_dump_json(indent=2),
            encoding="utf-8",
        )

        # Update index
        self._index[diagram_id] = {
            "name": metadata.name,
            "created_at": metadata.created_at.isoformat(),
            "checksum": checksum,
        }
        self._save_index()

        return StoredDiagram(
            diagram_id=diagram_id,
            metadata=metadata,
            code=code,
            file_paths=file_paths,
            file_size_bytes=total_size,
            checksum=checksum,
        )

    def get_diagram(self, diagram_id: str) -> Optional[StoredDiagram]:
        """Retrieve a stored diagram"""
        if diagram_id not in self._index:
            return None

        # Load metadata
        metadata_file = self.metadata_path / f"{diagram_id}.json"
        if not metadata_file.exists():
            return None

        metadata = DiagramMetadata.model_validate_json(
            metadata_file.read_text(encoding="utf-8")
        )

        # Load code
        code_file = self.diagrams_path / f"{diagram_id}.py"
        if not code_file.exists():
            return None

        code = code_file.read_text(encoding="utf-8")

        # Find output files
        file_paths: dict[str, str] = {}
        total_size = 0

        for format_type in settings.output_formats:
            output_file = self.diagrams_path / f"{diagram_id}.{format_type}"
            if output_file.exists():
                file_paths[format_type] = str(output_file)
                total_size += output_file.stat().st_size

        # Get checksum
        checksum = self._index[diagram_id]["checksum"]

        return StoredDiagram(
            diagram_id=diagram_id,
            metadata=metadata,
            code=code,
            file_paths=file_paths,
            file_size_bytes=total_size,
            checksum=checksum,
        )

    def list_diagrams(self, tag: Optional[str] = None) -> list[StoredDiagram]:
        """List all stored diagrams, optionally filtered by tag"""
        diagrams: list[StoredDiagram] = []

        for diagram_id in self._index.keys():
            diagram = self.get_diagram(diagram_id)
            if diagram:
                if tag is None or tag in diagram.metadata.tags:
                    diagrams.append(diagram)

        # Sort by creation time (newest first)
        diagrams.sort(
            key=lambda x: x.metadata.created_at,
            reverse=True,
        )

        return diagrams

    def delete_diagram(self, diagram_id: str) -> bool:
        """Delete a stored diagram"""
        if diagram_id not in self._index:
            return False

        # Remove files
        code_file = self.diagrams_path / f"{diagram_id}.py"
        if code_file.exists():
            code_file.unlink()

        for format_type in settings.output_formats:
            output_file = self.diagrams_path / f"{diagram_id}.{format_type}"
            if output_file.exists():
                output_file.unlink()

        # Remove metadata
        metadata_file = self.metadata_path / f"{diagram_id}.json"
        if metadata_file.exists():
            metadata_file.unlink()

        # Update index
        del self._index[diagram_id]
        self._save_index()

        return True

    def _calculate_checksum(self, data: str) -> str:
        """Calculate SHA256 checksum"""
        return hashlib.sha256(data.encode()).hexdigest()

    def _load_index(self) -> dict[str, dict[str, str]]:
        """Load index of stored diagrams"""
        if self.index_path.exists():
            with open(self.index_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_index(self) -> None:
        """Save index of stored diagrams"""
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(self._index, f, indent=2)
