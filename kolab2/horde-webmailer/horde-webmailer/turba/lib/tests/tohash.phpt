--TEST--
Turba_Driver::toHash() test.
--FILE--
<?php

require_once 'PEAR.php';
require_once 'Horde/iCalendar.php';
require dirname(__FILE__) . '/../Object.php';
require dirname(__FILE__) . '/../Driver.php';

$GLOBALS['tz']['Europe/Berlin'] = 'Europe/Berlin';
setlocale(LC_ALL, 'de_DE.ISO-8859-1');
bindtextdomain('turba', dirname(__FILE__) . '/../../locale');
textdomain('turba');

$vcard1 = '
BEGIN:VCARD
VERSION:2.1
FN;CHARSET=ISO-8859-1;ENCODING=QUOTED-PRINTABLE:=
Jan Schneider=F6
EMAIL:jan@horde.org
NICKNAME:yunosh
TEL;HOME:+49 521 555123
TEL;WORK:+49 521 555456
TEL;WORK:+49 521 999999
TEL;CELL:+49 177 555123
TEL;FAX:+49 521 555789
TEL;PAGER:+49 123 555789
BDAY:1971-10-01
TITLE;CHARSET=ISO-8859-1;ENCODING=QUOTED-PRINTABLE:=
Senior Developer (=E4=F6=FC)
ROLE;CHARSET=ISO-8859-1;ENCODING=QUOTED-PRINTABLE:=
Developer (=E4=F6=FC)
NOTE;CHARSET=ISO-8859-1;ENCODING=QUOTED-PRINTABLE:=
A German guy (=E4=F6=FC)
URL:http://janschneider.de
N;CHARSET=ISO-8859-1;ENCODING=QUOTED-PRINTABLE:=
Schneider=F6;Jan;K.;Mr.;
ORG;CHARSET=ISO-8859-1;ENCODING=QUOTED-PRINTABLE:=
Horde Project;=E4=F6=FC
ADR;HOME;CHARSET=ISO-8859-1;ENCODING=QUOTED-PRINTABLE:=
;;Sch=F6nestr. 15;Bielefeld;;33604;
ADR;WORK;CHARSET=ISO-8859-1;ENCODING=QUOTED-PRINTABLE:=
;;H=FCbschestr. 19;K=F6ln;Allg=E4u;;D=E4nemark
TZ;VALUE=text:+02:00; Europe/Berlin
GEO:13.377778,52.516276
BODY:
END:VCARD
';

$vcard2 = '
BEGIN:VCARD
VERSION:3.0
FN:Jan SchneiderÃ¶
EMAIL:jan@horde.org
NICKNAME:yunosh
TEL;TYPE=HOME:+49 521 555123
TEL;TYPE=WORK:+49 521 555456
TEL;TYPE=CELL:+49 177 555123
TEL;TYPE=FAX:+49 521 555789
TEL;TYPE=PAGER:+49 123 555789
BDAY:1971-10-01
TITLE:Senior Developer (Ã¤Ã¶Ã¼)
ROLE:Developer (Ã¤Ã¶Ã¼)
NOTE:A German guy (Ã¤Ã¶Ã¼)
URL:http://janschneider.de
N:SchneiderÃ¶;Jan;K.;Mr.;
ORG:Horde Project;Ã¤Ã¶Ã¼
ADR;TYPE=HOME:;;SchÃ¶nestr. 15;Bielefeld;;33604;;
ADR;TYPE=WORK:;;HÃ¼bschestr. 19;KÃ¶ln;AllgÃ¤u;;DÃ¤nemark
TZ;VALUE=text:+02:00; Europe/Berlin
GEO:52.516276;13.377778
BODY:
END:VCARD
';

$vcard3 = '
BEGIN:VCARD
VERSION:3.0
FN:Jan Schneider
N:Schneider;Jan;K.;Mr.;
END:VCARD
';

$vcard4 = '
BEGIN:VCARD
VERSION:3.0
N:Schneider;Jan;K.;Mr.;
END:VCARD
';

