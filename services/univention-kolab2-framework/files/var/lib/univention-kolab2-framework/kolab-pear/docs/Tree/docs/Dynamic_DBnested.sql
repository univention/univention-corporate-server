# phpMyAdmin MySQL-Dump
# version 2.3.0
# http://phpwizard.net/phpMyAdmin/
# http://www.phpmyadmin.net/ (download page)
#
# Host: localhost
# Generation Time: Jan 30, 2003 at 06:41 PM
# Server version: 3.23.48
# PHP Version: 4.3.0
# Database : `test`
# --------------------------------------------------------

#
# Table structure for table `nestedTree`
#

CREATE TABLE nestedTree (
  id int(11) NOT NULL default '0',
  name varchar(255) NOT NULL default '',
  l int(11) NOT NULL default '0',
  r int(11) NOT NULL default '0',
  parent int(11) NOT NULL default '0',
  comment varchar(255) NOT NULL default '',
  PRIMARY KEY  (id)
) TYPE=MyISAM;

#
# Dumping data for table `nestedTree`
#

INSERT INTO nestedTree VALUES (1, 'Root', 1, 24, 0, '');
INSERT INTO nestedTree VALUES (2, 'A1', 2, 11, 1, '');
INSERT INTO nestedTree VALUES (3, 'A2', 12, 23, 1, '');
INSERT INTO nestedTree VALUES (4, 'A3', 13, 16, 3, '');
INSERT INTO nestedTree VALUES (5, 'B1', 3, 10, 2, '');
INSERT INTO nestedTree VALUES (6, 'B2', 17, 18, 3, '');
INSERT INTO nestedTree VALUES (7, 'B3', 19, 22, 3, '');
INSERT INTO nestedTree VALUES (8, 'C1', 20, 21, 7, '');
INSERT INTO nestedTree VALUES (9, 'B4', 14, 15, 4, '');
# --------------------------------------------------------

#
# Table structure for table `nestedTree_seq`
#

CREATE TABLE nestedTree_seq (
  id int(10) unsigned NOT NULL auto_increment,
  PRIMARY KEY  (id)
) TYPE=MyISAM;

#
# Dumping data for table `nestedTree_seq`
#

INSERT INTO nestedTree_seq VALUES (3);

