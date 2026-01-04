"""Setup configuration for JSON Rule Engine package."""

from setuptools import setup, find_packages
import os

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
def read_requirements(filename):
    """Read requirements from file."""
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Base requirements
install_requires = []

# Optional requirements
extras_require = {
    'django': ['django>=3.2'],
    'dev': [
        'pytest>=7.0',
        'pytest-cov>=4.0',
        'black>=22.0',
        'flake8>=5.0',
        'mypy>=0.990',
        'isort>=5.10',
    ],
    'docs': [
        'sphinx>=5.0',
        'sphinx-rtd-theme>=1.0',
    ],
}

# All optional dependencies
extras_require['all'] = list(set(sum(extras_require.values(), [])))

setup(
    name="json-rule-engine",
    version="2.0.4",
    author="Ananda Behera",
    author_email="behera.anand1@gmail.com",
    description="A lightweight library for building, evaluating, and translating JSON-based rules",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/anandabehera/json-rule-engine",
    project_urls={
        "Bug Tracker": "https://github.com/ananda-callhub/json-rule-engine/issues",
        "Documentation": "https://json-rule-engine.readthedocs.io",
        "Source Code": "https://github.com/ananda-callhub/json-rule-engine",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Framework :: Django :: 4.2",
    ],
    python_requires=">=3.8",
    install_requires=install_requires,
    extras_require=extras_require,
    keywords=[
        "json",
        "rules",
        "rule-engine",
        "jsonlogic",
        "django",
        "query",
        "filter",
        "evaluation",
        "business-rules",
    ],
)