$vcard5 = '
BEGIN:VCARD
VERSION:2.1
REV:20080523T071425Z
N:B;A;;;
TEL;CELL:1
TEL;VOICE:4
X-CLASS:private
TEL;CELL;HOME:2
TEL;CELL;WORK:3
TEL;VOICE;HOME:5
TEL;VOICE;WORK:6
END:VCARD
';

$vcard6 = '
BEGIN:VCARD
VERSION:2.1
N:Lastname;Firstname;;;
FN:Lastname, Firstname
TITLE:
ORG:Company Name;
BDAY:
TEL;HOME;VOICE;X-Synthesis-Ref1:(xxx) xxx-xxxx
TEL;WORK;VOICE;X-Synthesis-Ref1:(xxx) xxx-xxxx
TEL;CELL;VOICE;X-Synthesis-Ref1:(xxx) xxx-xxxx
EMAIL:email@domain.com
URL:
CATEGORIES:Friends
NOTE;ENCODING=QUOTED-PRINTABLE:
EIN: xx-xxxxxxx
ADR;HOME:;;Street address;City;St;12345;USA
ADR;WORK:;;Street address;City;St;12345;USA
PHOTO:
END:VCARD
';

$vcard7 = '
BEGIN:VCARD
FN:Jan Schneider
N:Schneider;Jan;;;
PHOTO;ENCODING=b;TYPE=image/png:iVBORw0KGgoAAAANSUhEUgAAAAkAAAAJAgMAAACd/+6D
  AAAACVBMVEW6ABZmZmYAAACMtcxCAAAAAXRSTlMAQObYZgAAABpJREFUCFtjYACBBgYmRgEIZm
  GBYAFGMAYBABVmAOEH9qP8AAAAAElFTkSuQmCC
UID:nhCnPyv0u7
VERSION:2.1
END:VCARD
';

$vcard8 = '
BEGIN:VCARD
FN:Jan Schneider
N:Schneider;Jan;;;
EMAIL;WORK:work@example.com
EMAIL;HOME:home@example.com
EMAIL:mail@example.com
EMAIL;PREF:pref@example.com
UID:nhCnPyv0u7
VERSION:2.1
END:VCARD
';

$vcard9 = '
BEGIN:VCARD
VERSION:2.1
N:Blow;Joe;;;
FN:Blow, Joe
TITLE:
ORG:;
BDAY:19700327
TEL;HOME;VOICE;X-Synthesis-Ref1:302 834 9999
TEL;CELL;VOICE;X-Synthesis-Ref1:302 521 9999
EMAIL:Blow@somwhere.net
URL:
CATEGORIES:Personal
NOTE:
ADR;HOME:;;;;;;
PHOTO:
END:VCARD
';

// Invalid ENCODING value.
$vcard10 = '
BEGIN:VCARD
VERSION:3.0
PRODID:-//Synthesis AG//NONSGML SyncML Engine V3.1.6.10//EN
REV:20081004T151032
N:McTester;Testie;;;
FN:Testie McTester
ORG:Testers Inc;
TEL;TYPE=VOICE,CELL,X-Synthesis-Ref0:+44 775550555
TEL;TYPE=HOME,VOICE,X-Synthesis-Ref1:+44 205550555
TEL;TYPE=WORK,VOICE,X-Synthesis-Ref2:+44 205550556
EMAIL;TYPE=HOME,INTERNET,X-Synthesis-Ref0:test@example.org
EMAIL;TYPE=WORK,INTERNET,X-Synthesis-Ref1:test@example.com
ADR;TYPE=HOME,X-Synthesis-Ref0:;;111 One Street;London;;W1 1AA;
BDAY:20081008
PHOTO;TYPE=JPEG;ENCODING=BASE64:wolQTkcNChoKAAAADUlIRFIAAAAJAAAACQIDAAAAwp3
 Dv8OuwoMAAAAJUExURcK6ABZmZmYAAADCjMK1w4xCAAAAAXRSTlMAQMOmw5hmAAAAGklEQVQIW2
 NgAMKBBgYmRgEIZmHCgWABRjAGAQAVZgDDoQfDtsKjw7wAAAAASUVORMKuQmDCgg==
 
END:VCARD
';

$driver = new Turba_Driver(array());
$iCal = new Horde_iCalendar();

$iCal->parsevCalendar($vcard1);
var_export($driver->toHash($iCal->getComponent(0)));
echo "\n";

