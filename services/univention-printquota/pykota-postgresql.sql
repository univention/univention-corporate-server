--
-- PyKota - Print Quotas for CUPS and LPRng
--
-- (c) 2003, 2004, 2005, 2006, 2007 Jerome Alet <alet@librelogiciel.com>
-- This program is free software; you can redistribute it and/or modify
-- it under the terms of the GNU General Public License as published by
-- the Free Software Foundation; either version 2 of the License, or
-- (at your option) any later version.
--
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU General Public License for more details.
-- 
-- You should have received a copy of the GNU General Public License
-- along with this program.  If not, see <https://www.gnu.org/licenses/>.
--
-- $Id: pykota-postgresql.sql 3133 2007-01-17 22:19:42Z jerome $
--
--

--
-- PyKota Database creation script for PostgreSQL
--
-- Launch this as PostgreSQL administrator with \i
--


--
-- Create the print quota database
--
CREATE DATABASE pykota WITH TEMPLATE=template0 ENCODING='UTF-8';

--
-- Create the print quota database users
-- NOTE: Change the password values to the passwords you would like.
-- 
CREATE USER pykotauser WITH UNENCRYPTED PASSWORD 'readonlypw' NOCREATEDB;
CREATE USER pykotaadmin WITH UNENCRYPTED PASSWORD 'readwritepw' NOCREATEDB;

-- 
-- Now connect to the new database
-- 
\connect pykota

--
-- Create the users table
--
CREATE TABLE users(id SERIAL PRIMARY KEY NOT NULL,
                   username TEXT UNIQUE NOT NULL,
                   email TEXT, 
                   balance FLOAT DEFAULT 0.0,
                   lifetimepaid FLOAT DEFAULT 0.0,
                   limitby TEXT DEFAULT 'quota',
                   description TEXT,
                   overcharge FLOAT NOT NULL DEFAULT 1.0);
                   
--
-- Create the groups table
--
CREATE TABLE groups(id SERIAL PRIMARY KEY NOT NULL,
                    groupname TEXT UNIQUE NOT NULL,
                    description TEXT,
                    limitby TEXT DEFAULT 'quota');
                    
--
-- Create the printers table
--
CREATE TABLE printers(id SERIAL PRIMARY KEY NOT NULL,
                      printername TEXT UNIQUE NOT NULL,
                      description TEXT,
                      priceperpage FLOAT DEFAULT 0.0,
                      priceperjob FLOAT DEFAULT 0.0,
                      passthrough BOOLEAN DEFAULT FALSE,
                      maxjobsize INT4);
                    
--
-- Create the print quota table for users
--
CREATE TABLE userpquota(id SERIAL PRIMARY KEY NOT NULL,
                        userid INT4 REFERENCES users(id),
                        printerid INT4 REFERENCES printers(id),
                        lifepagecounter INT4 DEFAULT 0,
                        pagecounter INT4 DEFAULT 0,
                        softlimit INT4,
                        hardlimit INT4,
                        datelimit TIMESTAMP,
                        maxjobsize INT4,
                        warncount INT4 DEFAULT 0); 
CREATE INDEX userpquota_u_id_ix ON userpquota (userid);
CREATE INDEX userpquota_p_id_ix ON userpquota (printerid);
CREATE UNIQUE INDEX userpquota_up_id_ix ON userpquota (userid, printerid);
                        
--
-- Create the job history table
--
CREATE TABLE jobhistory(id SERIAL PRIMARY KEY NOT NULL,
                        jobid TEXT,
                        userid INT4,
                        printerid INT4,
                        pagecounter INT4 DEFAULT 0,
                        jobsizebytes INT8,
                        jobsize INT4,
                        jobprice FLOAT,
                        action TEXT,
                        filename TEXT,
                        title TEXT,
                        copies INT4,
                        options TEXT,
                        hostname TEXT,
                        md5sum TEXT,
                        pages TEXT,
                        billingcode TEXT,
                        precomputedjobsize INT4,
                        precomputedjobprice FLOAT,
                        jobdate TIMESTAMP DEFAULT now(),
                        CONSTRAINT checkUserPQuota FOREIGN KEY (userid, printerid) REFERENCES userpquota(userid, printerid));
