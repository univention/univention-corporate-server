CREATE TABLE IF NOT EXISTS entries (
	id SERIAL PRIMARY KEY,
	username VARCHAR NOT NULL,
	hostname VARCHAR NOT NULL,
	message TEXT,
	args VARCHAR[],
	timestamp TIMESTAMPTZ NOT NULL,
	tags VARCHAR[],
	context_id VARCHAR NOT NULL,
	event_id INT REFERENCES events (id) ON DELETE RESTRICT,
	main_id INT REFERENCES entries (id) ON DELETE CASCADE,
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE entries OWNER TO admindiary;
CREATE INDEX idx_entries_context    ON entries           (context_id);
CREATE INDEX idx_entries_main_id    ON entries           (main_id);
CREATE INDEX idx_entries_hostname   ON entries           (hostname);
CREATE INDEX idx_entries_timestamp  ON entries           (timestamp);
CREATE INDEX idx_entries_tags       ON entries USING GIN (tags);
CREATE TABLE IF NOT EXISTS events (
	id SERIAL PRIMARY KEY,
	name VARCHAR NOT NULL UNIQUE
);
ALTER TABLE events OWNER TO admindiary;
CREATE TABLE IF NOT EXISTS event_message_translations (
	event_id INT REFERENCES events (id) ON DELETE CASCADE,
	locale VARCHAR NOT NULL,
	locked BOOLEAN DEFAULT FALSE,
	message VARCHAR NOT NULL,
	UNIQUE (event_id, locale)
);
ALTER TABLE event_message_translations OWNER TO admindiary;

INSERT INTO events (name) VALUES ('USER_CREATED') ON CONFLICT DO NOTHING;
INSERT INTO event_message_translations (event_id, locale, locked, message) VALUES ((SELECT id FROM events WHERE name = 'USER_CREATED'), 'en', TRUE, 'User {0} created') ON CONFLICT ON CONSTRAINT event_message_translations_event_id_locale_key DO UPDATE SET locked = TRUE, message = 'User {0} created';
INSERT INTO event_message_translations (event_id, locale, locked, message) VALUES ((SELECT id FROM events WHERE name = 'USER_CREATED'), 'de', TRUE, 'Benutzer {0} angelegt') ON CONFLICT ON CONSTRAINT event_message_translations_event_id_locale_key DO UPDATE SET locked = TRUE, message = 'Benutzer {0} angelegt';

INSERT INTO events (name) VALUES ('APP_ACTION_START') ON CONFLICT DO NOTHING;
INSERT INTO event_message_translations (event_id, locale, locked, message) VALUES ((SELECT id FROM events WHERE name = 'APP_ACTION_START'), 'en', TRUE, 'App {0}: Start of {1}') ON CONFLICT ON CONSTRAINT event_message_translations_event_id_locale_key DO UPDATE SET locked = TRUE, message = 'App {0}: Start of {1}';
INSERT INTO event_message_translations (event_id, locale, locked, message) VALUES ((SELECT id FROM events WHERE name = 'APP_ACTION_START'), 'de', TRUE, 'App {1}: Start von {2}') ON CONFLICT ON CONSTRAINT event_message_translations_event_id_locale_key DO UPDATE SET locked = TRUE, message = 'App {0}: Start von {1}';

INSERT INTO events (name) VALUES ('APP_ACTION_SUCCESS') ON CONFLICT DO NOTHING;
INSERT INTO event_message_translations (event_id, locale, locked, message) VALUES ((SELECT id FROM events WHERE name = 'APP_ACTION_SUCCESS'), 'en', TRUE, 'App {0} ({1}): Success') ON CONFLICT ON CONSTRAINT event_message_translations_event_id_locale_key DO UPDATE SET locked = TRUE, message = 'App {0} ({1}): Success';
INSERT INTO event_message_translations (event_id, locale, locked, message) VALUES ((SELECT id FROM events WHERE name = 'APP_ACTION_SUCCESS'), 'de', TRUE, 'App {0} ({1}): Erfolg') ON CONFLICT ON CONSTRAINT event_message_translations_event_id_locale_key DO UPDATE SET locked = TRUE, message = 'App {0} ({1}): Erfolg';

INSERT INTO events (name) VALUES ('APP_ACTION_FAILURE') ON CONFLICT DO NOTHING;
INSERT INTO event_message_translations (event_id, locale, locked, message) VALUES ((SELECT id FROM events WHERE name = 'APP_ACTION_FAILURE'), 'en', TRUE, 'App {0} ({1}): Failure. Error {2}') ON CONFLICT ON CONSTRAINT event_message_translations_event_id_locale_key DO UPDATE SET locked = TRUE, message = 'App {0} ({1}): Failure. Error {2}';
INSERT INTO event_message_translations (event_id, locale, locked, message) VALUES ((SELECT id FROM events WHERE name = 'APP_ACTION_FAILURE'), 'de', TRUE, 'App {0} ({1}): Fehlschlag. Fehler {2}') ON CONFLICT ON CONSTRAINT event_message_translations_event_id_locale_key DO UPDATE SET locked = TRUE, message = 'App {0} ({1}): Fehlschlag. Fehler {2}';

INSERT INTO events (name) VALUES ('SERVER_PASSWORD_CHANGED') ON CONFLICT DO NOTHING;
INSERT INTO event_message_translations (event_id, locale, locked, message) VALUES ((SELECT id FROM events WHERE name = 'SERVER_PASSWORD_CHANGED'), 'en', TRUE, 'Machine account password changed successfully') ON CONFLICT ON CONSTRAINT event_message_translations_event_id_locale_key DO UPDATE SET locked = TRUE, message = 'Machine account password changed successfully';
INSERT INTO event_message_translations (event_id, locale, locked, message) VALUES ((SELECT id FROM events WHERE name = 'SERVER_PASSWORD_CHANGED'), 'de', TRUE, 'Maschinenpasswort erfolgreich geändert') ON CONFLICT ON CONSTRAINT event_message_translations_event_id_locale_key DO UPDATE SET locked = TRUE, message = 'Maschinenpasswort erfolgreich geändert';

INSERT INTO events (name) VALUES ('SERVER_PASSWORD_CHANGED_FAILED') ON CONFLICT DO NOTHING;
INSERT INTO event_message_translations (event_id, locale, locked, message) VALUES ((SELECT id FROM events WHERE name = 'SERVER_PASSWORD_CHANGED_FAILED'), 'en', TRUE, 'Machine account password change failed') ON CONFLICT ON CONSTRAINT event_message_translations_event_id_locale_key DO UPDATE SET locked = TRUE, message = 'Machine account password change failed';
INSERT INTO event_message_translations (event_id, locale, locked, message) VALUES ((SELECT id FROM events WHERE name = 'SERVER_PASSWORD_CHANGED_FAILED'), 'de', TRUE, 'Änderung des Maschinenpassworts fehlgeschlagen') ON CONFLICT ON CONSTRAINT event_message_translations_event_id_locale_key DO UPDATE SET locked = TRUE, message = 'Änderung des Maschinenpassworts fehlgeschlagen';