$iCal->parsevCalendar($vcard2);
var_export($driver->toHash($iCal->getComponent(0)));
echo "\n";

$iCal->parsevCalendar($vcard3);
var_export($driver->toHash($iCal->getComponent(0)));
echo "\n";

$iCal->parsevCalendar($vcard4);
var_export($driver->toHash($iCal->getComponent(0)));
echo "\n";

$driver->map['name'] = array(
    'fields' => array('namePrefix', 'firstname', 'middlenames',
                      'lastname', 'nameSuffix'),
    'attribute' => 'object_name',
    'format' => '%s %s %s %s %s');
$iCal->parsevCalendar($vcard4);
var_export($driver->toHash($iCal->getComponent(0)));
echo "\n";

$iCal->parsevCalendar($vcard5);
var_export($driver->toHash($iCal->getComponent(0)));
echo "\n";

$iCal->parsevCalendar($vcard6);
var_export($driver->toHash($iCal->getComponent(0)));
echo "\n";

$iCal->parsevCalendar($vcard7);
$hash = $driver->toHash($iCal->getComponent(0));
var_export($hash['photo'] == file_get_contents(dirname(__FILE__) . '/az.png'));
echo "\n";

$iCal->parsevCalendar($vcard8);
var_export($driver->toHash($iCal->getComponent(0)));
echo "\n";

$iCal->parsevCalendar($vcard9);
var_export($driver->toHash($iCal->getComponent(0)));
echo "\n";

$iCal->parsevCalendar($vcard10);
$hash = $driver->toHash($iCal->getComponent(0));
var_export(strlen($hash['photo']));
echo "\n";
unset($hash['photo']);
var_export($hash);

