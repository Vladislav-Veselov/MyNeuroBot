#!/usr/bin/env python3
"""
Test file for the pricing service.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import tempfile
import shutil

from pricing_service import PricingService

class TestPricingService(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.pricing_service = PricingService()
        self.pricing_service.pricing_file = Path(self.test_dir) / 'model_pricing.json'
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def test_get_moscow_time(self):
        """Test that Moscow time is correctly calculated."""
        moscow_time = self.pricing_service.get_moscow_time()
        self.assertIsInstance(moscow_time, datetime)
        self.assertEqual(moscow_time.tzinfo, self.pricing_service.moscow_tz)
    
    def test_should_update_pricing_new_file(self):
        """Test that pricing should update when file doesn't exist."""
        self.assertFalse(self.pricing_service.pricing_file.exists())
        self.assertTrue(self.pricing_service.should_update_pricing())
    
    def test_should_update_pricing_old_data(self):
        """Test that pricing should update when data is old."""
        # Create old pricing data
        old_time = datetime.now(timezone.utc) - timedelta(days=2)
        old_data = {
            "last_updated": old_time.isoformat(),
            "models": {},
            "exchange_rates": {}
        }
        
        with open(self.pricing_service.pricing_file, 'w') as f:
            json.dump(old_data, f)
        
        self.assertTrue(self.pricing_service.should_update_pricing())
    
    def test_should_update_pricing_recent_data(self):
        """Test that pricing should not update when data is recent."""
        # Create recent pricing data
        recent_time = datetime.now(timezone.utc) - timedelta(hours=12)
        recent_data = {
            "last_updated": recent_time.isoformat(),
            "models": {},
            "exchange_rates": {}
        }
        
        with open(self.pricing_service.pricing_file, 'w') as f:
            json.dump(recent_data, f)
        
        self.assertFalse(self.pricing_service.should_update_pricing())
    
    @patch('requests.get')
    def test_fetch_exchange_rates_success(self, mock_get):
        """Test successful exchange rate fetching."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rates": {
                "RUB": 95.5
            }
        }
        mock_get.return_value = mock_response
        
        rates = self.pricing_service.fetch_exchange_rates()
        
        self.assertIn("USD_to_RUB", rates)
        self.assertIn("RUB_to_USD", rates)
        self.assertEqual(rates["USD_to_RUB"], 95.5)
        self.assertEqual(rates["RUB_to_USD"], 1/95.5)
    
    @patch('requests.get')
    def test_fetch_exchange_rates_fallback(self, mock_get):
        """Test exchange rate fetching with fallback."""
        # Mock failed responses
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        rates = self.pricing_service.fetch_exchange_rates()
        
        self.assertIn("USD_to_RUB", rates)
        self.assertIn("RUB_to_USD", rates)
        self.assertEqual(rates["USD_to_RUB"], 95.5)  # Fallback value
        self.assertEqual(rates["RUB_to_USD"], 0.0125)  # Fallback value
    
    def test_fetch_openai_pricing(self):
        """Test OpenAI pricing fetching."""
        pricing = self.pricing_service.fetch_openai_pricing()
        
        self.assertIn("models", pricing)
        self.assertIn("gpt-4o", pricing["models"])
        self.assertIn("gpt-4o-mini", pricing["models"])
        
        # Check that pricing data has required fields
        for model in pricing["models"].values():
            self.assertIn("input_price_per_1k_tokens", model)
            self.assertIn("output_price_per_1k_tokens", model)
            self.assertIn("currency", model)
    
    @patch.object(PricingService, 'fetch_openai_pricing')
    @patch.object(PricingService, 'fetch_exchange_rates')
    def test_update_pricing_data(self, mock_exchange_rates, mock_openai_pricing):
        """Test pricing data update."""
        # Mock the fetch methods
        mock_openai_pricing.return_value = {
            "models": {
                "gpt-4o": {
                    "name": "PRO",
                    "input_price_per_1k_tokens": 0.005,
                    "output_price_per_1k_tokens": 0.015,
                    "currency": "USD"
                }
            }
        }
        
        mock_exchange_rates.return_value = {
            "USD_to_RUB": 95.5,
            "RUB_to_USD": 0.0125,
            "last_updated": "2024-01-01T00:00:00+03:00",
            "source": "Test"
        }
        
        # Test update
        success = self.pricing_service.update_pricing_data()
        self.assertTrue(success)
        
        # Check that file was created
        self.assertTrue(self.pricing_service.pricing_file.exists())
        
        # Check file contents
        with open(self.pricing_service.pricing_file, 'r') as f:
            data = json.load(f)
        
        self.assertIn("models", data)
        self.assertIn("exchange_rates", data)
        self.assertIn("last_updated", data)
        self.assertIn("markup_coefficient", data)
        self.assertIn("markup_notes", data)
        
        # Check markup coefficient value
        self.assertEqual(data["markup_coefficient"], 1.7)
        self.assertIn("1.7", data["markup_notes"])
        self.assertIn("70%", data["markup_notes"])
    
    def test_get_pricing_data_fallback(self):
        """Test getting pricing data with fallback."""
        # Remove the pricing file to trigger fallback
        if self.pricing_service.pricing_file.exists():
            self.pricing_service.pricing_file.unlink()
        
        data = self.pricing_service.get_pricing_data()
        
        self.assertIn("models", data)
        self.assertIn("exchange_rates", data)
        self.assertIn("last_updated", data)
        self.assertIn("markup_coefficient", data)
        self.assertIn("markup_notes", data)
        
        # Check markup coefficient value
        self.assertEqual(data["markup_coefficient"], 1.7)

if __name__ == '__main__':
    unittest.main() 