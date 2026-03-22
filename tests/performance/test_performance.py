import pytest
import io
from src.storage_service import app
from fastapi.testclient import TestClient
from concurrent.futures import ThreadPoolExecutor, as_completed

client = TestClient(app)

FILE_SIZE = 5 * 1024 * 1024  # 5MB
NUM_CONCURRENT_REQUESTS = 10

def upload_file(index):
    data = io.BytesIO(b"x" * FILE_SIZE)
    response = client.post("/files", files={"file": (f"file_{index}.txt", data, "application/octet-stream")})
    return response

def download_file(file_id):
    response = client.get(f"/files/{file_id}")
    return response

# 10 uploads at the same time
# Should succeed with no file_id collisions
def test_concurrent_uploads():
    results = []
    with ThreadPoolExecutor(max_workers=NUM_CONCURRENT_REQUESTS) as executor:
        futures = [executor.submit(upload_file, i) for i in range(NUM_CONCURRENT_REQUESTS)]
        for future in as_completed(futures):
            results.append(future.result())

    for result in results:
        assert result.status_code == 201
    
    file_ids = [result.json()["file_id"] for result in results]
    assert len(set(file_ids)) == NUM_CONCURRENT_REQUESTS, "duplicate file_ids detected"


# 10 threads downloading the same file
# all should get the same content back
def test_concurrent_downloads():
    upload_res = upload_file(0)
    assert upload_res.status_code == 201
    file_id = upload_res.json()["file_id"]

    with ThreadPoolExecutor(max_workers=NUM_CONCURRENT_REQUESTS) as executor:
        futures = [executor.submit(download_file, file_id) for _ in range(NUM_CONCURRENT_REQUESTS)]
        for future in as_completed(futures):
            response = future.result()
            assert response.status_code == 200
    
    # make sure all responses are the same
    responses = [future.result() for future in futures]
    assert len(set([response.content for response in responses])) == 1, "different responses for same file"

# upload 50 files, age them all and verify tiering moves all 50
def test_tiering():
    file_ids = []
    for i in range(50):
        upload_res = upload_file(i)
        assert upload_res.status_code == 201
        file_ids.append(upload_res.json()["file_id"])
    
    # age all files by 31 days so they move from HOT -> WARM tier
    for file_id in file_ids:
        response = client.post(f"/admin/files/{file_id}/update-last-accessed", json={"days_ago": 31})
        assert response.status_code == 200
    
    tiering_response = client.post("/admin/tiering/run")
    assert tiering_response.status_code == 200
    assert tiering_response.json()["files_moved"] == 50