import pytest
from unittest.mock import patch
from app.api.endpoints.aggregator import _entity_v3_active

def test_entity_v3_active_modes():
    with patch('app.api.endpoints.aggregator.settings') as mock_settings:
        mock_settings.entity_resolution_mode = 'shadow'
        mock_settings.entity_resolution_rollback_to_legacy = False
        assert _entity_v3_active(category='Shopping', exact_match=True) is True
    
    with patch('app.api.endpoints.aggregator.settings') as mock_settings:
        mock_settings.entity_resolution_mode = 'v3'
        mock_settings.entity_resolution_rollback_to_legacy = False
        assert _entity_v3_active(category='Shopping', exact_match=True) is True
        
    with patch('app.api.endpoints.aggregator.settings') as mock_settings:
        mock_settings.entity_resolution_mode = 'dual'
        mock_settings.entity_resolution_rollback_to_legacy = False
        assert _entity_v3_active(category='Shopping', exact_match=True) is True
        
    with patch('app.api.endpoints.aggregator.settings') as mock_settings:
        mock_settings.entity_resolution_mode = 'legacy'
        mock_settings.entity_resolution_rollback_to_legacy = False
        assert _entity_v3_active(category='Shopping', exact_match=True) is False

def test_rollback_overrides_modes():
    with patch('app.api.endpoints.aggregator.settings') as mock_settings:
        mock_settings.entity_resolution_mode = 'v3'
        mock_settings.entity_resolution_rollback_to_legacy = True
        assert _entity_v3_active(category='Shopping', exact_match=True) is False
