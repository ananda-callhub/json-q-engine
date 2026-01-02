"""
JSON Rule Engine - A lightweight library for building, evaluating, and translating JSON-based rules.

Features:
- Pythonic Rule Builder: Build JSON rules using fluent API
- Rule Evaluator: Evaluate rules against any data
- Django Q Translator: Convert rules to Django ORM queries

Quick Start:
    # Build rules
    from json_rule_engine import Field, Q
    
    rule = Field('city').equals('NYC') & Field('age').gt(18)
    # or
    rule = Q(city='NYC') & Q(age__gt=18)
    
    # Evaluate
    from json_rule_engine import evaluate
    
    result = evaluate(rule, {'city': 'NYC', 'age': 25})  # True
    
    # Django Q
    from json_rule_engine import to_q
    
    q = to_q(rule)
    contacts = Contact.objects.filter(q)

Documentation: https://github.com/anandabehera/json-rule-engine
"""

__version__ = '1.0.0'
__author__ = 'Ananda Behera'
__email__ = 'ananda.behera@example.com'
__license__ = 'MIT'


# Core classes
from .core import (
    Evaluatable,
    Rule,
    RuleSet,
    EvalResult,
    Dependencies,
    Operator,
    Logic,
)

# Builder classes
from .builder import (
    Field,
    Condition,
    Q,
    RuleBuilder,
    JsonRule,
    AND,
    OR,
    NOT,
)

# Evaluator classes
from .evaluator import (
    RuleEngine,
    evaluate,
    matches,
)

# Django Q classes (optional)
try:
    from .django_q import (
        QTranslator,
        JsonToQ,
        to_q,
        json_to_q,
    )
    _HAS_DJANGO = True
except ImportError:
    _HAS_DJANGO = False
    QTranslator = None
    JsonToQ = None
    to_q = None
    json_to_q = None


__all__ = [
    # Version
    '__version__',
    '__author__',
    '__email__',
    '__license__',
    
    # Core
    'Evaluatable',
    'Rule',
    'RuleSet',
    'EvalResult',
    'Dependencies',
    'Operator',
    'Logic',
    
    # Builder
    'Field',
    'Condition',
    'Q',
    'RuleBuilder',
    'JsonRule',
    'AND',
    'OR',
    'NOT',
    
    # Evaluator
    'RuleEngine',
    'evaluate',
    'matches',
    
    # Django (if available)
    'QTranslator',
    'JsonToQ',
    'to_q',
    'json_to_q',
]