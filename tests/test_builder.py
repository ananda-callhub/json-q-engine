"""Tests for rule builder module."""

import pytest
from json_rule_engine import Field, Q, AND, OR, NOT, RuleBuilder, JsonRule, Condition
from json_rule_engine.core import Operator, Logic


class TestField:
    """Test Field builder."""
    
    def test_equals(self):
        rule = Field('city').equals('NYC')
        assert rule.to_json() == {"==": [{"var": "city"}, "NYC"]}
    
    def test_not_equals(self):
        rule = Field('city').not_equals('NYC')
        assert rule.to_json() == {"!=": [{"var": "city"}, "NYC"]}
    
    def test_greater_than(self):
        rule = Field('age').greater_than(18)
        assert rule.to_json() == {">": [{"var": "age"}, 18]}
    
    def test_greater_or_equal(self):
        rule = Field('age').greater_or_equal(18)
        assert rule.to_json() == {">=": [{"var": "age"}, 18]}
    
    def test_less_than(self):
        rule = Field('age').less_than(65)
        assert rule.to_json() == {"<": [{"var": "age"}, 65]}
    
    def test_less_or_equal(self):
        rule = Field('age').less_or_equal(65)
        assert rule.to_json() == {"<=": [{"var": "age"}, 65]}
    
    def test_contains(self):
        rule = Field('email').contains('@gmail')
        assert rule.to_json() == {"in": ["@gmail", {"var": "email"}]}
    
    def test_startswith(self):
        rule = Field('name').startswith('John')
        assert rule.to_json() == {"_startswith": [{"var": "name"}, "John"]}
    
    def test_endswith(self):
        rule = Field('email').endswith('.com')
        assert rule.to_json() == {"_endswith": [{"var": "email"}, ".com"]}
    
    def test_is_empty(self):
        rule = Field('notes').is_empty()
        expected = {"or": [{"==": [{"var": "notes"}, None]}, {"==": [{"var": "notes"}, ""]}]}
        assert rule.to_json() == expected
    
    def test_is_not_empty(self):
        rule = Field('notes').is_not_empty()
        expected = {"and": [{"!=": [{"var": "notes"}, None]}, {"!=": [{"var": "notes"}, ""]}]}
        assert rule.to_json() == expected
    
    def test_has_any(self):
        rule = Field('tags').has_any(['vip', 'premium'])
        expected = {"some": [{"var": "tags"}, {"in": [{"var": ""}, ["vip", "premium"]]}]}
        assert rule.to_json() == expected
    
    def test_has_all(self):
        rule = Field('tags').has_all(['read', 'write'])
        expected = {
            "and": [
                {"some": [{"var": "tags"}, {"==": [{"var": ""}, "read"]}]},
                {"some": [{"var": "tags"}, {"==": [{"var": ""}, "write"]}]}
            ]
        }
        assert rule.to_json() == expected
    
    def test_has_none(self):
        rule = Field('tags').has_none(['blocked'])
        expected = {"none": [{"var": "tags"}, {"in": [{"var": ""}, ["blocked"]]}]}
        assert rule.to_json() == expected
    
    def test_is_in(self):
        rule = Field('status').is_in(['active', 'pending'])
        assert rule.to_json() == {"in": [{"var": "status"}, ["active", "pending"]]}
    
    def test_operator_overloading(self):
        # ==
        rule = Field('city') == 'NYC'
        assert rule.to_json() == {"==": [{"var": "city"}, "NYC"]}
        
        # !=
        rule = Field('city') != 'LA'
        assert rule.to_json() == {"!=": [{"var": "city"}, "LA"]}
        
        # >
        rule = Field('age') > 18
        assert rule.to_json() == {">": [{"var": "age"}, 18]}
        
        # >=
        rule = Field('age') >= 18
        assert rule.to_json() == {">=": [{"var": "age"}, 18]}
        
        # <
        rule = Field('age') < 65
        assert rule.to_json() == {"<": [{"var": "age"}, 65]}
        
        # <=
        rule = Field('age') <= 65
        assert rule.to_json() == {"<=": [{"var": "age"}, 65]}


