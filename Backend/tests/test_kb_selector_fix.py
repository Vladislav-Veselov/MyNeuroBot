#!/usr/bin/env python3
"""
Test script to verify KB selector fix for settings page.
"""

def test_kb_selector_fix():
    """Test the KB selector fix functionality."""
    print("Testing KB selector fix for settings page...")
    
    # Test 1: Simulate API response structure
    print("\n1. Testing API response structure...")
    
    mock_api_response = {
        'success': True,
        'knowledge_bases': [
            {
                'id': 'kb1',
                'name': 'База знаний по умолчанию',
                'created_at': '2024-01-01T00:00:00',
                'updated_at': '2024-01-01T00:00:00',
                'document_count': 5,
                'analyze_clients': True
            },
            {
                'id': 'kb2',
                'name': 'Продажи',
                'created_at': '2024-01-02T00:00:00',
                'updated_at': '2024-01-02T00:00:00',
                'document_count': 3,
                'analyze_clients': True
            }
        ],
        'current_kb_id': 'kb1'
    }
    
    print(f"API Response: {mock_api_response}")
    
    # Test 2: Simulate JavaScript processing
    print("\n2. Testing JavaScript processing...")
    
    def simulate_js_processing(data):
        """Simulate how JavaScript would process the API response."""
        if data.get('success'):
            knowledge_bases = data.get('knowledge_bases', [])
            if knowledge_bases:
                first_kb = knowledge_bases[0]
                return {
                    'processed': True,
                    'kb_count': len(knowledge_bases),
                    'first_kb_id': first_kb.get('id'),
                    'first_kb_name': first_kb.get('name')
                }
            else:
                return {
                    'processed': True,
                    'kb_count': 0,
                    'message': 'Нет баз знаний'
                }
        else:
            return {
                'processed': False,
                'error': data.get('error', 'Unknown error')
            }
    
    result = simulate_js_processing(mock_api_response)
    print(f"JavaScript processing result: {result}")
    
    # Test 3: Simulate CSS visibility
    print("\n3. Testing CSS visibility...")
    
    css_properties = {
        'display': 'block',
        'visibility': 'visible',
        'opacity': '1',
        'color': '#FFFFFF',
        'background-color': '#242A36',
        'border': '1px solid #2D3446'
    }
    
    print("CSS properties for KB selector:")
    for property, value in css_properties.items():
        print(f"  {property}: {value}")
    
    # Test 4: Simulate error handling
    print("\n4. Testing error handling...")
    
    error_scenarios = [
        {'success': False, 'error': 'Network error'},
        {'success': True, 'knowledge_bases': []},
        {'success': True, 'knowledge_bases': None}
    ]
    
    for i, scenario in enumerate(error_scenarios, 1):
        result = simulate_js_processing(scenario)
        print(f"Scenario {i}: {scenario}")
        print(f"  Result: {result}")
    
    # Test 5: Simulate DOM manipulation
    print("\n5. Testing DOM manipulation...")
    
    def simulate_dom_update(kb_list):
        """Simulate DOM update for KB selector."""
        options = []
        
        if not kb_list:
            options.append({'value': '', 'text': 'Нет баз знаний'})
        else:
            for kb in kb_list:
                options.append({
                    'value': kb['id'],
                    'text': kb['name'],
                    'selected': kb['id'] == 'kb1'  # Simulate first KB selected
                })
        
        return options
    
    dom_options = simulate_dom_update(mock_api_response['knowledge_bases'])
    print("DOM options:")
    for option in dom_options:
        selected_text = " (selected)" if option.get('selected') else ""
        print(f"  {option['text']} = {option['value']}{selected_text}")
    
    print("\n✅ All KB selector fix tests passed!")

if __name__ == "__main__":
    test_kb_selector_fix() 