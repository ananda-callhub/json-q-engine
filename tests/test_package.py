#!/usr/bin/env python
"""Test that the package works correctly."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from json_rule_engine import (
    Field, Q, RuleEngine,
    evaluate, matches
)


def main():
    print("Testing JSON Rule Engine Package")
    print("=" * 40)
    
    # Test 1: Build and evaluate a simple rule
    print("\nTest 1: Simple rule")
    rule = Field('city').equals('NYC')
    data = {'city': 'NYC', 'age': 25}
    result = evaluate(rule, data)
    print(f"  Rule: city == 'NYC'")
    print(f"  Data: {data}")
    print(f"  Result: {result}")
    assert result is True, "Simple rule evaluation failed"
    
    # Test 2: Combined rules
    print("\nTest 2: Combined rules")
    rule = Field('city').equals('NYC') & Field('age').gt(18)
    result = evaluate(rule, data)
    print(f"  Rule: city == 'NYC' AND age > 18")
    print(f"  Data: {data}")
    print(f"  Result: {result}")
    assert result is True, "Combined rule evaluation failed"
    
    # Test 3: Q objects
    print("\nTest 3: Q objects")
    rule = Q(city='NYC') & Q(age__gt=18)
    result = evaluate(rule, data)
    print(f"  Rule: Q(city='NYC') & Q(age__gt=18)")
    print(f"  Data: {data}")
    print(f"  Result: {result}")
    assert result is True, "Q object evaluation failed"
    
    # Test 4: Array operations
    print("\nTest 4: Array operations")
    data_with_tags = {**data, 'tags': ['vip', 'premium']}
    rule = Field('tags').has_any(['vip'])
    result = evaluate(rule, data_with_tags)
    print(f"  Rule: tags has any ['vip']")
    print(f"  Data: {data_with_tags}")
    print(f"  Result: {result}")
    assert result is True, "Array operation failed"
    
    # Test 5: JSON evaluation
    print("\nTest 5: Direct JSON evaluation")
    json_rule = {"==": [{"var": "city"}, "NYC"]}
    result = evaluate(json_rule, data)
    print(f"  JSON: {json_rule}")
    print(f"  Data: {data}")
    print(f"  Result: {result}")
    assert result is True, "JSON evaluation failed"
    
    print("\n" + "=" * 40)
    print("✓ All tests passed successfully!")


if __name__ == "__main__":
    main()