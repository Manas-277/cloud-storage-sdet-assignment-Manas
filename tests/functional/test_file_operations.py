import pytest

# === Upload Tests ===
def test_upload_valid_file(upload_test_file):
    response = upload_test_file("test_file.txt", 10*1024*1024) # 10MB
    assert response.status_code == 201
    assert response.json()["tier"] == "HOT"

def test_upload_zero_byte_file(upload_test_file):
    response = upload_test_file("test_file.txt", 0) # 0 byte
    assert response.status_code == 400
    
def test_upload_below_lower_limit_file(upload_test_file):
    response = upload_test_file("test_file.txt", 500 * 1024) # 500Kb
    assert response.status_code == 400

def test_upload_just_below_lower_limit_file(upload_test_file):
    response = upload_test_file("test_file.txt", 900 * 1024) # 0.9MB
    assert response.status_code == 400

def test_upload_exactly_at_lower_limit_file(upload_test_file):
    response = upload_test_file("document.txt", 1024 * 1024) # 1MB
    assert response.status_code == 201
    assert response.json()["tier"] == "HOT"

def test_upload_1byte_minus_lower_limit_file(upload_test_file):
    response = upload_test_file("test_file.txt", 1024 * 1024 - 1) # 1MB - 1 byte
    assert response.status_code == 400

@pytest.mark.skip(reason="Allocating 10GB in memory during tests is not feasible")               
def test_upload_exactly_at_upper_limit_file(upload_test_file):
    response = upload_test_file("test_file.txt", 10 * 1024 * 1024 * 1024) # 10GB
    assert response.status_code == 201
    assert response.json()["tier"] == "HOT"

@pytest.mark.skip(reason="Allocating 10GB+ in memory during tests is not feasible")
def test_upload_1byte_plus_upper_limit_file(upload_test_file):
    response = upload_test_file("test_file.txt", 10 * 1024 * 1024 * 1024 + 1) # 10GB + 1 byte
    assert response.status_code == 400

@pytest.mark.skip(reason="Allocating 11GB+ in memory during tests is not feasible")
def test_upload_above_upper_limit_file(upload_test_file):
    response = upload_test_file("test_file.txt", 11 * 1024 * 1024 * 1024 + 1) # 11GB
    assert response.status_code == 400

def test_upload_file_with_special_characters(upload_test_file):
    response = upload_test_file("file@$m%.txt", 5 * 1024 * 1024) # file@$m%.txt
    assert response.status_code == 201

# === Download File Tests ===
def test_download_existing_file(client, upload_test_file):
    response = upload_test_file("test_file.txt", 10 * 1024 * 1024) # 10MB
    assert response.status_code == 201
    file_id = response.json()["file_id"]

    download_response = client.get(f"/files/{file_id}")
    assert download_response.status_code == 200

def test_download_non_existing_file(client):
    response = client.get("/files/abc123")
    assert response.status_code == 404

def test_download_file_with_invalid_id(client):
    response = client.get("/files/123!%#")
    assert response.status_code == 404

def test_check_last_updated_after_download(client, upload_test_file):
    # upload a file
    response = upload_test_file("test_file.txt", 5 * 1024 * 1024)
    assert response.status_code == 201
    file_id = response.json()['file_id']
    # fetch meta data
    meta_response = client.get(f"/files/{file_id}/metadata")
    assert meta_response.status_code == 200
    last_updated = meta_response.json()['last_accessed']
    # download the file
    download_response = client.get(f'/files/{file_id}')
    assert download_response.status_code == 200
    # fetch meta data again
    meta_response = client.get(f"/files/{file_id}/metadata")
    assert meta_response.status_code == 200
    new_last_updated = meta_response.json()['last_accessed']
    # assert new timestamp is greater/equal to the last_updated timestamp
    assert new_last_updated >= last_updated

# === Get Metadata Tests ===
def test_get_metadata_of_existing_file(client, upload_test_file):
    upload_response = upload_test_file('doc.txt', 10 * 1024 * 1024)
    assert upload_response.status_code == 201
    file_id = upload_response.json()['file_id']

    meta_response = client.get(f"/files/{file_id}/metadata")
    assert meta_response.status_code == 200

    meta = meta_response.json()
    # verify all expected fields are present and have correct values
    assert meta['filename'] == 'doc.txt'
    assert meta['size'] == 10 * 1024 * 1024
    assert meta['file_id'] == file_id
    assert meta['tier'] == 'HOT'
    assert 'last_accessed' in meta
    assert 'created_at' in meta

def test_get_metadata_of_non_existing_file(client):
    response = client.get("/files/abc123/metadata")
    assert response.status_code == 404

# === Delete File Tests ===
def test_delete_existing_file(client, upload_test_file):
    response = upload_test_file("test_file.txt", 10 * 1024 * 1024)
    assert response.status_code == 201
    file_id = response.json()["file_id"]

    delete_response = client.delete(f"/files/{file_id}")
    assert delete_response.status_code == 204

    # confirm file is fully gone
    get_response = client.get(f"/files/{file_id}")
    assert get_response.status_code == 404

def test_delete_non_existing_file(client):
    response = client.delete("/files/abc123")
    assert response.status_code == 404

def test_delete_same_file_twice(client, upload_test_file):
    response = upload_test_file("test_file.txt", 10 * 1024 * 1024)
    assert response.status_code == 201
    file_id = response.json()["file_id"]

    delete_response = client.delete(f"/files/{file_id}")
    assert delete_response.status_code == 204

    delete_response = client.delete(f"/files/{file_id}")
    assert delete_response.status_code == 404 # file should not exist

    