?>
--EXPECT--
array (
  'name' => 'Jan Schneiderö',
  'email' => 'jan@horde.org',
  'emails' => 'jan@horde.org',
  'nickname' => 'yunosh',
  'alias' => 'yunosh',
  'homePhone' => '+49 521 555123',
  'workPhone' => '+49 521 555456',
  'cellPhone' => '+49 177 555123',
  'fax' => '+49 521 555789',
  'pager' => '+49 123 555789',
  'birthday' => '1971-10-01',
  'title' => 'Senior Developer (äöü)',
  'role' => 'Developer (äöü)',
  'notes' => 'A German guy (äöü)',
  'website' => 'http://janschneider.de',
  'lastname' => 'Schneiderö',
  'firstname' => 'Jan',
  'middlenames' => 'K.',
  'namePrefix' => 'Mr.',
  'company' => 'Horde Project',
  'department' => 'äöü',
  'homeAddress' => 'Schönestr. 15
Bielefeld 33604',
  'homeStreet' => 'Schönestr. 15',
  'homeCity' => 'Bielefeld',
  'homePostalCode' => '33604',
  'workAddress' => 'Hübschestr. 19
Köln, Allgäu
Dänemark',
  'workStreet' => 'Hübschestr. 19',
  'workCity' => 'Köln',
  'workProvince' => 'Allgäu',
  'workCountry' => 'DK',
  'timezone' => 'Europe/Berlin',
  'latitude' => 52.516276,
  'longitude' => 13.377778,
)
array (
  'name' => 'Jan Schneiderö',
  'email' => 'jan@horde.org',
  'emails' => 'jan@horde.org',
  'nickname' => 'yunosh',
  'alias' => 'yunosh',
  'homePhone' => '+49 521 555123',
  'workPhone' => '+49 521 555456',
  'cellPhone' => '+49 177 555123',
  'fax' => '+49 521 555789',
  'pager' => '+49 123 555789',
  'birthday' => '1971-10-01',
  'title' => 'Senior Developer (äöü)',
  'role' => 'Developer (äöü)',
  'notes' => 'A German guy (äöü)',
  'website' => 'http://janschneider.de',
  'lastname' => 'Schneiderö',
  'firstname' => 'Jan',
  'middlenames' => 'K.',
  'namePrefix' => 'Mr.',
  'company' => 'Horde Project',
  'department' => 'äöü',
  'homeAddress' => 'Schönestr. 15
Bielefeld 33604',
  'homeStreet' => 'Schönestr. 15',
  'homeCity' => 'Bielefeld',
  'homePostalCode' => '33604',
  'workAddress' => 'Hübschestr. 19
Köln, Allgäu
Dänemark',
  'workStreet' => 'Hübschestr. 19',
  'workCity' => 'Köln',
  'workProvince' => 'Allgäu',
  'workCountry' => 'DK',
  'timezone' => 'Europe/Berlin',
  'latitude' => 52.516276,
  'longitude' => 13.377778,
)
array (
  'name' => 'Jan Schneider',
  'lastname' => 'Schneider',
  'firstname' => 'Jan',
  'middlenames' => 'K.',
  'namePrefix' => 'Mr.',
)
array (
  'lastname' => 'Schneider',
  'firstname' => 'Jan',
  'middlenames' => 'K.',
  'namePrefix' => 'Mr.',
  'name' => 'Jan Schneider',
)
array (
  'lastname' => 'Schneider',
  'firstname' => 'Jan',
  'middlenames' => 'K.',
  'namePrefix' => 'Mr.',
  'name' => 'Mr. Jan K. Schneider',
)
array (
  'lastname' => 'B',
  'firstname' => 'A',
  'cellPhone' => '1',
  'phone' => '4',
  'homeCellPhone' => '2',
  'workCellPhone' => '3',
  'homePhone' => '5',
  'workPhone' => '6',
  'name' => 'A  B',
)
array (
  'lastname' => 'Lastname',
  'firstname' => 'Firstname',
  'name' => 'Lastname, Firstname',
  'company' => 'Company Name',
  'department' => '',
  'homePhone' => '(xxx) xxx-xxxx',
  'workPhone' => '(xxx) xxx-xxxx',
  'cellPhone' => '(xxx) xxx-xxxx',
  'email' => 'email@domain.com',
  'emails' => 'email@domain.com',
  'category' => 'Friends',
  'businessCategory' => 'Friends',
  'homeAddress' => 'Street address
City, St 12345
USA',
  'homeStreet' => 'Street address',
  'homeCity' => 'City',
  'homeProvince' => 'St',
  'homePostalCode' => '12345',
  'homeCountry' => 'USA',
  'workAddress' => 'Street address
City, St 12345
USA',
  'workStreet' => 'Street address',
  'workCity' => 'City',
  'workProvince' => 'St',
  'workPostalCode' => '12345',
  'workCountry' => 'USA',
)
true
array (
  'name' => 'Jan Schneider',
  'lastname' => 'Schneider',
  'firstname' => 'Jan',
  'workEmail' => 'work@example.com',
  'emails' => 'work@example.com, home@example.com, mail@example.com, pref@example.com',
  'homeEmail' => 'home@example.com',
  'email' => 'pref@example.com',
)
array (
  'lastname' => 'Blow',
  'firstname' => 'Joe',
  'name' => 'Blow, Joe',
  'company' => '',
  'department' => '',
  'birthday' => '1970-03-27',
  'homePhone' => '302 834 9999',
  'cellPhone' => '302 521 9999',
  'email' => 'Blow@somwhere.net',
  'emails' => 'Blow@somwhere.net',
  'category' => 'Personal',
  'businessCategory' => 'Personal',
  'homeAddress' => '',
)
136
array (
  'lastname' => 'McTester',
  'firstname' => 'Testie',
  'name' => 'Testie McTester',
  'company' => 'Testers Inc',
  'department' => '',
  'cellPhone' => '+44 775550555',
  'homePhone' => '+44 205550555',
  'workPhone' => '+44 205550556',
  'homeEmail' => 'test@example.org',
  'emails' => 'test@example.org, test@example.com',
  'workEmail' => 'test@example.com',
  'homeAddress' => '111 One Street
London W1 1AA',
  'homeStreet' => '111 One Street',
  'homeCity' => 'London',
  'homePostalCode' => 'W1 1AA',
  'commonAddress' => '111 One Street
London W1 1AA',
  'commonStreet' => '111 One Street',
  'commonCity' => 'London',
  'commonPostalCode' => 'W1 1AA',
  'birthday' => '2008-10-08',
  'phototype' => 'JPEG',
)
