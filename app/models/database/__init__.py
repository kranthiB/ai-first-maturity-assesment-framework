"""
Database Adapter Module for AFS Assessment Framework

This module provides a pluggable database adapter system that supports
multiple database backends (H2, PostgreSQL, MySQL, SQLite) through
a unified interface.
"""

from .adapters import DatabaseAdapter, DatabaseFactory, get_database_adapter
from .h2_adapter import H2Adapter
from .postgres_adapter import PostgreSQLAdapter
from .mysql_adapter import MySQLAdapter

__all__ = [
    'DatabaseAdapter',
    'DatabaseFactory',
    'get_database_adapter',
    'H2Adapter',
    'PostgreSQLAdapter',
    'MySQLAdapter'
]