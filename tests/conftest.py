"""
Shared fixtures for Presentation Coach Pytest suite
"""
import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest
from bson import ObjectId

# Ensure backend directory is in python search path
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import create_app
from models import User, PracticeSession


@pytest.fixture(scope='session')
def app():
    """Create Flask application configured for testing"""
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'True'
    
    # Try creating testing app
    test_app = create_app('testing')
    test_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key-12345',
        'WTF_CSRF_ENABLED': False
    })

    # If real MongoDB is not available in local test run, attach mongomock
    if test_app.extensions.get('mongo_db') is None:
        try:
            import mongomock
            mock_client = mongomock.MongoClient()
            mock_db = mock_client['presentation_coach_test']
            test_app.extensions['mongo_db'] = mock_db
            import app as backend_app_module
            backend_app_module.db = mock_db
        except ImportError:
            pass

    return test_app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def mongo_db(app):
    """Database fixture providing access to test database"""
    db = app.extensions.get('mongo_db')
    return db


@pytest.fixture
def sample_user(mongo_db):
    """Create and return a sample user in the test database"""
    user_doc = User.create_document(
        firebase_uid='firebase-test-uid-123',
        google_id='google-test-id-123',
        email='testuser@example.com',
        name='Test Presenter',
        picture='https://example.com/avatar.png',
        access_token='ya29.test-access-token',
        refresh_token='1//test-refresh-token',
        token_expiry=datetime.utcnow()
    )
    if mongo_db is not None:
        result = mongo_db.users.insert_one(user_doc)
        user_doc['_id'] = result.inserted_id
    else:
        user_doc['_id'] = ObjectId()
    return user_doc


@pytest.fixture
def auth_headers():
    """Valid Firebase authorization headers"""
    return {
        'Authorization': 'Bearer test-valid-firebase-jwt',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def mock_firebase():
    """Mock Firebase Admin SDK authentication verification"""
    mock_decoded = {
        'uid': 'fb-uid-999',
        'email': 'newuser@example.com',
        'name': 'New Presenter',
        'picture': 'https://example.com/avatar.png'
    }
    with patch('firebase_admin.auth.verify_id_token', return_value=mock_decoded), \
         patch('routes.auth.get_firebase_user_from_request', return_value=mock_decoded):
        yield mock_decoded


@pytest.fixture
def mock_gemini():
    """Mock Google Gemini Generative AI Service"""
    mock_svc = MagicMock()
    mock_svc.generate_realtime_feedback.return_value = {
        'wpm_feedback': 'Optimal pace',
        'eye_contact_feedback': 'Great engagement',
        'posture_feedback': 'Upright posture',
        'tip': 'Keep up the confident eye contact with your audience.'
    }
    mock_svc.generate_voice_tip.return_value = 'Slow down slightly and maintain eye contact.'
    mock_svc.generate_session_summary.return_value = {
        'overallScore': 88,
        'summary': 'Excellent presentation with articulate delivery and strong posture.',
        'strengths': [{'area': 'Natural gestures', 'detail': 'Engaging hand movements'}],
        'areasForImprovement': [{'area': 'Filler words', 'detail': 'Reduce filler words'}],
        'nextSessionGoals': ['Maintain steady 130-140 WPM pace'],
        'motivationalMessage': 'Keep up the amazing work!'
    }
    mock_svc.analyze_text_for_fillers.return_value = {
        'filler_count': 3,
        'fillers_detected': ['um', 'like', 'uh'],
        'filler_percentage': 2.1
    }

    with patch('services.gemini_service.gemini_service', mock_svc), \
         patch('routes.analyze.gemini_service', mock_svc):
        yield mock_svc


@pytest.fixture
def mock_google_auth():
    """Mock Google OAuth and Slides service methods"""
    mock_auth = MagicMock()
    mock_auth.get_authorization_url.return_value = (
        'https://accounts.google.com/o/oauth2/auth?client_id=test',
        'test-state-token'
    )
    mock_auth.exchange_code_for_tokens.return_value = {
        'access_token': 'mock-access-token-123',
        'refresh_token': 'mock-refresh-token-123',
        'token_expiry': datetime.utcnow()
    }
    mock_auth.get_user_info.return_value = {
        'id': 'google-test-id-123',
        'email': 'testuser@example.com',
        'name': 'Test Presenter',
        'picture': 'https://example.com/avatar.png'
    }
    mock_creds = MagicMock()
    mock_creds.valid = True
    mock_auth.get_valid_credentials_from_doc.return_value = mock_creds

    with patch('services.google_auth.google_auth_service', mock_auth), \
         patch('routes.presentations.google_auth_service', mock_auth):
        yield mock_auth


@pytest.fixture
def mock_cache():
    """Mock Redis cache service"""
    with patch('services.cache_service.cache_service') as mock_c:
        mock_c.get.return_value = None
        mock_c.set.return_value = True
        mock_c.delete.return_value = True
        mock_c.clear_user_cache.return_value = True
        yield mock_c
