#!/usr/bin/env python
"""Example showing Django integration (requires Django installed)."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from json_rule_engine import RuleEngine, Field, Q, DependencyConfig


def main():
    print("Django Integration Examples")
    print("=" * 50)
    
    # Initialize engine with Django field mappings
    engine = RuleEngine(
        django_field_map={
            'tags': 'tags__id',
            'categories': 'categories__id',
            'author': 'author__username',
            'created': 'created_at',
            'status': 'status',
            'views': 'view_count',
        }
    )
    
    print("\n1. Simple Django Q Conversion")
    print("-" * 30)
    
    # Build rule
    rule = Field('status').equals('published')
    print(f"Rule: Field('status').equals('published')")
    
    try:
        q = engine.to_q(rule)
        print(f"Django Q: {q}")
        print("\nUsage in Django ORM:")
        print("  articles = Article.objects.filter(q)")
    except ImportError:
        print("Django not installed - showing what would be generated")
        print("Django Q would be: Q(status='published')")
    
    print("\n2. Complex Filter with M2M")
    print("-" * 30)
    
    # Build complex rule
    rule = (
        Field('status').equals('published') &
        Field('views').gt(1000) &
        Field('tags').has_any([1, 2, 3]) &  # Tags with IDs 1, 2, or 3
        Field('author').equals('john_doe')
    )
    
    print("Complex rule with M2M relationships")
    
    try:
        q = engine.to_q(rule)
        print(f"\nDjango Q: {q}")
        print("\nUsage in Django ORM:")
        print("  popular_articles = Article.objects.filter(q)")
    except ImportError:
        print("\nDjango not installed - would generate:")
        print("  Q(status='published') & Q(view_count__gt=1000) &")
        print("  Q(tags__id__in=[1,2,3]) & Q(author__username='john_doe')")
    
    print("\n3. OR Conditions")
    print("-" * 30)
    
    # Build OR rule
    rule = (
        Field('status').equals('featured') |
        (
            Field('status').equals('published') &
            Field('views').gt(5000)
        )
    )
    
    print("Rule: Featured OR (Published with > 5000 views)")
    
    try:
        q = engine.to_q(rule)
        print(f"\nDjango Q: {q}")
    except ImportError:
        print("\nWould generate: Q(status='featured') | (Q(status='published') & Q(view_count__gt=5000))")
    
    print("\n4. NOT Conditions")
    print("-" * 30)
    
    # Build NOT rule
    from json_rule_engine import NOT
    
    rule = (
        Field('status').equals('published') &
        NOT(Field('categories').has_any([10, 11]))  # NOT in spam categories
    )
    
    print("Rule: Published but NOT in spam categories")
    
    try:
        q = engine.to_q(rule)
        print(f"\nDjango Q: {q}")
    except ImportError:
        print("\nWould generate: Q(status='published') & ~Q(categories__id__in=[10, 11])")
    
    print("\n5. Custom Field Mappings")
    print("-" * 30)
    
    # Configure custom mappings
    engine.configure_django_fields({
        'custom_score': 'metadata__score',
        'region': 'address__region__code',
        'premium': 'subscription__type',
    })
    
    rule = (
        Field('custom_score').gte(80) &
        Field('region').equals('US') &
        Field('premium').equals('pro')
    )
    
    print("Rule with custom field mappings")
    
    try:
        q = engine.to_q(rule)
        print(f"\nDjango Q: {q}")
        print("\nWould query through relationships:")
        print("  - metadata__score >= 80")
        print("  - address__region__code == 'US'")
        print("  - subscription__type == 'pro'")
    except ImportError:
        print("\nDjango not installed - custom mappings configured")
    
    print("\n6. Working with Explanations")
    print("-" * 30)
    
    rule = (
        Field('status').equals('active') &
        Field('tags').has_any([5, 6, 7])
    )
    
    try:
        q, explanation = engine.to_q_with_explanation(rule)
        print(f"Rule explanation: {explanation}")
        print(f"Django Q: {q}")
    except ImportError:
        print("Would provide human-readable explanation of the query")
    
    print("\n" + "=" * 50)
    print("Django integration examples completed")
    print("\nNote: Install Django to see actual Q objects:")
    print("  pip install json-rule-engine[django]")


if __name__ == "__main__":
    main()