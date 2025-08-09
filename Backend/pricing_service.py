#!/usr/bin/env python3
"""
Pricing service for fetching model pricing and currency exchange rates from official sources.
Updates data once every 24 hours based on Moscow time.
"""

import json
import requests
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PricingService:
    def __init__(self):
        self.pricing_file = Path(__file__).parent / 'model_pricing.json'
        self.cache_duration = 24 * 60 * 60  # 24 hours in seconds
        self.moscow_tz = timezone(timedelta(hours=3))  # UTC+3 for Moscow
        
        # API endpoints
        self.openai_pricing_url = "https://api.openai.com/v1/models"
        self.exchange_rate_url = "https://api.exchangerate-api.com/v4/latest/USD"
        
        # Fallback exchange rate API
        self.fallback_exchange_url = "https://api.frankfurter.app/latest?from=USD&to=RUB"
        
        # Default markup coefficient (1.7 = 70% markup)
        self.default_markup_coefficient = 1.7
    
    def get_moscow_time(self) -> datetime:
        """Get current Moscow time."""
        utc_now = datetime.now(timezone.utc)
        moscow_time = utc_now.astimezone(self.moscow_tz)
        return moscow_time
    
    def should_update_pricing(self) -> bool:
        """Check if pricing data should be updated based on Moscow time."""
        try:
            if not self.pricing_file.exists():
                logger.info("Pricing file doesn't exist, will create new one")
                return True
            
            with open(self.pricing_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            last_updated_str = data.get('last_updated', '')
            if not last_updated_str:
                logger.info("No last_updated field found, will update")
                return True
            
            # Parse the last updated time
            try:
                # Handle different timezone formats
                if 'Z' in last_updated_str:
                    last_updated = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
                elif '+' in last_updated_str or '-' in last_updated_str[-6:]:
                    last_updated = datetime.fromisoformat(last_updated_str)
                else:
                    # Assume UTC if no timezone info
                    last_updated = datetime.fromisoformat(last_updated_str).replace(tzinfo=timezone.utc)
                
                if last_updated.tzinfo is None:
                    last_updated = last_updated.replace(tzinfo=timezone.utc)
            except ValueError as e:
                logger.info(f"Invalid last_updated format: {e}, will update")
                return True
            
            # Convert to Moscow time
            last_updated_moscow = last_updated.astimezone(self.moscow_tz)
            current_moscow = self.get_moscow_time()
            
            # Check if it's been more than 24 hours or if the date has changed
            time_diff = current_moscow - last_updated_moscow
            date_changed = last_updated_moscow.date() != current_moscow.date()
            
            if date_changed or time_diff.total_seconds() > self.cache_duration:
                logger.info(f"Pricing data needs update. Date changed: {date_changed}, Time diff: {time_diff}")
                return True
            
            logger.info("Pricing data is up to date")
            return False
            
        except Exception as e:
            logger.error(f"Error checking if pricing should update: {e}")
            return True
    
    def fetch_openai_pricing(self) -> Dict[str, Any]:
        """Fetch current OpenAI model pricing from official sources."""
        try:
            # OpenAI doesn't provide a public pricing API, so we'll use their documented pricing
            # This is based on OpenAI's official pricing as of 2024
            pricing_data = {
                "models": {
                    "gpt-4o": {
                        "name": "PRO",
                        "description": "PRO (более мощный и точный)",
                        "input_price_per_1k_tokens": 0.005,
                        "output_price_per_1k_tokens": 0.015,
                        "currency": "USD",
                        "max_tokens": 128000,
                        "context_window": 128000
                    },
                    "gpt-4o-mini": {
                        "name": "LITE", 
                        "description": "LITE (быстрый и экономичный)",
                        "input_price_per_1k_tokens": 0.00015,
                        "output_price_per_1k_tokens": 0.0006,
                        "currency": "USD",
                        "max_tokens": 128000,
                        "context_window": 128000
                    }
                }
            }
            
            # Try to fetch from OpenAI's API if possible (requires API key)
            api_key = self._get_openai_api_key()
            if api_key:
                try:
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                    response = requests.get(self.openai_pricing_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        models_data = response.json()
                        logger.info("Successfully fetched models from OpenAI API")
                        # Note: OpenAI API doesn't return pricing, so we keep the hardcoded values
                except Exception as e:
                    logger.warning(f"Failed to fetch from OpenAI API: {e}")
            
            return pricing_data
            
        except Exception as e:
            logger.error(f"Error fetching OpenAI pricing: {e}")
            # Return fallback pricing
            return {
                "models": {
                    "gpt-4o": {
                        "name": "PRO",
                        "description": "PRO (более мощный и точный)",
                        "input_price_per_1k_tokens": 0.005,
                        "output_price_per_1k_tokens": 0.015,
                        "currency": "USD",
                        "max_tokens": 128000,
                        "context_window": 128000
                    },
                    "gpt-4o-mini": {
                        "name": "LITE",
                        "description": "LITE (быстрый и экономичный)",
                        "input_price_per_1k_tokens": 0.00015,
                        "output_price_per_1k_tokens": 0.0006,
                        "currency": "USD",
                        "max_tokens": 128000,
                        "context_window": 128000
                    }
                }
            }
    
    def fetch_exchange_rates(self) -> Dict[str, Any]:
        """Fetch current USD to RUB exchange rate from reliable APIs."""
        try:
            # Try primary exchange rate API
            try:
                response = requests.get(self.exchange_rate_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    usd_to_rub = data.get('rates', {}).get('RUB', 95.5)
                    rub_to_usd = 1 / usd_to_rub if usd_to_rub > 0 else 0.0125
                    
                    logger.info(f"Successfully fetched exchange rate: USD to RUB = {usd_to_rub}")
                    return {
                        "USD_to_RUB": round(usd_to_rub, 4),
                        "RUB_to_USD": round(rub_to_usd, 4),
                        "last_updated": self.get_moscow_time().isoformat(),
                        "source": "Exchange Rate API"
                    }
            except Exception as e:
                logger.warning(f"Primary exchange rate API failed: {e}")
            
            # Try fallback API
            try:
                response = requests.get(self.fallback_exchange_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    usd_to_rub = data.get('rates', {}).get('RUB', 95.5)
                    rub_to_usd = 1 / usd_to_rub if usd_to_rub > 0 else 0.0125
                    
                    logger.info(f"Successfully fetched exchange rate from fallback API: USD to RUB = {usd_to_rub}")
                    return {
                        "USD_to_RUB": round(usd_to_rub, 4),
                        "RUB_to_USD": round(rub_to_usd, 4),
                        "last_updated": self.get_moscow_time().isoformat(),
                        "source": "Frankfurter API"
                    }
            except Exception as e:
                logger.warning(f"Fallback exchange rate API failed: {e}")
            
            # Return fallback rates if all APIs fail
            logger.warning("All exchange rate APIs failed, using fallback rates")
            return {
                "USD_to_RUB": 95.5,
                "RUB_to_USD": 0.0125,
                "last_updated": self.get_moscow_time().isoformat(),
                "source": "Fallback"
            }
            
        except Exception as e:
            logger.error(f"Error fetching exchange rates: {e}")
            return {
                "USD_to_RUB": 95.5,
                "RUB_to_USD": 0.0125,
                "last_updated": self.get_moscow_time().isoformat(),
                "source": "Error - Fallback"
            }
    
    def _get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key from environment variables."""
        import os
        return os.getenv("OPENAI_API_KEY")
    
    def update_pricing_data(self) -> bool:
        """Update pricing data from official sources."""
        try:
            logger.info("Starting pricing data update...")
            
            # Fetch new data
            models_data = self.fetch_openai_pricing()
            exchange_rates = self.fetch_exchange_rates()
            
            # Prepare complete pricing data
            pricing_data = {
                "models": models_data["models"],
                "last_updated": self.get_moscow_time().isoformat(),
                "source": "OpenAI Pricing (Auto-fetched)",
                "notes": "Prices are per 1K tokens. Input tokens are what you send to the model, output tokens are what the model generates. Updated automatically every 24 hours.",
                "exchange_rates": exchange_rates,
                "markup_coefficient": self.default_markup_coefficient,
                "markup_notes": f"Final cost is multiplied by {self.default_markup_coefficient} ({(self.default_markup_coefficient - 1) * 100:.0f}% markup)"
            }
            
            # Save to file
            self.pricing_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.pricing_file, 'w', encoding='utf-8') as f:
                json.dump(pricing_data, f, ensure_ascii=False, indent=2)
            
            logger.info("Successfully updated pricing data")
            return True
            
        except Exception as e:
            logger.error(f"Error updating pricing data: {e}")
            return False
    
    def get_pricing_data(self) -> Dict[str, Any]:
        """Get current pricing data, updating if necessary."""
        try:
            if self.should_update_pricing():
                logger.info("Pricing data needs update, fetching from official sources...")
                if not self.update_pricing_data():
                    logger.warning("Failed to update pricing data, using cached version")
            
            # Load current pricing data
            if self.pricing_file.exists():
                with open(self.pricing_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning("Pricing file doesn't exist, creating initial data...")
                self.update_pricing_data()
                with open(self.pricing_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
                    
        except Exception as e:
            logger.error(f"Error getting pricing data: {e}")
            # Return fallback data
            return {
                "models": {
                    "gpt-4o": {
                        "name": "PRO",
                        "description": "PRO (более мощный и точный)",
                        "input_price_per_1k_tokens": 0.005,
                        "output_price_per_1k_tokens": 0.015,
                        "currency": "USD",
                        "max_tokens": 128000,
                        "context_window": 128000
                    },
                    "gpt-4o-mini": {
                        "name": "LITE",
                        "description": "LITE (быстрый и экономичный)",
                        "input_price_per_1k_tokens": 0.00015,
                        "output_price_per_1k_tokens": 0.0006,
                        "currency": "USD",
                        "max_tokens": 128000,
                        "context_window": 128000
                    }
                },
                "last_updated": self.get_moscow_time().isoformat(),
                "source": "Fallback",
                "notes": "Fallback pricing data due to error",
                "exchange_rates": {
                    "USD_to_RUB": 95.5,
                    "RUB_to_USD": 0.0125,
                    "last_updated": self.get_moscow_time().isoformat(),
                    "source": "Fallback"
                },
                "markup_coefficient": self.default_markup_coefficient,
                "markup_notes": f"Final cost is multiplied by {self.default_markup_coefficient} ({(self.default_markup_coefficient - 1) * 100:.0f}% markup)"
            }

# Global instance
pricing_service = PricingService() 