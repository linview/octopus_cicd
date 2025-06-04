#!/bin/bash

set -ex

PROJ_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd ${PROJ_ROOT}

# Test configuration
PYTHON_VERSIONS=("3.9" "3.10" "3.11" "3.12")
TEST_DIRS=(
    "octopus/dsl/ut"
    # Add other test directories here
)

# Install dependencies
install_dependencies() {
    echo "Installing dependencies..."
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
}

# Run tests for a single directory
run_test_dir() {
    local test_dir=$1
    echo "Running tests in $test_dir"
    pytest $test_dir -v --cov=$test_dir/.. --cov-report=xml
}

# Main function
main() {
    # Install dependencies
    install_dependencies

    # Run all tests
    local failed=0
    for test_dir in "${TEST_DIRS[@]}"; do
        if ! run_test_dir "$test_dir"; then
            failed=1
            echo "Tests in $test_dir failed"
        fi
    done

    # Upload coverage report
    if [ -f "coverage.xml" ]; then
        echo "Uploading coverage report..."
        # Add coverage report upload code here
    fi

    exit $failed
}

main
