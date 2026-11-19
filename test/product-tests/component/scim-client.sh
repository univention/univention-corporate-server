# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

# Utils for the SCIM client tests.

TEST_SERVICES="test-against-reference-server test-against-wire-com test-against-univention-server"
ALL_INVOLVED_SERVICES="$TEST_SERVICES scim-server-reference scim-server-univention downstream-udm-rest-api downstream-ldap-server"

DOCKER_COMPOSE_CMD="docker-compose -p scim-client-producttests -f /root/scim-services/scim-client/tests/docker-compose.yaml -f /root/scim-services/scim-client/tests/docker-compose.producttests.yaml"
CURL_WAIT_CMD="curl --fail --location --silent --show-error --retry 30 --retry-delay 2 --retry-all-errors --max-time 15 --cacert /var/www/ucs-root-ca.crt --output /dev/null"

# Initialize the exit code files for all test containers with NOT_RUN. These let
# us fail the run if any test hasn't run for some reason.
initialize_exit_code_files () {
    for service in $TEST_SERVICES ; do
        echo "NOT-RUN" > "/root/artifacts/scim-client/$service.exit" || exit 1
    done
}

# Wait for local dependencies to be available. the /root/scim-client.env must
# exist.
wait_for_dependencies_to_be_available () {
    # UDM REST API, keycloak and provisioning must be up.
    . /root/scim-client.env && \
        $CURL_WAIT_CMD --user "$TESTCONF_UDM_USERNAME:$TESTCONF_UDM_PASSWORD" \
        "${TESTCONF_UDM_BASE_URL%/}/schema/" || return 1
    . /root/scim-client.env && \
        $CURL_WAIT_CMD \
        "$(univention-keycloak get-keycloak-base-url)/realms/master/.well-known/openid-configuration" \
        || return 1
    . /root/scim-client.env && \
        $CURL_WAIT_CMD \
        --user "admin:$TESTCONF_PROVISIONING_API_ADMIN_PASSWORD" \
        "https://$(ucr get ldap/master)/univention/provisioning/v1/subscriptions" \
        || return 1
    # We expect these docker networks to exist.
    docker network inspect nubus-provisioning keycloak_appcenter_net > /dev/null
}

# Pull all necessary images so we don't accidentally build. The scim-services
# git repo with the compose files must exist at /root/scim-services.
pull_images () {
    . /root/scim-client.env && $DOCKER_COMPOSE_CMD pull $ALL_INVOLVED_SERVICES
}

start_and_wait_for_reference_server () {
    # Start only the reference SCIM server. The docker-compose version used on
    # UCS has no "up --wait". Wait explicitly for the ServiceProviderConfig
    # endpoint.
    . /root/scim-client.env && \
        $DOCKER_COMPOSE_CMD up -d --no-build --no-deps scim-server-reference
    $CURL_WAIT_CMD http://127.0.0.1:8888/ServiceProviderConfig
}

start_and_wait_for_univention_server () {
    # Use the profile so the server can also up its dependencies (downstream UDM
    # and LDAP).
    . /root/scim-client.env && \
        $DOCKER_COMPOSE_CMD --profile dependencies-univention-server \
        up -d --no-build scim-server-univention
    # Unlike the reference implementation, the Univention server uses /v2.
    $CURL_WAIT_CMD http://127.0.0.1:8888/v2/ServiceProviderConfig
}

# Run the test suite against the reference server if UCS_TEST_RUN!=false. The
# reference server must be running.
maybe_run_tests_against_reference () {
    if [ "$UCS_TEST_RUN" = false ]; then
        echo "Skipping tests against reference server"
        echo "SKIPPED" > /root/artifacts/scim-client/test-against-reference-server.exit
        return 0
    fi
    status=0
    . /root/scim-client.env && \
        $DOCKER_COMPOSE_CMD run -T --no-deps \
        --name test-against-reference-server test-against-reference-server \
        --junitxml=/tmp/pytest-junit.xml || status=$?
    echo "$status" > /root/artifacts/scim-client/test-against-reference-server.exit
}

# Run the test suite against wire.com if UCS_TEST_RUN!=false.
maybe_run_tests_against_wire_com () {
    if [ "$UCS_TEST_RUN" = false ]; then
        echo "Skipping tests against wire.com"
        echo "SKIPPED" > /root/artifacts/scim-client/test-against-wire-com.exit
        return 0
    fi
    status=0
    # Passing pytest arguments replaces the service's command, so repeat
    # "-m".
    . /root/scim-client.env && \
    $DOCKER_COMPOSE_CMD run -T --no-deps \
    --name test-against-wire-com test-against-wire-com \
    -m wire_com_integration_tests --junitxml=/tmp/pytest-junit.xml \
    || status=$?
    echo "$status" > /root/artifacts/scim-client/test-against-wire-com.exit
}