class TestQ:
    """Test Q objects."""
    
    def test_simple_equals(self):
        rule = Q(city='NYC')
        assert rule.to_json() == {"==": [{"var": "city"}, "NYC"]}
    
    def test_with_operator(self):
        rule = Q(age__gt=18)
        assert rule.to_json() == {">": [{"var": "age"}, 18]}
        
        rule = Q(age__gte=18)
        assert rule.to_json() == {">=": [{"var": "age"}, 18]}
        
        rule = Q(age__lt=65)
        assert rule.to_json() == {"<": [{"var": "age"}, 65]}
        
        rule = Q(age__lte=65)
        assert rule.to_json() == {"<=": [{"var": "age"}, 65]}
    
    def test_string_operators(self):
        rule = Q(email__contains='@gmail')
        assert rule.to_json() == {"in": ["@gmail", {"var": "email"}]}
        
        rule = Q(name__startswith='John')
        assert rule.to_json() == {"_startswith": [{"var": "name"}, "John"]}
        
        rule = Q(email__endswith='.com')
        assert rule.to_json() == {"_endswith": [{"var": "email"}, ".com"]}
    
    def test_array_operators(self):
        rule = Q(tags__has_any=['vip'])
        expected = {"some": [{"var": "tags"}, {"in": [{"var": ""}, ["vip"]]}]}
        assert rule.to_json() == expected
        
        rule = Q(tags__has_all=['read', 'write'])
        expected = {
            "and": [
                {"some": [{"var": "tags"}, {"==": [{"var": ""}, "read"]}]},
                {"some": [{"var": "tags"}, {"==": [{"var": ""}, "write"]}]}
            ]
        }
        assert rule.to_json() == expected
        
        rule = Q(tags__has_none=['blocked'])
        expected = {"none": [{"var": "tags"}, {"in": [{"var": ""}, ["blocked"]]}]}
        assert rule.to_json() == expected
    
    def test_invalid_q(self):
        with pytest.raises(ValueError, match="exactly one keyword"):
            Q()
        
        with pytest.raises(ValueError, match="exactly one keyword"):
            Q(city='NYC', age=25)


class TestRuleCombination:
    """Test combining rules."""
    
    def test_and_combination(self):
        rule = Field('city').equals('NYC') & Field('age').gt(18)
        expected = {
            "and": [
                {"==": [{"var": "city"}, "NYC"]},
                {">": [{"var": "age"}, 18]}
            ]
        }
        assert rule.to_json() == expected
    
    def test_or_combination(self):
        rule = Field('city').equals('NYC') | Field('city').equals('LA')
        expected = {
            "or": [
                {"==": [{"var": "city"}, "NYC"]},
                {"==": [{"var": "city"}, "LA"]}
            ]
        }
        assert rule.to_json() == expected
    
    def test_not_combination(self):
        rule = ~Field('status').equals('blocked')
        expected = {"!": {"==": [{"var": "status"}, "blocked"]}}
        assert rule.to_json() == expected
    
    def test_complex_combination(self):
        rule = (
            Field('city').equals('NYC') &
            (Field('age').gt(18) | Field('vip').equals(True)) &
            ~Field('blocked').equals(True)
        )
        expected = {
            "and": [
                {"==": [{"var": "city"}, "NYC"]},
                {"or": [
                    {">": [{"var": "age"}, 18]},
                    {"==": [{"var": "vip"}, True]}
                ]},
                {"!": {"==": [{"var": "blocked"}, True]}}
            ]
        }
        assert rule.to_json() == expected
    
    def test_and_function(self):
        rule = AND(
            Field('city').equals('NYC'),
            Field('age').gt(18),
            Field('status').equals('active')
        )
        expected = {
            "and": [
                {"==": [{"var": "city"}, "NYC"]},
                {">": [{"var": "age"}, 18]},
                {"==": [{"var": "status"}, "active"]}
            ]
        }
        assert rule.to_json() == expected
    
    def test_or_function(self):
        rule = OR(
            Field('city').equals('NYC'),
            Field('city').equals('LA'),
            Field('city').equals('Chicago')
        )
        expected = {
            "or": [
                {"==": [{"var": "city"}, "NYC"]},
                {"==": [{"var": "city"}, "LA"]},
                {"==": [{"var": "city"}, "Chicago"]}
            ]
        }
        assert rule.to_json() == expected
    
    def test_not_function(self):
        rule = NOT(Field('status').equals('blocked'))
        expected = {"!": {"==": [{"var": "status"}, "blocked"]}}
        assert rule.to_json() == expected


