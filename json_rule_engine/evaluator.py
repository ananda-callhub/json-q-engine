"""
Unified Rule Engine with all functionality in a single class.

This refactored version eliminates standalone functions and provides
a consistent, discoverable API through the RuleEngine class.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Callable, Union, Tuple
import time
import re

from .core import Rule, RuleEntity, EvaluationResult, RuleFields, DependencyConfig

# Conditional Django import
try:
    from django.db.models import Q as DjangoQ
    HAS_DJANGO = True
except ImportError:
    HAS_DJANGO = False
    DjangoQ = None


class RuleEngine:
    """
    Unified Rule Engine with evaluation, Django Q conversion, and dependency extraction.
    
    This single class provides all rule engine functionality in a consistent,
    discoverable API without the confusion of multiple standalone functions.
    
    Examples:
        >>> engine = RuleEngine()
        >>> 
        >>> # Evaluation
        >>> result = engine.evaluate(rule, data)
        >>> matches = engine.filter(rule, objects)
        >>> 
        >>> # Django Q conversion (if Django available)
        >>> q = engine.to_q(rule)
        >>> contacts = Contact.objects.filter(q)
        >>> 
        >>> # Dependency extraction
        >>> deps = engine.get_dependencies(rule)
        >>> 
        >>> # Custom configuration
        >>> config = DependencyConfig(id_fields={'categories': 'category_ids'})
        >>> engine_with_config = RuleEngine(dependency_config=config)
    """
    
    def __init__(
        self, 
        dependency_config: Optional[DependencyConfig] = None,
        django_field_map: Optional[Dict[str, str]] = None
    ):
        """
        Initialize rule engine with optional configuration.
        
        Args:
            dependency_config: Custom dependency extraction configuration
            django_field_map: Custom field mappings for Django Q conversion
        """
        self._custom_ops: Dict[str, Callable] = {}
        self._dependency_config = dependency_config or DependencyConfig()
        self._django_field_map = django_field_map or self._get_default_django_fields()
        
        if HAS_DJANGO:
            self._q_translator = None
    
    def _get_default_django_fields(self) -> Dict[str, str]:
        """Get default Django field mappings."""
        return {
            'tags': 'tags__id',
            'phonebooks': 'phonebooks__id',
            'sms_campaigns': 'smscampaignsubscriber__sms_campaign_id',
            'power_campaigns': 'powersubscriber__campaign_id',
            'first_name': 'first_name',
            'last_name': 'last_name',
            'email': 'email',
            'city': 'city',
            'state': 'state',
            'zipcode': 'zipcode',
            'country': 'country',
        }
    
    # =========================================================================
    # Rule Evaluation
    # =========================================================================
    
    def evaluate(self, rules: Union[Dict, Rule], data: Dict[str, Any]) -> Any:
        """
        Evaluate rules against a data dictionary.
        
        Args:
            rules: JsonLogic dict or Rule object
            data: Data dictionary with field values
            
        Returns:
            Evaluation result (typically bool)
        """
        if isinstance(rules, Rule):
            rules = rules.to_json()
        return self._eval(rules, data)
    
    def matches(self, rules: Union[Dict, Rule], data: Dict[str, Any]) -> bool:
        """
        Check if data matches rules (returns bool).
        
        Args:
            rules: JsonLogic dict or Rule object
            data: Data dictionary
            
        Returns:
            True if matches, False otherwise
        """
        return bool(self.evaluate(rules, data))
    
    def test(self, rules: Union[Dict, Rule], obj: RuleEntity) -> EvaluationResult:
        """
        Test rules against an Evaluatable object.
        
        Args:
            rules: JsonLogic dict or Rule object
            obj: Object implementing Evaluatable interface
            
        Returns:
            EvalResult with match status and timing
        """
        start = time.perf_counter()
        
        if isinstance(rules, Rule):
            rules = rules.to_json()
        
        data = obj.to_eval_dict()
        matches = bool(self._eval(rules, data))
        
        elapsed = (time.perf_counter() - start) * 1000
        
        return EvaluationResult(matches=matches, eval_time_ms=elapsed)
    
    def batch(
        self, 
        rules: Union[Dict, Rule], 
        objects: List[RuleEntity]
    ) -> Dict[str, List]:
        """
        Evaluate rules against multiple objects.
        
        Args:
            rules: JsonLogic dict or Rule object
            objects: List of Evaluatable objects
            
        Returns:
            Dict with 'matches' and 'non_matches' lists
        """
        if isinstance(rules, Rule):
            rules = rules.to_json()
        
        matches = []
        non_matches = []
        
        for obj in objects:
            data = obj.to_eval_dict()
            if self._eval(rules, data):
                matches.append(obj)
            else:
                non_matches.append(obj)
        
        return {'matches': matches, 'non_matches': non_matches}
    
    def filter(
        self, 
        rules: Union[Dict, Rule], 
        objects: List[RuleEntity]
    ) -> List[RuleEntity]:
        """
        Filter objects that match the rules.
        
        Args:
            rules: JsonLogic dict or Rule object
            objects: List of Evaluatable objects
            
        Returns:
            List of matching objects
        """
        return self.batch(rules, objects)['matches']
    
    # =========================================================================
    # Django Q Conversion
    # =========================================================================
    
    def to_q(self, rules: Union[Dict, Rule]) -> DjangoQ:
        """
        Convert rules to Django Q object.
        
        Args:
            rules: JsonLogic dict or Rule object
            
        Returns:
            Django Q object
            
        Raises:
            ImportError: If Django is not installed
        """
        if not HAS_DJANGO:
            raise ImportError("Django is required for Q object conversion. Install with: pip install django")
        
        if self._q_translator is None:
            from .django_q import QTranslator
            self._q_translator = QTranslator(field_map=self._django_field_map)
        
        return self._q_translator.translate(rules)
    
    def to_q_with_explanation(self, rules: Union[Dict, Rule]) -> Tuple[DjangoQ, str]:
        """
        Convert rules to Django Q object with human-readable explanation.
        
        Args:
            rules: JsonLogic dict or Rule object
            
        Returns:
            Tuple of (Q object, explanation string)
        """
        if not HAS_DJANGO:
            raise ImportError("Django is required for Q object conversion.")
        
        from .django_q import JsonToQ
        converter = JsonToQ(field_map=self._django_field_map)
        
        if isinstance(rules, Rule):
            rules = rules.to_json()
        
        return converter.convert_with_explanation(rules)
    
    def validate_json_rules(self, json_rules: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate JSON rules structure.
        
        Args:
            json_rules: Raw JsonLogic dict
            
        Returns:
            Tuple of (is_valid, list of errors)
        """
        if not HAS_DJANGO:
            raise ImportError("Django is required for rule validation.")
        
        from .django_q import JsonToQ
        converter = JsonToQ()
        return converter.validate(json_rules)
    
    # =========================================================================
    # Dependency Extraction
    # =========================================================================
    
    def get_dependencies(self, rules: Union[Dict, Rule]) -> RuleFields:
        """
        Extract dependencies from rules.
        
        Args:
            rules: JsonLogic dict or Rule object
            
        Returns:
            Dependencies object with extracted field and ID references
        """
        if isinstance(rules, Rule):
            return rules.get_dependencies(self._dependency_config)
        else:
            # Handle raw JSON rules
            from .builder import JsonRule
            json_rule = JsonRule(rules)
            return json_rule.get_dependencies(self._dependency_config)
    
    def configure_dependencies(self, config: DependencyConfig) -> 'RuleEngine':
        """
        Update dependency extraction configuration.
        
        Args:
            config: New dependency configuration
            
        Returns:
            Self for chaining
        """
        self._dependency_config = config
        return self
    
    # =========================================================================
    # Custom Operators
    # =========================================================================
    
    def register_operator(self, name: str, func: Callable) -> 'RuleEngine':
        """
        Register a custom operator.
        
        Args:
            name: Operator name (e.g., 'between', 'regex_match')
            func: Function(values, data) -> result
            
        Returns:
            Self for chaining
        """
        self._custom_ops[name] = func
        return self
    
    # =========================================================================
    # Configuration
    # =========================================================================
    
    def configure_django_fields(self, field_map: Dict[str, str]) -> 'RuleEngine':
        """
        Update Django field mappings.
        
        Args:
            field_map: Custom field name to Django ORM path mapping
            
        Returns:
            Self for chaining
        """
        self._django_field_map = {**self._django_field_map, **field_map}
        # Reset Q translator to use new mappings
        self._q_translator = None
        return self
    
    # =========================================================================
    # Internal Evaluation (same as before)
    # =========================================================================
    
    def _eval(self, rules: Any, data: Any) -> Any:
        """Recursively evaluate JsonLogic (implementation same as original)."""
        # ... [Same implementation as original RuleEngine._eval]
        # [Keeping this short for brevity but would include full implementation]
        if rules is None or not isinstance(rules, dict):
            return rules
        
        if not rules:
            return True
        
        op = list(rules.keys())[0]
        operands = rules[op]
        
        if not isinstance(operands, (list, tuple)):
            operands = [operands]
        
        if op == 'var':
            return self._op_var(operands, data)
        
        if op in ('some', 'all', 'none'):
            return self._op_array(op, operands, data)
        
        if op == 'if':
            return self._op_if(operands, data)
        
        values = [self._eval(o, data) for o in operands]
        
        if op in self._custom_ops:
            return self._custom_ops[op](values, data)
        
        return self._apply_op(op, values)
    
    def _op_var(self, operands: List, data: Any) -> Any:
        """Variable access operator."""
        if not operands:
            return data
        
        var_name = self._eval(operands[0], data)
        default = operands[1] if len(operands) > 1 else None
        
        if var_name == "" or var_name is None:
            return data
        
        if isinstance(data, dict):
            return data.get(var_name, default)
        
        return default
    
    def _op_array(self, op: str, operands: List, data: Any) -> bool:
        """Array operators: some, all, none."""
        if len(operands) != 2:
            return op != 'some'
        
        array = self._eval(operands[0], data)
        condition = operands[1]
        
        if not isinstance(array, (list, tuple)):
            return op == 'none'
        
        if len(array) == 0:
            return op != 'some' and op != 'all'
        
        for item in array:
            result = self._eval(condition, item)
            
            if op == 'some' and result:
                return True
            if op == 'all' and not result:
                return False
            if op == 'none' and result:
                return False
        
        return op != 'some'
    
    def _op_if(self, operands: List, data: Any) -> Any:
        """If/then/else operator."""
        i = 0
        while i < len(operands) - 1:
            if self._eval(operands[i], data):
                return self._eval(operands[i + 1], data)
            i += 2
        
        if len(operands) % 2 == 1:
            return self._eval(operands[-1], data)
        
        return None
    
    def _apply_op(self, op: str, values: List) -> Any:
        """Apply standard operators."""
        # Logic
        if op == 'and':
            return all(values)
        if op == 'or':
            return any(values)
        if op == '!':
            return not values[0] if values else True
        
        # Comparison
        if len(values) >= 2:
            a, b = values[0], values[1]
            if op == '==':
                return self._soft_eq(a, b)
            if op == '!=':
                return not self._soft_eq(a, b)
            if op == '>':
                if a is None or b is None:
                    return False
                return self._compare(a, b) > 0
            if op == '>=':
                if a is None or b is None:
                    return False
                return self._compare(a, b) >= 0
            if op == '<':
                if a is None or b is None:
                    return False
                return self._compare(a, b) < 0
            if op == '<=':
                if a is None or b is None:
                    return False
                return self._compare(a, b) <= 0
        
        # String/Array
        if op == 'in':
            if len(values) >= 2:
                needle, haystack = values[0], values[1]
                if haystack is None:
                    return False
                if isinstance(haystack, str):
                    return str(needle).lower() in haystack.lower()
                return needle in haystack
            return False
        
        if op == 'cat':
            return ''.join(str(v) for v in values)
        
        # Custom string operators
        if op == '_contains':
            if len(values) >= 2:
                return str(values[1]).lower() in str(values[0]).lower() if values[0] else False
            return False
        
        if op == '_startswith':
            if len(values) >= 2:
                return str(values[0]).lower().startswith(str(values[1]).lower()) if values[0] else False
            return False
        
        if op == '_endswith':
            if len(values) >= 2:
                return str(values[0]).lower().endswith(str(values[1]).lower()) if values[0] else False
            return False
        
        if op == '_is_empty':
            v = values[0] if values else None
            return v is None or v == '' or v == []
        
        if op == '_is_not_empty':
            v = values[0] if values else None
            return v is not None and v != '' and v != []
        
        # Arithmetic
        if op == '+':
            if len(values) == 1:
                return float(values[0])
            return sum(float(v) for v in values)
        if op == '-':
            if len(values) == 1:
                return -float(values[0])
            return float(values[0]) - sum(float(v) for v in values[1:])
        if op == '*':
            result = 1
            for v in values:
                result *= float(v)
            return result
        if op == '/':
            if len(values) >= 2 and float(values[1]) != 0:
                return float(values[0]) / float(values[1])
            return 0
        if op == '%':
            if len(values) >= 2:
                return float(values[0]) % float(values[1])
            return 0
        if op == 'min':
            return min(values)
        if op == 'max':
            return max(values)
        
        # Array
        if op == 'merge':
            result = []
            for v in values:
                if isinstance(v, (list, tuple)):
                    result.extend(v)
                else:
                    result.append(v)
            return result
        
        if op == 'missing':
            return [v for v in values if v not in data or data.get(v) in (None, '')]
        
        # Ternary
        if op == '?:':
            if len(values) >= 3:
                return values[1] if values[0] else values[2]
            return None
        
        return None
    
    def _soft_eq(self, a: Any, b: Any) -> bool:
        """JavaScript-like soft equality."""
        if a is None and b is None:
            return True
        if a is None or b is None:
            return False
        
        if isinstance(a, str) and isinstance(b, (int, float)):
            try:
                return float(a) == b
            except ValueError:
                return False
        if isinstance(b, str) and isinstance(a, (int, float)):
            try:
                return a == float(b)
            except ValueError:
                return False
        
        return a == b
    
    def _compare(self, a: Any, b: Any) -> int:
        """Compare two values, returns -1, 0, or 1."""
        try:
            a_num = float(a)
            b_num = float(b)
            if a_num < b_num:
                return -1
            if a_num > b_num:
                return 1
            return 0
        except (ValueError, TypeError):
            if str(a) < str(b):
                return -1
            if str(a) > str(b):
                return 1
            return 0