import pytest
import io
import sys
import os


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.storage_service import app, files_content, files_metadata
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    return TestClient(app)

# cleanup before and after each test
@pytest.fixture(autouse=True)
def clean_storage():
    files_content.clear()
    files_metadata.clear()
    yield
    files_content.clear()
    files_metadata.clear()


# creates a mock file with a given size for testing purpose
@pytest.fixture
def create_test_file():
    def _create(name, size):
        return name, io.BytesIO(b"x" * size)
    return _create

# uploads a file and returns the full response
@pytest.fixture
def upload_test_file(client, create_test_file):
    def _upload(name = "test_file.txt", size = 5 * 1024 * 1024): # considering 5MB as default file size here
        fname, file = create_test_file(name, size)
        response = client.post("/files", files={"file": (fname, file, "application/octet-stream")})
        return response
    return _upload

# Simulates time passing by changing the last accessed time of a file.
# Useful for tiering tests where we don't need to wait for 30/90 days.
@pytest.fixture
def simulate_time_passing(client):
    def _simulate(file_id, days):
        response = client.post(f"/admin/files/{file_id}/update-last-accessed", json={"days_ago": days})
        return response
    return _simulate