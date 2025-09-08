#!/usr/bin/env python3
"""Setup script for BTCTurk Trading Bot."""

import os
from setuptools import setup, find_packages

# Read version from __version__.py
version_file = os.path.join(os.path.dirname(__file__), '__version__.py')
with open(version_file, 'r', encoding='utf-8') as f:
    exec(f.read())

# Read README for long description
readme_file = os.path.join(os.path.dirname(__file__), 'README.md')
try:
    with open(readme_file, 'r', encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "BTCTurk Trading Bot - Automated cryptocurrency trading bot for BTCTurk exchange."

# Read requirements
requirements_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
try:
    with open(requirements_file, 'r', encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
except FileNotFoundError:
    requirements = [
        'requests>=2.28.0',
        'tkinter',
        'cryptography>=3.4.8',
        'loguru>=0.6.0',
        'python-dotenv>=0.19.0'
    ]

setup(
    name="btcturk-trading-bot",
    version=__version__,
    author="BTCTurk Trading Bot Team",
    author_email="",
    description="Automated cryptocurrency trading bot for BTCTurk exchange",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/btcturk-trading-bot",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/btcturk-trading-bot/issues",
        "Documentation": "https://github.com/yourusername/btcturk-trading-bot/wiki",
        "Source Code": "https://github.com/yourusername/btcturk-trading-bot",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: X11 Applications :: Qt",
        "Environment :: Win32 (MS Windows)",
        "Environment :: MacOS X",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
            "pre-commit>=2.0",
        ],
        "test": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "pytest-mock>=3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "btcturk-bot=gui_main:main",
            "btcturk-bot-cli=main:main",
            "btcturk-version=__version__:print_version_info",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml", "*.json"],
    },
    zip_safe=False,
    keywords=[
        "btcturk",
        "trading",
        "bot",
        "cryptocurrency",
        "bitcoin",
        "ethereum",
        "automated-trading",
        "api",
        "finance",
        "investment",
    ],
    license="MIT",
)