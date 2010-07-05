--TEST--
Bug #7068: Single EXDATE properties not imported
--FILE--
<?php

class Driver {
    function getCalendar()
    {
        return 'foo';
    }
}

require 'Date/Calc.php';
require 'Horde/Date.php';
require 'Horde/Util.php';
require 'Horde/iCalendar.php';

$iCal = new Horde_iCalendar();
$iCal->parsevCalendar(file_get_contents(dirname(__FILE__) . '/bug7068.ics'));
$components = $iCal->getComponents();

define('KRONOLITH_BASE', dirname(__FILE__) . '/../..');
require KRONOLITH_BASE . '/lib/Kronolith.php';
require KRONOLITH_BASE . '/lib/Driver.php';
require KRONOLITH_BASE . '/lib/Recurrence.php';
$event = new Kronolith_Event(new Driver);
foreach ($components as $content) {
    if (is_a($content, 'Horde_iCalendar_vevent')) {
        $event->fromiCalendar($content);
        var_export($event->recurrence->exceptions);
        echo "\n";
    }
}

?>
--EXPECT--
array (
  0 => '20080729',
)
array (
  0 => '20080722',
  1 => '20080729',
)
