"""
Unit tests for Cache Service
"""
from unittest.mock import MagicMock
from services.cache_service import CacheService


def test_cache_miss_when_uninitialized(app):
    """Test get_presentation returns None when cache client is not configured"""
    with app.test_request_context():
        service = CacheService()
        service._initialized = True
        service._lang_cache = None
        result = service.get_presentation('pres-123', 'user-456')
        assert result is None


def test_set_and_get_presentation(app):
    """Test setting and getting presentation from mock cache"""
    with app.test_request_context():
        service = CacheService()
        service._initialized = True
        mock_client = MagicMock()

        # Mock hit
        mock_hit = MagicMock()
        mock_hit.prompt = "presentation:user-456:pres-123"
        mock_hit.response = '{"title": "Deck A"}'
        mock_response = MagicMock()
        mock_response.hits = [mock_hit]
        mock_client.search.return_value = mock_response

        service._lang_cache = mock_client
        service.set_presentation('pres-123', 'user-456', {'title': 'Deck A'})
        mock_client.set.assert_called_once()

        res = service.get_presentation('pres-123', 'user-456')
        assert res == {'title': 'Deck A'}


def test_invalidate_presentation(app):
    """Test invalidation overwrites entry in cache with empty dict"""
    with app.test_request_context():
        service = CacheService()
        service._initialized = True
        mock_client = MagicMock()

        service._lang_cache = mock_client
        res = service.invalidate_presentation('pres-123', 'user-456')
        assert res is True
        mock_client.set.assert_called_once()
