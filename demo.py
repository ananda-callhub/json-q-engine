#!/usr/bin/env python
"""
QueryLogic - Demo

Run: python demo.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from querylogic import (
    # Builder
    Field, Q, AND, OR, NOT,
    RuleBuilder, JsonRule,
    
    # Engine
    RuleEngine,
    
    # Core
    Evaluatable, EvalResult, Dependencies,
)


# =============================================================================
# 1. RULE BUILDER
# =============================================================================

print("=" * 60)
print("1. RULE BUILDER")
print("=" * 60)

# Method 1: Field builder (fluent)
rule1 = Field('city').equals('NYC')
print(f"\nField('city').equals('NYC')")
print(f"  → {rule1.to_json()}")

# Method 2: Field with operators
rule2 = Field('age').greater_than(18)
print(f"\nField('age').greater_than(18)")
print(f"  → {rule2.to_json()}")

# Method 3: Python operators
rule3 = Field('score') >= 90
print(f"\nField('score') >= 90")
print(f"  → {rule3.to_json()}")

# Method 4: Q style (Django-like)
rule4 = Q(city='NYC')
print(f"\nQ(city='NYC')")
print(f"  → {rule4.to_json()}")

rule5 = Q(age__gt=18)
print(f"\nQ(age__gt=18)")
print(f"  → {rule5.to_json()}")

# M2M / Array operations
rule6 = Field('tags').has_any(['vip', 'premium'])
print(f"\nField('tags').has_any(['vip', 'premium'])")
print(f"  → {rule6.to_json()}")

rule7 = Field('phonebooks').has_none(['blocked'])
print(f"\nField('phonebooks').has_none(['blocked'])")
print(f"  → {rule7.to_json()}")

# String operations
rule8 = Field('email').contains('@gmail')
print(f"\nField('email').contains('@gmail')")
print(f"  → {rule8.to_json()}")

# Combining rules
combined = (
    Field('city').equals('NYC') &
    Field('age').greater_than(18) &
    Field('tags').has_any(['vip'])
)
print(f"\nCombined (AND):")
print(f"  Field('city').equals('NYC') &")
print(f"  Field('age').greater_than(18) &")
print(f"  Field('tags').has_any(['vip'])")
print(f"  → {combined.to_json()}")

# OR combination
or_rule = Q(city='NYC') | Q(city='LA') | Q(city='Chicago')
print(f"\nCombined (OR):")
print(f"  Q(city='NYC') | Q(city='LA') | Q(city='Chicago')")
print(f"  → {or_rule.to_json()}")

# NOT
not_rule = ~Q(status='blocked')
print(f"\nNOT:")
print(f"  ~Q(status='blocked')")
print(f"  → {not_rule.to_json()}")


# =============================================================================
# 2. NESTED RULE BUILDER
# =============================================================================

print("\n" + "=" * 60)
print("2. NESTED RULE BUILDER")
print("=" * 60)

# Using RuleBuilder for complex nested structures
nested_rule = RuleBuilder.and_(
    RuleBuilder.field('city').equals('NYC'),
    RuleBuilder.or_(
        RuleBuilder.field('state').equals('NY'),
        RuleBuilder.field('state').equals('CA'),
    ),
    RuleBuilder.field('tags').has_any(['vip']),
)

print(f"\nNested rule using RuleBuilder:")
print(f"  RuleBuilder.and_(")
print(f"      RuleBuilder.field('city').equals('NYC'),")
print(f"      RuleBuilder.or_(")
print(f"          RuleBuilder.field('state').equals('NY'),")
print(f"          RuleBuilder.field('state').equals('CA'),")
print(f"      ),")
print(f"      RuleBuilder.field('tags').has_any(['vip']),")
print(f"  )")
print(f"\n  → JSON:")
import json
print(f"  {json.dumps(nested_rule.to_json(), indent=4)}")

# Using JsonRule to wrap existing JSON
existing_json = {"==": [{"var": "status"}, "active"]}
json_rule = JsonRule(existing_json)

# Combine JsonRule with builder rules
combined_with_json = json_rule & Field('age').gt(18)
print(f"\nCombine existing JSON with builder:")
print(f"  JsonRule({existing_json}) & Field('age').gt(18)")
print(f"  → {combined_with_json.to_json()}")


# =============================================================================
# 3. RULE ENGINE - EVALUATION
# =============================================================================

print("\n" + "=" * 60)
print("3. RULE ENGINE - EVALUATION")
print("=" * 60)

# Create engine instance
engine = RuleEngine()

# Test data
data = {
    'city': 'NYC',
    'state': 'NY',
    'age': 25,
    'tags': ['vip', 'newsletter'],
    'score': 85,
    'email': 'john@gmail.com',
    'status': 'active',
}
print(f"\nTest data: {data}")

# Evaluate nested rule
result = engine.evaluate(nested_rule, data)
print(f"\nNested rule evaluation: {result}")

# Evaluate rules
tests = [
    (Field('city').equals('NYC'), "city == 'NYC'"),
    (Field('age').greater_than(18), "age > 18"),
    (Field('age').greater_than(30), "age > 30"),
    (Field('tags').has_any(['vip']), "has any tags ['vip']"),
    (Field('tags').has_any(['premium']), "has any tags ['premium']"),
    (Field('email').contains('@gmail'), "email contains '@gmail'"),
    (Q(city='NYC') & Q(age__gt=18), "city='NYC' AND age>18"),
    (Q(city='LA') | Q(city='NYC'), "city='LA' OR city='NYC'"),
    (~Q(status='blocked'), "NOT status='blocked'"),
]

print("\nEvaluations using engine.evaluate():")
for rule, desc in tests:
    result = engine.evaluate(rule, data)
    icon = "✓" if result else "✗"
    print(f"  {icon} {desc}: {result}")

# Using engine.matches() for explicit bool
print(f"\nUsing engine.matches():")
print(f"  engine.matches(rules, data) → {engine.matches(nested_rule, data)}")


# =============================================================================
# 4. RAW JSON EVALUATION
# =============================================================================

print("\n" + "=" * 60)
print("4. RAW JSON EVALUATION")
print("=" * 60)

# Direct JSON rules
json_rules = [
    ({"==": [{"var": "city"}, "NYC"]}, "city == 'NYC'"),
    ({">": [{"var": "age"}, 18]}, "age > 18"),
    ({"and": [
        {"==": [{"var": "city"}, "NYC"]},
        {">": [{"var": "age"}, 18]}
    ]}, "city='NYC' AND age>18"),
    ({"some": [{"var": "tags"}, {"in": [{"var": ""}, ["vip", "admin"]]}]}, "has any tags"),
    ({"in": ["gmail", {"var": "email"}]}, "email contains 'gmail'"),
]

print(f"\nTest data: {data}")
print("\nJSON rule evaluations:")
for rule, desc in json_rules:
    result = engine.evaluate(rule, data)
    icon = "✓" if result else "✗"
    print(f"  {icon} {desc}: {result}")


# =============================================================================
# 5. EVALUATABLE OBJECTS
# =============================================================================

print("\n" + "=" * 60)
print("5. EVALUATABLE OBJECTS")
print("=" * 60)

class Contact(Evaluatable):
    """Example evaluatable contact."""
    
    def __init__(self, id, name, city, age, tags=None):
        self.id = id
        self.name = name
        self.city = city
        self.age = age
        self.tags = tags or []
    
    def to_eval_dict(self):
        return {
            'name': self.name,
            'city': self.city,
            'age': self.age,
            'tags': self.tags,
        }
    
    def __repr__(self):
        return f"Contact({self.id}, {self.name}, {self.city})"


# Create contacts
contacts = [
    Contact(1, 'John', 'NYC', 25, ['vip']),
    Contact(2, 'Jane', 'LA', 30, ['premium']),
    Contact(3, 'Bob', 'NYC', 17, []),
    Contact(4, 'Alice', 'NYC', 35, ['vip', 'premium']),
    Contact(5, 'Charlie', 'Chicago', 28, ['newsletter']),
]

# Rule: NYC + age > 18
rule = Field('city').equals('NYC') & Field('age').gt(18)

print(f"\nRule: city='NYC' AND age>18")
print(f"Contacts (using engine.test()):")

for contact in contacts:
    result = engine.test(rule, contact)
    icon = "✓" if result.matches else "✗"
    print(f"  {icon} {contact}: matches={result.matches} ({result.eval_time_ms:.3f}ms)")

# Batch evaluation
print(f"\nBatch evaluation (engine.batch()):")
results = engine.batch(rule, contacts)
print(f"  Matches: {results['matches']}")
print(f"  Non-matches: {results['non_matches']}")

# Filter
print(f"\nFilter (engine.filter()):")
matching = engine.filter(rule, contacts)
print(f"  Matching contacts: {matching}")


# =============================================================================
# 6. DEPENDENCIES EXTRACTION
# =============================================================================

print("\n" + "=" * 60)
print("6. DEPENDENCIES EXTRACTION (for CDC)")
print("=" * 60)

rule = (
    Field('city').equals('NYC') &
    Field('tags').has_any(['101', '102']) &
    Field('phonebooks').has_none(['999']) &
    Field('cf.123.number').gt(50000)
)

deps = rule.get_dependencies()
print(f"\nRule:")
print(f"  city='NYC' AND")
print(f"  has tags [101, 102] AND")
print(f"  has no phonebooks [999] AND")
print(f"  cf.123.number > 50000")

print(f"\nExtracted Dependencies:")
print(f"  fields: {deps.fields}")
print(f"  tag_ids: {deps.tag_ids}")
print(f"  phonebook_ids: {deps.phonebook_ids}")
print(f"  custom_field_ids: {deps.custom_field_ids}")

# Dependencies from JsonRule
json_rule = JsonRule({
    "and": [
        {"==": [{"var": "city"}, "NYC"]},
        {"some": [{"var": "tags"}, {"in": [{"var": ""}, ["201", "202"]]}]},
    ]
})
json_deps = json_rule.get_dependencies()
print(f"\nDependencies from JsonRule:")
print(f"  fields: {json_deps.fields}")
print(f"  tag_ids: {json_deps.tag_ids}")


# =============================================================================
# 7. CUSTOM OPERATORS
# =============================================================================

print("\n" + "=" * 60)
print("7. CUSTOM OPERATORS")
print("=" * 60)

# Create engine with custom operator
engine = RuleEngine()

# Register custom operator (chainable)
def between(values, data):
    """Check if value is between min and max."""
    if len(values) != 3:
        return False
    value, min_val, max_val = values
    return min_val <= value <= max_val

engine.register_operator('between', between)

# Use custom operator
rule = {"between": [{"var": "age"}, 20, 30]}
data = {"age": 25}

result = engine.evaluate(rule, data)
print(f"\nCustom operator 'between':")
print(f"  Rule: between(age, 20, 30)")
print(f"  Data: age=25")
print(f"  Result: {result}")


# =============================================================================
# 8. JSON TO Q OBJECT (Django)
# =============================================================================

print("\n" + "=" * 60)
print("8. JSON TO Q OBJECT (Django)")
print("=" * 60)

try:
    from querylogic import json_to_q, JsonToQ, to_q
    
    # Simple JSON to Q
    simple_json = {"==": [{"var": "city"}, "NYC"]}
    print(f"\nSimple JSON:")
    print(f"  Input: {simple_json}")
    print(f"  json_to_q() → Q(city='NYC')")
    
    # Nested JSON to Q
    nested_json = {
        "and": [
            {"==": [{"var": "city"}, "NYC"]},
            {"or": [
                {"==": [{"var": "state"}, "NY"]},
                {"==": [{"var": "state"}, "CA"]}
            ]},
            {">": [{"var": "age"}, 18]}
        ]
    }
    print(f"\nNested JSON:")
    print(f"  Input: {json.dumps(nested_json, indent=4)}")
    print(f"  json_to_q() → Q(city='NYC') & (Q(state='NY') | Q(state='CA')) & Q(age__gt=18)")
    
    # M2M JSON to Q
    m2m_json = {
        "some": [{"var": "tags"}, {"in": [{"var": ""}, ["101", "102"]]}]
    }
    print(f"\nM2M JSON:")
    print(f"  Input: {m2m_json}")
    print(f"  json_to_q() → Q(tags__id__in=['101', '102'])")
    
    # From Rule builder to Q
    builder_rule = Field('city').equals('NYC') & Field('age').gt(18)
    print(f"\nFrom Rule builder:")
    print(f"  Rule: Field('city').equals('NYC') & Field('age').gt(18)")
    print(f"  to_q() → Q(city='NYC') & Q(age__gt=18)")
    
    # Using JsonToQ class
    print(f"\nUsing JsonToQ class:")
    converter = JsonToQ()
    is_valid, errors = converter.validate(nested_json)
    print(f"  Validate: is_valid={is_valid}, errors={errors}")
    
    q, explanation = converter.convert_with_explanation(nested_json)
    print(f"  Explanation:")
    print(f"    {explanation}")

except ImportError:
    print("\n  (Django not installed - skipping Q object examples)")
    print("  Install with: pip install querylogic[django]")


# =============================================================================
# 9. FRONTEND RULES PARSING
# =============================================================================

print("\n" + "=" * 60)
print("9. FRONTEND RULES PARSING")
print("=" * 60)

# Frontend format from rule builder UI
frontend_rules = {
    "condition": "AND",
    "rules": [
        {"field": "contact_fields", "contact_field": "city", "operator": "is", "value": "NYC", "custom": False},
        {"field": "tags", "operator": "in", "value": ["101", "102"]},
    ],
    "children": [
        {
            "condition": "OR",
            "rules": [
                {"field": "contact_fields", "contact_field": "state", "operator": "is", "value": "NY", "custom": False},
                {"field": "contact_fields", "contact_field": "state", "operator": "is", "value": "CA", "custom": False},
            ]
        }
    ]
}

print(f"\nFrontend format:")
print(f"  {json.dumps(frontend_rules, indent=2)}")

rule = RuleBuilder.from_frontend(frontend_rules)
print(f"\nParsed to Rule:")
print(f"  {json.dumps(rule.to_json(), indent=2)}")

# Test evaluation
data = {'city': 'NYC', 'state': 'NY', 'tags': ['101']}
result = engine.evaluate(rule, data)
print(f"\nEvaluate against {data}:")
print(f"  Result: {result}")


# =============================================================================
# SUMMARY
# =============================================================================

print("\n" + "=" * 60)
print("SUMMARY - API Reference")
print("=" * 60)

print("""
RULE BUILDER:
  Field('name').equals(value)     → {"==": [{"var": "name"}, value]}
  Field('name').gt(value)         → {">": [{"var": "name"}, value]}
  Field('tags').has_any([...])    → {"some": [...]}
  Field('tags').has_none([...])   → {"none": [...]}
  Q(name='value')                 → {"==": [{"var": "name"}, "value"]}
  Q(name__gt=value)               → {">": [{"var": "name"}, value]}
  rule1 & rule2                   → {"and": [rule1, rule2]}
  rule1 | rule2                   → {"or": [rule1, rule2]}
  ~rule                           → {"!": rule}

