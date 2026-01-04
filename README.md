# JSON Rule Engine

[![Python Version](https://img.shields.io/pypi/pyversions/json-rule-engine.svg)](https://pypi.org/project/json-rule-engine/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/json-rule-engine.svg)](https://badge.fury.io/py/json-rule-engine)

A powerful and lightweight Python library for building, evaluating, and translating JSON-based business rules. Perfect for creating dynamic filtering systems, decision engines, and converting rules to Django ORM queries.

## Key Features

- 🎯 **Unified API**: Single `RuleEngine` class for all functionality
- 🔧 **Configurable**: No hardcoded domain assumptions - works for any use case
- 🐍 **Pythonic**: Intuitive `Field()` and `Q()` builders for rule creation
- ⚡ **Zero Dependencies**: Core functionality requires no external packages
- 🔌 **Django Integration**: Optional Django Q object conversion
- 📊 **Extensible**: Add custom operators and configurations

## Installation

```bash
# Basic installation
pip install json-rule-engine

# With Django support
pip install json-rule-engine[django]
```

## Quick Start

### Initialize the Engine

```python
from json_rule_engine import RuleEngine, Field, Q

# Create the engine - single entry point for all functionality
engine = RuleEngine()
```

### Build Rules

```python
# Using Field builder (recommended)
rule = Field('age').greater_than(18)
rule = Field('city').equals('NYC')
rule = Field('email').contains('@gmail.com')

# Combine rules with & (AND), | (OR), ~ (NOT)
rule = (
    Field('city').equals('NYC') &
    Field('age').gt(18) &
    Field('tags').has_any(['premium', 'vip'])
)

# Using Django-style Q objects
rule = Q(city='NYC') & Q(age__gt=18)
```

### Evaluate Rules

```python
# Evaluate against dictionary
data = {'city': 'NYC', 'age': 25, 'tags': ['vip']}
result = engine.evaluate(rule, data)  # True

# Check matches (returns bool)
matches = engine.matches(rule, data)  # True
```

### Django Integration

```python
# Convert to Django Q object (requires Django)
q = engine.to_q(rule)

# Use in Django ORM
from myapp.models import Contact
contacts = Contact.objects.filter(q)
```

## Advanced Usage

### Custom Configuration

The engine is fully configurable - no hardcoded assumptions:

```python
from json_rule_engine import RuleEngine, DependencyConfig, RuleFields

# Configure for your domain (e-commerce example)
config = DependencyConfig(
    id_fields={
        'categories': 'category_ids',
        'products': 'product_ids',
        'vendors': 'vendor_ids',
    },
    custom_field_pattern=r'^custom\.(\d+)\.(\w+)$'
)

# Initialize engine with custom config
engine = RuleEngine(dependency_config=config)

# Now your fields are recognized
rule = Field('categories').has_any([101, 102])
deps = engine.get_dependencies(rule)  # Returns RuleFields
print(deps.id_references['category_ids'])  # {101, 102}
```

### Working with Objects

```python
from json_rule_engine import RuleEntity

class Customer(RuleEntity):
    def __init__(self, name, age, city, tags=None):
        self.name = name
        self.age = age
        self.city = city
        self.tags = tags or []
    
    def to_eval_dict(self):
        return {
            'name': self.name,
            'age': self.age,
            'city': self.city,
            'tags': self.tags
        }

# Create customers
customers = [
    Customer('Alice', 25, 'NYC', ['vip']),
    Customer('Bob', 17, 'LA', ['regular']),
    Customer('Charlie', 30, 'NYC', ['premium'])
]

# Define rule
rule = Field('city').equals('NYC') & Field('age').gte(18)

# Batch evaluation
results = engine.batch(rule, customers)
print(f"Matches: {results['matches']}")      # [Alice, Charlie]
print(f"Non-matches: {results['non_matches']}") # [Bob]

# Filter matching objects
nyc_adults = engine.filter(rule, customers)  # [Alice, Charlie]

# Test with timing
result = engine.test(rule, customers[0])  # Returns EvaluationResult
print(f"Match: {result.matches}, Time: {result.eval_time_ms}ms")
```

### Custom Operators

```python
# Register custom operators
def between(values, data):
    """Check if value is between min and max."""
    val, min_val, max_val = values
    return min_val <= val <= max_val

engine.register_operator('between', between)

# Use custom operator
rule = {"between": [{"var": "age"}, 18, 65]}
result = engine.evaluate(rule, {"age": 25})  # True
```

### Complex Nested Rules

```python
# Build complex business logic
rule = RuleBuilder.and_(
    RuleBuilder.field('status').equals('active'),
    RuleBuilder.or_(
        RuleBuilder.field('role').equals('admin'),
        RuleBuilder.and_(
            RuleBuilder.field('role').equals('user'),
            RuleBuilder.field('permissions').has_any(['write', 'delete'])
        )
    ),
    RuleBuilder.not_(
        RuleBuilder.field('banned').equals(True)
    )
)

# Evaluate complex rule
data = {
    'status': 'active',
    'role': 'user',
    'permissions': ['read', 'write'],
    'banned': False
}
result = engine.evaluate(rule, data)  # True
```

### Working with JSON Rules

```python
# Parse existing JSON rules
json_rule = {
    "and": [
        {"==": [{"var": "status"}, "active"]},
        {"or": [
            {">": [{"var": "credits"}, 100]},
            {"==": [{"var": "plan"}, "premium"]}
        ]}
    ]
}

# Evaluate JSON directly
result = engine.evaluate(json_rule, data)

# Or wrap and combine with builder
from json_rule_engine import JsonRule

wrapped = JsonRule(json_rule)
combined = wrapped & Field('region').equals('US')
```

## API Reference

### RuleEngine Methods

The `RuleEngine` class is the main API entry point:

```python
engine = RuleEngine(
    dependency_config=None,  # Optional: Custom dependency configuration
    django_field_map=None    # Optional: Custom Django field mappings
)

# Rule Evaluation
engine.evaluate(rule, data)           # Evaluate rule against data
engine.matches(rule, data)            # Returns bool
engine.test(rule, obj)                # Test RuleEntity object with timing
engine.batch(rule, objects)           # Evaluate multiple objects
engine.filter(rule, objects)          # Filter matching objects

# Django Integration
engine.to_q(rule)                      # Convert to Django Q object
engine.to_q_with_explanation(rule)    # Get Q object with explanation
engine.validate_json_rules(json)      # Validate JSON structure

# Dependency Extraction
engine.get_dependencies(rule)         # Extract field dependencies → RuleFields

# Configuration
engine.register_operator(name, func)  # Add custom operator
engine.configure_dependencies(config) # Update dependency config
engine.configure_django_fields(map)   # Update Django mappings
```

### Rule Builders

```python
# Field builder (recommended)
Field('name').equals(value)
Field('name').not_equals(value)
Field('name').greater_than(value)
Field('name').greater_or_equal(value)
Field('name').less_than(value)
Field('name').less_or_equal(value)
Field('name').contains(substring)
Field('name').startswith(prefix)
Field('name').endswith(suffix)
Field('name').is_empty()
Field('name').is_not_empty()
Field('name').has_any([values])    # For array fields
Field('name').has_all([values])    # Must have all
Field('name').has_none([values])   # Must have none

# Q objects (Django-style)
Q(field='value')              # equals
Q(field__ne='value')          # not equals
Q(field__gt=10)               # greater than
Q(field__gte=10)              # greater or equal
Q(field__lt=10)               # less than
Q(field__lte=10)              # less or equal
Q(field__contains='text')     # contains
Q(field__has_any=[1,2])       # array operations

# Combining rules
rule1 & rule2    # AND
rule1 | rule2    # OR
~rule           # NOT

# Helper functions
AND(rule1, rule2, rule3)
OR(rule1, rule2)
NOT(rule)
```

## Supported Operators

### Comparison
- `==` (equals)
- `!=` (not equals)
- `>` (greater than)
- `>=` (greater or equal)
- `<` (less than)
- `<=` (less or equal)

### String
- `contains` - Substring check
- `startswith` - String prefix
- `endswith` - String suffix
- `is_empty` - Null or empty string
- `is_not_empty` - Has value

### Array/Set
- `has_any` - Has at least one value
- `has_all` - Has all values
- `has_none` - Has none of the values
- `is_in` - Value is in list

### Logic
- `&` / `AND` - Logical AND
- `|` / `OR` - Logical OR
- `~` / `NOT` - Logical NOT

## Migration from v1.x

Version 2.0 introduces a cleaner, unified API:

### Old API (v1.x)
```python
# Multiple confusing entry points
from json_rule_engine import evaluate, matches, to_q, json_to_q

result = evaluate(rule, data)
q = to_q(rule)
q = json_to_q(json_rules)
```

### New API (v2.0)
```python
# Single, clear entry point
from json_rule_engine import RuleEngine

engine = RuleEngine()
result = engine.evaluate(rule, data)
q = engine.to_q(rule)
```

### Key Changes
1. **Unified API**: All functionality through `RuleEngine` class
2. **Configurable Dependencies**: No more hardcoded field assumptions
3. **Professional Class Names**: 
   - `Evaluatable` → `RuleEntity`
   - `Dependencies` → `RuleFields`
   - `EvalResult` → `EvaluationResult`
4. **Cleaner Imports**: Single entry point for discoverability
5. **Better Typing**: Full type hints throughout

## Examples

### E-commerce Product Filtering
```python
# Configure for e-commerce domain
config = DependencyConfig(
    id_fields={
        'categories': 'category_ids',
        'brands': 'brand_ids',
        'tags': 'tag_ids'
    }
)
engine = RuleEngine(dependency_config=config)

# Build product filter rule
rule = (
    Field('price').between(10, 100) &
    Field('categories').has_any(['electronics', 'computers']) &
    Field('in_stock').equals(True) &
    (Field('rating').gte(4) | Field('featured').equals(True))
)

# Filter products
matching_products = engine.filter(rule, all_products)
```

### User Permission System
```python
# Define permission rule
can_edit = (
    Field('role').equals('admin') |
    (
        Field('role').equals('editor') &
        Field('departments').has_any(['content', 'marketing'])
    )
)

# Check user permission
user_data = {
    'role': 'editor',
    'departments': ['content', 'design']
}
has_permission = engine.evaluate(can_edit, user_data)  # True
```

### Dynamic Form Validation
```python
# Build validation rule from configuration
validation_rule = RuleBuilder.and_(
    RuleBuilder.field('age').gte(18),
    RuleBuilder.field('email').contains('@'),
    RuleBuilder.or_(
        RuleBuilder.field('phone').is_not_empty(),
        RuleBuilder.field('email').is_not_empty()
    )
)

# Validate form submission
form_data = {
    'age': 25,
    'email': 'user@example.com',
    'phone': ''
}
is_valid = engine.matches(validation_rule, form_data)  # True
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any problems or have questions, please [open an issue](https://github.com/anandabehera/json-rule-engine/issues) on GitHub.