"""
Unit tests for Google OAuth Service
"""
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from services.google_auth import GoogleAuthService


def test_get_authorization_url(app):
    """Test generating Google OAuth authorization URL"""
    with app.test_request_context():
        with patch('services.google_auth.Flow.from_client_config') as mock_flow_cls:
            mock_flow = MagicMock()
            mock_flow_cls.return_value = mock_flow
            mock_flow.authorization_url.return_value = (
                'https://accounts.google.com/o/oauth2/auth?client_id=123',
                'state-xyz'
            )

            service = GoogleAuthService()
            url, state = service.get_authorization_url(state='state-xyz')
            assert url.startswith('https://accounts.google.com')
            assert state == 'state-xyz'


def test_exchange_code_for_tokens(app):
    """Test exchanging auth code for access/refresh tokens"""
    with app.test_request_context():
        with patch('services.google_auth.Flow.from_client_config') as mock_flow_cls:
            mock_flow = MagicMock()
            mock_flow_cls.return_value = mock_flow
            
            mock_creds = MagicMock()
            mock_creds.token = 'access-token-123'
            mock_creds.refresh_token = 'refresh-token-456'
            mock_creds.expiry = datetime.utcnow()
            mock_flow.credentials = mock_creds

            service = GoogleAuthService()
            tokens = service.exchange_code_for_tokens('auth-code-789')
            assert tokens['access_token'] == 'access-token-123'
            assert tokens['refresh_token'] == 'refresh-token-456'


def test_get_valid_credentials_unexpired(app):
    """Test retrieving valid unexpired credentials from user doc"""
    with app.test_request_context():
        service = GoogleAuthService()
        user_doc = {
            '_id': 'user-1',
            'access_token': 'unexpired-token',
            'refresh_token': 'refresh-token',
            'token_expiry': datetime.utcnow() + timedelta(hours=1)
        }
        creds = service.get_valid_credentials_from_doc(user_doc, db=MagicMock())
        assert creds.token == 'unexpired-token'
