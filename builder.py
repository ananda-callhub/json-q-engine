"""
QueryLogic - Fluent Rule Builder

Build JSON rules using Pythonic syntax instead of raw JSON.

Example:
    from querylogic import Field, Rule
    
    # Simple
    rule = Field('city').equals('NYC')
    
    # Complex
    rule = (
        Field('city').equals('NYC') &
        Field('age').greater_than(18) &
        Field('tags').has_any(['vip', 'premium'])
    )
    
    # Nested
    rule = RuleBuilder.from_json(existing_json)
    
    # Get JSON
    json_rule = rule.to_json()
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
import re

from .core import Rule, RuleSet, Dependencies, Operator, Logic


__all__ = [
    'Field',
    'Condition',
    'Q',
    'RuleBuilder',
    'JsonRule',
    'AND',
    'OR',
    'NOT',
]


# =============================================================================
# Field Builder
# =============================================================================

class Field:
    """
    Fluent builder for field-based conditions.
    
    Usage:
        Field('city').equals('NYC')
        Field('age').greater_than(18)
        Field('tags').has_any(['vip'])
        Field('cf.123.number').greater_than(50000)
    """
    
    def __init__(self, name: str):
        """
        Initialize field reference.
        
        Args:
            name: Field name (e.g., 'city', 'tags', 'cf.123.number')
        """
        self.name = name
    
    # -------------------------------------------------------------------------
    # Comparison Operators
    # -------------------------------------------------------------------------
    
    def equals(self, value: Any) -> Condition:
        """Field == value"""
        return Condition(self.name, Operator.EQ, value)
    
    def eq(self, value: Any) -> Condition:
        """Alias for equals()"""
        return self.equals(value)
    
    def not_equals(self, value: Any) -> Condition:
        """Field != value"""
        return Condition(self.name, Operator.NE, value)
    
    def ne(self, value: Any) -> Condition:
        """Alias for not_equals()"""
        return self.not_equals(value)
    
    def greater_than(self, value: Any) -> Condition:
        """Field > value"""
        return Condition(self.name, Operator.GT, value)
    
    def gt(self, value: Any) -> Condition:
        """Alias for greater_than()"""
        return self.greater_than(value)
    
    def greater_or_equal(self, value: Any) -> Condition:
        """Field >= value"""
        return Condition(self.name, Operator.GTE, value)
    
    def gte(self, value: Any) -> Condition:
        """Alias for greater_or_equal()"""
        return self.greater_or_equal(value)
    
    def less_than(self, value: Any) -> Condition:
        """Field < value"""
        return Condition(self.name, Operator.LT, value)
    
    def lt(self, value: Any) -> Condition:
        """Alias for less_than()"""
        return self.less_than(value)
    
    def less_or_equal(self, value: Any) -> Condition:
        """Field <= value"""
        return Condition(self.name, Operator.LTE, value)
    
    def lte(self, value: Any) -> Condition:
        """Alias for less_or_equal()"""
        return self.less_or_equal(value)
    
    # -------------------------------------------------------------------------
    # String Operators
    # -------------------------------------------------------------------------
    
    def contains(self, value: str) -> Condition:
        """Field contains substring"""
        return Condition(self.name, Operator.CONTAINS, value)
    
    def startswith(self, value: str) -> Condition:
        """Field starts with value"""
        return Condition(self.name, Operator.STARTS_WITH, value)
    
    def endswith(self, value: str) -> Condition:
        """Field ends with value"""
        return Condition(self.name, Operator.ENDS_WITH, value)
    
    def is_empty(self) -> Condition:
        """Field is empty or null"""
        return Condition(self.name, Operator.IS_EMPTY, None)
    
    def is_not_empty(self) -> Condition:
        """Field is not empty"""
        return Condition(self.name, Operator.IS_NOT_EMPTY, None)
    
    # -------------------------------------------------------------------------
    # Array/M2M Operators
    # -------------------------------------------------------------------------
    
    def has_any(self, values: List[Any]) -> Condition:
        """
        Field contains ANY of the values (M2M).
        
        For tags/phonebooks: contact has at least one of these.
        """
        return Condition(self.name, Operator.SOME, values)
    
    def has_all(self, values: List[Any]) -> Condition:
        """
        Field contains ALL of the values (M2M).
        
        For tags/phonebooks: contact has all of these.
        """
        return Condition(self.name, Operator.ALL, values)
    
    def has_none(self, values: List[Any]) -> Condition:
        """
        Field contains NONE of the values (M2M).
        
        For tags/phonebooks: contact has none of these.
        """
        return Condition(self.name, Operator.NONE, values)
    
    def is_in(self, values: List[Any]) -> Condition:
        """Field value is in list"""
        return Condition(self.name, Operator.IN, values)
    
    # -------------------------------------------------------------------------
    # Comparison Sugar
    # -------------------------------------------------------------------------
    
    def __eq__(self, value: Any) -> Condition:
        """Enable: Field('city') == 'NYC'"""
        return self.equals(value)
    
    def __ne__(self, value: Any) -> Condition:
        """Enable: Field('city') != 'LA'"""
        return self.not_equals(value)
    
    def __gt__(self, value: Any) -> Condition:
        """Enable: Field('age') > 18"""
        return self.greater_than(value)
    
    def __ge__(self, value: Any) -> Condition:
        """Enable: Field('age') >= 18"""
        return self.greater_or_equal(value)
    
    def __lt__(self, value: Any) -> Condition:
        """Enable: Field('age') < 65"""
        return self.less_than(value)
    
    def __le__(self, value: Any) -> Condition:
        """Enable: Field('age') <= 65"""
        return self.less_or_equal(value)


# =============================================================================
# Condition (Single Rule)
# =============================================================================

class Condition(Rule):
    """
    A single condition representing a field comparison.
    
    This is the leaf node in a rule tree.
    """
    
    # M2M field names that use array operators
    M2M_FIELDS = {'tags', 'phonebooks', 'sms_campaigns', 'power_campaigns'}
    
    def __init__(self, field: str, operator: Operator, value: Any):
        self.field = field
        self.operator = operator
        self.value = value
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JsonLogic format."""
        var = {"var": self.field}
        
        # Array operators (M2M)
        if self.operator == Operator.SOME:
            values = self._normalize_values(self.value)
            return {"some": [var, {"in": [{"var": ""}, values]}]}
        
        if self.operator == Operator.NONE:
            values = self._normalize_values(self.value)
            return {"none": [var, {"in": [{"var": ""}, values]}]}
        
        if self.operator == Operator.ALL:
            # ALL requires special handling - every value must be present
            values = self._normalize_values(self.value)
            conditions = [
                {"some": [var, {"==": [{"var": ""}, v]}]}
                for v in values
            ]
            return {"and": conditions} if len(conditions) > 1 else conditions[0]
        
        # String contains (in JsonLogic: needle in haystack)
        if self.operator == Operator.CONTAINS:
            return {"in": [self.value, var]}
        
        if self.operator == Operator.IN:
            return {"in": [var, self.value]}
        
        # Empty checks
        if self.operator == Operator.IS_EMPTY:
            return {"or": [
                {"==": [var, None]},
                {"==": [var, ""]}
            ]}
        
        if self.operator == Operator.IS_NOT_EMPTY:
            return {"and": [
                {"!=": [var, None]},
                {"!=": [var, ""]}
            ]}
        
        # Custom string operators
        if self.operator in (Operator.STARTS_WITH, Operator.ENDS_WITH):
            return {self.operator.value: [var, self.value]}
        
        # Standard comparison
        return {self.operator.value: [var, self.value]}
    
    def _normalize_values(self, values: Any) -> List[str]:
        """Ensure values are a list of strings."""
        if not isinstance(values, (list, tuple)):
            values = [values]
        return [str(v) for v in values]
    
    def get_dependencies(self) -> Dependencies:
        """Extract dependencies from this condition."""
        deps = Dependencies()
        
        if self.field == 'tags' and self.operator in (Operator.SOME, Operator.NONE, Operator.ALL):
            for v in self._normalize_values(self.value):
                try:
                    deps.tag_ids.add(int(v))
                except ValueError:
                    pass
        
        elif self.field == 'phonebooks' and self.operator in (Operator.SOME, Operator.NONE, Operator.ALL):
            for v in self._normalize_values(self.value):
                try:
                    deps.phonebook_ids.add(int(v))
                except ValueError:
                    pass
        
        elif self.field.startswith('cf.'):
            # Custom field: cf.123.number
            match = re.match(r'^cf\.(\d+)\.\w+$', self.field)
            if match:
                deps.custom_field_ids.add(int(match.group(1)))
        
        else:
            deps.fields.add(self.field)
        
        return deps
    
    def __repr__(self) -> str:
        return f"Condition({self.field} {self.operator.value} {self.value!r})"


