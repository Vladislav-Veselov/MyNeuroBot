#!/usr/bin/env python3
"""
Manual test script for the pricing service.
Run this script to test the pricing service functionality.
"""

import sys
from pathlib import Path

# Add the current directory to the Python path
sys.path.append(str(Path(__file__).parent))

from pricing_service import pricing_service
import json

def test_pricing_service():
    """Test the pricing service functionality."""
    print("Testing Pricing Service...")
    print("=" * 50)
    
    # Test 1: Get Moscow time
    print("1. Testing Moscow time...")
    moscow_time = pricing_service.get_moscow_time()
    print(f"   Current Moscow time: {moscow_time}")
    print(f"   Timezone: {moscow_time.tzinfo}")
    print()
    
    # Test 2: Check if pricing should update
    print("2. Checking if pricing should update...")
    should_update = pricing_service.should_update_pricing()
    print(f"   Should update: {should_update}")
    print()
    
    # Test 3: Get pricing data
    print("3. Getting pricing data...")
    pricing_data = pricing_service.get_pricing_data()
    print(f"   Models available: {list(pricing_data.get('models', {}).keys())}")
    print(f"   Last updated: {pricing_data.get('last_updated', 'N/A')}")
    print(f"   Source: {pricing_data.get('source', 'N/A')}")
    print()
    
    # Test 4: Check exchange rates
    print("4. Checking exchange rates...")
    exchange_rates = pricing_data.get('exchange_rates', {})
    print(f"   USD to RUB: {exchange_rates.get('USD_to_RUB', 'N/A')}")
    print(f"   RUB to USD: {exchange_rates.get('RUB_to_USD', 'N/A')}")
    print(f"   Exchange rate source: {exchange_rates.get('source', 'N/A')}")
    print()
    
    # Test 4.5: Check markup coefficient
    print("4.5. Checking markup coefficient...")
    markup_coefficient = pricing_data.get('markup_coefficient', 'N/A')
    markup_notes = pricing_data.get('markup_notes', 'N/A')
    print(f"   Markup coefficient: {markup_coefficient}")
    print(f"   Markup notes: {markup_notes}")
    print()
    
    # Test 5: Test cost calculation
    print("5. Testing cost calculation...")
    from balance_manager import balance_manager
    
    # Test with some sample tokens
    input_tokens = 1000
    output_tokens = 500
    model = "gpt-4o-mini"
    
    cost_usd, cost_rub = balance_manager.calculate_token_cost(input_tokens, output_tokens, model)
    print(f"   Model: {model}")
    print(f"   Input tokens: {input_tokens}")
    print(f"   Output tokens: {output_tokens}")
    print(f"   Cost USD: ${cost_usd:.6f}")
    print(f"   Cost RUB: ₽{cost_rub:.2f}")
    print()
    
    # Test 5.5: Test cost calculation without markup (for comparison)
    print("5.5. Testing cost calculation without markup...")
    # Get base pricing data
    models = pricing_data.get('models', {})
    if model in models:
        model_pricing = models[model]
        usd_to_rub = exchange_rates.get('USD_to_RUB', 95.5)
        
        # Calculate base costs without markup
        input_cost_usd = (input_tokens / 1000) * model_pricing['input_price_per_1k_tokens']
        output_cost_usd = (output_tokens / 1000) * model_pricing['output_price_per_1k_tokens']
        base_cost_usd = input_cost_usd + output_cost_usd
        base_cost_rub = base_cost_usd * usd_to_rub
        
        print(f"   Base cost USD: ${base_cost_usd:.6f}")
        print(f"   Base cost RUB: ₽{base_cost_rub:.2f}")
        print(f"   Markup applied: {markup_coefficient}x")
        print(f"   Cost increase: {((cost_usd / base_cost_usd - 1) * 100):.1f}%")
    print()
    
    print("Pricing service test completed successfully!")
    print("=" * 50)

if __name__ == "__main__":
    test_pricing_service() 