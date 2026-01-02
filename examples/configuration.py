#!/usr/bin/env python
"""Example showing custom configuration for different domains."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from json_rule_engine import RuleEngine, DependencyConfig, Field


def ecommerce_example():
    """E-commerce domain configuration example."""
    print("E-Commerce Configuration Example")
    print("=" * 50)
    
    # Configure for e-commerce domain
    config = DependencyConfig(
        id_fields={
            'categories': 'category_ids',
            'brands': 'brand_ids',  
            'vendors': 'vendor_ids',
            'tags': 'tag_ids',
        },
        custom_field_pattern=r'^product\.(\d+)\.(\w+)$'
    )
    
    # Initialize engine with custom config
    engine = RuleEngine(dependency_config=config)
    
    # Build product filter rule
    rule = (
        Field('price').gte(10) &
        Field('price').lte(100) &
        Field('categories').has_any([101, 102]) &  # Electronics, Computers
        Field('brands').has_any([201, 202]) &      # Apple, Samsung
        Field('in_stock').equals(True)
    )
    
    # Extract dependencies
    deps = engine.get_dependencies(rule)
    print(f"\nExtracted dependencies:")
    print(f"  Fields: {deps.fields}")
    print(f"  Category IDs: {deps.id_references.get('category_ids', set())}")
    print(f"  Brand IDs: {deps.id_references.get('brand_ids', set())}")
    
    # Test with product data
    product = {
        'price': 49.99,
        'categories': [101, 103],  # Has Electronics
        'brands': [201],           # Has Apple
        'in_stock': True
    }
    
    result = engine.evaluate(rule, product)
    print(f"\nProduct matches: {result}")


def crm_example():
    """CRM domain configuration example."""
    print("\n\nCRM Configuration Example")
    print("=" * 50)
    
    # Configure for CRM domain
    config = DependencyConfig(
        id_fields={
            'tags': 'tag_ids',
            'lists': 'list_ids',
            'segments': 'segment_ids',
            'campaigns': 'campaign_ids',
        },
        custom_field_pattern=r'^custom\.(\d+)\.(\w+)$'
    )
    
    engine = RuleEngine(dependency_config=config)
    
    # Build contact filter rule
    rule = (
        Field('status').equals('active') &
        (
            Field('tags').has_any([301, 302]) |  # VIP or Premium
            Field('lifetime_value').gt(1000)
        ) &
        Field('lists').has_all([401, 402])  # Must be in both lists
    )
    
    # Extract dependencies
    deps = engine.get_dependencies(rule)
    print(f"\nExtracted dependencies:")
    print(f"  Fields: {deps.fields}")
    print(f"  Tag IDs: {deps.id_references.get('tag_ids', set())}")
    print(f"  List IDs: {deps.id_references.get('list_ids', set())}")
    
    # Test with contact data
    contact = {
        'status': 'active',
        'tags': [301, 303],        # Has VIP
        'lists': [401, 402, 403],  # Has both required lists
        'lifetime_value': 500      # Less than 1000
    }
    
    result = engine.evaluate(rule, contact)
    print(f"\nContact matches: {result}")


def permissions_example():
    """Permission system configuration example."""
    print("\n\nPermissions Configuration Example")
    print("=" * 50)
    
    # Configure for permission system
    config = DependencyConfig(
        id_fields={
            'roles': 'role_ids',
            'permissions': 'permission_ids',
            'groups': 'group_ids',
        }
    )
    
    engine = RuleEngine(dependency_config=config)
    
    # Build permission rule
    can_edit_content = (
        Field('roles').has_any([1, 2]) |  # Admin or Editor
        (
            Field('roles').has_any([3]) &  # Contributor
            Field('permissions').has_all([10, 11])  # Must have both write and publish
        )
    )
    
    # Test different users
    users = [
        {'name': 'Admin', 'roles': [1], 'permissions': []},
        {'name': 'Editor', 'roles': [2], 'permissions': [10, 11, 12]},
        {'name': 'Contributor with perms', 'roles': [3], 'permissions': [10, 11]},
        {'name': 'Contributor without', 'roles': [3], 'permissions': [10]},
        {'name': 'Viewer', 'roles': [4], 'permissions': []},
    ]
    
    print("\nPermission check results:")
    for user in users:
        can_edit = engine.evaluate(can_edit_content, user)
        status = "✓" if can_edit else "✗"
        print(f"  {status} {user['name']}: {can_edit}")


def main():
    """Run all examples."""
    ecommerce_example()
    crm_example()
    permissions_example()
    
    print("\n" + "=" * 50)
    print("Configuration examples completed")


if __name__ == "__main__":
    main()