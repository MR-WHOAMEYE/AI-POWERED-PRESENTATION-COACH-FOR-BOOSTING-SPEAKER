"""
Unit and integration tests for Google Presentations Routes
"""
from unittest.mock import patch, MagicMock


def test_list_presentations_requires_auth(client):
    """GET /presentations/ without active session returns 401"""
    response = client.get('/presentations/')
    assert response.status_code == 401
    assert 'error' in response.get_json()


def test_list_presentations_with_auth(client, sample_user, mock_google_auth):
    """GET /presentations/ with authenticated session returns slides list"""
    with client.session_transaction() as sess:
        sess['user_id'] = str(sample_user['_id'])

    with patch('routes.presentations.get_drive_service') as mock_drive:
        mock_drive.return_value.list_presentations.return_value = [
            {'id': 'pres-1', 'title': 'Demo Slides', 'thumbnail': 'https://example.com/thumb.png'}
        ]
        response = client.get('/presentations/')
        assert response.status_code == 200
        data = response.get_json()
        assert 'presentations' in data
        assert len(data['presentations']) == 1
        assert data['presentations'][0]['id'] == 'pres-1'


def test_get_presentation_with_cache(client, sample_user, mock_google_auth):
    """GET /presentations/<id> returns cached presentation when available"""
    with client.session_transaction() as sess:
        sess['user_id'] = str(sample_user['_id'])

    with patch('routes.presentations.cache_service') as mock_cache:
        mock_cache.get_presentation.return_value = {
            'id': 'pres-cached',
            'title': 'Cached Deck',
            'slides': []
        }
        response = client.get('/presentations/pres-cached')
        assert response.status_code == 200
        data = response.get_json()
        assert data['cached'] is True
        assert data['title'] == 'Cached Deck'


def test_get_presentation_fresh(client, sample_user, mock_google_auth):
    """GET /presentations/<id> fetches fresh from Google Slides when cache misses"""
    with client.session_transaction() as sess:
        sess['user_id'] = str(sample_user['_id'])

    with patch('routes.presentations.cache_service') as mock_cache, \
         patch('routes.presentations.get_slides_service') as mock_slides:
        mock_cache.get_presentation.return_value = None
        mock_slides.return_value.get_presentation.return_value = {
            'id': 'pres-fresh',
            'title': 'Fresh Presentation Deck',
            'slides': [{'id': 'slide-1'}]
        }
        response = client.get('/presentations/pres-fresh')
        assert response.status_code == 200
        data = response.get_json()
        assert data['cached'] is False
        assert data['title'] == 'Fresh Presentation Deck'


def test_write_feedback(client, sample_user, mock_google_auth):
    """POST /presentations/<id>/feedback updates speaker notes"""
    with client.session_transaction() as sess:
        sess['user_id'] = str(sample_user['_id'])

    with patch('routes.presentations.get_slides_service') as mock_slides, \
         patch('routes.presentations.cache_service') as mock_cache:
        mock_slides.return_value.update_speaker_notes.return_value = True
        payload = {
            'slideId': 'slide-123',
            'feedback': 'Pace was great on this slide, keep eye contact steady.'
        }
        response = client.post('/presentations/pres-123/feedback', json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True


def test_clear_cache(client, sample_user, mock_google_auth):
    """POST /presentations/cache/clear invalidates all user presentation cache"""
    with client.session_transaction() as sess:
        sess['user_id'] = str(sample_user['_id'])

    with patch('routes.presentations.cache_service') as mock_cache:
        response = client.post('/presentations/cache/clear')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        mock_cache.clear_user_cache.assert_called_once_with(str(sample_user['_id']))
