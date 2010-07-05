--TEST--
Import of all-day events
--FILE--
<?php

class Driver {
    function getCalendar()
    {
        return 'foo';
    }
}
class Prefs {
    function getValue()
    {
        return 0;
    }
}
$prefs = new Prefs;

require 'Date/Calc.php';
require 'Horde/Date.php';
require 'Horde/Util.php';
require 'Horde/iCalendar.php';

$iCal = new Horde_iCalendar();
$iCal->parsevCalendar(file_get_contents(dirname(__FILE__) . '/allday.ics'));
$components = $iCal->getComponents();

define('KRONOLITH_BASE', dirname(__FILE__) . '/../..');
require KRONOLITH_BASE . '/lib/Kronolith.php';
require KRONOLITH_BASE . '/lib/Driver.php';
foreach ($components as $content) {
    if (is_a($content, 'Horde_iCalendar_vevent')) {
        $event = new Kronolith_Event(new Driver);
        $event->fromiCalendar($content);
        echo $event->start->rfc3339DateTime() . "\n";
        echo $event->end->rfc3339DateTime() . "\n";
        var_export($event->isAllDay());
        echo "\n";
    }
}

?>
--EXPECT--
2006-10-23T00:00:00
2006-10-24T00:00:00
true
2006-10-23T00:00:00
2006-10-24T00:00:00
true
2006-10-23T12:00:00
2006-10-23T13:00:00
false
