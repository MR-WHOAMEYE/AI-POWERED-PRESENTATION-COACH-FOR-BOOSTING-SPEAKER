"""
Unit and integration tests for AI Analyze Routes
"""
from unittest.mock import patch


def test_analyze_realtime_requires_auth(client):
    """POST /analyze/realtime without auth returns 401"""
    response = client.post('/analyze/realtime', json={})
    assert response.status_code == 401


def test_analyze_realtime_feedback(client, sample_user, mock_gemini):
    """POST /analyze/realtime returns AI coaching feedback"""
    with client.session_transaction() as sess:
        sess['user_id'] = str(sample_user['_id'])

    payload = {
        'metrics': {
            'wpm': 135,
            'eyeContact': 80,
            'posture': 90
        },
        'transcript': 'Hello everyone, welcome to the presentation.'
    }
    response = client.post('/analyze/realtime', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert 'feedback' in data
    assert 'tip' in data['feedback']


def test_analyze_session_summary(client, sample_user, mock_gemini):
    """POST /analyze/session-summary returns post-session scorecard"""
    with client.session_transaction() as sess:
        sess['user_id'] = str(sample_user['_id'])

    mock_gemini.generate_session_summary.return_value = {
        'overallScore': 85,
        'grade': 'B+',
        'headline': 'Great delivery!',
        'naturalInsights': ['Audience connection was solid'],
        'strengths': [{'area': 'Eye Contact', 'detail': 'Maintained direct focus'}],
        'areasForImprovement': [{'area': 'Pacing', 'detail': 'Slow down on transitions'}],
        'nextSessionGoals': ['Use pauses effectively'],
        'motivationalMessage': 'Excellent progress!'
    }

    payload = {
        'transcript': 'Today we are exploring our product strategy.',
        'metrics': {'postureScore': 85, 'eyeContactPercent': 90, 'fillerCount': 2},
        'durationSeconds': 300
    }
    response = client.post('/analyze/session-summary', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data['overallScore'] == 85
    assert data['grade'] == 'B+'
    assert len(data['positives']) > 0
