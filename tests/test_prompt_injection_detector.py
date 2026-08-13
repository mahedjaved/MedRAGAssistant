from unittest.mock import patch, MagicMock
from server.modules import prompt_injection_detector

def test_clean_query_passes():
    mock_guard = MagicMock()
    with patch.object(prompt_injection_detector, 'injection_guard', mock_guard):
        with patch.object(prompt_injection_detector.settings, 'prompt_injection_detection_enabled', True):
            # Act
            prompt_injection_detector.validate_query("What are the side effects of ibuprofen?")

            # Assert
            mock_guard.validate.assert_called_once_with("What are the side effects of ibuprofen?")