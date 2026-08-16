import pytest
from unittest.mock import patch
from fastapi import HTTPException
from server.modules import pii_detector


@pytest.mark.asyncio
async def test_clean_medical_query_passes():
    """A normal medical query should not be redacted."""
    with patch.object(pii_detector.settings, 'pii_detection_enabled', True):
        result = await pii_detector.detect_and_redact("What are the side effects of ibuprofen?")
        assert result == "What are the side effects of ibuprofen?"


@pytest.mark.asyncio
async def test_patient_id_is_redacted():
    """Patient ID should be redacted when detected."""
    with patch.object(pii_detector.settings, 'pii_detection_enabled', True):
        result = await pii_detector.detect_and_redact("Patient ID: 123-45-6789")
        assert "[REDACTED]" in result
        assert "123-45-6789" not in result


@pytest.mark.asyncio
async def test_mrn_is_redacted():
    """MRN should be redacted when detected."""
    with patch.object(pii_detector.settings, 'pii_detection_enabled', True):
        result = await pii_detector.detect_and_redact("MRN: ABC-1234")
        assert "[REDACTED]" in result
        assert "ABC-1234" not in result


@pytest.mark.asyncio
async def test_disabled_mode_skips_redaction():
    """When PII detection is disabled, original text should be returned."""
    with patch.object(pii_detector.settings, 'pii_detection_enabled', False):
        result = await pii_detector.detect_and_redact("Patient ID: 123-45-6789")
        assert result == "Patient ID: 123-45-6789"


@pytest.mark.asyncio
async def test_strict_mode_raises_422():
    """When strict mode is enabled and PII is found, HTTPException(422) should be raised."""
    with patch.object(pii_detector.settings, 'pii_detection_enabled', True):
        with patch.object(pii_detector.settings, 'pii_strict_mode', True):
            with pytest.raises(HTTPException) as exc_info:
                await pii_detector.detect_and_redact("Patient ID: 123-45-6789")
            assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_mask_mode_produces_masked_output():
    """When redaction mode is mask, output should be masked."""
    with patch.object(pii_detector.settings, 'pii_detection_enabled', True):
        with patch.object(pii_detector.settings, 'pii_redaction_mode', 'mask'):
            result = await pii_detector.detect_and_redact("Patient ID: 123-45-6789")
            # mask mode should alter the matched span, not remove it entirely
            assert result != "Patient ID: 123-45-6789"
            assert "***" in result


@pytest.mark.asyncio
async def test_non_pii_text_passes_through():
    """Non-PII text should pass through unchanged."""
    with patch.object(pii_detector.settings, 'pii_detection_enabled', True):
        result = await pii_detector.detect_and_redact("What are the side effects of ibuprofen?")
        assert result == "What are the side effects of ibuprofen?"
