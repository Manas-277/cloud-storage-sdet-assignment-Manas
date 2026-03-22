import pytest

def test_file_stays_in_hot_tier(client, simulate_time_passing, upload_test_file):
    response = upload_test_file()
    file_id = response.json()['file_id']

    simulate_time_passing(file_id, 29)
    # trigger tiering
    tiering_response = client.post('/admin/tiering/run')
    assert tiering_response.json()['files_moved'] == 0

    # confirm file is still in hot
    meta = client.get(f"/files/{file_id}/metadata").json()
    assert meta['tier'] == 'HOT'

def test_hot_to_warm(client, upload_test_file, simulate_time_passing):
    response = upload_test_file()
    file_id = response.json()['file_id']

    simulate_time_passing(file_id, 30)

    # trigger tiering
    tiering_response = client.post('/admin/tiering/run')
    assert tiering_response.json()['files_moved'] == 1

    # confirm file is now in warm
    meta = client.get(f"/files/{file_id}/metadata").json()
    assert meta['tier'] == 'WARM'

# test file at 31 days should also move to warm
def test_hot_to_warm_31_days(client, upload_test_file, simulate_time_passing):
    response = upload_test_file()
    file_id = response.json()['file_id']

    simulate_time_passing(file_id, 31)

    # trigger tiering
    tiering_response = client.post('/admin/tiering/run')
    assert tiering_response.json()['files_moved'] == 1

    # confirm file is now in warm
    meta = client.get(f"/files/{file_id}/metadata").json()
    assert meta['tier'] == 'WARM'

def test_file_stays_in_warm_tier(client, upload_test_file, simulate_time_passing):
    response = upload_test_file()
    file_id = response.json()['file_id']

    # first move to warm
    simulate_time_passing(file_id, 31)
    client.post('/admin/tiering/run')

    # simulating 89 more days
    simulate_time_passing(file_id, 89)
    tiering_response = client.post('/admin/tiering/run')
    assert tiering_response.json()['files_moved'] == 0

    # confirm file is still in warm
    meta = client.get(f"/files/{file_id}/metadata").json()
    assert meta['tier'] == 'WARM'

def test_warm_to_cold(client, upload_test_file, simulate_time_passing):
    response = upload_test_file()
    file_id = response.json()['file_id']

    # first move to warm
    simulate_time_passing(file_id, 31)
    client.post('/admin/tiering/run')

    # simulating 90 more days
    simulate_time_passing(file_id, 90)
    tiering_response = client.post('/admin/tiering/run')
    assert tiering_response.json()['files_moved'] == 1

    # confirm file is now in cold
    meta = client.get(f"/files/{file_id}/metadata").json()
    assert meta['tier'] == 'COLD'

def test_warm_to_cold_91_days(client, upload_test_file, simulate_time_passing):
    response = upload_test_file()
    file_id = response.json()['file_id']

    # first move to warm
    simulate_time_passing(file_id, 31)
    client.post('/admin/tiering/run')

    # simulating 91 more days
    simulate_time_passing(file_id, 91)
    tiering_response = client.post('/admin/tiering/run')
    assert tiering_response.json()['files_moved'] == 1

    # confirm file is now in cold
    meta = client.get(f"/files/{file_id}/metadata").json()
    assert meta['tier'] == 'COLD'

def test_file_in_cold_stays_in_cold(client, upload_test_file, simulate_time_passing):
    response = upload_test_file()
    file_id = response.json()['file_id']

    # move to WARM
    simulate_time_passing(file_id, 31)
    client.post('/admin/tiering/run')

    # move to COLD
    simulate_time_passing(file_id, 91)
    client.post('/admin/tiering/run')

    # now verify it stays in COLD
    simulate_time_passing(file_id, 200)
    tiering_response = client.post('/admin/tiering/run')
    assert tiering_response.json()['files_moved'] == 0

    meta = client.get(f"/files/{file_id}/metadata").json()
    assert meta['tier'] == 'COLD'

# Files containing "_PRIORITY_" in filename should stay in HOT tier
def test_priority_file(client, upload_test_file, simulate_time_passing):
    response = upload_test_file('_PRIORITY_balances.txt')
    file_id = response.json()['file_id']

    simulate_time_passing(file_id, 90)

    # trigger tiering
    tiering_response = client.post('/admin/tiering/run')
    assert tiering_response.json()['files_moved'] == 0

    # confirm file is still in hot
    meta = client.get(f"/files/{file_id}/metadata").json()
    assert meta['tier'] == 'HOT'

# Legal documents have extended retention in WARM tier (180 days instead of 90)
def test_legal_document(client, upload_test_file, simulate_time_passing):
    response = upload_test_file('LEGAL_contracts.txt')
    file_id = response.json()['file_id']

    # move to WARM first
    simulate_time_passing(file_id, 31)
    client.post('/admin/tiering/run')

    # at 179 days rule not expired, stay in WARM
    simulate_time_passing(file_id, 179)
    tiering_response = client.post('/admin/tiering/run')
    assert tiering_response.json()['files_moved'] == 0
    meta = client.get(f"/files/{file_id}/metadata").json()
    assert meta['tier'] == 'WARM'

    # at 181 days rule expired, move to COLD
    simulate_time_passing(file_id, 181)
    tiering_response = client.post('/admin/tiering/run')
    assert tiering_response.json()['files_moved'] == 1
    meta = client.get(f"/files/{file_id}/metadata").json()
    assert meta['tier'] == 'COLD'
    
