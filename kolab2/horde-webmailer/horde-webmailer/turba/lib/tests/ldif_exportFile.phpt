--TEST--
Export Simple LDIF file
--FILE--
<?php

error_reporting(E_ALL);

require 'Horde.php';
require 'Horde/Data.php';
require dirname(__FILE__) . '/../Data/ldif.php';

$ldif = new Horde_Data_ldif();

$data = array(array('firstname' => 'John',
                    'lastname' => 'Smith',
                    'name' => 'John Smith',
                    'email' => 'js23@school.edu'),
              array('firstname' => 'Charles',
                    'lastname' => 'Brown',
                    'name' => 'Charlie Brown',
                    'alias' => 'Chuck',
                    'birthday' => 'May 1',
                    'workPhone' => '+1 212 876 5432',
                    'homePhone' => '+1 203 234 5678',
                    'fax' => '+1 203 999 9999',
                    'cellPhone' => '+1 917 321 0987',
                    'homeStreet' => '12 west 57 street',
                    'homeCity' => 'New York',
                    'homeProvince' => 'New York',
                    'homePostalCode' => '10001',
                    'homeCountry' => 'USA',
                    'workStreet' => '12 west 55 street',
                    'workCity' => 'New York',
                    'workProvince' => 'New York',
                    'workPostalCode' => '10001',
                    'workCountry' => 'USA',
                    'title' => 'Senior Systems Programmer',
                    'department' => 'SUIT',
                    'company' => 'School University',
                    'website' => 'http://www.school.edu/',
                    'freebusyUrl' => 'http://www.school.edu/~chuck/fb.ics',
                    'notes' => 'hi mom
',
                    'email' => 'brown@school.edu'),
              );

echo $ldif->exportData($data, false) . "\n";
?>
--EXPECT--
dn: cn=John Smith,mail=js23@school.edu
objectclass: top
objectclass: person
objectclass: organizationalPerson
objectclass: inetOrgPerson
objectclass: mozillaAbPersonAlpha
cn: John Smith
givenName: John
sn: Smith
mail: js23@school.edu
modifytimestamp: 0Z

dn: cn=Charlie Brown,mail=brown@school.edu
objectclass: top
objectclass: person
objectclass: organizationalPerson
objectclass: inetOrgPerson
objectclass: mozillaAbPersonAlpha
cn: Charlie Brown
givenName: Charles
sn: Brown
mail: brown@school.edu
mozillaHomeStreet2: 12 west 57 street
mozillaHomeLocalityName: New York
mozillaHomeState: New York
mozillaHomePostalCode: 10001
mozillaHomeCountryName: USA
mozillaWorkStreet2: 12 west 55 street
l: New York
st: New York
postalCode: 10001
c: USA
homePhone: +1 203 234 5678
telephoneNumber: +1 212 876 5432
mobile: +1 917 321 0987
fax: +1 203 999 9999
title: Senior Systems Programmer
company: School University
description:: aGkgbW9tCg==
mozillaWorkUrl: http://www.school.edu/
department: SUIT
modifytimestamp: 0Z