# =============================================================================
# Q - Django-Style Shorthand
# =============================================================================

class Q(Rule):
    """
    Django-style Q object for building rules.
    
    Usage:
        Q(city='NYC')
        Q(age__gt=18)
        Q(tags__has_any=['vip'])
        
        Q(city='NYC') & Q(age__gt=18)
        Q(city='NYC') | Q(city='LA')
        ~Q(status='blocked')
    """
    
    # Operator suffixes
    OPERATORS = {
        'eq': Operator.EQ,
        'ne': Operator.NE,
        'gt': Operator.GT,
        'gte': Operator.GTE,
        'lt': Operator.LT,
        'lte': Operator.LTE,
        'contains': Operator.CONTAINS,
        'startswith': Operator.STARTS_WITH,
        'endswith': Operator.ENDS_WITH,
        'in': Operator.IN,
        'has_any': Operator.SOME,
        'has_all': Operator.ALL,
        'has_none': Operator.NONE,
        'is_empty': Operator.IS_EMPTY,
        'is_not_empty': Operator.IS_NOT_EMPTY,
    }
    
    def __init__(self, **kwargs):
        """
        Build condition from kwargs.
        
        Args:
            **kwargs: field__operator=value pairs
        """
        if len(kwargs) != 1:
            raise ValueError("Q() requires exactly one keyword argument")
        
        key, value = list(kwargs.items())[0]
        self.field, self.operator, self.value = self._parse_kwarg(key, value)
        self._condition = Condition(self.field, self.operator, self.value)
    
    def _parse_kwarg(self, key: str, value: Any) -> tuple:
        """Parse field__operator=value into components."""
        parts = key.split('__')
        
        if len(parts) == 1:
            # Simple: city='NYC' -> equals
            return parts[0], Operator.EQ, value
        
        field = '__'.join(parts[:-1])
        op_str = parts[-1]
        
        if op_str in self.OPERATORS:
            return field, self.OPERATORS[op_str], value
        
        # Unknown operator suffix - treat as field name
        return key, Operator.EQ, value
    
    def to_json(self) -> Dict[str, Any]:
        return self._condition.to_json()
    
    def get_dependencies(self) -> Dependencies:
        return self._condition.get_dependencies()
    
    def __repr__(self) -> str:
        return f"Q({self.field}__{self.operator.name.lower()}={self.value!r})"


