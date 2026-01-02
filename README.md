# JSON Rule Engine

[![Python Version](https://img.shields.io/pypi/pyversions/json-rule-engine.svg)](https://pypi.org/project/json-rule-engine/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/json-rule-engine.svg)](https://badge.fury.io/py/json-rule-engine)

A powerful and lightweight Python library for building, evaluating, and translating JSON-based business rules. Perfect for creating dynamic filtering systems, decision engines, and converting rules to Django ORM queries.

## Features

- **Pythonic Rule Builder**: Build JSON rules using fluent API
- **Nested Rule Support**: Build complex nested AND/OR/NOT structures
- **JSON to Q Conversion**: Convert JSON rules directly to Django Q objects  
- **Rule Evaluator**: Evaluate rules against any data object
- **Dependency Extraction**: Extract field dependencies for CDC/caching
- **Frontend Parser**: Parse UI rule builder format
- **Extensible**: Add custom operators easily
- **Zero Dependencies**: Core library has no external dependencies

## Installation

```bash
# Basic installation
pip install json-rule-engine

# With Django support
pip install json-rule-engine[django]

# Development installation
pip install json-rule-engine[dev]
```

## Quick Start

### 1. Build Rules (Pythonic)

```python
from json_rule_engine import Field, Q

# Fluent builder
rule = Field('city').equals('NYC')
rule = Field('age').greater_than(18)
rule = Field('tags').has_any(['vip', 'premium'])

# Django-style Q
rule = Q(city='NYC')
rule = Q(age__gt=18)
rule = Q(tags__has_any=['vip'])

# Combine with & | ~
rule = (
    Field('city').equals('NYC') &
    Field('age').gt(18) |
    ~Field('status').equals('blocked')
)

# Get JSON
json_rule = rule.to_json()
# {"and": [{"==": [{"var": "city"}, "NYC"]}, {">": [{"var": "age"}, 18]}]}
```

### 2. Nested Rule Building

```python
from json_rule_engine import RuleBuilder, JsonRule

# Complex nested structures
rule = RuleBuilder.and_(
    RuleBuilder.field('city').equals('NYC'),
    RuleBuilder.or_(
        RuleBuilder.field('state').equals('NY'),
        RuleBuilder.field('state').equals('CA'),
    ),
    RuleBuilder.field('tags').has_any(['vip']),
)

# Wrap existing JSON and combine with builder
existing_json = {"==": [{"var": "status"}, "active"]}
combined = JsonRule(existing_json) & Field('age').gt(18)
```

### 3. Rule Engine - Evaluate Rules

```python
from json_rule_engine import RuleEngine

engine = RuleEngine()

# Evaluate against dict
data = {'city': 'NYC', 'age': 25, 'tags': ['vip']}
result = engine.evaluate(rule, data)  # Any (result)
result = engine.matches(rule, data)   # bool (True/False)

# Evaluate raw JSON
json_rule = {"==": [{"var": "city"}, "NYC"]}
result = engine.evaluate(json_rule, data)  # True
```

### 4. Evaluate Against Objects

```python
from json_rule_engine import Evaluatable, RuleEngine

class Contact(Evaluatable):
    def __init__(self, name, city, age):
        self.name = name
        self.city = city
        self.age = age
    
    def to_eval_dict(self):
        return {
            'name': self.name,
            'city': self.city,
            'age': self.age,
        }

engine = RuleEngine()
contact = Contact('John', 'NYC', 25)

# Single evaluation with timing
result = engine.test(rule, contact)
# EvalResult(matches=True, eval_time_ms=0.01)

# Batch evaluation
contacts = [Contact(...), Contact(...), ...]
results = engine.batch(rule, contacts)
# {'matches': [...], 'non_matches': [...]}

# Filter matching
matches = engine.filter(rule, contacts)
# [Contact(...), Contact(...)]
```

### 5. JSON to Django Q (Direct Conversion)

```python
from json_rule_engine import json_to_q, to_q, JsonToQ

# Direct JSON to Q conversion
json_rules = {
    "and": [
        {"==": [{"var": "city"}, "NYC"]},
        {"or": [
            {"==": [{"var": "state"}, "NY"]},
            {"==": [{"var": "state"}, "CA"]}
        ]}
    ]
}

q = json_to_q(json_rules)
# Result: Q(city='NYC') & (Q(state='NY') | Q(state='CA'))

# From Rule builder
rule = Field('city').equals('NYC') & Field('tags').has_any(['vip'])
q = to_q(rule)

# Using JsonToQ class with validation
converter = JsonToQ()
is_valid, errors = converter.validate(json_rules)
q, explanation = converter.convert_with_explanation(json_rules)

# Use with Django ORM
contacts = Contact.objects.filter(q)
```

## API Reference

### Rule Builder

| Method | JSON Output |
|--------|-------------|
| `Field('x').equals(v)` | `{"==": [{"var": "x"}, v]}` |
| `Field('x').not_equals(v)` | `{"!=": [{"var": "x"}, v]}` |
| `Field('x').gt(v)` | `{">": [{"var": "x"}, v]}` |
| `Field('x').gte(v)` | `{">=": [{"var": "x"}, v]}` |
| `Field('x').lt(v)` | `{"<": [{"var": "x"}, v]}` |
| `Field('x').lte(v)` | `{"<=": [{"var": "x"}, v]}` |
| `Field('x').contains(v)` | `{"in": [v, {"var": "x"}]}` |
| `Field('x').startswith(v)` | `{"_startswith": [...]}` |
| `Field('x').endswith(v)` | `{"_endswith": [...]}` |
| `Field('x').is_empty()` | `{"or": [{"==": [...]}, ...]}` |
| `Field('x').has_any([...])` | `{"some": [{"var": "x"}, ...]}` |
| `Field('x').has_all([...])` | `{"and": [...]}` |
| `Field('x').has_none([...])` | `{"none": [{"var": "x"}, ...]}` |

### Nested Building

```python
RuleBuilder.and_(rule1, rule2, ...)    # Nested AND
RuleBuilder.or_(rule1, rule2, ...)     # Nested OR  
RuleBuilder.not_(rule)                  # Nested NOT
RuleBuilder.field('name')               # Create Field
RuleBuilder.from_json(dict)             # Wrap existing JSON
RuleBuilder.from_frontend(dict)         # Parse frontend format

JsonRule(dict)                          # JSON wrapper
JsonRule(dict) & Field('x').eq(y)       # Combine JSON with builder
```

### Q Style Builder

```python
Q(field='value')           # equals
Q(field__eq='value')       # equals
Q(field__ne='value')       # not equals
Q(field__gt=10)            # greater than
Q(field__gte=10)           # greater or equal
Q(field__lt=10)            # less than
Q(field__lte=10)           # less or equal
Q(field__contains='x')     # contains
Q(field__startswith='x')   # starts with
Q(field__endswith='x')     # ends with
Q(field__in=[1,2,3])       # in list
Q(field__has_any=[...])    # has any (M2M)
Q(field__has_all=[...])    # has all (M2M)
Q(field__has_none=[...])   # has none (M2M)
```

### Combining Rules

```python
rule1 & rule2    # AND
rule1 | rule2    # OR
~rule            # NOT

# Or use functions
from json_rule_engine import AND, OR, NOT
AND(rule1, rule2, rule3)
OR(rule1, rule2)
NOT(rule)
```

### JSON to Q Conversion

```python
from json_rule_engine import json_to_q, to_q, JsonToQ

# Direct conversion
q = json_to_q(json_dict)              # JSON dict → Q
q = to_q(rule)                         # Rule builder → Q
q = to_q(json_dict)                    # Also accepts JSON

# Class-based with validation
converter = JsonToQ(field_map={'tags': 'profile__tags__id'})
q = converter.convert(json_dict)
q, explanation = converter.convert_with_explanation(json_dict)
is_valid, errors = converter.validate(json_dict)
```

### RuleEngine

```python
from json_rule_engine import RuleEngine

engine = RuleEngine()

# Evaluation
result = engine.evaluate(rule, data)       # Any (raw result)
result = engine.matches(rule, data)        # bool (True/False)

# Object evaluation
result = engine.test(rule, obj)            # EvalResult (with timing)
results = engine.batch(rule, [objs])       # {'matches': [], 'non_matches': []}
matches = engine.filter(rule, [objs])      # [matching objects]

# Custom operators
engine.register_operator('between', lambda vals, data: ...)
```

### Dependencies (for CDC)

```python
rule = Field('city').eq('NYC') & Field('tags').has_any(['101'])
deps = rule.get_dependencies()

deps.fields           # {'city'}
deps.tag_ids          # {101}
deps.phonebook_ids    # set()
deps.custom_field_ids # set()

# From JSON
json_rule = JsonRule(json_dict)
deps = json_rule.get_dependencies()
```

## Supported JsonLogic Operators

### Comparison
`==`, `!=`, `===`, `!==`, `>`, `>=`, `<`, `<=`

### Logic  
`and`, `or`, `!`, `!!`, `if`, `?:`

### Array
`in`, `some`, `all`, `none`, `merge`

### String
`in` (substring), `cat`

### Arithmetic
`+`, `-`, `*`, `/`, `%`, `min`, `max`

### Data
`var`, `missing`

### Custom (Extended)
`_contains`, `_startswith`, `_endswith`, `_is_empty`, `_is_not_empty`

## License

MIT
