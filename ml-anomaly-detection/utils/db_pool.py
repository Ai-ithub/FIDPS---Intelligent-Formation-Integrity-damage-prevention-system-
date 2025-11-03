"""
Database Connection Pool Utilities for ML Service
Provides connection pooling for PostgreSQL
"""

import psycopg2
from psycopg2 import pool
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

class PostgreSQLPool:
    """PostgreSQL connection pool manager"""
    
    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        min_size: int = 2,
        max_size: int = 10
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[pool.ThreadedConnectionPool] = None
    
    def initialize(self):
        """Initialize the connection pool"""
        try:
            self.pool = pool.ThreadedConnectionPool(
                minconn=self.min_size,
                maxconn=self.max_size,
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            logger.info(f"PostgreSQL connection pool created (min={self.min_size}, max={self.max_size})")
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL connection pool: {e}")
            raise
    
    def get_connection(self):
        """Get a connection from the pool"""
        if not self.pool:
            raise RuntimeError("Connection pool not initialized")
        return self.pool.getconn()
    
    def put_connection(self, conn):
        """Return a connection to the pool"""
        if self.pool:
            self.pool.putconn(conn)
    
    def close_all(self):
        """Close all connections in the pool"""
        if self.pool:
            self.pool.closeall()
            logger.info("PostgreSQL connection pool closed")
    
    @classmethod
    def from_env(cls):
        """Create pool from environment variables"""
        return cls(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=int(os.getenv('POSTGRES_PORT', '5432')),
            database=os.getenv('POSTGRES_DB', 'fidps_operational'),
            user=os.getenv('POSTGRES_USER', 'fidps_user'),
            password=os.getenv('POSTGRES_PASSWORD', 'fidps_password'),
            min_size=int(os.getenv('DB_CONNECTION_POOL_MIN_SIZE', '2')),
            max_size=int(os.getenv('DB_CONNECTION_POOL_MAX_SIZE', '10'))
        )

