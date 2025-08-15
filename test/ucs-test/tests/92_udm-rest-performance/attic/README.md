# UDM REST API Performance Tests

This directory contains Locust-based performance tests for the Univention Directory Manager (UDM) REST API. The tests are split into focused, 2-minute test suites that benchmark specific operations on users and groups.

## Test Structure

The original comprehensive test has been split into smaller, focused tests that each run for 2 minutes. This allows for:
- Better isolation of performance issues
- Faster feedback on specific operations
- Easier analysis of individual operation types
- Reduced test execution time per test

## Test Files

### Individual Performance Tests (2 minutes each)

- **`01_user_creation.py`** - User creation performance tests
  - Basic user creation
  - Users with email addresses
  - Users with first names
  - Bulk user creation operations

- **`02_group_creation.py`** - Group creation performance tests
  - Basic group creation
  - Security groups
  - Distribution groups
  - Bulk group creation operations

- **`03_user_search.py`** - User search performance tests
  - Search all users
  - Filtered searches by username patterns
  - Search by lastname, email, and other attributes
  - Recently created and disabled user searches

- **`04_group_search.py`** - Group search performance tests
  - Search all groups
  - Filtered searches by group name patterns
  - Security and distribution group searches
  - Groups with members and recent groups

- **`05_object_retrieval.py`** - Object retrieval performance tests
  - Single user/group retrieval by DN
  - Retrieval with specific properties
  - Full object details retrieval
  - Sequential multiple object retrieval
  - Search-then-retrieve workflows

- **`06_object_modification.py`** - Object modification performance tests
  - User description, email, phone modifications
  - Group description modifications
  - Multiple field modifications
  - Sequential modifications on same objects

- **`07_mixed_operations.py`** - Mixed operation workflows
  - Create-search-modify workflows
  - Bulk operation sequences
  - Cross-reference operations between users and groups
  - Error handling scenarios

### Original Comprehensive Test

- **`udm_rest_core_operations.py`** - Original 10-minute comprehensive test (kept for reference)

### Test Execution Scripts

- **`run_all_tests.sh`** - Script to execute all 2-minute tests sequentially
- **`run_tests.sh`** - Original test execution script

### Utility Files

- **`rest_utils.py`** - Shared utilities and classes for UDM REST API testing

## Usage

### Running Individual Tests

Each test can be run independently:

```bash
# Run user creation test
/usr/share/ucs-test/runner /usr/share/ucs-test/locust-docker UserCreationTest

# Run group search test
/usr/share/ucs-test/runner /usr/share/ucs-test/locust-docker GroupSearchTest

# Run with custom parameters
/usr/share/ucs-test/runner /usr/share/ucs-test/locust \
  --spawn-rate 5 -u 20 -t 2m \
  --csv UserCreation --html UserCreation.html \
  UserCreationTest
```

### Running All Tests Sequentially

Use the provided script to run all tests in sequence:

```bash
# Run all tests with default settings
./run_all_tests.sh

# Run with custom configuration
UCS_HOST=https://your-server.domain \
LOCUST_USERS=30 \
LOCUST_SPAWN_RATE=10 \
OUTPUT_DIR=./my-results \
./run_all_tests.sh
```

### Running Original Comprehensive Test

```bash
# Run the original 10-minute comprehensive test
/usr/share/ucs-test/runner /usr/share/ucs-test/locust-docker UDMRestCoreOperations
```

## Configuration

### Environment Variables

All tests support the same configuration variables:

- `LOCUST_SPAWN_RATE` - Rate of user spawning (default: 5 for 2-min tests)
- `LOCUST_RUN_TIME` - Test duration (default: 2m for individual tests)
- `LOCUST_USERS` - Number of concurrent users (default: 20)
- `WAIT_MIN` - Minimum wait time between requests (default: 1s)
- `WAIT_MAX` - Maximum wait time between requests (default: 3s)
- `TIMEOUT` - HTTP request timeout (default: 300s)

