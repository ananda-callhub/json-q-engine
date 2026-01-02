"""Tests for rule evaluator module."""

import pytest
from json_rule_engine import (
    RuleEngine, Field, Q,
    RuleEntity, EvaluationResult
)


class TestRuleEngine:
    """Test RuleEngine evaluation."""
    
    def setup_method(self):
        """Setup test engine and data."""
        self.engine = RuleEngine()
        self.data = {
            'city': 'NYC',
            'state': 'NY',
            'age': 25,
            'tags': ['vip', 'newsletter'],
            'score': 85,
            'email': 'john@gmail.com',
            'status': 'active',
            'notes': 'Some notes'
        }
    
    def test_simple_equals(self):
        rule = Field('city').equals('NYC')
        assert self.engine.evaluate(rule, self.data) is True
        
        rule = Field('city').equals('LA')
        assert self.engine.evaluate(rule, self.data) is False
    
    def test_comparison_operators(self):
        # Greater than
        rule = Field('age').gt(18)
        assert self.engine.evaluate(rule, self.data) is True
        
        rule = Field('age').gt(30)
        assert self.engine.evaluate(rule, self.data) is False
        
        # Greater or equal
        rule = Field('age').gte(25)
        assert self.engine.evaluate(rule, self.data) is True
        
        # Less than
        rule = Field('age').lt(30)
        assert self.engine.evaluate(rule, self.data) is True
        
        # Less or equal
        rule = Field('age').lte(25)
        assert self.engine.evaluate(rule, self.data) is True
    
    def test_string_operators(self):
        # Contains
        rule = Field('email').contains('@gmail')
        assert self.engine.evaluate(rule, self.data) is True
        
        rule = Field('email').contains('@yahoo')
        assert self.engine.evaluate(rule, self.data) is False
        
        # Starts with
        rule = Field('email').startswith('john')
        assert self.engine.evaluate(rule, self.data) is True
        
        # Ends with
        rule = Field('email').endswith('.com')
        assert self.engine.evaluate(rule, self.data) is True
    
    def test_empty_checks(self):
        # Not empty
        rule = Field('notes').is_not_empty()
        assert self.engine.evaluate(rule, self.data) is True
        
        # Is empty
        empty_data = {**self.data, 'notes': ''}
        rule = Field('notes').is_empty()
        assert self.engine.evaluate(rule, empty_data) is True
        
        null_data = {**self.data, 'notes': None}
        assert self.engine.evaluate(rule, null_data) is True
    
    def test_array_operators(self):
        # Has any
        rule = Field('tags').has_any(['vip'])
        assert self.engine.evaluate(rule, self.data) is True
        
        rule = Field('tags').has_any(['admin', 'vip'])
        assert self.engine.evaluate(rule, self.data) is True
        
        rule = Field('tags').has_any(['admin', 'premium'])
        assert self.engine.evaluate(rule, self.data) is False
        
        # Has none
        rule = Field('tags').has_none(['admin', 'premium'])
        assert self.engine.evaluate(rule, self.data) is True
        
        rule = Field('tags').has_none(['vip'])
        assert self.engine.evaluate(rule, self.data) is False
    
    def test_logical_combinations(self):
        # AND
        rule = Field('city').equals('NYC') & Field('age').gt(18)
        assert self.engine.evaluate(rule, self.data) is True
        
        rule = Field('city').equals('NYC') & Field('age').gt(30)
        assert self.engine.evaluate(rule, self.data) is False
        
        # OR
        rule = Field('city').equals('LA') | Field('city').equals('NYC')
        assert self.engine.evaluate(rule, self.data) is True
        
        rule = Field('city').equals('LA') | Field('city').equals('Chicago')
        assert self.engine.evaluate(rule, self.data) is False
        
        # NOT
        rule = ~Field('status').equals('blocked')
        assert self.engine.evaluate(rule, self.data) is True
        
        rule = ~Field('status').equals('active')
        assert self.engine.evaluate(rule, self.data) is False
    
    def test_complex_nested(self):
        rule = (
            Field('city').equals('NYC') &
            (Field('age').gt(18) | Field('score').gt(90)) &
            Field('tags').has_any(['vip', 'premium'])
        )
        assert self.engine.evaluate(rule, self.data) is True
        
        rule = (
            Field('city').equals('NYC') &
            (Field('age').gt(30) & Field('score').gt(90))
        )
        assert self.engine.evaluate(rule, self.data) is False
    
    def test_json_evaluation(self):
        # Direct JSON evaluation
        json_rule = {"==": [{"var": "city"}, "NYC"]}
        assert self.engine.evaluate(json_rule, self.data) is True
        
        # Complex JSON
        json_rule = {
            "and": [
                {"==": [{"var": "city"}, "NYC"]},
                {">": [{"var": "age"}, 18]}
            ]
        }
        assert self.engine.evaluate(json_rule, self.data) is True
        
        # Array operators in JSON
        json_rule = {"some": [{"var": "tags"}, {"in": [{"var": ""}, ["vip", "admin"]]}]}
        assert self.engine.evaluate(json_rule, self.data) is True
    
    def test_matches_method(self):
        rule = Field('city').equals('NYC')
        assert self.engine.matches(rule, self.data) is True
        
        rule = Field('city').equals('LA')
        assert self.engine.matches(rule, self.data) is False


