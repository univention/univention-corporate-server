--
-- Univention Package Database
--  database table definitions
--
-- SPDX-FileCopyrightText: 2004-2026 Univention GmbH
-- SPDX-License-Identifier: AGPL-3.0-only

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET client_min_messages = warning;

\connect pkgdb

BEGIN;

ALTER DATABASE pkgdb OWNER TO postgres;

REVOKE ALL PRIVILEGES ON TABLE             systems              FROM pkgdbu;
REVOKE ALL PRIVILEGES ON TABLE packages_on_systems              FROM pkgdbu;

REVOKE ALL PRIVILEGES ON TABLE             systems              FROM pkgdbg;
REVOKE ALL PRIVILEGES ON TABLE packages_on_systems              FROM pkgdbg;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE             systems TO pkgdbg;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE packages_on_systems TO pkgdbg;

DROP TABLE packages;

ALTER TABLE systems
      ALTER sysname    TYPE text,
      ALTER sysversion TYPE text,
      ALTER sysrole    TYPE text,
      ALTER ldaphostdn TYPE text,
      ALTER scandate   TYPE timestamp with time zone,
      DROP  updatedate,
      DROP  updatemessage,
      DROP  upgradedate,
      DROP  upgrademessage,
      DROP  installdate,
      DROP  installmessage,
      DROP  removedate,
      DROP  removemessage,
      ADD   architecture    text
;

ALTER TABLE packages_on_systems
      ALTER sysname    TYPE text,
      ALTER pkgname    TYPE text,
      ALTER vername    TYPE text,
      ALTER vername    DROP NOT NULL,
      ALTER scandate   TYPE timestamp with time zone,
      ADD CONSTRAINT packages_on_systems_sysname_fkey
          FOREIGN KEY (sysname)
          REFERENCES systems(sysname)
;

COMMIT;
