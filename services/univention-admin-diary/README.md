[loading relationships]: https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html

# QA and troubleshooting

This section represent short introduction to some common QA and
troubleshooting tasks.

## Performance

Most performance issues come from the lack of SqlAlchemy join strategy ,which
is not easily detectable when you communicate with a database running locally.
In order to check do you have such problems, first thing is to check does your
code matches [loading relationships] recommendations.

Additionally, to be sure you have fond a bottleneck it would be the best
practice that before changing your code, you first trace sql command executed
by your RDBMS server. This depends on system you are actually using:

### PostgreSql

To trace the sql commands you have to increase the log level of postgres. Log
in via SSH to system where your PostgreSql instance is running and find out
where is configuration file located. There are multiple options available but
simplest one is:

```console
# you have to be superuser
$ su - postgres -c "psql -t -c 'SHOW config_file;' | xargs"
```

Output is something similar to `/etc/postgresql/13/main/postgresql.conf`. For
versions of at least 8.0 you have to apply some configuration changes and
restart the service (you have to be superuser for these):

```shell
# config file (output from the previous block)
$ CFG_FILE="/etc/postgresql/13/main/postgresql.conf"
# backup current configuration file
$ cp "${CFG_FILE}" "${CFG_FILE}.bkp"
# apply changes
$ sed -i\
 -e "s/.*log_statement\s*=.*/log_statement = 'all'/"\
 -e "s/.*log_directory\s*=.*/log_directory = 'pg_log'/"\
 -e "s/.*log_filename\s*=.*/log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'/"\
 -e "s/.*logging_collector\s*=.*/logging_collector = on/"\
 -e "s/.*log_min_error_statement\s*=.*/log_min_error_statement = error/"\
 "${CFG_FILE}"
# restart service
$ systemctl restart postgresql
```

When finished, restore original configuration and restart the service:

```shell
$ cp "${CFG_FILE}.bkp" "${CFG_FILE}"
$ systemctl restart postgresql
```

### MariaDb

TBD

### MySQL

TBD

### Testing

This chapter will demonstrate how to track performance issues using model from
[backend.py](./python/admindiary/backend.py).

After installing the `univention-admin-diary`, we have to modify existing data
inserted during the installation process. Those are minimal, but will serve the
purpose. We will set first three rows in table `entries` for columns
`context_id` and `message` to some fixed values, e.g.

```console
# you have to be superuser
su - postgres -c "psql -t -d admindiary -c \"UPDATE entries SET context_id = 'ctx1', message = 'msg1' WHERE id < 4;\""
```

If you visit the `portal` -> `Domain` -> `Admin Diary` you will notice first
three records have a note-like icon in `Comments` section. Clicking any of
those should display three comments which are linked with the above SQL
command.

Starting with version **2.0.7-2** of `univention-admin-diary` there are some
improved loading techniques used in oder to lower the number of SQL commands
that has to be executed when populating results. General rule of thumb is: the
fewer queries the better performance is.

You have to observer statements executed by inspecting log file. Please note
that location of this file depends on system - like RDBMS used, its version and
current date. Following is an example of optimized query - there is only one
SQL command executed to get both entries and events:

```text
2023-06-30 10:10:10.753 CEST [2070-13] admindiary@admindiary LOG:  statement: SELECT anon_1.entries_id AS anon_1_entries_id, anon_1.entries_username AS anon_1
_entries_username, anon_1.entries_hostname AS anon_1_entries_hostname, anon_1.entries_message AS anon_1_entries_message, anon_1.entries_timestamp AS anon_1_en
tries_timestamp, anon_1.entries_context_id AS anon_1_entries_context_id, anon_1.entries_event_id AS anon_1_entries_event_id, anon_1.entries_main_id AS anon_1_
entries_main_id, events_1.id AS events_1_id, events_1.name AS events_1_name, args_1.id AS args_1_id, args_1.entry_id AS args_1_entry_id, args_1.key AS args_1_
key, args_1.value AS args_1_value, entries_1.id AS entries_1_id, entries_1.username AS entries_1_username, entries_1.hostname AS entries_1_hostname, entries_1
.message AS entries_1_message, entries_1.timestamp AS entries_1_timestamp, entries_1.context_id AS entries_1_context_id, entries_1.event_id AS entries_1_event
_id, entries_1.main_id AS entries_1_main_id
        FROM (SELECT entries.id AS entries_id, entries.username AS entries_username, entries.hostname AS entries_hostname, entries.message AS entries_message,
 entries.timestamp AS entries_timestamp, entries.context_id AS entries_context_id, entries.event_id AS entries_event_id, entries.main_id AS entries_main_id
        FROM entries LEFT OUTER JOIN events ON events.id = entries.event_id LEFT OUTER JOIN args ON args.entry_id = entries.id
        WHERE entries.timestamp >= '2023-06-24' AND entries.timestamp < '2023-07-01' ORDER BY entries.id, entries.id
         LIMIT 1000) AS anon_1 LEFT OUTER JOIN events AS events_1 ON events_1.id = anon_1.entries_event_id LEFT OUTER JOIN args AS args_1 ON anon_1.entries_id
 = args_1.entry_id LEFT OUTER JOIN entries AS entries_1 ON entries_1.context_id = anon_1.entries_context_id ORDER BY anon_1.entries_id, anon_1.entries_id
2023-06-30 10:10:11.142 CEST [2070-14] admindiary@admindiary LOG:  statement: SELECT anon_1.entries_id AS anon_1_entries_id, anon_1.entries_username AS anon_1
_entries_username, anon_1.entries_hostname AS anon_1_entries_hostname, anon_1.entries_message AS anon_1_entries_message, anon_1.entries_timestamp AS anon_1_en
tries_timestamp, anon_1.entries_context_id AS anon_1_entries_context_id, anon_1.entries_event_id AS anon_1_entries_event_id, anon_1.entries_main_id AS anon_1_
entries_main_id, events_1.id AS events_1_id, events_1.name AS events_1_name, args_1.id AS args_1_id, args_1.entry_id AS args_1_entry_id, args_1.key AS args_1_
key, args_1.value AS args_1_value, entries_1.id AS entries_1_id, entries_1.username AS entries_1_username, entries_1.hostname AS entries_1_hostname, entries_1
.message AS entries_1_message, entries_1.timestamp AS entries_1_timestamp, entries_1.context_id AS entries_1_context_id, entries_1.event_id AS entries_1_event
_id, entries_1.main_id AS entries_1_main_id
        FROM (SELECT entries.id AS entries_id, entries.username AS entries_username, entries.hostname AS entries_hostname, entries.message AS entries_message,
 entries.timestamp AS entries_timestamp, entries.context_id AS entries_context_id, entries.event_id AS entries_event_id, entries.main_id AS entries_main_id
        FROM entries LEFT OUTER JOIN events ON events.id = entries.event_id LEFT OUTER JOIN args ON args.entry_id = entries.id
        WHERE entries.timestamp >= '2023-06-24' AND entries.timestamp < '2023-07-01' AND entries.id > 10 ORDER BY entries.id, entries.id
         LIMIT 1000) AS anon_1 LEFT OUTER JOIN events AS events_1 ON events_1.id = anon_1.entries_event_id LEFT OUTER JOIN args AS args_1 ON anon_1.entries_id
 = args_1.entry_id LEFT OUTER JOIN entries AS entries_1 ON entries_1.context_id = anon_1.entries_context_id ORDER BY anon_1.entries_id, anon_1.entries_id
2023-06-30 10:10:11.143 CEST [2070-15] admindiary@admindiary LOG:  statement: ROLLBACK
2023-06-30 10:10:11.153 CEST [2076-1] admindiary@admindiary LOG:  statement: BEGIN
2023-06-30 10:10:11.153 CEST [2076-2] admindiary@admindiary LOG:  statement: SELECT t.oid, typarray
        FROM pg_type t JOIN pg_namespace ns
            ON typnamespace = ns.oid
        WHERE typname = 'hstore';
```

With unoptimized join for only two rows, it looks similar to:

