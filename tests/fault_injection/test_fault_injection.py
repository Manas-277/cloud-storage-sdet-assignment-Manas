import pytest
import io
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.storage_service import files_content, files_metadata, app
import src.storage_service as storage_module

client = TestClient(app, raise_server_exceptions=False)

FILE_SIZE = 5 * 1024 * 1024  # 5MB

def upload_file(name = "test.txt"):
    data = io.BytesIO(b"x" * FILE_SIZE)
    response = client.post("/files", files={"file": (name, data, "application/octet-stream")})
    return response

#simulate the storage layer going down
# file exists in metadata but content cannot be retrieved
def test_storage_failure_during_download():
    res = upload_file()
    assert res.status_code == 201
    file_id = res.json()["file_id"]
    
    # replace the real content store with the fake one that raises on access
    broken_content = MagicMock()
    broken_content.__contains__.return_value = True
    broken_content.__getitem__.side_effect = Exception("Storage unavailable")

    with patch.object(storage_module, "files_content", broken_content):
        response = client.get(f"/files/{file_id}")
        assert response.status_code == 500

#simulate a partial upload where the metadata was saved but the content was not
def test_corrupted_state_missing_content():
    res = upload_file()
    assert res.status_code == 201
    file_id = res.json()["file_id"]
    
    # remove the content from the store
    del storage_module.files_content[file_id]
    
    response = client.get(f"/files/{file_id}")
    assert response.status_code == 500