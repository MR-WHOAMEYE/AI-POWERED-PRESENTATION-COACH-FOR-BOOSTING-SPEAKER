"""
Unit and integration tests for Authentication Routes
"""
import json
from bson import ObjectId


def test_firebase_sync_missing_uid_returns_400(client):
    """Missing UID or email in sync request should return 400"""
    response = client.post('/auth/firebase-sync', json={})
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_firebase_sync_creates_new_user(client, mongo_db, mock_firebase):
    """POST /auth/firebase-sync creates a new user in database"""
    payload = {
        'uid': 'fb-uid-999',
        'email': 'newuser@example.com',
        'name': 'New Presenter',
        'picture': 'https://example.com/new.jpg'
    }
    response = client.post(
        '/auth/firebase-sync',
        json=payload,
        headers={'Authorization': 'Bearer fake-token'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['user']['email'] == 'newuser@example.com'
    assert data['user']['name'] == 'New Presenter'


def test_firebase_sync_updates_existing_user(client, mongo_db, mock_firebase, sample_user):
    """POST /auth/firebase-sync updates existing user info"""
    payload = {
        'uid': sample_user['firebase_uid'],
        'email': sample_user['email'],
        'name': 'Updated Presenter Name'
    }
    response = client.post(
        '/auth/firebase-sync',
        json=payload,
        headers={'Authorization': 'Bearer fake-token'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['user']['name'] == 'Updated Presenter Name'


def test_auth_status_unauthenticated(client):
    """GET /auth/status without session returns unauthenticated"""
    response = client.get('/auth/status')
    assert response.status_code == 200
    data = response.get_json()
    assert data['authenticated'] is False


def test_auth_status_authenticated(client, sample_user):
    """GET /auth/status with active session returns user info"""
    with client.session_transaction() as sess:
        sess['user_id'] = str(sample_user['_id'])
        sess['firebase_uid'] = sample_user['firebase_uid']

    response = client.get('/auth/status')
    assert response.status_code == 200
    data = response.get_json()
    assert data['authenticated'] is True
    assert data['user']['email'] == sample_user['email']


def test_logout_clears_session(client, sample_user):
    """POST /auth/logout clears user session"""
    with client.session_transaction() as sess:
        sess['user_id'] = str(sample_user['_id'])

    response = client.post('/auth/logout')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True

    # Confirm session is cleared
    status_response = client.get('/auth/status')
    assert status_response.get_json()['authenticated'] is False


def test_google_drive_status(client, sample_user):
    """GET /auth/google-drive/status returns drive connection status"""
    with client.session_transaction() as sess:
        sess['user_id'] = str(sample_user['_id'])

    response = client.get('/auth/google-drive/status')
    assert response.status_code == 200
    data = response.get_json()
    assert 'connected' in data
