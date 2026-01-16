#!/usr/bin/env python3
"""
PredictBot Stack - Database Health Check Script

This script verifies the health of PostgreSQL and Redis connections,
checks that TimescaleDB extension is enabled, and validates the database schema.

Usage:
    python scripts/check_db.py
    python scripts/check_db.py --verbose
    python scripts/check_db.py --json

Exit codes:
    0 - All checks passed
    1 - One or more checks failed
    2 - Configuration error
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Try to import required packages
try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(2)

try:
    import redis
except ImportError:
    print("ERROR: redis not installed. Run: pip install redis")
    sys.exit(2)


class HealthCheckResult:
    """Represents the result of a health check."""
    
    def __init__(self, name: str, passed: bool, message: str, details: Optional[Dict] = None):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp
        }


class DatabaseHealthChecker:
    """Health checker for PostgreSQL and Redis databases."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[HealthCheckResult] = []
        
        # Load configuration from environment
        self.postgres_config = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "user": os.getenv("POSTGRES_USER", "predictbot"),
            "password": os.getenv("POSTGRES_PASSWORD", ""),
            "database": os.getenv("POSTGRES_DB", "predictbot"),
        }
        
        self.redis_config = {
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", "6379")),
            "password": os.getenv("REDIS_PASSWORD", None),
        }
        
        # Parse DATABASE_URL if provided
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            self._parse_database_url(database_url)
        
        # Parse REDIS_URL if provided
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            self._parse_redis_url(redis_url)
    
    def _parse_database_url(self, url: str) -> None:
        """Parse PostgreSQL connection URL."""
        try:
            # Format: postgresql://user:password@host:port/database
            if url.startswith("postgresql://"):
                url = url[13:]
            elif url.startswith("postgres://"):
                url = url[11:]
            
            # Split user:password from host:port/database
            if "@" in url:
                auth, rest = url.split("@", 1)
                if ":" in auth:
                    self.postgres_config["user"], self.postgres_config["password"] = auth.split(":", 1)
                else:
                    self.postgres_config["user"] = auth
            else:
                rest = url
            
            # Split host:port from database
            if "/" in rest:
                host_port, database = rest.split("/", 1)
                self.postgres_config["database"] = database.split("?")[0]  # Remove query params
            else:
                host_port = rest
            
            # Split host from port
            if ":" in host_port:
                host, port = host_port.split(":", 1)
                self.postgres_config["host"] = host
                self.postgres_config["port"] = int(port)
            else:
                self.postgres_config["host"] = host_port
        except Exception as e:
            if self.verbose:
                print(f"Warning: Could not parse DATABASE_URL: {e}")
    
    def _parse_redis_url(self, url: str) -> None:
        """Parse Redis connection URL."""
        try:
            # Format: redis://[:password@]host:port[/db]
            if url.startswith("redis://"):
                url = url[8:]
            
            # Check for password
            if "@" in url:
                auth, rest = url.split("@", 1)
                if auth:
                    self.redis_config["password"] = auth.lstrip(":")
            else:
                rest = url
            
            # Split host:port from db
            if "/" in rest:
                host_port, _ = rest.split("/", 1)
            else:
                host_port = rest
            
            # Split host from port
            if ":" in host_port:
                host, port = host_port.split(":", 1)
                self.redis_config["host"] = host
                self.redis_config["port"] = int(port)
            else:
                self.redis_config["host"] = host_port
        except Exception as e:
            if self.verbose:
                print(f"Warning: Could not parse REDIS_URL: {e}")
    
    def log(self, message: str) -> None:
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(f"  {message}")
    
    def check_postgres_connection(self) -> HealthCheckResult:
        """Check PostgreSQL connection."""
        name = "PostgreSQL Connection"
        try:
            self.log(f"Connecting to PostgreSQL at {self.postgres_config['host']}:{self.postgres_config['port']}...")
            
            conn = psycopg2.connect(
                host=self.postgres_config["host"],
                port=self.postgres_config["port"],
                user=self.postgres_config["user"],
                password=self.postgres_config["password"],
                database=self.postgres_config["database"],
                connect_timeout=10
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            self.log(f"Connected successfully: {version[:50]}...")
            
            return HealthCheckResult(
                name=name,
                passed=True,
                message="PostgreSQL connection successful",
                details={"version": version, "host": self.postgres_config["host"]}
            )
        except Exception as e:
            return HealthCheckResult(
                name=name,
                passed=False,
                message=f"PostgreSQL connection failed: {str(e)}",
                details={"host": self.postgres_config["host"], "error": str(e)}
            )
    
    def check_timescaledb_extension(self) -> HealthCheckResult:
        """Check if TimescaleDB extension is enabled."""
        name = "TimescaleDB Extension"
        try:
            self.log("Checking TimescaleDB extension...")
            
            conn = psycopg2.connect(
                host=self.postgres_config["host"],
                port=self.postgres_config["port"],
                user=self.postgres_config["user"],
                password=self.postgres_config["password"],
                database=self.postgres_config["database"],
                connect_timeout=10
            )
            
            cursor = conn.cursor()
            
            # Check if TimescaleDB extension exists
            cursor.execute("""
                SELECT extname, extversion 
                FROM pg_extension 
                WHERE extname = 'timescaledb';
            """)
            result = cursor.fetchone()
            
            if result:
                ext_name, ext_version = result
                self.log(f"TimescaleDB version: {ext_version}")
                
                # Check for hypertables
                cursor.execute("""
                    SELECT hypertable_name 
                    FROM timescaledb_information.hypertables;
                """)
                hypertables = [row[0] for row in cursor.fetchall()]
                self.log(f"Hypertables found: {hypertables}")
                
                cursor.close()
                conn.close()
                
                return HealthCheckResult(
                    name=name,
                    passed=True,
                    message=f"TimescaleDB {ext_version} is enabled",
                    details={"version": ext_version, "hypertables": hypertables}
                )
            else:
                cursor.close()
                conn.close()
                
                return HealthCheckResult(
                    name=name,
                    passed=False,
                    message="TimescaleDB extension is not installed",
                    details={}
                )
        except Exception as e:
            return HealthCheckResult(
                name=name,
                passed=False,
                message=f"TimescaleDB check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    def check_database_schema(self) -> HealthCheckResult:
        """Check if required database tables exist."""
        name = "Database Schema"
        required_tables = [
            "positions",
            "trades",
            "pnl_snapshots",
            "ai_forecasts",
            "alerts",
            "config_history"
        ]
        
        try:
            self.log("Checking database schema...")
            
            conn = psycopg2.connect(
                host=self.postgres_config["host"],
                port=self.postgres_config["port"],
                user=self.postgres_config["user"],
                password=self.postgres_config["password"],
                database=self.postgres_config["database"],
                connect_timeout=10
            )
            
            cursor = conn.cursor()
            
            # Get list of existing tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE';
            """)
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            # Check which required tables exist
            missing_tables = [t for t in required_tables if t not in existing_tables]
            found_tables = [t for t in required_tables if t in existing_tables]
            
            self.log(f"Found tables: {found_tables}")
            if missing_tables:
                self.log(f"Missing tables: {missing_tables}")
            
            cursor.close()
            conn.close()
            
            if not missing_tables:
                return HealthCheckResult(
                    name=name,
                    passed=True,
                    message="All required tables exist",
                    details={"tables": found_tables}
                )
            else:
                return HealthCheckResult(
                    name=name,
                    passed=False,
                    message=f"Missing tables: {', '.join(missing_tables)}",
                    details={"found": found_tables, "missing": missing_tables}
                )
        except Exception as e:
            return HealthCheckResult(
                name=name,
                passed=False,
                message=f"Schema check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    def check_redis_connection(self) -> HealthCheckResult:
        """Check Redis connection."""
        name = "Redis Connection"
        try:
            self.log(f"Connecting to Redis at {self.redis_config['host']}:{self.redis_config['port']}...")
            
            r = redis.Redis(
                host=self.redis_config["host"],
                port=self.redis_config["port"],
                password=self.redis_config["password"],
                socket_timeout=10,
                decode_responses=True
            )
            
            # Test connection with PING
            response = r.ping()
            
            if response:
                # Get Redis info
                info = r.info("server")
                redis_version = info.get("redis_version", "unknown")
                
                self.log(f"Connected successfully: Redis {redis_version}")
                
                return HealthCheckResult(
                    name=name,
                    passed=True,
                    message="Redis connection successful",
                    details={"version": redis_version, "host": self.redis_config["host"]}
                )
            else:
                return HealthCheckResult(
                    name=name,
                    passed=False,
                    message="Redis PING failed",
                    details={"host": self.redis_config["host"]}
                )
        except Exception as e:
            return HealthCheckResult(
                name=name,
                passed=False,
                message=f"Redis connection failed: {str(e)}",
                details={"host": self.redis_config["host"], "error": str(e)}
            )
    
    def check_redis_persistence(self) -> HealthCheckResult:
        """Check Redis persistence configuration."""
        name = "Redis Persistence"
        try:
            self.log("Checking Redis persistence configuration...")
            
            r = redis.Redis(
                host=self.redis_config["host"],
                port=self.redis_config["port"],
                password=self.redis_config["password"],
                socket_timeout=10,
                decode_responses=True
            )
            
            # Get persistence info
            info = r.info("persistence")
            
            aof_enabled = info.get("aof_enabled", 0) == 1
            rdb_last_save = info.get("rdb_last_save_time", 0)
            
            self.log(f"AOF enabled: {aof_enabled}")
            self.log(f"RDB last save: {rdb_last_save}")
            
            if aof_enabled:
                return HealthCheckResult(
                    name=name,
                    passed=True,
                    message="Redis AOF persistence is enabled",
                    details={"aof_enabled": aof_enabled, "rdb_last_save": rdb_last_save}
                )
            else:
                return HealthCheckResult(
                    name=name,
                    passed=False,
                    message="Redis AOF persistence is not enabled (recommended for data safety)",
                    details={"aof_enabled": aof_enabled, "rdb_last_save": rdb_last_save}
                )
        except Exception as e:
            return HealthCheckResult(
                name=name,
                passed=False,
                message=f"Redis persistence check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    def run_all_checks(self) -> Tuple[bool, List[HealthCheckResult]]:
        """Run all health checks and return results."""
        checks = [
            ("PostgreSQL Connection", self.check_postgres_connection),
            ("TimescaleDB Extension", self.check_timescaledb_extension),
            ("Database Schema", self.check_database_schema),
            ("Redis Connection", self.check_redis_connection),
            ("Redis Persistence", self.check_redis_persistence),
        ]
        
        all_passed = True
        
        for check_name, check_func in checks:
            if self.verbose:
                print(f"\n[CHECK] {check_name}")
            
            result = check_func()
            self.results.append(result)
            
            if not result.passed:
                all_passed = False
        
        return all_passed, self.results


def print_results_text(results: List[HealthCheckResult], all_passed: bool) -> None:
    """Print results in human-readable format."""
    print("\n" + "=" * 60)
    print("PredictBot Database Health Check Results")
    print("=" * 60)
    
    for result in results:
        status = "✓ PASS" if result.passed else "✗ FAIL"
        print(f"\n{status}: {result.name}")
        print(f"       {result.message}")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("Overall Status: ✓ ALL CHECKS PASSED")
    else:
        print("Overall Status: ✗ SOME CHECKS FAILED")
    print("=" * 60)


def print_results_json(results: List[HealthCheckResult], all_passed: bool) -> None:
    """Print results in JSON format."""
    output = {
        "timestamp": datetime.utcnow().isoformat(),
        "all_passed": all_passed,
        "checks": [r.to_dict() for r in results]
    }
    print(json.dumps(output, indent=2))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check health of PostgreSQL and Redis databases for PredictBot"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="Output results in JSON format"
    )
    
    args = parser.parse_args()
    
    # Check for required environment variables
    if not os.getenv("POSTGRES_PASSWORD") and not os.getenv("DATABASE_URL"):
        print("WARNING: POSTGRES_PASSWORD or DATABASE_URL not set in environment")
        print("Using default connection parameters (may fail)")
    
    # Run health checks
    checker = DatabaseHealthChecker(verbose=args.verbose)
    all_passed, results = checker.run_all_checks()
    
    # Print results
    if args.json:
        print_results_json(results, all_passed)
    else:
        print_results_text(results, all_passed)
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
