import pytest

# stats on a fresh system
def test_stats_empty_system(client):
    response = client.get('/admin/stats')
    assert response.status_code == 200
    stats = response.json()
    assert stats['total_files'] == 0
    assert stats['total_size'] == 0
    assert stats['tiers']['HOT']['count'] == 0
    assert stats['tiers']['WARM']['count'] == 0
    assert stats['tiers']['COLD']['count'] == 0

# stats after a single upload
def test_stats_single_upload(client, upload_test_file):
    file_size = 5 * 1024 * 1024  # 5MB
    upload_test_file("file1.txt", file_size)

    stats = client.get('/admin/stats').json()
    assert stats['total_files'] == 1
    assert stats['total_size'] == file_size
    assert stats['tiers']['HOT']['count'] == 1
    assert stats['tiers']['HOT']['size'] == file_size

# stats after multiple uploads
def test_stats_multiple_uploads(client, upload_test_file):
    file_size1 = 5 * 1024 * 1024  # 5MB
    file_size2 = 10 * 1024 * 1024  # 10MB
    upload_test_file("file1.txt", file_size1)
    upload_test_file("file1.txt", file_size2)

    stats = client.get('/admin/stats').json()
    assert stats['total_files'] == 2
    assert stats['total_size'] == file_size1 + file_size2
    assert stats['tiers']['HOT']['count'] == 2
    assert stats['tiers']['HOT']['size'] == file_size1 + file_size2


# stats after files across tiers
def test_stats_files_across_tiers(client, upload_test_file, simulate_time_passing):
    file_size1 = 5 * 1024 * 1024  # 5MB
    file_size2 = 10 * 1024 * 1024  # 10MB
    f1 = upload_test_file("file1.txt", file_size1)
    f2 = upload_test_file("file1.txt", file_size2)

    file_id_1 = f1.json()['file_id']
    file_id_2 = f2.json()['file_id']

    # move f2 from hot to warm tier
    simulate_time_passing(file_id_2, 31)
    client.post('/admin/tiering/run')

    stats = client.get('/admin/stats').json()
    assert stats['total_files'] == 2
    assert stats['total_size'] == file_size1 + file_size2
    assert stats['tiers']['HOT']['count'] == 1
    assert stats['tiers']['WARM']['count'] == 1
    assert stats['tiers']['COLD']['count'] == 0

# stats after file deletion
def test_stats_after_file_deletion(client, upload_test_file, simulate_time_passing):
    file_size = 5 * 1024 * 1024  # 5MB
    f = upload_test_file("file1.txt", file_size)
    file_id = f.json()['file_id']

    stats = client.get('/admin/stats').json()
    assert stats['total_files'] == 1
    
    client.delete(f'/files/{file_id}')
    
    stats = client.get('/admin/stats').json()
    assert stats['total_files'] == 0
    assert stats['total_size'] == 0



