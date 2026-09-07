"""
Unit tests for Gemini AI coaching service
"""
from unittest.mock import MagicMock, patch
from services.gemini_service import GeminiService


@patch('google.generativeai.configure')
@patch('google.generativeai.GenerativeModel')
def test_generate_realtime_feedback(mock_model_cls, mock_configure):
    """Test generating real-time coaching feedback with Gemini"""
    mock_model = MagicMock()
    mock_model_cls.return_value = mock_model
    
    mock_response = MagicMock()
    mock_response.text = '```json\n{"tip": "Good posture", "score": 85}\n```'
    mock_model.generate_content.return_value = mock_response

    service = GeminiService()
    metrics = {
        'headPose': {'yaw': 15, 'pitch': 0, 'roll': 0},
        'engagement': {'score': 75, 'level': 'good'},
        'eyeContactPercent': 78
    }
    result = service.generate_realtime_feedback(metrics, transcript="Hello everyone")
    assert isinstance(result, dict)
    assert result.get('tip') == 'Good posture'


@patch('google.generativeai.configure')
@patch('google.generativeai.GenerativeModel')
def test_fallback_on_api_error(mock_model_cls, mock_configure):
    """Test fallback feedback generation when Gemini raises an exception"""
    mock_model = MagicMock()
    mock_model_cls.return_value = mock_model
    mock_model.generate_content.side_effect = Exception("API Quota exceeded")

    service = GeminiService()
    result = service.generate_realtime_feedback(
        metrics={'headPose': {'yaw': 0, 'pitch': 0, 'roll': 0}},
        transcript="Hello"
    )
    assert isinstance(result, dict)
    assert 'overallScore' in result or 'naturalInsights' in result or 'positives' in result


@patch('google.generativeai.configure')
@patch('google.generativeai.GenerativeModel')
def test_analyze_text_for_fillers(mock_model_cls, mock_configure):
    """Test text filler words analysis fallback and parsing"""
    mock_model = MagicMock()
    mock_model_cls.return_value = mock_model
    mock_model.generate_content.side_effect = Exception("Model offline")

    service = GeminiService()
    text = "Um, so basically we are like presenting today, uh, our project."
    result = service.analyze_text_for_fillers(text)
    assert isinstance(result, dict)
    assert 'fillerWords' in result
    assert result['totalFillerCount'] >= 1
