#!/usr/bin/env python3
"""
Test Runner Script
==================

Comprehensive test runner for PredictBot Stack.
Supports running unit, integration, and e2e tests with various options.

Usage:
    python scripts/run_tests.py                    # Run all tests
    python scripts/run_tests.py --unit             # Run unit tests only
    python scripts/run_tests.py --integration      # Run integration tests only
    python scripts/run_tests.py --e2e              # Run e2e tests only
    python scripts/run_tests.py --coverage         # Run with coverage report
    python scripts/run_tests.py --fast             # Skip slow tests
    python scripts/run_tests.py --verbose          # Verbose output
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime


# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(message: str):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(message: str):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")


def print_error(message: str):
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_info(message: str):
    """Print an info message."""
    print(f"{Colors.CYAN}ℹ {message}{Colors.ENDC}")


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def check_dependencies():
    """Check if required test dependencies are installed."""
    required = ['pytest', 'pytest-asyncio', 'pytest-cov']
    missing = []
    
    for package in required:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print_error(f"Missing dependencies: {', '.join(missing)}")
        print_info("Install with: pip install pytest pytest-asyncio pytest-cov")
        return False
    
    return True


def run_tests(
    test_type: str = "all",
    coverage: bool = False,
    verbose: bool = False,
    fast: bool = False,
    parallel: bool = False,
    output_file: str = None,
) -> int:
    """
    Run tests with specified options.
    
    Args:
        test_type: Type of tests to run (all, unit, integration, e2e)
        coverage: Whether to generate coverage report
        verbose: Whether to use verbose output
        fast: Whether to skip slow tests
        parallel: Whether to run tests in parallel
        output_file: File to write test results to
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    project_root = get_project_root()
    tests_dir = project_root / "tests"
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test directory based on type
    if test_type == "unit":
        cmd.append(str(tests_dir / "unit"))
        print_header("Running Unit Tests")
    elif test_type == "integration":
        cmd.append(str(tests_dir / "integration"))
        print_header("Running Integration Tests")
    elif test_type == "e2e":
        cmd.append(str(tests_dir / "e2e"))
        print_header("Running End-to-End Tests")
    else:
        cmd.append(str(tests_dir))
        print_header("Running All Tests")
    
    # Add options
    if verbose:
        cmd.append("-v")
        cmd.append("--tb=long")
    else:
        cmd.append("--tb=short")
    
    if fast:
        cmd.extend(["-m", "not slow"])
        print_info("Skipping slow tests")
    
    if coverage:
        cmd.extend([
            "--cov=.",
            "--cov-report=term-missing",
            "--cov-report=html:coverage_report",
            "--cov-config=.coveragerc",
        ])
        print_info("Coverage reporting enabled")
    
    if parallel:
        cmd.extend(["-n", "auto"])
        print_info("Running tests in parallel")
    
    if output_file:
        cmd.extend(["--junitxml", output_file])
        print_info(f"Writing results to {output_file}")
    
    # Add color output
    cmd.append("--color=yes")
    
    # Print command
    print_info(f"Command: {' '.join(cmd)}")
    print()
    
    # Run tests
    start_time = datetime.now()
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            env={**os.environ, "PYTHONPATH": str(project_root)},
        )
        exit_code = result.returncode
    except KeyboardInterrupt:
        print_error("\nTests interrupted by user")
        exit_code = 130
    except Exception as e:
        print_error(f"Error running tests: {e}")
        exit_code = 1
    
    # Print summary
    duration = datetime.now() - start_time
    print()
    
    if exit_code == 0:
        print_success(f"All tests passed! (Duration: {duration})")
    else:
        print_error(f"Tests failed with exit code {exit_code} (Duration: {duration})")
    
    return exit_code


def run_specific_test(test_path: str, verbose: bool = False) -> int:
    """Run a specific test file or test function."""
    project_root = get_project_root()
    
    cmd = ["python", "-m", "pytest", test_path, "-v" if verbose else ""]
    cmd = [c for c in cmd if c]  # Remove empty strings
    
    print_header(f"Running: {test_path}")
    
    result = subprocess.run(
        cmd,
        cwd=str(project_root),
        env={**os.environ, "PYTHONPATH": str(project_root)},
    )
    
    return result.returncode


def generate_coverage_report():
    """Generate HTML coverage report."""
    project_root = get_project_root()
    
    print_header("Generating Coverage Report")
    
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "--cov=.",
        "--cov-report=html:coverage_report",
        "--cov-report=term-missing",
        "-q",
    ]
    
    result = subprocess.run(
        cmd,
        cwd=str(project_root),
        env={**os.environ, "PYTHONPATH": str(project_root)},
    )
    
    if result.returncode == 0:
        report_path = project_root / "coverage_report" / "index.html"
        print_success(f"Coverage report generated: {report_path}")
    
    return result.returncode


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="PredictBot Stack Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/run_tests.py                    # Run all tests
    python scripts/run_tests.py --unit             # Run unit tests only
    python scripts/run_tests.py --integration      # Run integration tests
    python scripts/run_tests.py --e2e              # Run e2e tests
    python scripts/run_tests.py --coverage         # With coverage report
    python scripts/run_tests.py --fast             # Skip slow tests
    python scripts/run_tests.py -t tests/unit/test_event_bus.py  # Specific test
        """
    )
    
    # Test type selection
    type_group = parser.add_mutually_exclusive_group()
    type_group.add_argument(
        "--unit", "-u",
        action="store_true",
        help="Run unit tests only"
    )
    type_group.add_argument(
        "--integration", "-i",
        action="store_true",
        help="Run integration tests only"
    )
    type_group.add_argument(
        "--e2e", "-e",
        action="store_true",
        help="Run end-to-end tests only"
    )
    type_group.add_argument(
        "-t", "--test",
        type=str,
        help="Run specific test file or function"
    )
    
    # Options
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--fast", "-f",
        action="store_true",
        help="Skip slow tests"
    )
    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Run tests in parallel (requires pytest-xdist)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file for test results (JUnit XML format)"
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Generate coverage report only (no tests)"
    )
    
    args = parser.parse_args()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Handle report-only mode
    if args.report_only:
        sys.exit(generate_coverage_report())
    
    # Handle specific test
    if args.test:
        sys.exit(run_specific_test(args.test, args.verbose))
    
    # Determine test type
    if args.unit:
        test_type = "unit"
    elif args.integration:
        test_type = "integration"
    elif args.e2e:
        test_type = "e2e"
    else:
        test_type = "all"
    
    # Run tests
    exit_code = run_tests(
        test_type=test_type,
        coverage=args.coverage,
        verbose=args.verbose,
        fast=args.fast,
        parallel=args.parallel,
        output_file=args.output,
    )
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
