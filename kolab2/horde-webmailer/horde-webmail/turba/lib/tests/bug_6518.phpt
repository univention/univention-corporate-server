--TEST--
Data_ldif: Bug #6518
--FILE--
<?php

error_reporting(E_ALL);

require 'Horde.php';
require 'Horde/Data.php';
require dirname(__FILE__) . '/../Data/ldif.php';

$ldif = new Horde_Data_ldif();

$data = array(array('firstname' => 'John',
                    'lastname' => 'Püblic',
                    'name' => 'John Püblic',
                    'email' => 'john@example.com'),
              );

echo $ldif->exportData($data, false) . "\n";
?>
--EXPECT--
dn:: Y249Sm9obiBQw7xibGljLG1haWw9am9obkBleGFtcGxlLmNvbQ==
objectclass: top
objectclass: person
objectclass: organizationalPerson
objectclass: inetOrgPerson
objectclass: mozillaAbPersonAlpha
cn:: Sm9obiBQw7xibGlj
givenName: John
sn:: UMO8YmxpYw==
mail: john@example.com
modifytimestamp: 0Z

