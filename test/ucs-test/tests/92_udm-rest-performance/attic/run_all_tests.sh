#!/bin/bash
# Script to run all UDM REST performance tests sequentially
# Each test runs for 2 minutes with the specified configuration

# Removed set -e to continue running all tests even if one fails

# Configuration
HOST="${UCS_HOST:-https://master.ucs.test}"
SPAWN_RATE="${LOCUST_SPAWN_RATE:-1}"
USERS="${LOCUST_USERS:-20}"
RUN_TIME="${LOCUST_RUN_TIME:-2m}"
OUTPUT_DIR="${OUTPUT_DIR:-./results}"

# Failure tracking
FAILED_TESTS=()
TOTAL_TESTS=0
SUCCESSFUL_TESTS=0

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "Starting UDM REST Performance Test Suite"
echo "========================================"
echo "Host: $HOST"
echo "Users: $USERS"
echo "Spawn Rate: $SPAWN_RATE"
echo "Run Time per test: $RUN_TIME"
echo "Output Directory: $OUTPUT_DIR"
echo ""

# List of test files and their descriptions
declare -a TESTS=(
    "01_user_creation.py:User Creation Tests"
    "02_group_creation.py:Group Creation Tests"
    "03_user_search.py:User Search Tests"
    "04_group_search.py:Group Search Tests"
    "05_object_retrieval.py:Object Retrieval Tests"
    "06_object_modification.py:Object Modification Tests"
    "07_mixed_operations.py:Mixed Operations Tests"
)

# Function to run a single test
run_test() {
    local test_file=$1
    local test_name=$2
    local base_name=$(basename "$test_file" .py)

    echo "Running: $test_name"
    echo "File: $test_file"
    echo "Time: $(date)"
    echo "----------------------------------------"

    # Run the test with locust
    locust \
        -f "./$test_file" \
        --host "$HOST" \
        -u "$USERS" \
        -r "$SPAWN_RATE" \
        -t "$RUN_TIME" \
        --csv "$OUTPUT_DIR/$base_name" \
        --html "$OUTPUT_DIR/$base_name.html" \
        --headless \
        --print-stats

    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        echo "✓ $test_name completed successfully"
        SUCCESSFUL_TESTS=$((SUCCESSFUL_TESTS + 1))
    else
        echo "✗ $test_name failed with exit code $exit_code"
        FAILED_TESTS+=("$test_name (exit code: $exit_code)")
    fi

    echo ""
    echo "Waiting 1 second before next test..."
    sleep 1
    echo ""
}

# Main execution
echo "Starting test execution at $(date)"
echo ""

total_tests=${#TESTS[@]}
current_test=0

for test_entry in "${TESTS[@]}"; do
    current_test=$((current_test + 1))
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    # Split the entry into file and description
    IFS=':' read -r test_file test_description <<< "$test_entry"

    echo "[$current_test/$total_tests] $test_description"
    run_test "$test_file" "$test_description"
done

echo "All tests completed at $(date)"
echo ""

# Display test results summary
echo "Test Execution Summary:"
echo "======================="
echo "Total tests: $TOTAL_TESTS"
echo "Successful tests: $SUCCESSFUL_TESTS"
echo "Failed tests: ${#FAILED_TESTS[@]}"

if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
    echo ""
    echo "Failed tests:"
    for failed_test in "${FAILED_TESTS[@]}"; do
        echo "  - $failed_test"
    done
    echo ""
fi

# Generate summary report
echo "Generating summary report..."
cat > "$OUTPUT_DIR/test_summary.txt" << EOF
UDM REST Performance Test Suite Summary
======================================
Execution Date: $(date)
Host: $HOST
Users: $USERS
Spawn Rate: $SPAWN_RATE
Run Time per test: $RUN_TIME

Tests Executed:
EOF

for test_entry in "${TESTS[@]}"; do
    IFS=':' read -r test_file test_description <<< "$test_entry"
    base_name=$(basename "$test_file" .py)
    echo "- $test_description ($base_name)" >> "$OUTPUT_DIR/test_summary.txt"
done

cat >> "$OUTPUT_DIR/test_summary.txt" << EOF

Test Results Summary:
Total tests: $TOTAL_TESTS
Successful tests: $SUCCESSFUL_TESTS
Failed tests: ${#FAILED_TESTS[@]}
EOF

if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
    cat >> "$OUTPUT_DIR/test_summary.txt" << EOF

Failed tests:
EOF
    for failed_test in "${FAILED_TESTS[@]}"; do
        echo "  - $failed_test" >> "$OUTPUT_DIR/test_summary.txt"
    done
fi

cat >> "$OUTPUT_DIR/test_summary.txt" << EOF

Output Files:
- Individual CSV results: ${base_name}_stats.csv, ${base_name}_stats_history.csv, ${base_name}_failures.csv
- Individual HTML reports: ${base_name}.html
- This summary: test_summary.txt

To view detailed results, open the HTML files in a web browser.
EOF

echo "Summary report saved to: $OUTPUT_DIR/test_summary.txt"
echo ""
echo "Test suite execution completed!"
echo "Results are available in: $OUTPUT_DIR"

# Exit with error code if any tests failed
if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
    exit 1
else
    exit 0
fi