```text
2023-06-30 11:08:50.649 CEST [22820] admindiary@admindiary LOG:  statement: BEGIN
2023-06-30 11:08:50.650 CEST [22820] admindiary@admindiary LOG:  statement: SELECT entries.id AS entries_id, entries.username AS entries_username, entries.hos
tname AS entries_hostname, entries.message AS entries_message, entries.timestamp AS entries_timestamp, entries.context_id AS entries_context_id, entries.event
_id AS entries_event_id, entries.main_id AS entries_main_id
        FROM entries
        WHERE entries.timestamp >= '2023-06-02'
2023-06-30 11:08:50.652 CEST [22820] admindiary@admindiary LOG:  statement: SELECT entries.id AS entries_id, entries.username AS entries_username, entries.hos
tname AS entries_hostname, entries.message AS entries_message, entries.timestamp AS entries_timestamp, entries.context_id AS entries_context_id, entries.event
_id AS entries_event_id, entries.main_id AS entries_main_id
        FROM entries
        WHERE entries.timestamp < '2023-07-01'
2023-06-30 11:08:50.656 CEST [22820] admindiary@admindiary LOG:  statement: SELECT entries.id AS entries_id, entries.username AS entries_username, entries.hos
tname AS entries_hostname, entries.message AS entries_message, entries.timestamp AS entries_timestamp, entries.context_id AS entries_context_id, entries.event
_id AS entries_event_id, entries.main_id AS entries_main_id
        FROM entries
        WHERE entries.id IN (1, 2) AND entries.event_id IS NOT NULL
         LIMIT 1000
2023-06-30 11:08:50.657 CEST [22820] admindiary@admindiary LOG:  statement: SELECT events.id AS events_id, events.name AS events_name
        FROM events
        WHERE events.id = 10
2023-06-30 11:08:50.657 CEST [22820] admindiary@admindiary LOG:  statement: SELECT args.id AS args_id, args.entry_id AS args_entry_id, args.key AS args_key, a
rgs.value AS args_value
        FROM args
        WHERE 1 = args.entry_id
2023-06-30 11:08:50.660 CEST [22820] admindiary@admindiary LOG:  statement: SELECT count(*) AS count_1
        FROM (SELECT entries.id AS entries_id, entries.username AS entries_username, entries.hostname AS entries_hostname, entries.message AS entries_message,
 entries.timestamp AS entries_timestamp, entries.context_id AS entries_context_id, entries.event_id AS entries_event_id, entries.main_id AS entries_main_id
        FROM entries
        WHERE entries.context_id = 'ctx1' AND entries.message IS NOT NULL) AS anon_1
2023-06-30 11:08:50.660 CEST [22820] admindiary@admindiary LOG:  statement: SELECT args.id AS args_id, args.entry_id AS args_entry_id, args.key AS args_key, a
rgs.value AS args_value
        FROM args
        WHERE 2 = args.entry_id
2023-06-30 11:08:50.663 CEST [22820] admindiary@admindiary LOG:  statement: SELECT count(*) AS count_1
        FROM (SELECT entries.id AS entries_id, entries.username AS entries_username, entries.hostname AS entries_hostname, entries.message AS entries_message,
 entries.timestamp AS entries_timestamp, entries.context_id AS entries_context_id, entries.event_id AS entries_event_id, entries.main_id AS entries_main_id
        FROM entries
        WHERE entries.context_id = 'ctx1' AND entries.message IS NOT NULL) AS anon_1
2023-06-30 11:08:50.664 CEST [22820] admindiary@admindiary LOG:  statement: SELECT event_messages.event_id AS event_messages_event_id, event_messages.locale A
S event_messages_locale, event_messages.message AS event_messages_message, event_messages.locked AS event_messages_locked
        FROM event_messages, events
        WHERE event_messages.event_id = events.id AND event_messages.locale = 'en' AND events.name = 'JOIN_FINISHED_FAILURE'
2023-06-30 11:08:50.665 CEST [22820] admindiary@admindiary LOG:  statement: COMMIT
```

With increased number of related data this will make progressively more SQL
queries leading to unresponsive system.