class TestRuleBuilder:
    """Test RuleBuilder factory."""
    
    def test_field_builder(self):
        field = RuleBuilder.field('city')
        rule = field.equals('NYC')
        assert rule.to_json() == {"==": [{"var": "city"}, "NYC"]}
    
    def test_from_json(self):
        json_data = {"==": [{"var": "city"}, "NYC"]}
        rule = RuleBuilder.from_json(json_data)
        assert rule.to_json() == json_data
    
    def test_nested_and(self):
        rule = RuleBuilder.and_(
            RuleBuilder.field('city').equals('NYC'),
            RuleBuilder.field('age').gt(18)
        )
        expected = {
            "and": [
                {"==": [{"var": "city"}, "NYC"]},
                {">": [{"var": "age"}, 18]}
            ]
        }
        assert rule.to_json() == expected
    
    def test_nested_or(self):
        rule = RuleBuilder.or_(
            RuleBuilder.field('status').equals('active'),
            RuleBuilder.field('status').equals('pending')
        )
        expected = {
            "or": [
                {"==": [{"var": "status"}, "active"]},
                {"==": [{"var": "status"}, "pending"]}
            ]
        }
        assert rule.to_json() == expected
    
    def test_nested_not(self):
        rule = RuleBuilder.not_(
            RuleBuilder.field('blocked').equals(True)
        )
        expected = {"!": {"==": [{"var": "blocked"}, True]}}
        assert rule.to_json() == expected
    
    def test_complex_nested(self):
        rule = RuleBuilder.and_(
            RuleBuilder.field('city').equals('NYC'),
            RuleBuilder.or_(
                RuleBuilder.field('state').equals('NY'),
                RuleBuilder.field('state').equals('CA')
            ),
            RuleBuilder.field('tags').has_any(['vip'])
        )
        expected = {
            "and": [
                {"==": [{"var": "city"}, "NYC"]},
                {"or": [
                    {"==": [{"var": "state"}, "NY"]},
                    {"==": [{"var": "state"}, "CA"]}
                ]},
                {"some": [{"var": "tags"}, {"in": [{"var": ""}, ["vip"]]}]}
            ]
        }
        assert rule.to_json() == expected


class TestJsonRule:
    """Test JsonRule wrapper."""
    
    def test_wrap_json(self):
        json_data = {"==": [{"var": "city"}, "NYC"]}
        rule = JsonRule(json_data)
        assert rule.to_json() == json_data
    
    def test_combine_with_builder(self):
        json_data = {"==": [{"var": "status"}, "active"]}
        json_rule = JsonRule(json_data)
        combined = json_rule & Field('age').gt(18)
        
        expected = {
            "and": [
                {"==": [{"var": "status"}, "active"]},
                {">": [{"var": "age"}, 18]}
            ]
        }
        assert combined.to_json() == expected
    
    def test_dependencies_extraction(self):
        json_data = {
            "and": [
                {"==": [{"var": "city"}, "NYC"]},
                {"some": [{"var": "tags"}, {"in": [{"var": ""}, ["101", "102"]]}]}
            ]
        }
        rule = JsonRule(json_data)
        deps = rule.get_dependencies()
        
        assert 'city' in deps.fields
        assert 101 in deps.tag_ids
        assert 102 in deps.tag_ids


class TestDependencies:
    """Test dependency extraction."""
    
    def test_simple_field_dependency(self):
        rule = Field('city').equals('NYC')
        deps = rule.get_dependencies()
        assert 'city' in deps.fields
        assert len(deps.tag_ids) == 0
        assert len(deps.phonebook_ids) == 0
        assert len(deps.custom_field_ids) == 0
    
    def test_tag_dependency(self):
        rule = Field('tags').has_any(['101', '102'])
        deps = rule.get_dependencies()
        assert 101 in deps.tag_ids
        assert 102 in deps.tag_ids
        assert 'tags' not in deps.fields
    
    def test_phonebook_dependency(self):
        rule = Field('phonebooks').has_any(['201', '202'])
        deps = rule.get_dependencies()
        assert 201 in deps.phonebook_ids
        assert 202 in deps.phonebook_ids
        assert 'phonebooks' not in deps.fields
    
    def test_custom_field_dependency(self):
        rule = Field('cf.123.number').gt(100)
        deps = rule.get_dependencies()
        assert 123 in deps.custom_field_ids
        assert 'cf.123.number' not in deps.fields
    
    def test_combined_dependencies(self):
        rule = (
            Field('city').equals('NYC') &
            Field('tags').has_any(['101']) &
            Field('phonebooks').has_none(['201']) &
            Field('cf.123.number').gt(100)
        )
        deps = rule.get_dependencies()
        
        assert 'city' in deps.fields
        assert 101 in deps.tag_ids
        assert 201 in deps.phonebook_ids
        assert 123 in deps.custom_field_ids