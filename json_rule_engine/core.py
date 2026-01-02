"""
Core classes and interfaces for JSON Rule Engine.

This module provides the base classes and data structures used throughout the engine.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Set, Optional


class Operator(Enum):
    """Supported comparison and logic operators."""
    
    # Comparison
    EQ = "=="
    NE = "!="
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    
    # String
    CONTAINS = "_contains"
    STARTS_WITH = "_startswith"
    ENDS_WITH = "_endswith"
    IS_EMPTY = "_is_empty"
    IS_NOT_EMPTY = "_is_not_empty"
    
    # Array/Set
    IN = "in"
    SOME = "some"
    ALL = "all"
    NONE = "none"


class Logic(Enum):
    """Logic operators for combining rules."""
    AND = "and"
    OR = "or"
    NOT = "!"


@dataclass
class Dependencies:
    """
    Dependencies extracted from rules.
    
    Used for tracking which fields, tags, and custom fields are referenced
    by a rule for optimization and validation.
    """
    fields: Set[str]
    tag_ids: Set[int]
    phonebook_ids: Set[int]
    custom_field_ids: Set[int]
    
    def __init__(self):
        self.fields = set()
        self.tag_ids = set()
        self.phonebook_ids = set()
        self.custom_field_ids = set()
    
    def merge(self, other: Dependencies) -> Dependencies:
        """Merge with another Dependencies object."""
        merged = Dependencies()
        merged.fields = self.fields | other.fields
        merged.tag_ids = self.tag_ids | other.tag_ids
        merged.phonebook_ids = self.phonebook_ids | other.phonebook_ids
        merged.custom_field_ids = self.custom_field_ids | other.custom_field_ids
        return merged


@dataclass
class EvalResult:
    """Result of rule evaluation."""
    matches: bool
    eval_time_ms: float
    
    def __bool__(self) -> bool:
        return self.matches


class Rule(ABC):
    """
    Abstract base class for rules.
    
    All rule types (Condition, RuleSet, JsonRule) must implement these methods.
    """
    
    @abstractmethod
    def to_json(self) -> Dict[str, Any]:
        """Convert rule to JsonLogic format."""
        pass
    
    @abstractmethod
    def get_dependencies(self) -> Dependencies:
        """Extract dependencies from the rule."""
        pass
    
    def __and__(self, other: Rule) -> RuleSet:
        """Combine rules with AND logic."""
        from .builder import RuleSet
        if isinstance(self, RuleSet) and self.logic == Logic.AND:
            return RuleSet(Logic.AND, self.rules + [other])
        if isinstance(other, RuleSet) and other.logic == Logic.AND:
            return RuleSet(Logic.AND, [self] + other.rules)
        return RuleSet(Logic.AND, [self, other])
    
    def __or__(self, other: Rule) -> RuleSet:
        """Combine rules with OR logic."""
        from .builder import RuleSet
        if isinstance(self, RuleSet) and self.logic == Logic.OR:
            return RuleSet(Logic.OR, self.rules + [other])
        if isinstance(other, RuleSet) and other.logic == Logic.OR:
            return RuleSet(Logic.OR, [self] + other.rules)
        return RuleSet(Logic.OR, [self, other])
    
    def __invert__(self) -> RuleSet:
        """Negate rule with NOT logic."""
        from .builder import RuleSet
        return RuleSet(Logic.NOT, [self])


class RuleSet(Rule):
    """
    A collection of rules combined with logic operators.
    
    This represents a branch node in the rule tree.
    """
    
    def __init__(self, logic: Logic, rules: List[Rule]):
        self.logic = logic
        self.rules = rules
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JsonLogic format."""
        if self.logic == Logic.NOT:
            if self.rules:
                return {"!": self.rules[0].to_json()}
            return {}
        
        # AND/OR
        children = [rule.to_json() for rule in self.rules]
        
        if len(children) == 0:
            return {}
        if len(children) == 1:
            return children[0]
        
        return {self.logic.value: children}
    
    def get_dependencies(self) -> Dependencies:
        """Extract dependencies from all child rules."""
        deps = Dependencies()
        for rule in self.rules:
            deps = deps.merge(rule.get_dependencies())
        return deps
    
    def __repr__(self) -> str:
        return f"RuleSet({self.logic.name}, {len(self.rules)} rules)"


class Evaluatable(ABC):
    """
    Interface for objects that can be evaluated against rules.
    
    Classes implementing this interface can be tested against rules
    using the RuleEngine.
    """
    
    @abstractmethod
    def to_eval_dict(self) -> Dict[str, Any]:
        """
        Convert object to dictionary for evaluation.
        
        Returns:
            Dictionary with field values for rule evaluation
        """
        pass