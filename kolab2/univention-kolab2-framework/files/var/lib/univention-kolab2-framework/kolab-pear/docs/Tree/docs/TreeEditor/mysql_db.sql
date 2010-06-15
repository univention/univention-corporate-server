# phpMyAdmin MySQL-Dump
# version 2.3.0
# http://phpwizard.net/phpMyAdmin/
# http://www.phpmyadmin.net/ (download page)
#
# Host: localhost
# Generation Time: Jan 30, 2003 at 06:40 PM
# Server version: 3.23.48
# PHP Version: 4.3.0
# Database : `test`
# --------------------------------------------------------

#
# Table structure for table `Tree_Nested`
#

CREATE TABLE Tree_Nested (
  id int(11) NOT NULL default '0',
  name varchar(255) NOT NULL default '',
  l int(11) NOT NULL default '0',
  r int(11) NOT NULL default '0',
  parent int(11) NOT NULL default '0',
  comment varchar(255) NOT NULL default '',
  PRIMARY KEY  (id)
) TYPE=MyISAM;

#
# Dumping data for table `Tree_Nested`
#

INSERT INTO Tree_Nested VALUES (8, 'Root', 1, 32, 0, '');
INSERT INTO Tree_Nested VALUES (9, 'PEAR', 6, 23, 8, '');
INSERT INTO Tree_Nested VALUES (10, 'Tree', 21, 22, 9, '');
INSERT INTO Tree_Nested VALUES (11, 'HTML', 7, 16, 9, '');
INSERT INTO Tree_Nested VALUES (12, 'Auth', 17, 18, 9, '');
INSERT INTO Tree_Nested VALUES (13, 'PEAR compatible', 0, 5, 8, '');
INSERT INTO Tree_Nested VALUES (14, 'SimpleTemplate', 3, 4, 13, '');
INSERT INTO Tree_Nested VALUES (15, 'Auth', 1, 2, 13, '');
INSERT INTO Tree_Nested VALUES (18, 'Template', 8, 15, 11, '');
INSERT INTO Tree_Nested VALUES (17, 'DB', 19, 20, 9, '');
INSERT INTO Tree_Nested VALUES (19, 'Xipe', 13, 14, 18, '');
INSERT INTO Tree_Nested VALUES (21, 'html', -6, 1, 8, '');
INSERT INTO Tree_Nested VALUES (22, 'test', -1, 0, 8, '');
INSERT INTO Tree_Nested VALUES (23, 'cbvcvbc', 11, 12, 18, '');
INSERT INTO Tree_Nested VALUES (24, 'Flexy', 9, 10, 18, 'Alan\\\'s template class');
# --------------------------------------------------------

#
# Table structure for table `Tree_Nested_seq`
#

CREATE TABLE Tree_Nested_seq (
  id int(10) unsigned NOT NULL auto_increment,
  PRIMARY KEY  (id)
) TYPE=MyISAM;

#
# Dumping data for table `Tree_Nested_seq`
#

INSERT INTO Tree_Nested_seq VALUES (24);

