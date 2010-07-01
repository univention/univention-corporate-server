--TEST--
Import Simple LDIF file, LF terminated
--FILE--
<?php

error_reporting(E_ALL);

require 'Horde.php';
require 'Horde/Data.php';
require dirname(__FILE__) . '/../Data/ldif.php';

$data = new Horde_Data_ldif();
var_dump($data->importFile(dirname(__FILE__) . '/import.ldif', false));

?>
--EXPECT--
array(2) {
  [0]=>
  array(4) {
    ["givenName"]=>
    string(4) "John"
    ["sn"]=>
    string(5) "Smith"
    ["cn"]=>
    string(10) "John Smith"
    ["mail"]=>
    string(15) "js23@school.edu"
  }
  [1]=>
  array(26) {
    ["givenName"]=>
    string(7) "Charles"
    ["sn"]=>
    string(5) "Brown"
    ["cn"]=>
    string(13) "Charlie Brown"
    ["mozillaNickname"]=>
    string(5) "Chuck"
    ["mail"]=>
    string(16) "brown@school.edu"
    ["telephoneNumber"]=>
    string(15) "+1 212 876 5432"
    ["homePhone"]=>
    string(15) "+1 203 234 5678"
    ["fax"]=>
    string(15) "+1 203 999 9999"
    ["mobile"]=>
    string(15) "+1 917 321 0987"
    ["homeStreet"]=>
    string(17) "12 west 57 street"
    ["mozillaHomeStreet2"]=>
    string(8) "Apt 2076"
    ["mozillaHomeLocalityName"]=>
    string(8) "New York"
    ["mozillaHomeState"]=>
    string(8) "New York"
    ["mozillaHomePostalCode"]=>
    string(5) "10001"
    ["mozillaHomeCountryName"]=>
    string(3) "USA"
    ["street"]=>
    string(19) "12 West 55th Street"
    ["mozillaWorkStreet2"]=>
    string(7) "Room 22"
    ["l"]=>
    string(8) "New York"
    ["st"]=>
    string(8) "New York"
    ["postalCode"]=>
    string(5) "10001"
    ["c"]=>
    string(3) "USA"
    ["title"]=>
    string(25) "Senior Systems Programmer"
    ["department"]=>
    string(4) "CUIT"
    ["company"]=>
    string(17) "School University"
    ["mozillaWorkUrl"]=>
    string(22) "http://www.school.edu/"
    ["description"]=>
    string(7) "hi mom
"
  }
}
