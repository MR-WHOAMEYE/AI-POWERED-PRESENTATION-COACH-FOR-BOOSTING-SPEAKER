"""
Unit tests for MongoDB User and PracticeSession Models
"""
from datetime import datetime
from bson import ObjectId
from models import User, PracticeSession


def test_user_create_document():
    """Test User.create_document factory method structure"""
    doc = User.create_document(
        firebase_uid='uid-456',
        google_id='gid-789',
        email='presenter@example.com',
        name='Alex Morgan',
        picture='https://example.com/alex.jpg',
        access_token='token-abc',
        refresh_token='refresh-xyz'
    )
    assert doc['firebase_uid'] == 'uid-456'
    assert doc['google_id'] == 'gid-789'
    assert doc['email'] == 'presenter@example.com'
    assert doc['name'] == 'Alex Morgan'
    assert doc['access_token'] == 'token-abc'
    assert 'preferences' in doc
    assert doc['preferences']['eyeContact'] is True
    assert doc['preferences']['fillerWords'] is True
    assert isinstance(doc['created_at'], datetime)


def test_user_to_dict():
    """Test User.to_dict serialization for API responses"""
    user_id = ObjectId()
    raw_doc = {
        '_id': user_id,
        'email': 'presenter@example.com',
        'name': 'Alex Morgan',
        'picture': 'https://example.com/alex.jpg',
        'access_token': 'token-abc',
        'preferences': {
            'eyeContact': True,
            'sensitivity': 85
        }
    }
    result = User.to_dict(raw_doc)
    assert result['id'] == str(user_id)
    assert result['email'] == 'presenter@example.com'
    assert result['name'] == 'Alex Morgan'
    assert result['hasGoogleToken'] is True
    assert result['preferences']['sensitivity'] == 85

    # None check
    assert User.to_dict(None) is None


def test_practice_session_create_document():
    """Test PracticeSession.create_document structure"""
    user_id = ObjectId()
    session_doc = PracticeSession.create_document(
        user_id=user_id,
        presentation_id='slides-12345',
        presentation_title='Q3 Business Review'
    )
    assert session_doc['user_id'] == user_id
    assert session_doc['presentation_id'] == 'slides-12345'
    assert session_doc['presentation_title'] == 'Q3 Business Review'
    assert session_doc['metrics'] == {}
    assert session_doc['ended_at'] is None
    assert isinstance(session_doc['started_at'], datetime)


def test_practice_session_to_dict():
    """Test PracticeSession.to_dict serialization"""
    session_id = ObjectId()
    start_time = datetime(2026, 9, 1, 10, 0, 0)
    end_time = datetime(2026, 9, 1, 10, 15, 0)

    raw_doc = {
        '_id': session_id,
        'presentation_id': 'slides-12345',
        'presentation_title': 'Q3 Business Review',
        'started_at': start_time,
        'ended_at': end_time,
        'duration_seconds': 900,
        'metrics': {
            'wpm': 135,
            'eye_contact_percentage': 82
        },
        'overall_score': 88,
        'recording_url': 'https://res.cloudinary.com/demo/video.mp4'
    }
    result = PracticeSession.to_dict(raw_doc)
    assert result['id'] == str(session_id)
    assert result['presentationId'] == 'slides-12345'
    assert result['durationSeconds'] == 900
    assert result['overallScore'] == 88
    assert result['hasRecording'] is True
    assert result['recordingUrl'] == 'https://res.cloudinary.com/demo/video.mp4'

    assert PracticeSession.to_dict(None) is None
