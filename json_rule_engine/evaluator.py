"""
Rule Engine - JSON rule evaluation engine.

Evaluates JsonLogic rules against data dictionaries or Evaluatable objects.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Callable, Union
import time

from .core import Rule, Evaluatable, EvalResult


__all__ = [
    'RuleEngine',
    'evaluate',
    'matches',
]


class RuleEngine:
    """
    JSON Rule evaluation engine.
    
    Evaluates JsonLogic rules against data dictionaries or Evaluatable objects.
    
    Examples:
        >>> engine = RuleEngine()
        >>> 
        >>> # Evaluate against dict
        >>> result = engine.evaluate(rules, {"city": "NYC"})
        >>> 
        >>> # Test against Evaluatable object
        >>> result = engine.test(rules, contact)
        >>> 
        >>> # Batch evaluation
        >>> results = engine.batch(rules, contacts)
        >>> 
        >>> # Filter matching objects
        >>> matches = engine.filter(rules, contacts)
        >>> 
        >>> # Custom operators
        >>> engine.register_operator('between', lambda vals, data: ...)
    """
    
    def __init__(self):
        """Initialize rule engine with standard operators."""
        self._custom_ops: Dict[str, Callable] = {}
    
    def evaluate(self, rules: Union[Dict, Rule], data: Dict[str, Any]) -> Any:
        """
        Evaluate rules against a data dictionary.
        
        Args:
            rules: JsonLogic dict or Rule object
            data: Data dictionary with field values
            
        Returns:
            Evaluation result (typically bool)
            
        Example:
            >>> engine = RuleEngine()
            >>> result = engine.evaluate(
            ...     {"==": [{"var": "city"}, "NYC"]},
            ...     {"city": "NYC", "age": 25}
            ... )
            >>> # True
        """
        if isinstance(rules, Rule):
            rules = rules.to_json()
        
        return self._eval(rules, data)
    
    def test(self, rules: Union[Dict, Rule], obj: Evaluatable) -> EvalResult:
        """
        Test rules against an Evaluatable object.
        
        Args:
            rules: JsonLogic dict or Rule object
            obj: Object implementing Evaluatable interface
            
        Returns:
            EvalResult with match status and timing
            
        Example:
            >>> engine = RuleEngine()
            >>> result = engine.test(rules, contact)
            >>> if result.matches:
            ...     print(f"Matched in {result.eval_time_ms}ms")
        """
        start = time.perf_counter()
        
        if isinstance(rules, Rule):
            rules = rules.to_json()
        
        data = obj.to_eval_dict()
        matches = bool(self._eval(rules, data))
        
        elapsed = (time.perf_counter() - start) * 1000
        
        return EvalResult(matches=matches, eval_time_ms=elapsed)
    
    def batch(
        self, 
        rules: Union[Dict, Rule], 
        objects: List[Evaluatable]
    ) -> Dict[str, List]:
        """
        Evaluate rules against multiple objects.
        
        Args:
            rules: JsonLogic dict or Rule object
            objects: List of Evaluatable objects
            
        Returns:
            Dict with 'matches' and 'non_matches' lists
            
        Example:
            >>> engine = RuleEngine()
            >>> results = engine.batch(rules, contacts)
            >>> print(f"Matched: {len(results['matches'])}")
            >>> print(f"Not matched: {len(results['non_matches'])}")
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
        objects: List[Evaluatable]
    ) -> List[Evaluatable]:
        """
        Filter objects that match the rules.
        
        Args:
            rules: JsonLogic dict or Rule object
            objects: List of Evaluatable objects
            
        Returns:
            List of matching objects
            
        Example:
            >>> engine = RuleEngine()
            >>> vip_contacts = engine.filter(
            ...     Field('tags').has_any(['vip']),
            ...     all_contacts
            ... )
        """
        return self.batch(rules, objects)['matches']
    
    def matches(self, rules: Union[Dict, Rule], data: Dict[str, Any]) -> bool:
        """
        Check if data matches rules (returns bool).
        
        Convenience method that always returns bool.
        
        Args:
            rules: JsonLogic dict or Rule object
            data: Data dictionary
            
        Returns:
            True if matches, False otherwise
        """
        return bool(self.evaluate(rules, data))
    
    def register_operator(self, name: str, func: Callable) -> 'RuleEngine':
        """
        Register a custom operator.
        
        Args:
            name: Operator name (e.g., 'between', 'regex_match')
            func: Function(values, data) -> result
            
        Returns:
            Self for chaining
            
        Example:
            >>> def between(values, data):
            ...     val, min_v, max_v = values
            ...     return min_v <= val <= max_v
            ... 
            >>> engine = RuleEngine()
            >>> engine.register_operator('between', between)
            >>> 
            >>> result = engine.evaluate(
            ...     {"between": [{"var": "age"}, 18, 65]},
            ...     {"age": 25}
            ... )
        """
        self._custom_ops[name] = func
        return self
    
    def _eval(self, rules: Any, data: Any) -> Any:
        """Recursively evaluate JsonLogic."""
        # Primitives
        if rules is None or not isinstance(rules, dict):
            return rules
        
        if not rules:
            return True
        
        # Get operator
        op = list(rules.keys())[0]
        operands = rules[op]
        
        # Normalize operands
        if not isinstance(operands, (list, tuple)):
            operands = [operands]
        
        # Special operators (control evaluation)
        if op == 'var':
            return self._op_var(operands, data)
        
        if op in ('some', 'all', 'none'):
            return self._op_array(op, operands, data)
        
        if op == 'if':
            return self._op_if(operands, data)
        
        # Evaluate operands first
        values = [self._eval(o, data) for o in operands]
        
        # Custom operators
        if op in self._custom_ops:
            return self._custom_ops[op](values, data)
        
        # Standard operators
        return self._apply_op(op, values)
    
    def _op_var(self, operands: List, data: Any) -> Any:
        """Variable access operator."""
        if not operands:
            return data
        
        var_name = self._eval(operands[0], data)
        default = operands[1] if len(operands) > 1 else None
        
        if var_name == "" or var_name is None:
            return data
        
        # Simple lookup
        if isinstance(data, dict):
            return data.get(var_name, default)
        
        return default
    
    def _op_array(self, op: str, operands: List, data: Any) -> bool:
        """Array operators: some, all, none."""
        if len(operands) != 2:
            return op != 'some'
        
        array = self._eval(operands[0], data)
        condition = operands[1]  # Keep unevaluated
        
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
        if op == '!!':
            return bool(values[0]) if values else False
        
        # Comparison
        if len(values) >= 2:
            a, b = values[0], values[1]
            
            if op == '==':
                return self._soft_eq(a, b)
            if op == '===':
                return type(a) == type(b) and a == b
            if op == '!=':
                return not self._soft_eq(a, b)
            if op == '!==':
                return not (type(a) == type(b) and a == b)
            if op == '>':
                return self._compare(a, b) > 0
            if op == '>=':
                return self._compare(a, b) >= 0
            if op == '<':
                return self._compare(a, b) < 0
            if op == '<=':
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
        
        # String/number coercion
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


# Module-level convenience functions

_default_engine: Optional[RuleEngine] = None


def evaluate(rules: Union[Dict, Rule], data: Dict[str, Any]) -> Any:
    """
    Evaluate rules against data using the default engine.
    
    Args:
        rules: JsonLogic dict or Rule object
        data: Data dictionary
        
    Returns:
        Evaluation result
    """
    global _default_engine
    if _default_engine is None:
        _default_engine = RuleEngine()
    return _default_engine.evaluate(rules, data)


def matches(rules: Union[Dict, Rule], data: Dict[str, Any]) -> bool:
    """
    Check if data matches rules using the default engine.
    
    Args:
        rules: JsonLogic dict or Rule object
        data: Data dictionary
        
    Returns:
        True if matches, False otherwise
    """
    global _default_engine
    if _default_engine is None:
        _default_engine = RuleEngine()
    return _default_engine.matches(rules, data)