NESTED BUILDER:
  RuleBuilder.and_(rule1, rule2)          → Nested AND
  RuleBuilder.or_(rule1, rule2)           → Nested OR
  RuleBuilder.not_(rule)                  → Nested NOT
  RuleBuilder.from_json(dict)             → JsonRule wrapper
  RuleBuilder.from_frontend(dict)         → Parse frontend format
  JsonRule(dict) & Field('x').eq(y)       → Combine JSON with builder

RULE ENGINE:
  engine = RuleEngine()
  engine.evaluate(rule, data)     → Any (result of evaluation)
  engine.matches(rule, data)      → bool (True/False)
  engine.test(rule, obj)          → EvalResult (with timing)
  engine.batch(rule, [objs])      → {'matches': [], 'non_matches': []}
  engine.filter(rule, [objs])     → [matching objects]
  engine.register_operator(name, fn) → self (chainable)

JSON TO DJANGO Q:
  json_to_q(json_dict)            → Q(...)  # Explicit JSON to Q
  to_q(rule)                      → Q(...)  # Rule builder to Q
  to_q(json_dict)                 → Q(...)  # Also accepts JSON
  
  JsonToQ().convert(json)         → Q(...)
  JsonToQ().convert_with_explanation(json) → (Q, str)
  JsonToQ().validate(json)        → (bool, [errors])

DEPENDENCIES:
  rule.get_dependencies()         → Dependencies(fields, tag_ids, ...)
  JsonRule(json).get_dependencies() → Dependencies from JSON
""")


if __name__ == '__main__':
    print("\n✓ All demos completed!")
