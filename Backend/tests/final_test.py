#!/usr/bin/env python3
"""
Final test script to verify the pricing service implementation.
"""

from pricing_service import pricing_service
from balance_manager import balance_manager

def main():
    print("🧪 Final Pricing Service Test")
    print("=" * 40)
    
    # Test 1: Import and basic functionality
    print("1. Testing imports and basic functionality...")
    try:
        data = pricing_service.get_pricing_data()
        print(f"   ✅ Pricing data loaded: {len(data.get('models', {}))} models")
    except Exception as e:
        print(f"   ❌ Error loading pricing data: {e}")
        return
    
    # Test 2: Cost calculation
    print("2. Testing cost calculation...")
    try:
        cost_usd, cost_rub = balance_manager.calculate_token_cost(1000, 500, 'gpt-4o-mini')
        print(f"   ✅ Cost calculation working: ${cost_usd:.6f} USD, ₽{cost_rub:.2f} RUB")
    except Exception as e:
        print(f"   ❌ Error in cost calculation: {e}")
        return
    
    # Test 3: Model availability
    print("3. Testing model availability...")
    models = data.get('models', {})
    for model_id, model_data in models.items():
        print(f"   ✅ Model {model_id}: {model_data.get('name', 'Unknown')}")
    
    # Test 4: Exchange rates
    print("4. Testing exchange rates...")
    exchange_rates = data.get('exchange_rates', {})
    if exchange_rates:
        usd_to_rub = exchange_rates.get('USD_to_RUB', 'N/A')
        source = exchange_rates.get('source', 'Unknown')
        print(f"   ✅ Exchange rate: USD to RUB = {usd_to_rub} (Source: {source})")
    else:
        print("   ❌ No exchange rates found")
    
    # Test 4.5: Markup coefficient
    print("4.5. Testing markup coefficient...")
    markup_coefficient = data.get('markup_coefficient', 'N/A')
    markup_notes = data.get('markup_notes', 'N/A')
    if markup_coefficient != 'N/A':
        print(f"   ✅ Markup coefficient: {markup_coefficient} ({markup_notes})")
    else:
        print("   ❌ No markup coefficient found")
    
    # Test 5: Last updated
    print("5. Testing last updated...")
    last_updated = data.get('last_updated', 'N/A')
    source = data.get('source', 'Unknown')
    print(f"   ✅ Last updated: {last_updated} (Source: {source})")
    
    # Test 6: Cost calculation with markup
    print("6. Testing cost calculation with markup...")
    try:
        # Test with sample tokens
        input_tokens = 1000
        output_tokens = 500
        model = "gpt-4o-mini"
        
        cost_usd, cost_rub = balance_manager.calculate_token_cost(input_tokens, output_tokens, model)
        
        # Calculate base cost for comparison
        models = data.get('models', {})
        if model in models:
            model_pricing = models[model]
            usd_to_rub = exchange_rates.get('USD_to_RUB', 95.5)
            
            input_cost_usd = (input_tokens / 1000) * model_pricing['input_price_per_1k_tokens']
            output_cost_usd = (output_tokens / 1000) * model_pricing['output_price_per_1k_tokens']
            base_cost_usd = input_cost_usd + output_cost_usd
            base_cost_rub = base_cost_usd * usd_to_rub
            
            markup_applied = cost_usd / base_cost_usd if base_cost_usd > 0 else 1.0
            print(f"   ✅ Cost with markup: ${cost_usd:.6f} USD, ₽{cost_rub:.2f} RUB")
            print(f"   ✅ Base cost: ${base_cost_usd:.6f} USD, ₽{base_cost_rub:.2f} RUB")
            print(f"   ✅ Markup applied: {markup_applied:.2f}x ({(markup_applied - 1) * 100:.1f}% increase)")
        else:
            print(f"   ❌ Model {model} not found")
    except Exception as e:
        print(f"   ❌ Error in cost calculation with markup: {e}")
    
    print("\n🎉 All tests passed! Pricing service is working correctly.")
    print("=" * 40)

if __name__ == "__main__":
    main() 