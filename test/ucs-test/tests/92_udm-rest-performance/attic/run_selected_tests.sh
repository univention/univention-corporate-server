#!/bin/bash
# Flexible test runner for UDM REST performance tests
# Allows running selected tests or test categories

set -e

# Configuration
HOST="${UCS_HOST:-https://master.ucs.test}"
SPAWN_RATE="${LOCUST_SPAWN_RATE:-1}"
USERS="${LOCUST_USERS:-20}"
RUN_TIME="${LOCUST_RUN_TIME:-2m}"
OUTPUT_DIR="${OUTPUT_DIR:-./results}"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Define test categories
declare -A TESTS=(
    ["user-creation"]="01_user_creation.py:User Creation Tests"
    ["group-creation"]="02_group_creation.py:Group Creation Tests"
    ["user-search"]="03_user_search.py:User Search Tests"
    ["group-search"]="04_group_search.py:Group Search Tests"
    ["object-retrieval"]="05_object_retrieval.py:Object Retrieval Tests"
    ["object-modification"]="06_object_modification.py:Object Modification Tests"
    ["mixed-operations"]="07_mixed_operations.py:Mixed Operations Tests"
)

# Define test categories
declare -A CATEGORIES=(
    ["creation"]="user-creation group-creation"
    ["search"]="user-search group-search"
    ["crud"]="user-creation group-creation object-retrieval object-modification"
    ["core"]="user-creation group-creation user-search group-search object-retrieval"
    ["all"]="user-creation group-creation user-search group-search object-retrieval object-modification mixed-operations"
)

# Function to display usage
show_usage() {
    echo "Usage: $0 [OPTIONS] [TESTS...]"
    echo ""
    echo "Run selected UDM REST performance tests"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help              Show this help message"
    echo "  -l, --list              List available tests and categories"
    echo "  -c, --category CATEGORY Run tests in a specific category"
    echo "  -u, --users USERS       Number of concurrent users (default: $USERS)"
    echo "  -r, --rate RATE         Spawn rate (default: $SPAWN_RATE)"
    echo "  -t, --time TIME         Run time per test (default: $RUN_TIME)"
    echo "  --host HOST             Target host (default: $HOST)"
    echo "  -o, --output DIR        Output directory (default: $OUTPUT_DIR)"
    echo "  -q, --quiet             Quiet mode - less output"
    echo "  -v, --verbose           Verbose mode - more output"
    echo ""
    echo "TESTS:"
    echo "  Individual test names or categories to run"
    echo "  If no tests specified, runs 'core' category"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Run core tests"
    echo "  $0 user-creation group-creation      # Run specific tests"
    echo "  $0 -c creation                       # Run creation category"
    echo "  $0 -c all -u 50 -t 5m               # Run all tests with custom config"
    echo "  $0 --list                            # Show available tests"
}

# Function to list available tests and categories
list_tests() {
    echo "Available Tests:"
    echo "================"
    for test_key in "${!TESTS[@]}"; do
        IFS=':' read -r test_file test_name <<< "${TESTS[$test_key]}"
        echo "  $test_key - $test_name"
    done
    echo ""
    echo "Available Categories:"
    echo "===================="
    for category in "${!CATEGORIES[@]}"; do
        echo "  $category - ${CATEGORIES[$category]}"
    done
}

# Function to run a single test
run_test() {
    local test_key=$1
    local test_entry="${TESTS[$test_key]}"

    if [[ -z "$test_entry" ]]; then
        echo "Error: Unknown test '$test_key'"
        return 1
    fi

    IFS=':' read -r test_file test_name <<< "$test_entry"
    local base_name=$(basename "$test_file" .py)

    if [[ "$VERBOSE" == "true" ]]; then
        echo "Running: $test_name"
        echo "File: $test_file"
        echo "Time: $(date)"
        echo "----------------------------------------"
    elif [[ "$QUIET" != "true" ]]; then
        echo "Running $test_name..."
    fi

    # Build locust command
    local cmd=(
        locust
        -f "92_udm-rest-performance/$test_file"
        --host "$HOST"
        -u "$USERS"
        -r "$SPAWN_RATE"
        -t "$RUN_TIME"
        --csv "$OUTPUT_DIR/$base_name"
        --html "$OUTPUT_DIR/$base_name.html"
        --headless
    )

    if [[ "$QUIET" == "true" ]]; then
        cmd+=(--quiet)
    elif [[ "$VERBOSE" == "true" ]]; then
        cmd+=(--print-stats)
    fi

    # Run the test
    "${cmd[@]}"
    local exit_code=$?

    if [[ "$QUIET" != "true" ]]; then
        if [ $exit_code -eq 0 ]; then
            echo "✓ $test_name completed successfully"
        else
            echo "✗ $test_name failed with exit code $exit_code"
        fi
    fi

    return $exit_code
}

