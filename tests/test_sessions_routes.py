"""
Unit and integration tests for Sessions Routes
"""
from bson import ObjectId
from models import PracticeSession


def test_create_session(client, sample_user):
    """POST /sessions/ creates a new practice session"""
    with client.session_transaction() as sess:
        sess['user_id'] = str(sample_user['_id'])

    payload = {
        'presentationId': 'deck-101',
        'presentationTitle': 'Quarterly Demo'
    }
    response = client.post('/sessions/', json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert 'session' in data
    assert data['session']['presentationId'] == 'deck-101'
    assert data['session']['presentationTitle'] == 'Quarterly Demo'


def test_get_session(client, sample_user, mongo_db):
    """GET /sessions/<id> returns session details"""
    with client.session_transaction() as sess:
        sess['user_id'] = str(sample_user['_id'])

    session_doc = PracticeSession.create_document(
        user_id=sample_user['_id'],
        presentation_id='deck-101',
        presentation_title='Quarterly Demo'
    )
    result = mongo_db.practice_sessions.insert_one(session_doc)
    session_id = str(result.inserted_id)

    response = client.get(f'/sessions/{session_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['session']['id'] == session_id
    assert data['session']['presentationId'] == 'deck-101'


def test_update_session_metrics(client, sample_user, mongo_db):
    """PUT /sessions/<id> updates session metrics and score"""
    with client.session_transaction() as sess:
        sess['user_id'] = str(sample_user['_id'])

    session_doc = PracticeSession.create_document(
        user_id=sample_user['_id'],
        presentation_id='deck-102'
    )
    result = mongo_db.practice_sessions.insert_one(session_doc)
    session_id = str(result.inserted_id)

    payload = {
        'metrics': {'wpm': 140, 'eyeContact': 85},
        'overallScore': 90
    }
    response = client.put(f'/sessions/{session_id}', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data['session']['overallScore'] == 90
    assert data['session']['metrics']['wpm'] == 140


def test_complete_session(client, sample_user, mongo_db):
    """POST /sessions/<id>/complete finalizes duration and state"""
    with client.session_transaction() as sess:
        sess['user_id'] = str(sample_user['_id'])

    session_doc = PracticeSession.create_document(
        user_id=sample_user['_id'],
        presentation_id='deck-103'
    )
    result = mongo_db.practice_sessions.insert_one(session_doc)
    session_id = str(result.inserted_id)

    response = client.post(f'/sessions/{session_id}/complete', json={})
    assert response.status_code == 200
    data = response.get_json()
    assert data['session']['endedAt'] is not None
