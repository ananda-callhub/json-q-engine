"""
QueryLogic - JSON Rule Engine for Python

A lightweight library for building, evaluating, and translating JSON-based rules.

Features:
- Pythonic Rule Builder: Build JSON rules using fluent API
- Rule Evaluator: Evaluate rules against any data
- Django Q Translator: Convert rules to Django ORM queries

Quick Start:
    # Build rules
    from querylogic import Field, Q
    
    rule = Field('city').equals('NYC') & Field('age').gt(18)
    # or
    rule = Q(city='NYC') & Q(age__gt=18)
    
    # Evaluate
    from querylogic import evaluate
    
    result = evaluate(rule, {'city': 'NYC', 'age': 25})  # True
    
    # Django Q
    from querylogic import to_q
    
    q = to_q(rule)
    contacts = Contact.objects.filter(q)

Documentation: https://github.com/your-repo/json-q-rule-engine
"""

__version__ = '0.1.0'
__author__ = 'Ananda Behera'


# =============================================================================
# Core
# =============================================================================

from .core import (
    # Base classes
    Evaluatable,
    Rule,
    RuleSet,
    
    # Data classes
    EvalResult,
    Dependencies,
    
    # Enums
    Operator,
    Logic,
)

# =============================================================================
# Builder
# =============================================================================

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

# =============================================================================
# Evaluator (now RuleEngine)
# =============================================================================

from .evaluator import (
    RuleEngine,
)

# =============================================================================
# Django Q (Optional)
# =============================================================================

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


# =============================================================================
# Public API
# =============================================================================

__all__ = [
    # Version
    '__version__',
    
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
    
    # Engine
    'RuleEngine',
    
    # Django (if available)
    'QTranslator',
    'JsonToQ',
    'to_q',
    'json_to_q',
]
