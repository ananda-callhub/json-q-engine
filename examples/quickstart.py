#!/usr/bin/env python
"""Quick start example for JSON Rule Engine."""

import sys
import os

# Add parent directory to path for importing the package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from json_rule_engine import (
    Field, Q, RuleEngine, 
    RuleBuilder, JsonRule,
    evaluate, matches
)


def main():
    print("JSON Rule Engine - Quick Start Examples")
    print("=" * 50)
    
    # 1. Build simple rules
    print("\n1. Building Simple Rules")
    print("-" * 30)
    
    # Using Field builder
    rule = Field('city').equals('NYC')
    print(f"Field('city').equals('NYC')")
    print(f"  JSON: {rule.to_json()}")
    
    # Using operators
    rule = Field('age') > 18
    print(f"\nField('age') > 18")
    print(f"  JSON: {rule.to_json()}")
    
    # Using Q objects (Django-style)
    rule = Q(city='NYC')
    print(f"\nQ(city='NYC')")
    print(f"  JSON: {rule.to_json()}")
    
    # 2. Combine rules
    print("\n\n2. Combining Rules")
    print("-" * 30)
    
    rule = (
        Field('city').equals('NYC') &
        Field('age').gt(18) &
        Field('tags').has_any(['vip', 'premium'])
    )
    print(f"Combined with & operator:")
    print(f"  JSON: {rule.to_json()}")
    
    # 3. Evaluate rules
    print("\n\n3. Evaluating Rules")
    print("-" * 30)
    
    data = {
        'city': 'NYC',
        'age': 25,
        'tags': ['vip', 'newsletter'],
        'email': 'user@gmail.com'
    }
    print(f"Data: {data}")
    
    # Create engine
    engine = RuleEngine()
    
    # Test various rules
    test_rules = [
        (Field('city').equals('NYC'), "city == 'NYC'"),
        (Field('age').gt(18), "age > 18"),
        (Field('tags').has_any(['vip']), "has tag 'vip'"),
        (Field('email').contains('@gmail'), "email contains '@gmail'"),
        (
            Field('city').equals('NYC') & Field('age').gt(18),
            "city == 'NYC' AND age > 18"
        ),
    ]
    
    print("\nEvaluation results:")
    for rule, description in test_rules:
        result = engine.evaluate(rule, data)
        status = "✓" if result else "✗"
        print(f"  {status} {description}: {result}")
    
    # 4. Working with JSON directly
    print("\n\n4. Working with JSON Rules")
    print("-" * 30)
    
    # Direct JSON evaluation
    json_rule = {
        "and": [
            {"==": [{"var": "city"}, "NYC"]},
            {">": [{"var": "age"}, 18]},
            {"some": [{"var": "tags"}, {"in": [{"var": ""}, ["vip", "admin"]]}]}
        ]
    }
    print(f"JSON Rule: {json_rule}")
    
    result = evaluate(json_rule, data)
    print(f"Evaluation result: {result}")
    
    # Wrap existing JSON and combine
    existing = JsonRule({"==": [{"var": "status"}, "active"]})
    combined = existing | Field('city').equals('NYC')
    print(f"\nCombined JSON with builder:")
    print(f"  {combined.to_json()}")
    
    # 5. Custom operators
    print("\n\n5. Custom Operators")
    print("-" * 30)
    
    # Register custom operator
    def between(values, data):
        val, min_val, max_val = values
        return min_val <= val <= max_val
    
    engine.register_operator('between', between)
    
    # Use custom operator
    custom_rule = {"between": [{"var": "age"}, 18, 65]}
    result = engine.evaluate(custom_rule, {"age": 25})
    print(f"Custom 'between' operator:")
    print(f"  Rule: age between 18 and 65")
    print(f"  Result: {result}")
    
    print("\n" + "=" * 50)
    print("End of Quick Start Examples")


if __name__ == "__main__":
    main()