class TestCustomOperators:
    """Test custom operator registration."""
    
    def test_register_custom_operator(self):
        engine = RuleEngine()
        
        # Register between operator
        def between(values, data):
            if len(values) != 3:
                return False
            val, min_val, max_val = values
            return min_val <= val <= max_val
        
        engine.register_operator('between', between)
        
        # Test custom operator
        rule = {"between": [{"var": "age"}, 18, 65]}
        assert engine.evaluate(rule, {"age": 25}) is True
        assert engine.evaluate(rule, {"age": 17}) is False
        assert engine.evaluate(rule, {"age": 66}) is False
    
    def test_chained_registration(self):
        engine = RuleEngine()
        
        def is_even(values, data):
            return values[0] % 2 == 0 if values else False
        
        def is_odd(values, data):
            return values[0] % 2 != 0 if values else False
        
        # Chained registration
        engine.register_operator('is_even', is_even).register_operator('is_odd', is_odd)
        
        assert engine.evaluate({"is_even": [{"var": "num"}]}, {"num": 4}) is True
        assert engine.evaluate({"is_even": [{"var": "num"}]}, {"num": 3}) is False
        assert engine.evaluate({"is_odd": [{"var": "num"}]}, {"num": 3}) is True


class TestRuleEntity:
    """Test Evaluatable interface."""
    
    class Contact(RuleEntity):
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
            return f"Contact({self.id}, {self.name})"
    
    def test_test_method(self):
        engine = RuleEngine()
        contact = self.Contact(1, 'John', 'NYC', 25, ['vip'])
        rule = Field('city').equals('NYC') & Field('age').gt(18)
        
        result = engine.test(rule, contact)
        assert isinstance(result, EvaluationResult)
        assert result.matches is True
        assert result.eval_time_ms >= 0
    
    def test_batch_evaluation(self):
        engine = RuleEngine()
        contacts = [
            self.Contact(1, 'John', 'NYC', 25, ['vip']),
            self.Contact(2, 'Jane', 'LA', 30, ['premium']),
            self.Contact(3, 'Bob', 'NYC', 17, []),
            self.Contact(4, 'Alice', 'NYC', 35, ['vip', 'premium']),
        ]
        
        rule = Field('city').equals('NYC') & Field('age').gt(18)
        results = engine.batch(rule, contacts)
        
        assert len(results['matches']) == 2
        assert len(results['non_matches']) == 2
        assert contacts[0] in results['matches']
        assert contacts[3] in results['matches']
        assert contacts[1] in results['non_matches']
        assert contacts[2] in results['non_matches']
    
    def test_filter_method(self):
        engine = RuleEngine()
        contacts = [
            self.Contact(1, 'John', 'NYC', 25, ['vip']),
            self.Contact(2, 'Jane', 'LA', 30, ['premium']),
            self.Contact(3, 'Bob', 'NYC', 17, []),
            self.Contact(4, 'Alice', 'NYC', 35, ['vip', 'premium']),
        ]
        
        rule = Field('tags').has_any(['vip'])
        matches = engine.filter(rule, contacts)
        
        assert len(matches) == 2
        assert contacts[0] in matches
        assert contacts[3] in matches


class TestUnifiedAPI:
    """Test unified API through RuleEngine."""
    
    def test_engine_evaluate(self):
        engine = RuleEngine()
        data = {'city': 'NYC', 'age': 25}
        
        # Test with rule
        rule = Field('city').equals('NYC')
        assert engine.evaluate(rule, data) is True
        
        # Test with JSON
        json_rule = {"==": [{"var": "city"}, "NYC"]}
        assert engine.evaluate(json_rule, data) is True
    
    def test_engine_matches(self):
        engine = RuleEngine()
        data = {'city': 'NYC', 'age': 25}
        
        # Test with rule
        rule = Field('city').equals('NYC')
        assert engine.matches(rule, data) is True
        
        rule = Field('city').equals('LA')
        assert engine.matches(rule, data) is False


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_missing_field(self):
        engine = RuleEngine()
        data = {'city': 'NYC'}
        
        rule = Field('age').gt(18)
        # Missing field should evaluate to false
        assert engine.evaluate(rule, data) is False
    
    def test_null_values(self):
        engine = RuleEngine()
        data = {'city': None, 'age': None}
        
        rule = Field('city').equals(None)
        assert engine.evaluate(rule, data) is True
        
        rule = Field('city').is_empty()
        assert engine.evaluate(rule, data) is True
    
    def test_type_coercion(self):
        engine = RuleEngine()
        
        # String to number comparison
        data = {'age': '25'}
        rule = Field('age').equals(25)
        assert engine.evaluate(rule, data) is True
        
        # Number to string comparison
        data = {'score': 100}
        rule = Field('score').equals('100')
        assert engine.evaluate(rule, data) is True
    
    def test_empty_rules(self):
        engine = RuleEngine()
        data = {'city': 'NYC'}
        
        # Empty dict should evaluate to True
        assert engine.evaluate({}, data) is True
        
        # None should return None
        assert engine.evaluate(None, data) is None
    
    def test_empty_data(self):
        engine = RuleEngine()
        rule = Field('city').equals('NYC')
        
        # Empty data should fail the rule
        assert engine.evaluate(rule, {}) is False
        
        # None data should fail
        assert engine.evaluate(rule, None) is False