# Function to expand category to test list
expand_category() {
    local category=$1
    local tests="${CATEGORIES[$category]}"

    if [[ -z "$tests" ]]; then
        echo "Error: Unknown category '$category'"
        return 1
    fi

    echo "$tests"
}

# Parse command line arguments
TESTS_TO_RUN=()
CATEGORY=""
QUIET="false"
VERBOSE="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -l|--list)
            list_tests
            exit 0
            ;;
        -c|--category)
            CATEGORY="$2"
            shift 2
            ;;
        -u|--users)
            USERS="$2"
            shift 2
            ;;
        -r|--rate)
            SPAWN_RATE="$2"
            shift 2
            ;;
        -t|--time)
            RUN_TIME="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            mkdir -p "$OUTPUT_DIR"
            shift 2
            ;;
        -q|--quiet)
            QUIET="true"
            shift
            ;;
        -v|--verbose)
            VERBOSE="true"
            shift
            ;;
        -*)
            echo "Error: Unknown option $1"
            show_usage
            exit 1
            ;;
        *)
            TESTS_TO_RUN+=("$1")
            shift
            ;;
    esac
done

# Determine tests to run
FINAL_TESTS=()

if [[ -n "$CATEGORY" ]]; then
    # Use specified category
    CATEGORY_TESTS=$(expand_category "$CATEGORY")
    if [[ $? -ne 0 ]]; then
        exit 1
    fi
    read -ra FINAL_TESTS <<< "$CATEGORY_TESTS"
elif [[ ${#TESTS_TO_RUN[@]} -gt 0 ]]; then
    # Use specified tests
    FINAL_TESTS=("${TESTS_TO_RUN[@]}")
else
    # Default to core category
    CATEGORY_TESTS=$(expand_category "core")
    read -ra FINAL_TESTS <<< "$CATEGORY_TESTS"
fi

# Display configuration
if [[ "$QUIET" != "true" ]]; then
    echo "UDM REST Performance Test Runner"
    echo "================================="
    echo "Host: $HOST"
    echo "Users: $USERS"
    echo "Spawn Rate: $SPAWN_RATE"
    echo "Run Time per test: $RUN_TIME"
    echo "Output Directory: $OUTPUT_DIR"
    echo "Tests to run: ${FINAL_TESTS[*]}"
    echo ""
fi

# Run tests
failed_tests=()
total_tests=${#FINAL_TESTS[@]}
current_test=0

for test_key in "${FINAL_TESTS[@]}"; do
    current_test=$((current_test + 1))

    if [[ "$QUIET" != "true" ]]; then
        echo "[$current_test/$total_tests] Running $test_key"
    fi

    if ! run_test "$test_key"; then
        failed_tests+=("$test_key")
    fi

    # Wait between tests (except for last test)
    if [[ $current_test -lt $total_tests ]] && [[ "$QUIET" != "true" ]]; then
        echo "Waiting 5 seconds before next test..."
        sleep 5
        echo ""
    fi
done

# Final summary
if [[ "$QUIET" != "true" ]]; then
    echo ""
    echo "Test execution completed at $(date)"
    echo ""

    if [[ ${#failed_tests[@]} -eq 0 ]]; then
        echo "✓ All tests passed successfully!"
    else
        echo "✗ Some tests failed:"
        for failed_test in "${failed_tests[@]}"; do
            echo "  - $failed_test"
        done
    fi

    echo ""
    echo "Results are available in: $OUTPUT_DIR"
fi

# Exit with error code if any tests failed
if [[ ${#failed_tests[@]} -gt 0 ]]; then
    exit 1
fi
