"""
Setup script for AI-First Software Engineering Maturity Assessment Framework
"""

from setuptools import setup, find_packages

# Read README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="afs-maturity-assessment",
    version="1.0.0",
    author="AFS Development Team",
    author_email="contact@afs-assessment.com",
    description="AI-First Software Engineering Maturity Assessment Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/ai-first-software-engineering-maturity-assessment-framework",
    project_urls={
        "Bug Tracker": "https://github.com/your-org/ai-first-software-engineering-maturity-assessment-framework/issues",
        "Documentation": "https://github.com/your-org/ai-first-software-engineering-maturity-assessment-framework/docs",
        "Source Code": "https://github.com/your-org/ai-first-software-engineering-maturity-assessment-framework",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Office/Business :: Financial :: Accounting",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Framework :: Flask",
        "Environment :: Web Environment",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "pre-commit>=3.3.0",
        ],
        "docs": [
            "Sphinx>=7.1.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
        "production": [
            "gunicorn>=21.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "afs-setup=scripts.setup:main",
            "afs-seed=scripts.seed_database:main",
            "afs-backup=scripts.backup:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.txt", "*.md", "*.yml", "*.yaml", "*.json", "*.sql"],
        "app": ["templates/*.html", "templates/**/*.html", "static/**/*"],
        "data": ["migrations/*.sql", "seeds/*.json"],
    },
    zip_safe=False,
    keywords=[
        "ai",
        "artificial intelligence",
        "software engineering",
        "maturity assessment",
        "development tools",
        "flask",
        "web application",
        "assessment framework",
        "devops",
        "quality assurance",
    ],
)