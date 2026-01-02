"""
Core classes and interfaces for JSON Rule Engine - Refactored Version.

This module provides the base classes and data structures with configurable dependencies.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Set, Optional, Union


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
class DependencyConfig:
    """
    Configuration for dependency extraction.
    
    Allows users to define custom field mappings and dependency types
    instead of hardcoding domain-specific assumptions.
    """
    # Field mappings for special handling
    id_fields: Dict[str, str] = field(default_factory=dict)  # e.g., {'tags': 'tag_ids'}
    custom_field_pattern: Optional[str] = None  # e.g., r'^cf\.(\d+)\.\w+$'
    custom_field_group: str = 'custom_fields'
    
    def __post_init__(self):
        if not self.id_fields:
            # Provide sensible defaults but allow override
            self.id_fields = {
                'tags': 'tag_ids',
                'phonebooks': 'phonebook_ids',
                'categories': 'category_ids',
            }


@dataclass
class RuleFields:
    """
    Field references and dependencies extracted from rules.
    
    Tracks which fields, ID references, and custom fields are used in a rule.
    No longer hardcoded to specific domain fields - users can configure
    what fields are treated as ID references.
    """
    fields: Set[str] = field(default_factory=set)
    id_references: Dict[str, Set[int]] = field(default_factory=dict)
    custom_fields: Set[int] = field(default_factory=set)
    
    def add_field(self, field_name: str) -> None:
        """Add a regular field dependency."""
        self.fields.add(field_name)
    
    def add_id_reference(self, reference_type: str, id_value: int) -> None:
        """Add an ID reference (e.g., tag_id, category_id)."""
        if reference_type not in self.id_references:
            self.id_references[reference_type] = set()
        self.id_references[reference_type].add(id_value)
    
    def add_custom_field(self, field_id: int) -> None:
        """Add a custom field ID."""
        self.custom_fields.add(field_id)
    
    def merge(self, other: RuleFields) -> RuleFields:
        """Merge with another RuleFields object."""
        merged = RuleFields()
        merged.fields = self.fields | other.fields
        merged.custom_fields = self.custom_fields | other.custom_fields
        
        # Merge ID references
        all_keys = set(self.id_references.keys()) | set(other.id_references.keys())
        for key in all_keys:
            self_ids = self.id_references.get(key, set())
            other_ids = other.id_references.get(key, set())
            merged.id_references[key] = self_ids | other_ids
        
        return merged
    
    # Backward compatibility properties
    @property
    def tag_ids(self) -> Set[int]:
        """Backward compatibility for tag_ids."""
        return self.id_references.get('tag_ids', set())
    
    @property
    def phonebook_ids(self) -> Set[int]:
        """Backward compatibility for phonebook_ids."""
        return self.id_references.get('phonebook_ids', set())
    
    @property
    def custom_field_ids(self) -> Set[int]:
        """Backward compatibility for custom_field_ids."""
        return self.custom_fields


@dataclass
class EvaluationResult:
    """Result of rule evaluation including match status and performance metrics."""
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
    def get_dependencies(self, config: Optional[DependencyConfig] = None) -> RuleFields:
        """
        Extract dependencies from the rule.
        
        Args:
            config: Optional dependency configuration for custom field handling
        """
        pass
    
    def __and__(self, other: Rule) -> RuleSet:
        """Combine rules with AND logic."""
        from .builder import RuleSet  # Avoid circular import
        if isinstance(self, RuleSet) and self.logic == Logic.AND:
            return RuleSet(Logic.AND, self.rules + [other])
        if isinstance(other, RuleSet) and other.logic == Logic.AND:
            return RuleSet(Logic.AND, [self] + other.rules)
        return RuleSet(Logic.AND, [self, other])
    
    def __or__(self, other: Rule) -> RuleSet:
        """Combine rules with OR logic."""
        from .builder import RuleSet  # Avoid circular import
        if isinstance(self, RuleSet) and self.logic == Logic.OR:
            return RuleSet(Logic.OR, self.rules + [other])
        if isinstance(other, RuleSet) and other.logic == Logic.OR:
            return RuleSet(Logic.OR, [self] + other.rules)
        return RuleSet(Logic.OR, [self, other])
    
    def __invert__(self) -> RuleSet:
        """Negate rule with NOT logic."""
        from .builder import RuleSet  # Avoid circular import
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
    
    def get_dependencies(self, config: Optional[DependencyConfig] = None) -> RuleFields:
        """Extract dependencies from all child rules."""
        deps = RuleFields()
        for rule in self.rules:
            deps = deps.merge(rule.get_dependencies(config))
        return deps
    
    def __repr__(self) -> str:
        return f"RuleSet({self.logic.name}, {len(self.rules)} rules)"


class RuleEntity(ABC):
    """
    Interface for objects that can be evaluated against rules.
    
    Classes implementing this interface can be tested against rules
    using the RuleEngine. This represents any business entity or data
    object that rules can be applied to.
    """
    
    @abstractmethod
    def to_eval_dict(self) -> Dict[str, Any]:
        """
        Convert object to dictionary for evaluation.
        
        Returns:
            Dictionary with field values for rule evaluation
        """
        pass