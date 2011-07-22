# Default init script logging functions suitable for usplash.
# See /lib/lsb/init-functions for usage help.

log_use_plymouth () {
    plymouth --ping >/dev/null 2>&1
}

log_begin_msg () {
    if [ -z "${1:-}" ]; then
        return 1
    fi
    if log_use_plymouth; then
        plymouth message --text="$@" || true
    fi
    echo -n "$@"
}

log_daemon_msg () {
    if [ -z "${1:-}" ]; then
        return 1
    fi
    log_daemon_msg_pre "$@"

    if log_use_plymouth; then
        plymouth message --text="$@" || true
    fi

    if [ -z "${2:-}" ]; then
        echo -n "$1:"
        return
    fi

    echo -n "$1: $2"
    log_daemon_msg_post "$@"
}

log_action_begin_msg () {
    echo -n "$@..."
    if log_use_plymouth; then
        plymouth message --text="$@" || true
    fi
}

#log_progress_msg () {
#    if [ -z "${1:-}" ]; then
#        return 1
#    fi
#    if log_use_plymouth; then
#        plymouth message --text="$@" || true
#    fi
#    echo -n " $@"
#}

log_action_msg () {
    if log_use_plymouth; then
        plymouth message --text="$@" || true
    fi
    echo "$@."
}

#log_action_begin_msg () {
#    log_daemon_msg "$@..."
#}
#
#log_action_cont_msg () {
#    log_daemon_msg "$@..."
#}
#
#log_action_end_msg () {
#    # In the future this may do something with $2 as well.
#    log_end_msg "$1" || :
#}