CREATE INDEX jobhistory_u_id_ix ON jobhistory (userid);
CREATE INDEX jobhistory_p_id_ix ON jobhistory (printerid);
CREATE INDEX jobhistory_pd_id_ix ON jobhistory (printerid, jobdate);
CREATE INDEX jobhistory_hostname_ix ON jobhistory (hostname);
                        
--
-- Create the print quota table for groups
--
CREATE TABLE grouppquota(id SERIAL PRIMARY KEY NOT NULL,
                         groupid INT4 REFERENCES groups(id),
                         printerid INT4 REFERENCES printers(id),
                         softlimit INT4,
                         hardlimit INT4,
                         maxjobsize INT4,
                         datelimit TIMESTAMP);
CREATE INDEX grouppquota_g_id_ix ON grouppquota (groupid);
CREATE INDEX grouppquota_p_id_ix ON grouppquota (printerid);
CREATE UNIQUE INDEX grouppquota_up_id_ix ON grouppquota (groupid, printerid);
                        
--                         
-- Create the groups/members relationship
--
CREATE TABLE groupsmembers(groupid INT4 REFERENCES groups(id),
                           userid INT4 REFERENCES users(id),
                           PRIMARY KEY (groupid, userid));
                           
--                         
-- Create the printer groups relationship
--
CREATE TABLE printergroupsmembers(groupid INT4 REFERENCES printers(id),
                           printerid INT4 REFERENCES printers(id),
                           PRIMARY KEY (groupid, printerid));
--
-- Create the table for payments
-- 
CREATE TABLE payments (id SERIAL PRIMARY KEY NOT NULL,
                       userid INT4 REFERENCES users(id),
                       amount FLOAT,
                       description TEXT,
                       date TIMESTAMP DEFAULT now());
CREATE INDEX payments_date_ix ON payments (date);

-- 
-- Create the table for coefficients wrt paper sizes and the like
--
CREATE TABLE coefficients (id SERIAL PRIMARY KEY NOT NULL, 
                           printerid INTEGER NOT NULL REFERENCES printers(id), 
                           label TEXT NOT NULL, 
                           coefficient FLOAT DEFAULT 1.0, 
                           CONSTRAINT coeffconstraint UNIQUE (printerid, label));

-- 
-- Create the table for the billing codes
--
CREATE TABLE billingcodes (id SERIAL PRIMARY KEY NOT NULL,
                           billingcode TEXT UNIQUE NOT NULL,
                           description TEXT,
                           balance FLOAT DEFAULT 0.0,
                           pagecounter INT4 DEFAULT 0);

--                        
-- Set some ACLs                        
--
REVOKE ALL ON users, groups, printers, userpquota, grouppquota, groupsmembers, printergroupsmembers, jobhistory, payments, coefficients, billingcodes FROM public;
REVOKE ALL ON users_id_seq, groups_id_seq, printers_id_seq, userpquota_id_seq, grouppquota_id_seq, jobhistory_id_seq, payments_id_seq, coefficients_id_seq, billingcodes_id_seq FROM public;

GRANT SELECT, INSERT, UPDATE, DELETE, REFERENCES ON users, groups, printers, userpquota, grouppquota, groupsmembers, printergroupsmembers, jobhistory, payments, coefficients, billingcodes TO pykotaadmin;
GRANT SELECT, UPDATE ON users_id_seq, groups_id_seq, printers_id_seq, userpquota_id_seq, grouppquota_id_seq, jobhistory_id_seq, payments_id_seq, coefficients_id_seq, billingcodes_id_seq TO pykotaadmin;
GRANT SELECT ON users, groups, printers, userpquota, grouppquota, groupsmembers, printergroupsmembers, jobhistory, payments, coefficients, billingcodes TO pykotauser;

