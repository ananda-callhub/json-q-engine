"""
QueryLogic - Django Q Object Translator

Convert JSON rules to Django Q objects for database queries.

Example:
    from querylogic import to_q, json_to_q, QTranslator
    
    # From JSON dict directly
    q = json_to_q({"==": [{"var": "city"}, "NYC"]})
    
    # From Rule builder
    rule = Field('city').equals('NYC') & Field('age').gt(18)
    q = to_q(rule)
    
    # Nested JSON to nested Q
    nested_json = {
        "and": [
            {"==": [{"var": "city"}, "NYC"]},
            {"or": [
                {"==": [{"var": "state"}, "NY"]},
                {"==": [{"var": "state"}, "CA"]}
            ]}
        ]
    }
    q = json_to_q(nested_json)
    # Result: Q(city="NYC") & (Q(state="NY") | Q(state="CA"))
    
    # Custom field mappings
    translator = QTranslator(field_map={'tags': 'tags__id'})
    q = translator.translate(rules)
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Union, Tuple
import re

from .core import Rule

# Conditional Django import
try:
    from django.db.models import Q as DjangoQ
    HAS_DJANGO = True
except ImportError:
    HAS_DJANGO = False
    DjangoQ = None


__all__ = [
    'QTranslator',
    'to_q',
    'json_to_q',
    'JsonToQ',
]


# =============================================================================
# Default Field Mappings
# =============================================================================

DEFAULT_FIELD_MAP = {
    # M2M relationships
    'tags': 'tags__id',
    'phonebooks': 'phonebooks__id',
    'sms_campaigns': 'smscampaignsubscriber__sms_campaign_id',
    'power_campaigns': 'powersubscriber__campaign_id',
    
    # Standard fields (passthrough)
    'first_name': 'first_name',
    'last_name': 'last_name',
    'email': 'email',
    'contact': 'contact',
    'mobile': 'mobile',
    'city': 'city',
    'state': 'state',
    'zipcode': 'zipcode',
    'country': 'country',
    'address': 'address',
    'company_name': 'company_name',
}


# =============================================================================
# Q Translator
# =============================================================================

class QTranslator:
    """
    Translates JsonLogic rules to Django Q objects.
    
    Example:
        translator = QTranslator()
        q = translator.translate({"==": [{"var": "city"}, "NYC"]})
        # Returns: Q(city="NYC")
        
        # Custom field mapping
        translator = QTranslator(field_map={'status': 'profile__status'})
    """
    
    def __init__(
        self,
        field_map: Optional[Dict[str, str]] = None,
        custom_field_base: str = 'contactcustomfieldvalues'
    ):
        """
        Initialize translator.
        
        Args:
            field_map: Custom field name to Django ORM path mapping
            custom_field_base: Base path for custom fields
        """
        if not HAS_DJANGO:
            raise ImportError("Django is required for QTranslator")
        
        self._field_map = {**DEFAULT_FIELD_MAP, **(field_map or {})}
        self._cf_base = custom_field_base
    
    def translate(self, rules: Union[Dict, Rule]) -> DjangoQ:
        """
        Translate rules to Django Q object.
        
        Args:
            rules: JsonLogic dict or Rule object
            
        Returns:
            Django Q object
        """
        if isinstance(rules, Rule):
            rules = rules.to_json()
        
        if not rules:
            return DjangoQ()
        
        return self._parse(rules)
    
    # -------------------------------------------------------------------------
    # Internal Parsing
    # -------------------------------------------------------------------------
    
    def _parse(self, logic: Any) -> DjangoQ:
        """Recursively parse JsonLogic to Q."""
        if not isinstance(logic, dict) or not logic:
            return DjangoQ()
        
        op = list(logic.keys())[0]
        operands = logic[op]
        
        # Logic operators
        if op == 'and':
            return self._and(operands)
        if op == 'or':
            return self._or(operands)
        if op == '!':
            return self._not(operands)
        
        # Array operators (M2M)
        if op == 'some':
            return self._some(operands)
        if op == 'none':
            return self._none(operands)
        if op == 'all':
            return self._all(operands)
        
        # Comparison
        if op == '==':
            return self._eq(operands)
        if op == '!=':
            return ~self._eq(operands)
        if op == '>':
            return self._cmp(operands, 'gt')
        if op == '>=':
            return self._cmp(operands, 'gte')
        if op == '<':
            return self._cmp(operands, 'lt')
        if op == '<=':
            return self._cmp(operands, 'lte')
        
        # String
        if op == 'in':
            return self._in(operands)
        if op == '_contains':
            return self._contains(operands)
        if op == '_startswith':
            return self._startswith(operands)
        if op == '_endswith':
            return self._endswith(operands)
        if op == '_is_empty':
            return self._is_empty(operands)
        if op == '_is_not_empty':
            return ~self._is_empty(operands)
        
        return DjangoQ()
    
    # -------------------------------------------------------------------------
    # Logic Operators
    # -------------------------------------------------------------------------
    
    def _and(self, operands: List) -> DjangoQ:
        """AND: combine with &"""
        q = DjangoQ()
        for operand in operands:
            q &= self._parse(operand)
        return q
    
    def _or(self, operands: List) -> DjangoQ:
        """OR: combine with |"""
        q = DjangoQ()
        first = True
        for operand in operands:
            if first:
                q = self._parse(operand)
                first = False
            else:
                q |= self._parse(operand)
        return q
    
    def _not(self, operand: Any) -> DjangoQ:
        """NOT: negate with ~"""
        return ~self._parse(operand)
    
    # -------------------------------------------------------------------------
    # Array Operators (M2M)
    # -------------------------------------------------------------------------
    
    def _some(self, operands: List) -> DjangoQ:
        """SOME: has any of values -> field__in"""
        if len(operands) != 2:
            return DjangoQ()
        
        field = self._get_var(operands[0])
        values = self._get_condition_values(operands[1])
        
        if not field:
            return DjangoQ()
        
        django_field = self._map_field(field)
        return DjangoQ(**{f'{django_field}__in': values})
    
    def _none(self, operands: List) -> DjangoQ:
        """NONE: has none of values -> ~field__in"""
        return ~self._some(operands)
    
    def _all(self, operands: List) -> DjangoQ:
        """ALL: has all values -> multiple ANDed conditions"""
        if len(operands) != 2:
            return DjangoQ()
        
        field = self._get_var(operands[0])
        values = self._get_condition_values(operands[1])
        
        if not field:
            return DjangoQ()
        
        django_field = self._map_field(field)
        
        # Each value must be present
        q = DjangoQ()
        for v in values:
            q &= DjangoQ(**{f'{django_field}': v})
        return q
    
    def _get_condition_values(self, condition: Any) -> List:
        """Extract values from M2M condition."""
        if not isinstance(condition, dict):
            return []
        
        if 'in' in condition:
            in_ops = condition['in']
            if isinstance(in_ops, list) and len(in_ops) == 2:
                return in_ops[1] if isinstance(in_ops[1], list) else [in_ops[1]]
        
        if '==' in condition:
            eq_ops = condition['==']
            if isinstance(eq_ops, list) and len(eq_ops) == 2:
                return [eq_ops[1]]
        
        return []
    
    # -------------------------------------------------------------------------
    # Comparison Operators
    # -------------------------------------------------------------------------
    
    def _eq(self, operands: List) -> DjangoQ:
        """Equality: field = value"""
        if len(operands) != 2:
            return DjangoQ()
        
        field = self._get_var(operands[0])
        value = operands[1]
        
        if not field:
            return DjangoQ()
        
        if field.startswith('cf.'):
            return self._cf_query(field, 'exact', value)
        
        django_field = self._map_field(field)
        return DjangoQ(**{django_field: value})
    
    def _cmp(self, operands: List, lookup: str) -> DjangoQ:
        """Comparison: gt, gte, lt, lte"""
        if len(operands) != 2:
            return DjangoQ()
        
        field = self._get_var(operands[0])
        value = operands[1]
        
        if not field:
            return DjangoQ()
        
        if field.startswith('cf.'):
            return self._cf_query(field, lookup, value)
        
        django_field = self._map_field(field)
        return DjangoQ(**{f'{django_field}__{lookup}': value})
    
    # -------------------------------------------------------------------------
    # String Operators
    # -------------------------------------------------------------------------
    
    def _in(self, operands: List) -> DjangoQ:
        """IN: substring check or membership"""
        if len(operands) != 2:
            return DjangoQ()
        
        needle = operands[0]
        haystack = operands[1]
        
        # String contains: {"in": ["needle", {"var": "field"}]}
        if isinstance(haystack, dict) and 'var' in haystack:
            field = haystack['var']
            if field.startswith('cf.'):
                return self._cf_query(field, 'icontains', needle)
            
            django_field = self._map_field(field)
            return DjangoQ(**{f'{django_field}__icontains': needle})
        
        # Membership: {"in": [{"var": "field"}, [values]]}
        if isinstance(needle, dict) and 'var' in needle:
            field = needle['var']
            django_field = self._map_field(field)
            return DjangoQ(**{f'{django_field}__in': haystack})
        
        return DjangoQ()
    
    def _contains(self, operands: List) -> DjangoQ:
        """Contains: field contains value"""
        if len(operands) != 2:
            return DjangoQ()
        
        field = self._get_var(operands[0])
        value = operands[1]
        
        if not field:
            return DjangoQ()
        
        if field.startswith('cf.'):
            return self._cf_query(field, 'icontains', value)
        
        django_field = self._map_field(field)
        return DjangoQ(**{f'{django_field}__icontains': value})
    
    def _startswith(self, operands: List) -> DjangoQ:
        """Starts with"""
        if len(operands) != 2:
            return DjangoQ()
        
        field = self._get_var(operands[0])
        value = operands[1]
        
        if not field:
            return DjangoQ()
        
        django_field = self._map_field(field)
        return DjangoQ(**{f'{django_field}__istartswith': value})
    
    def _endswith(self, operands: List) -> DjangoQ:
        """Ends with"""
        if len(operands) != 2:
            return DjangoQ()
        
        field = self._get_var(operands[0])
        value = operands[1]
        
        if not field:
            return DjangoQ()
        
        django_field = self._map_field(field)
        return DjangoQ(**{f'{django_field}__iendswith': value})
    
    def _is_empty(self, operands: List) -> DjangoQ:
        """Is empty or null"""
        if not operands:
            return DjangoQ()
        
        field = self._get_var(operands[0])
        if not field:
            return DjangoQ()
        
        django_field = self._map_field(field)
        return DjangoQ(**{f'{django_field}__isnull': True}) | DjangoQ(**{django_field: ''})
    
    # -------------------------------------------------------------------------
    # Custom Field Handling
    # -------------------------------------------------------------------------
    
    def _cf_query(self, field: str, lookup: str, value: Any) -> DjangoQ:
        """Build Q for custom field."""
        match = re.match(r'^cf\.(\d+)\.(\w+)$', field)
        if not match:
            return DjangoQ()
        
        field_id = int(match.group(1))
        field_type = match.group(2)
        
        # Map type to column
        column_map = {
            'text': 'value_text',
            'number': 'value_number',
            'boolean': 'value_boolean',
            'multichoice': 'value_multichoice',
        }
        column = column_map.get(field_type, 'value_text')
        
        # Build Q
        q = DjangoQ(**{f'{self._cf_base}__custom_field_id': field_id})
        
        if lookup == 'exact':
            q &= DjangoQ(**{f'{self._cf_base}__{column}': value})
        else:
            q &= DjangoQ(**{f'{self._cf_base}__{column}__{lookup}': value})
        
        return q
    
    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    
    def _get_var(self, expr: Any) -> Optional[str]:
        """Extract variable name from var expression."""
        if isinstance(expr, dict) and 'var' in expr:
            var = expr['var']
            return var[0] if isinstance(var, list) else var
        return None
    
    def _map_field(self, field: str) -> str:
        """Map field name to Django ORM path."""
        return self._field_map.get(field, field)


# =============================================================================
# Module-Level Functions
# =============================================================================

_default_translator: Optional[QTranslator] = None


def to_q(rules: Union[Dict, Rule], field_map: Optional[Dict] = None) -> DjangoQ:
    """
    Convert rules to Django Q object.
    
    Args:
        rules: JsonLogic dict or Rule object
        field_map: Optional custom field mappings
        
    Returns:
        Django Q object
    
    Example:
        # From Rule builder
        rule = Field('city').equals('NYC')
        q = to_q(rule)
        
        # From JSON
        q = to_q({"==": [{"var": "city"}, "NYC"]})
        
        contacts = Contact.objects.filter(q)
    """
    global _default_translator
    
    if field_map:
        translator = QTranslator(field_map=field_map)
        return translator.translate(rules)
    
    if _default_translator is None:
        _default_translator = QTranslator()
    
    return _default_translator.translate(rules)


def json_to_q(json_rules: Dict[str, Any], field_map: Optional[Dict] = None) -> DjangoQ:
    """
    Convert JSON rules directly to Django Q object.
    
    This is the explicit method for JSON → Q conversion.
    Supports nested JSON structures.
    
    Args:
        json_rules: Raw JsonLogic dict (can be nested)
        field_map: Optional custom field mappings
        
    Returns:
        Django Q object (nested structure preserved)
    
    Example:
        # Simple
        q = json_to_q({"==": [{"var": "city"}, "NYC"]})
        # Result: Q(city="NYC")
        
        # Nested AND/OR
        q = json_to_q({
            "and": [
                {"==": [{"var": "city"}, "NYC"]},
                {"or": [
                    {"==": [{"var": "state"}, "NY"]},
                    {"==": [{"var": "state"}, "CA"]}
                ]}
            ]
        })
        # Result: Q(city="NYC") & (Q(state="NY") | Q(state="CA"))
        
        # M2M
        q = json_to_q({
            "some": [{"var": "tags"}, {"in": [{"var": ""}, ["101", "102"]]}]
        })
        # Result: Q(tags__id__in=["101", "102"])
        
        # Usage
        contacts = Contact.objects.filter(q)
    """
    if not HAS_DJANGO:
        raise ImportError("Django is required for json_to_q")
    
    translator = QTranslator(field_map=field_map) if field_map else QTranslator()
    return translator.translate(json_rules)


# =============================================================================
# JsonToQ - Class-based JSON to Q Converter
# =============================================================================

class JsonToQ:
    """
    Class-based JSON to Django Q converter.
    
    Provides explicit methods for converting JSON rules to Q objects
    with full support for nested structures.
    
    Usage:
        converter = JsonToQ()
        
        # Simple conversion
        q = converter.convert({"==": [{"var": "city"}, "NYC"]})
        
        # With explanation
        q, explanation = converter.convert_with_explanation(json_rules)
        print(explanation)  # Shows Q structure
        
        # Validate before converting
        is_valid, errors = converter.validate(json_rules)
    """
    
    def __init__(self, field_map: Optional[Dict[str, str]] = None):
        """
        Initialize converter.
        
        Args:
            field_map: Custom field name to Django ORM path mapping
        """
        if not HAS_DJANGO:
            raise ImportError("Django is required for JsonToQ")
        
        self._translator = QTranslator(field_map=field_map)
    
    def convert(self, json_rules: Dict[str, Any]) -> DjangoQ:
        """
        Convert JSON rules to Django Q object.
        
        Args:
            json_rules: Raw JsonLogic dict
            
        Returns:
            Django Q object
        """
        return self._translator.translate(json_rules)
    
    def convert_with_explanation(
        self, 
        json_rules: Dict[str, Any]
    ) -> Tuple[DjangoQ, str]:
        """
        Convert JSON rules to Q with human-readable explanation.
        
        Args:
            json_rules: Raw JsonLogic dict
            
        Returns:
            Tuple of (Q object, explanation string)
        """
        q = self._translator.translate(json_rules)
        explanation = self._explain(json_rules, indent=0)
        return q, explanation
    
    def validate(self, json_rules: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate JSON rules structure.
        
        Args:
            json_rules: Raw JsonLogic dict
            
        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []
        self._validate_recursive(json_rules, errors, path='root')
        return len(errors) == 0, errors
    
    def _validate_recursive(
        self, 
        rules: Any, 
        errors: List[str], 
        path: str
    ) -> None:
        """Recursively validate rule structure."""
        if not isinstance(rules, dict):
            return
        
        if not rules:
            return
        
        op = list(rules.keys())[0]
        operands = rules[op]
        
        # Check known operators
        known_ops = {
            '==', '!=', '>', '>=', '<', '<=', '===', '!==',
            'and', 'or', '!', '!!',
            'var', 'if', '?:',
            'in', 'cat',
            'some', 'all', 'none', 'merge', 'missing',
            '+', '-', '*', '/', '%', 'min', 'max',
            '_contains', '_startswith', '_endswith', '_is_empty', '_is_not_empty',
        }
        
        if op not in known_ops:
            errors.append(f"Unknown operator '{op}' at {path}")
        
        # Validate operands
        if isinstance(operands, list):
            for i, operand in enumerate(operands):
                self._validate_recursive(operand, errors, f"{path}.{op}[{i}]")
        elif isinstance(operands, dict):
            self._validate_recursive(operands, errors, f"{path}.{op}")
    
    def _explain(self, rules: Any, indent: int) -> str:
        """Generate human-readable explanation of rules."""
        prefix = "  " * indent
        
        if not isinstance(rules, dict) or not rules:
            return f"{prefix}{rules}"
        
        op = list(rules.keys())[0]
        operands = rules[op]
        
        if op == 'var':
            var_name = operands if isinstance(operands, str) else operands[0]
            return f"{prefix}field({var_name})"
        
        if op in ('and', 'or'):
            lines = [f"{prefix}{op.upper()}:"]
            for operand in operands:
                lines.append(self._explain(operand, indent + 1))
            return "\n".join(lines)
        
        if op == '!':
            return f"{prefix}NOT:\n{self._explain(operands, indent + 1)}"
        
        if op in ('some', 'none', 'all'):
            field = operands[0].get('var', '?') if isinstance(operands[0], dict) else '?'
            return f"{prefix}{op.upper()}({field})"
        
        if op in ('==', '!=', '>', '>=', '<', '<='):
            left = self._explain(operands[0], 0).strip() if operands else '?'
            right = operands[1] if len(operands) > 1 else '?'
            return f"{prefix}{left} {op} {right}"
        
        return f"{prefix}{op}: {operands}"