# =============================================================================
# Helper Functions
# =============================================================================

def AND(*rules: Rule) -> RuleSet:
    """Combine rules with AND logic."""
    return RuleSet(Logic.AND, list(rules))


def OR(*rules: Rule) -> RuleSet:
    """Combine rules with OR logic."""
    return RuleSet(Logic.OR, list(rules))


def NOT(rule: Rule) -> RuleSet:
    """Negate a rule."""
    return RuleSet(Logic.NOT, [rule])


# =============================================================================
# JsonRule - Wrapper for Raw JSON
# =============================================================================

class JsonRule(Rule):
    """
    Wrapper for raw JSON rules.
    
    Use when you have existing JSON and want to use it with the builder API.
    
    Usage:
        # Wrap existing JSON
        json_rule = JsonRule({"==": [{"var": "city"}, "NYC"]})
        
        # Combine with builder rules
        combined = json_rule & Field('age').gt(18)
        
        # Get JSON back
        combined.to_json()
    """
    
    def __init__(self, json_data: Dict[str, Any]):
        """
        Initialize with JSON rule data.
        
        Args:
            json_data: Raw JsonLogic dict
        """
        self._json = json_data
        self._deps = None
    
    def to_json(self) -> Dict[str, Any]:
        """Return the wrapped JSON."""
        return self._json
    
    def get_dependencies(self) -> Dependencies:
        """Extract dependencies from the JSON rule."""
        if self._deps is None:
            self._deps = self._extract_deps(self._json)
        return self._deps
    
    def _extract_deps(self, rules: Any) -> Dependencies:
        """Recursively extract dependencies."""
        deps = Dependencies()
        
        if not isinstance(rules, dict):
            return deps
        
        for key, value in rules.items():
            if key == 'var' and isinstance(value, str):
                self._add_field_dep(value, deps)
            
            elif key in ('some', 'none', 'all') and isinstance(value, list):
                if len(value) >= 2:
                    # Extract field
                    if isinstance(value[0], dict) and 'var' in value[0]:
                        field = value[0]['var']
                        # Extract IDs from condition
                        ids = self._extract_ids(value[1])
                        self._add_m2m_deps(field, ids, deps)
                    deps = deps.merge(self._extract_deps(value[1]))
            
            elif isinstance(value, list):
                for item in value:
                    deps = deps.merge(self._extract_deps(item))
            
            elif isinstance(value, dict):
                deps = deps.merge(self._extract_deps(value))
        
        return deps
    
    def _add_field_dep(self, field: str, deps: Dependencies) -> None:
        """Add field to dependencies."""
        if not field or field == '':
            return
        
        if field.startswith('cf.'):
            match = re.match(r'^cf\.(\d+)\.\w+$', field)
            if match:
                deps.custom_field_ids.add(int(match.group(1)))
        elif field not in ('tags', 'phonebooks'):
            deps.fields.add(field)
    
    def _extract_ids(self, condition: Any) -> List[int]:
        """Extract IDs from M2M condition."""
        ids = []
        if isinstance(condition, dict) and 'in' in condition:
            in_ops = condition['in']
            if isinstance(in_ops, list) and len(in_ops) == 2:
                values = in_ops[1]
                if isinstance(values, list):
                    for v in values:
                        try:
                            ids.append(int(v))
                        except (ValueError, TypeError):
                            pass
        return ids
    
    def _add_m2m_deps(self, field: str, ids: List[int], deps: Dependencies) -> None:
        """Add M2M IDs to dependencies."""
        for id_val in ids:
            if field == 'tags':
                deps.tag_ids.add(id_val)
            elif field == 'phonebooks':
                deps.phonebook_ids.add(id_val)
    
    def __repr__(self) -> str:
        return f"JsonRule({self._json})"


