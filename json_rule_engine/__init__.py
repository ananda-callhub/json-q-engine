"""
JSON Rule Engine - A lightweight library for building, evaluating, and translating JSON-based rules.

Features:
- Pythonic Rule Builder: Build JSON rules using fluent API
- Rule Evaluator: Evaluate rules against any data
- Django Q Translator: Convert rules to Django ORM queries
- Configurable Dependencies: No hardcoded domain assumptions

Quick Start:
    # Initialize engine
    from json_rule_engine import RuleEngine, Field, Q
    
    engine = RuleEngine()
    
    # Build rules
    rule = Field('city').equals('NYC') & Field('age').gt(18)
    # or
    rule = Q(city='NYC') & Q(age__gt=18)
    
    # Evaluate
    result = engine.evaluate(rule, {'city': 'NYC', 'age': 25})  # True
    
    # Django Q (if Django installed)
    q = engine.to_q(rule)
    contacts = Contact.objects.filter(q)

Documentation: https://github.com/anandabehera/json-rule-engine
"""

__version__ = '2.0.5'  # Updated for README improvements
__author__ = 'Ananda Behera'
__email__ = 'behera.anand1@gmail.com'
__license__ = 'MIT'


# Core classes
from .core import (
    RuleEntity,
    Rule,
    RuleSet,
    EvaluationResult,
    RuleFields,
    DependencyConfig,
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

# Unified Rule Engine (main API)
from .evaluator import RuleEngine

# Django Q classes (optional) - now accessed through RuleEngine
try:
    from .django_q import QTranslator, JsonToQ
    _HAS_DJANGO = True
except ImportError:
    _HAS_DJANGO = False
    QTranslator = None
    JsonToQ = None


__all__ = [
    # Version
    '__version__',
    '__author__',
    '__email__',
    '__license__',
    
    # Main API - RuleEngine
    'RuleEngine',
    
    # Core interfaces
    'RuleEntity',
    'Rule',
    'RuleSet',
    'EvaluationResult',
    'RuleFields',
    'DependencyConfig',
    'Operator',
    'Logic',
    
    # Rule builders
    'Field',
    'Condition',
    'Q',
    'RuleBuilder',
    'JsonRule',
    'AND',
    'OR',
    'NOT',
    
    # Django (accessed through RuleEngine.to_q())
    'QTranslator',
    'JsonToQ',
]