# Run the test suite against the Univention server if UCS_TEST_RUN!=false.
maybe_run_tests_against_univention () {
    if [ "$UCS_TEST_RUN" = false ]; then
        echo "Skipping tests against Univention server"
        echo "SKIPPED" > /root/artifacts/scim-client/test-against-univention-server.exit
        return 0
    fi
    status=0
    . /root/scim-client.env && \
        $DOCKER_COMPOSE_CMD run -T --no-deps \
        --name test-against-univention-server \
        test-against-univention-server --junitxml=/tmp/pytest-junit.xml \
        || status=$?
    echo "$status" > /root/artifacts/scim-client/test-against-univention-server.exit
}

# Copy test results (junit.xml) from the test services to
# /root/test-reports/scim-client/ and logs to /root/artifacts/.
copy_test_results_and_logs () {
    status=0
    if [ "$UCS_TEST_RUN" != false ]; then
        for service in $TEST_SERVICES; do
            rm -f "/root/test-reports/scim-client/$service.xml" || status=1
            docker cp "$service:/tmp/pytest-junit.xml" "/root/test-reports/scim-client/$service.xml" || status=1
        done
    fi
    echo "$status" > /root/artifacts/scim-client/collection.exit
    for service in $ALL_INVOLVED_SERVICES; do
        if docker container inspect "$service" > /dev/null 2>&1; then
            docker logs "$service" > "/root/artifacts/$service.log" 2>&1
        fi
    done
    univention-app logs provisioning-service > /root/artifacts/provisioning-service.log 2>&1
    univention-app logs keycloak > /root/artifacts/keycloak.log 2>&1
}

# Remove any old results that may still exist locally, so a failed download
# cannot leave old XML/status files masquerading as this run.
remove_old_local_results () {
    if [ "$UCS_TEST_RUN" = false ]; then
        return 0
    fi
    if [ "$#" -ne 1 ] || [ -z "$1" ]; then
        echo "Usage: remove_old_local_results BASE_DIR" >&2
        return 2
    fi
    local base_dir="$1"
    status=0
    for suite in $TEST_SERVICES; do
        rm -f \
            "$base_dir/test-reports/scim-client/$suite.xml" \
            "$base_dir/artifacts/scim-client/$suite.exit" || status=1
    done
    rm -f "$base_dir/artifacts/scim-client/collection.exit" || status=1
    exit "$status"
}

# Validate results already downloaded to the runner. remove_old_local_results
# must run before fetch-results so stale files cannot satisfy these checks.
# Require nonempty files and successful exit codes. This function returns a
# status, it does not exit the shell sourcing this file.
check_local_test_results () {
    if [ "$UCS_TEST_RUN" = false ]; then
        return 0
    fi
    if [ "$#" -ne 1 ] || [ -z "$1" ]; then
        echo "Usage: check_local_test_results BASE_DIR" >&2
        return 2
    fi

    local base_dir="$1" status=0 service file code

    file="$base_dir/artifacts/scim-client/collection.exit"
    if [ ! -f "$file" ] || [ ! -s "$file" ]; then
        echo "Missing or empty collection status: $file" >&2
        status=1
    elif code="$(cat "$file")"; then
        if [ "$code" != 0 ]; then
            echo "Report collection failed: $file contains '$code'" >&2
            status=1
        fi
    else
        echo "Cannot read collection status: $file" >&2
        status=1
    fi

    for service in $TEST_SERVICES; do
        file="$base_dir/test-reports/scim-client/$service.xml"
        if [ ! -f "$file" ] || [ ! -s "$file" ] || [ ! -r "$file" ]; then
            echo "Missing, empty, or unreadable JUnit report: $file" >&2
            status=1
        fi

        file="$base_dir/artifacts/scim-client/$service.exit"
        if [ ! -f "$file" ] || [ ! -s "$file" ]; then
            echo "Missing or empty suite status: $file" >&2
            status=1
            continue
        fi
        if ! code="$(cat "$file")"; then
            echo "Cannot read suite status: $file" >&2
            status=1
            continue
        fi

        echo "$service: exit $code"
        if [ "$code" != 0 ] ; then
            echo "Unexpected suite status in $file: '$code'" >&2
            status=1
        fi
    done
    return "$status"
}