# =============================================================================
# RuleBuilder - Factory for Building Rules
# =============================================================================

class RuleBuilder:
    """
    Factory class for building rules from various sources.
    
    Usage:
        # From JSON
        rule = RuleBuilder.from_json({"==": [{"var": "city"}, "NYC"]})
        
        # Nested building
        rule = RuleBuilder.and_(
            RuleBuilder.field('city').equals('NYC'),
            RuleBuilder.or_(
                RuleBuilder.field('state').equals('NY'),
                RuleBuilder.field('state').equals('CA'),
            ),
            RuleBuilder.field('tags').has_any(['vip']),
        )
        
        # Parse frontend format
        rule = RuleBuilder.from_frontend(frontend_rules)
    """
    
    @staticmethod
    def field(name: str) -> Field:
        """Create a Field builder."""
        return Field(name)
    
    @staticmethod
    def from_json(json_data: Dict[str, Any]) -> JsonRule:
        """
        Create a rule from raw JSON.
        
        Args:
            json_data: Raw JsonLogic dict
            
        Returns:
            JsonRule that can be combined with other rules
        """
        return JsonRule(json_data)
    
    @staticmethod
    def and_(*rules: Rule) -> RuleSet:
        """Create AND combination."""
        return RuleSet(Logic.AND, list(rules))
    
    @staticmethod
    def or_(*rules: Rule) -> RuleSet:
        """Create OR combination."""
        return RuleSet(Logic.OR, list(rules))
    
    @staticmethod
    def not_(rule: Rule) -> RuleSet:
        """Create NOT rule."""
        return RuleSet(Logic.NOT, [rule])
    
    @staticmethod
    def nested(logic: str, *rules: Rule) -> RuleSet:
        """
        Create nested rule structure.
        
        Args:
            logic: 'and', 'or', or 'not'
            *rules: Child rules
            
        Returns:
            RuleSet
        """
        logic_map = {'and': Logic.AND, 'or': Logic.OR, 'not': Logic.NOT}
        return RuleSet(logic_map.get(logic.lower(), Logic.AND), list(rules))
    
    @staticmethod
    def from_frontend(frontend_rules: Dict) -> Rule:
        """
        Parse frontend rule builder format to Rule.
        
        Args:
            frontend_rules: Frontend format dict with condition/rules/children
            
        Returns:
            Rule object
            
        Frontend format:
            {
                "condition": "AND",
                "rules": [
                    {"field": "contact_fields", "contact_field": "city", "operator": "is", "value": "NYC"}
                ],
                "children": [...]
            }
        """
        return RuleBuilder._parse_frontend_ruleset(frontend_rules)
    
    @staticmethod
    def _parse_frontend_ruleset(ruleset: Dict) -> Rule:
        """Parse frontend ruleset recursively."""
        condition = ruleset.get('condition', 'AND').lower()
        children = ruleset.get('children', [])
        rules = ruleset.get('rules', [])
        
        parsed = []
        
        # Parse nested rulesets
        for child in children:
            parsed_child = RuleBuilder._parse_frontend_ruleset(child)
            if parsed_child:
                parsed.append(parsed_child)
        
        # Parse individual rules
        for rule in rules:
            parsed_rule = RuleBuilder._parse_frontend_rule(rule)
            if parsed_rule:
                parsed.append(parsed_rule)
        
        if not parsed:
            return JsonRule({})
        
        if len(parsed) == 1:
            return parsed[0]
        
        logic = Logic.AND if condition == 'and' else Logic.OR
        return RuleSet(logic, parsed)
    
    @staticmethod
    def _parse_frontend_rule(rule: Dict) -> Optional[Rule]:
        """Parse single frontend rule to Condition."""
        field_type = rule.get('field')
        operator = rule.get('operator')
        value = rule.get('value')
        
        if not field_type or not operator:
            return None
        
        # Determine field name
        field_name = RuleBuilder._get_field_name(rule)
        if not field_name:
            return None
        
        # Map operator
        field = Field(field_name)
        
        # M2M fields
        if field_name in ('tags', 'phonebooks'):
            if operator in ('in', 'equals', 'is'):
                return field.has_any([value] if not isinstance(value, list) else value)
            if operator in ('not_in', 'not_equals', 'is_not'):
                return field.has_none([value] if not isinstance(value, list) else value)
        
        # Standard operators
        op_map = {
            'equals': 'equals', 'is': 'equals',
            'not_equals': 'not_equals', 'is_not': 'not_equals',
            'greater': 'gt', 'greater_than': 'gt',
            'less': 'lt', 'less_than': 'lt',
            'greater_or_equal': 'gte',
            'less_or_equal': 'lte',
            'contains': 'contains',
            'not_contains': 'not_contains',
            'starts_with': 'startswith',
            'ends_with': 'endswith',
        }
        
        method_name = op_map.get(operator, 'equals')
        method = getattr(field, method_name, field.equals)
        
        return method(value)
    
    @staticmethod
    def _get_field_name(rule: Dict) -> Optional[str]:
        """Extract field name from frontend rule."""
        field_type = rule.get('field')
        
        if field_type in ('phonebook', 'list', 'lists', 'phonebooks'):
            return 'phonebooks'
        if field_type in ('tag', 'tags'):
            return 'tags'
        if field_type == 'contact_fields':
            if rule.get('custom'):
                field_id = rule.get('field_id')
                input_type = str(rule.get('input_type', '1'))
                type_map = {'1': 'text', '2': 'number', '3': 'boolean', '4': 'multichoice'}
                return f"cf.{field_id}.{type_map.get(input_type, 'text')}"
            else:
                return rule.get('contact_field')
        
        return field_type
