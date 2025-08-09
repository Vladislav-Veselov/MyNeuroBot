# Pricing Service Documentation

## Overview

The pricing service automatically fetches model pricing and currency exchange rates from official sources once every 24 hours based on Moscow time. This ensures that the application always uses up-to-date pricing information without manual intervention.

## Features

- **Automatic Updates**: Fetches pricing data every 24 hours or when the date changes in Moscow time
- **Multiple Data Sources**: Uses official APIs with fallback options
- **Timezone Awareness**: Based on Moscow time (UTC+3)
- **Error Handling**: Graceful fallback to cached data if APIs are unavailable
- **Logging**: Comprehensive logging for debugging and monitoring
- **Markup Coefficient**: Configurable markup applied to final costs (default: 1.7x = 70% markup)

## Components

### PricingService Class

Located in `Backend/pricing_service.py`

#### Key Methods

- `get_moscow_time()`: Returns current Moscow time
- `should_update_pricing()`: Checks if pricing data needs updating
- `fetch_openai_pricing()`: Fetches OpenAI model pricing
- `fetch_exchange_rates()`: Fetches USD to RUB exchange rates
- `update_pricing_data()`: Updates pricing data from all sources
- `get_pricing_data()`: Gets current pricing data (updates if necessary)

#### Configuration

```python
class PricingService:
    def __init__(self):
        self.pricing_file = Path(__file__).parent / 'model_pricing.json'
        self.cache_duration = 24 * 60 * 60  # 24 hours in seconds
        self.moscow_tz = timezone(timedelta(hours=3))  # UTC+3 for Moscow
```

## Data Sources

### Model Pricing

- **Primary**: OpenAI API (if API key available)
- **Fallback**: Hardcoded pricing based on official OpenAI documentation
- **Update Frequency**: Every 24 hours or when date changes

### Exchange Rates

- **Primary**: Exchange Rate API (https://api.exchangerate-api.com/v4/latest/USD)
- **Fallback**: Frankfurter API (https://api.frankfurter.app/latest?from=USD&to=RUB)
- **Final Fallback**: Hardcoded rates (USD to RUB: 95.5)

### Markup Coefficient

- **Default Value**: 1.7 (70% markup)
- **Purpose**: Applied to final costs to cover operational expenses and profit margin
- **Configuration**: Can be modified in the `PricingService` class
- **Application**: Multiplied to the base cost after all other calculations

## Usage

### Basic Usage

```python
from pricing_service import pricing_service

# Get current pricing data (updates automatically if needed)
pricing_data = pricing_service.get_pricing_data()

# Access model pricing
models = pricing_data['models']
gpt4o_pricing = models['gpt-4o']

# Access exchange rates
exchange_rates = pricing_data['exchange_rates']
usd_to_rub = exchange_rates['USD_to_RUB']
```

### Integration with Balance Manager

The balance manager automatically uses the pricing service:

```python
from balance_manager import balance_manager

# Calculate token costs using current pricing
cost_usd, cost_rub = balance_manager.calculate_token_cost(
    input_tokens=1000, 
    output_tokens=500, 
    model="gpt-4o-mini"
)
```

## File Structure

```
Backend/
├── pricing_service.py          # Main pricing service
├── model_pricing.json          # Cached pricing data
├── balance_manager.py          # Updated to use pricing service
├── test_pricing_service.py     # Unit tests
└── test_pricing_manual.py      # Manual test script
```

## Data Format

### model_pricing.json

```json
{
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
  "last_updated": "2025-08-07T12:00:00+03:00",
  "source": "OpenAI Pricing (Auto-fetched)",
  "notes": "Prices are per 1K tokens. Input tokens are what you send to the model, output tokens are what the model generates. Updated automatically every 24 hours.",
  "exchange_rates": {
    "USD_to_RUB": 95.5,
    "RUB_to_USD": 0.0125,
    "last_updated": "2025-08-07T12:00:00+03:00",
    "source": "Exchange Rate API"
  },
  "markup_coefficient": 1.7,
  "markup_notes": "Final cost is multiplied by 1.7 (70% markup)"
}
```

## Testing

### Unit Tests

Run the unit tests:

```bash
cd Backend
python -m pytest test_pricing_service.py -v
```

### Manual Testing

Run the manual test script:

```bash
cd Backend
python test_pricing_manual.py
```

## Logging

The pricing service uses Python's logging module with INFO level. Logs include:

- Pricing update status
- API request results
- Error messages
- Timezone conversions

## Error Handling

The service implements multiple layers of error handling:

1. **API Failures**: Falls back to alternative APIs
2. **Network Issues**: Uses cached data
3. **File Corruption**: Recreates pricing data
4. **Invalid Data**: Uses fallback values

## Dependencies

- `requests`: For API calls
- `datetime`: For timezone handling
- `pathlib`: For file operations
- `json`: For data serialization
- `logging`: For logging

## Migration from Static Pricing

The existing `model_pricing.json` file is automatically migrated:

1. **First Run**: Service checks if file exists and creates initial data
2. **Automatic Updates**: Service updates data based on Moscow time
3. **Backward Compatibility**: Existing code continues to work unchanged

## Monitoring

Monitor the pricing service through:

1. **Logs**: Check application logs for pricing service messages
2. **File Timestamps**: Check `last_updated` field in `model_pricing.json`
3. **API Responses**: Monitor exchange rate API responses

## Troubleshooting

### Common Issues

1. **Pricing not updating**: Check if 24 hours have passed and date has changed
2. **API failures**: Check network connectivity and API availability
3. **Timezone issues**: Verify Moscow timezone configuration
4. **File permissions**: Ensure write permissions for `model_pricing.json`

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

- **Additional APIs**: Support for more exchange rate APIs
- **Real-time Updates**: Webhook-based updates for critical changes
- **Historical Data**: Track pricing changes over time
- **Notifications**: Alert when pricing changes significantly 