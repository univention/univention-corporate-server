--TEST--
Bug #6031: Recurring events are not displayed in Kolab.
--FILE--
<?php
// Pretend that we are kronolith
require_once 'Horde/Kolab/Test.php';
require_once 'Horde/Share.php';
require_once 'Horde/Date.php';
require_once 'Horde/Date/Recurrence.php';
require_once 'Horde/Kolab.php';

// Find the base file path of Turba.
if (!defined('KRONOLITH_BASE')) {
    define('KRONOLITH_BASE', dirname(__FILE__) . '/../..');
}

// Load the Driver definitions
require_once KRONOLITH_BASE . '/lib/Driver.php';
require_once KRONOLITH_BASE . '/lib/Kronolith.php';

$test = new Horde_Kolab_Test();

$world = $test->prepareBasicSetup();

$test->assertTrue($world['auth']->authenticate('wrobel@example.org',
                                               array('password' => 'none')));

$GLOBALS['registry']->pushApp('kronolith');

$test->prepareNewFolder($world['storage'], 'Calendar', 'event', true);

/* Pretend that we are kronolith */
$kolab = &new Kolab();

/* Open our calendar */
$kolab->open('INBOX/Calendar', 1);

$object = array(
    'uid' => 1,
    'summary' => 'test',
    'start-date' => 0,
    'end-date' => 14400,
    'recurrence' => array(
        'interval' => 1,
        'cycle' => 'daily',
        'range-type' => 'number',
        'range' => 4,
        'exclusion' => array(
            '1970-01-02',
            '1970-01-03'
        )
    )
);

// Save the event
$kolab->_storage->save($object);
                          
// Check that the driver can be created
$kron = Kronolith_Driver::factory('kolab');
$kron->open('wrobel@example.org');

$start = &new Horde_Date(86400);
$end   = &new Horde_Date(172800);

// List the events of tomorrow (none, since recurrence has exception)
$a = $kron->listEvents($start, $end);
if (is_a($a, 'PEAR_Error')) {
  var_dump($a->getMessage());
} else {
  var_dump($a);
}

$start = &new Horde_Date(259200);
$end   = &new Horde_Date(345600);

// List the events in three days (recurring event)
$a = $kron->listEvents($start, $end);
if (is_a($a, 'PEAR_Error')) {
  var_dump($a->getMessage());
} else {
  var_dump($a);
}
--EXPECT--
array(0) {
}
array(1) {
  [1]=>
  string(1) "1"
}