### Test-Specific Configuration

#### run_all_tests.sh Variables
- `UCS_HOST` - Target UCS server (default: https://master.ucs.test)
- `OUTPUT_DIR` - Results output directory (default: ./results)

## Test Operations

### User Operations
- **Create User** - Various user creation scenarios with different attributes
- **Search Users** - Pattern-based searches, filtered queries, bulk searches
- **Get User** - Single and multiple user retrieval operations
- **Modify User** - Description, email, firstname, lastname, phone modifications

### Group Operations
- **Create Group** - Basic, security, and distribution group creation
- **Search Groups** - Pattern-based searches, type-specific queries
- **Get Group** - Single and multiple group retrieval operations
- **Modify Group** - Description and other property modifications

### Mixed Operations
- **Workflows** - Create-search-modify sequences
- **Cross-references** - Operations spanning users and groups
- **Error Handling** - Non-existent object handling
- **Bulk Operations** - Sequential and concurrent operation patterns

## Test Data Prefixes

Each test uses a unique prefix to avoid conflicts:
- User Creation: `usercreation`
- Group Creation: `groupcreation`
- User Search: `usersearch`
- Group Search: `groupsearch`
- Object Retrieval: `objretrieval`
- Object Modification: `objmod`
- Mixed Operations: `mixed`

## Results and Analysis

### Individual Test Results

Each test produces:
- **HTML Report** - `{test_name}.html` - Visual performance dashboard
- **CSV Stats** - `{test_name}_stats.csv` - Request statistics
- **CSV History** - `{test_name}_stats_history.csv` - Time-series data
- **CSV Failures** - `{test_name}_failures.csv` - Error details

### Sequential Test Results

When using `run_all_tests.sh`:
- Individual results for each test
- `test_summary.txt` - Execution summary
- Organized output directory structure

### Key Metrics per Test

1. **Creation Tests** - Object creation rate, success rate, response times
2. **Search Tests** - Search performance, result counts, pagination efficiency
3. **Retrieval Tests** - Individual object access times, batch retrieval performance
4. **Modification Tests** - Update operation speed, concurrent modification handling
5. **Mixed Tests** - Workflow completion times, complex operation sequences

## Performance Baselines

### Expected Performance (per test type)

- **Creation Tests** - 10-50 objects/second depending on complexity
- **Search Tests** - 50-200 searches/second depending on result size
- **Retrieval Tests** - 100-300 retrievals/second for individual objects
- **Modification Tests** - 20-100 modifications/second
- **Mixed Tests** - Varies by workflow complexity

## Troubleshooting

### Test-Specific Issues

1. **Creation Tests Failing**
   - Check LDAP write permissions
   - Verify sufficient disk space
   - Monitor LDAP server load

2. **Search Tests Slow**
   - Check LDAP indexing
   - Monitor memory usage
   - Verify network latency

3. **Retrieval Tests Errors**
   - Ensure objects exist from creation tests
   - Check object cleanup timing
   - Verify DN format correctness

4. **Sequential Test Issues**
   - Check script permissions (`chmod +x run_all_tests.sh`)
   - Verify output directory write access
   - Monitor system resources during full suite

### Common Solutions

- Run tests individually to isolate issues
- Check UCS system logs during test execution
- Verify UDM REST API service status
- Monitor LDAP backend performance

## Integration

### CI/CD Integration

The 2-minute test structure is ideal for CI/CD pipelines:

```bash
# Quick validation (single test)
./01_user_creation.py

# Full validation (all tests, ~20 minutes total)
./run_all_tests.sh
```

### Custom Test Selection

Run specific test combinations:

```bash
# Only creation tests
./01_user_creation.py && ./02_group_creation.py

# Only search tests
./03_user_search.py && ./04_group_search.py

# Core operations only
./05_object_retrieval.py && ./06_object_modification.py
```
