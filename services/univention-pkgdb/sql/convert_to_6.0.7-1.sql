--
-- Univention Package Database
--  database table definitions
--
-- Copyright 2004-2019 Univention GmbH
--
-- https://www.univention.de/
--
-- All rights reserved.
--
-- The source code of this program is made available
-- under the terms of the GNU Affero General Public License version 3
-- (GNU AGPL V3) as published by the Free Software Foundation.
--
-- Binary versions of this program provided by Univention to you as
-- well as other copyrighted, protected or trademarked materials like
-- Logos, graphics, fonts, specific documentations and configurations,
-- cryptographic keys etc. are subject to a license agreement between
-- you and Univention and not subject to the GNU AGPL V3.
--
-- In the case you use this program under the terms of the GNU AGPL V3,
-- the program is provided in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
-- GNU Affero General Public License for more details.
--
-- You should have received a copy of the GNU Affero General Public
-- License with the Debian GNU/Linux or Univention distribution in file
-- /usr/share/common-licenses/AGPL-3; if not, see
-- <https://www.gnu.org/licenses/>.

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
