"""Tests for diagram storage"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from src.storage import DiagramStorage
from src.models import DiagramMetadata, DiagramType


@pytest.fixture
def temp_storage_path():
    """Create temporary storage directory"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)


@pytest.fixture
def storage(temp_storage_path):
    """Create storage instance with temp directory"""
    return DiagramStorage(temp_storage_path)


@pytest.fixture
def sample_metadata():
    """Create sample diagram metadata"""
    return DiagramMetadata(
        name="Test Diagram",
        description="Test description",
        diagram_type=DiagramType.AWS_ARCHITECTURE,
        author="Test Author",
        tags=["test", "sample"],
    )


@pytest.fixture
def sample_code():
    """Sample diagram code"""
    return """
from diagrams import Diagram
from diagrams.aws.compute import Lambda

with Diagram("Test", show=False):
    lambda_func = Lambda("Function")
"""


def test_save_diagram(storage, sample_metadata, sample_code):
    """Test saving a diagram"""
    output_files = {}  # No actual files for this test
    stored = storage.save_diagram(sample_code, sample_metadata, output_files)

    assert stored.diagram_id is not None
    assert stored.metadata.name == "Test Diagram"
    assert stored.checksum is not None


def test_get_diagram(storage, sample_metadata, sample_code):
    """Test retrieving a stored diagram"""
    output_files = {}
    stored = storage.save_diagram(sample_code, sample_metadata, output_files)

    retrieved = storage.get_diagram(stored.diagram_id)
    assert retrieved is not None
    assert retrieved.diagram_id == stored.diagram_id
    assert retrieved.metadata.name == sample_metadata.name


def test_list_diagrams(storage, sample_metadata, sample_code):
    """Test listing diagrams"""
    # Save multiple diagrams
    for i in range(3):
        metadata = DiagramMetadata(
            name=f"Diagram {i}",
            tags=["test"] if i < 2 else ["other"],
        )
        storage.save_diagram(sample_code, metadata, {})

    all_diagrams = storage.list_diagrams()
    assert len(all_diagrams) == 3

    # Filter by tag
    test_tagged = storage.list_diagrams(tag="test")
    assert len(test_tagged) == 2


def test_delete_diagram(storage, sample_metadata, sample_code):
    """Test deleting a diagram"""
    stored = storage.save_diagram(sample_code, sample_metadata, {})
    diagram_id = stored.diagram_id

    # Verify it exists
    assert storage.get_diagram(diagram_id) is not None

    # Delete it
    assert storage.delete_diagram(diagram_id) is True

    # Verify it's gone
    assert storage.get_diagram(diagram_id) is None


def test_checksum_calculation(storage, sample_metadata, sample_code):
    """Test that checksums are calculated correctly"""
    stored = storage.save_diagram(sample_code, sample_metadata, {})

    # Retrieve and verify checksum matches
    retrieved = storage.get_diagram(stored.diagram_id)
    assert retrieved.checksum == stored.checksum

    # Verify it's a valid SHA256 hash (64 hex characters)
    assert len(stored.checksum) == 64
    assert all(c in "0123456789abcdef" for c in stored.checksum)


def test_metadata_persistence(storage, sample_code):
    """Test that metadata is properly persisted"""
    metadata = DiagramMetadata(
        name="Persistent Diagram",
        description="This should persist",
        author="Test Author",
        tags=["persistent", "test"],
    )
    stored = storage.save_diagram(sample_code, metadata, {})

    # Retrieve and verify all metadata fields
    retrieved = storage.get_diagram(stored.diagram_id)
    assert retrieved.metadata.name == "Persistent Diagram"
    assert retrieved.metadata.description == "This should persist"
    assert retrieved.metadata.author == "Test Author"
    assert "persistent" in retrieved.metadata.tags


def test_index_persistence(storage, temp_storage_path, sample_metadata, sample_code):
    """Test that index is properly saved and loaded"""
    # Save a diagram
    stored1 = storage.save_diagram(sample_code, sample_metadata, {})

    # Create new storage instance (should load from disk)
    storage2 = DiagramStorage(temp_storage_path)

    # Should be able to retrieve the diagram
    retrieved = storage2.get_diagram(stored1.diagram_id)
    assert retrieved is not None
    assert retrieved.diagram_id == stored1.diagram_id
