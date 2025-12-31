--
-- Univention Package Database
--  database table definitions
--
-- SPDX-FileCopyrightText: 2004-2026 Univention GmbH
-- SPDX-License-Identifier: AGPL-3.0-only

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET client_min_messages = warning;

CREATE DATABASE pkgdb WITH ENCODING = 'UTF8' TEMPLATE = template0;
CREATE GROUP pkgdbg;

\connect pkgdb

BEGIN;
SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET client_min_messages = warning;

CREATE TABLE systems (
    sysname     text                         NOT NULL,
    sysversion  text                         NOT NULL,
    sysrole     text                         NOT NULL,
    ldaphostdn  text                         NOT NULL,
    scandate    timestamp with time zone     NOT NULL,
    architecture   text,
    PRIMARY KEY (sysname)
);

CREATE TABLE packages_on_systems (
    sysname        text                      NOT NULL,
    pkgname        text                      NOT NULL,
    vername        text,
    scandate       timestamp with time zone  NOT NULL,
    inststatus     character(1)              NOT NULL,
    selectedstate  smallint                  NOT NULL,
    inststate      smallint                  NOT NULL,
    currentstate   smallint                  NOT NULL,
    PRIMARY KEY (sysname, pkgname),
    FOREIGN KEY (sysname) REFERENCES systems(sysname)
);

-- TODO which indexes are actually helpful?
CREATE INDEX systems_sysname_index                   ON systems (sysname);
CREATE INDEX systems_sysrole_index                   ON systems (sysrole);
CREATE INDEX systems_sysversion_index                ON systems (sysversion);
CREATE INDEX packages_on_systems_currentstate_index  ON packages_on_systems (currentstate);
CREATE INDEX packages_on_systems_inststate_index     ON packages_on_systems (inststate);
CREATE INDEX packages_on_systems_pkgname_index       ON packages_on_systems (pkgname);
CREATE INDEX packages_on_systems_selectedstate_index ON packages_on_systems (selectedstate);
CREATE INDEX packages_on_systems_sysname_index       ON packages_on_systems (sysname);
CREATE INDEX packages_on_systems_vername_index       ON packages_on_systems (vername);

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE systems TO pkgdbg;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE packages_on_systems TO pkgdbg;

COMMIT;
