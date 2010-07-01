--TEST--
Horde_Date_Recurrence tests.
--FILE--
<?php

function recur($r)
{
    $ical = new Horde_iCalendar();
    echo $r->toRRule10($ical) . "\n";
    echo $r->toRRule20($ical) . "\n";
    $protect = 0;
    $next = new Horde_Date('2007-03-01 00:00:00');
    while ($next = $r->nextRecurrence($next)) {
        if (++$protect > 10) {
            die('Infinite loop');
        }
        echo $next->rfc3339DateTime() . "\n";
        $next->mday++;
    }
    var_dump($next);
    echo "\n";
}

function dump($rrule, $version)
{
    $r = new Horde_Date_Recurrence('2007-03-01 10:00:00');
    if ($version == 1) {
        $r->fromRRule10($rrule);
    } else {
        $r->fromRRule20($rrule);
    }

    var_dump($r->getRecurType());
    var_dump((int)$r->getRecurInterval());
    var_dump($r->getRecurOnDays());
    var_dump($r->getRecurCount());
    if ($r->hasRecurEnd()) {
        $datetime = $r->recurEnd->rfc3339DateTime();
        // Fix for pre Horde 3.2.
        if (substr($datetime, -6) != ':00:00') {
            $datetime .= ':00';
        }
        echo $datetime . "\n";
    }
    echo "\n";
}

require_once 'Horde/iCalendar.php';
require dirname(__FILE__) . '/../Recurrence.php';

$r = new Horde_Date_Recurrence('2007-03-01 10:00:00');

$r->setRecurType(HORDE_DATE_RECUR_DAILY);
$r->setRecurInterval(2);
$r->setRecurEnd(new Horde_Date('2007-03-07 10:00:00'));
recur($r);
$r->setRecurCount(4);
recur($r);

$r->setRecurType(HORDE_DATE_RECUR_WEEKLY);
$r->setRecurOnDay(HORDE_DATE_MASK_THURSDAY);
$r->setRecurInterval(1);
$r->setRecurEnd(new Horde_Date('2007-03-29 10:00:00'));
recur($r);
$r->setRecurCount(4);
recur($r);
$r->setRecurInterval(2);
recur($r);

$r->setRecurType(HORDE_DATE_RECUR_MONTHLY_DATE);
$r->setRecurInterval(1);
$r->setRecurEnd(new Horde_Date('2007-05-01 10:00:00'));
recur($r);
$r->setRecurCount(4);
recur($r);
$r->setRecurInterval(2);
recur($r);

$r->setRecurType(HORDE_DATE_RECUR_MONTHLY_WEEKDAY);
$r->setRecurInterval(1);
$r->setRecurEnd(new Horde_Date('2007-05-01 10:00:00'));
recur($r);
$r->setRecurCount(4);
recur($r);

$r->setRecurType(HORDE_DATE_RECUR_YEARLY_DATE);
$r->setRecurEnd(new Horde_Date('2009-03-01 10:00:00'));
recur($r);
$r->setRecurCount(4);
recur($r);

$r->setRecurType(HORDE_DATE_RECUR_YEARLY_DAY);
$r->setRecurEnd(new Horde_Date('2009-03-01 10:00:00'));
recur($r);
$r->setRecurCount(4);
recur($r);

$r->setRecurType(HORDE_DATE_RECUR_YEARLY_WEEKDAY);
$r->setRecurEnd(new Horde_Date('2009-03-01 10:00:00'));
recur($r);
$r->setRecurCount(4);
recur($r);

$r = new Horde_Date_Recurrence('2007-04-25 12:00:00');
$r->setRecurType(HORDE_DATE_RECUR_YEARLY_DATE);
$r->setRecurEnd(new Horde_Date('2011-04-25 23:00:00'));
$r->setRecurInterval(2);
$next = new Horde_Date('2009-03-30 00:00:00');
$next = $r->nextRecurrence($next);
echo $next->rfc3339DateTime() . "\n\n";

$r = new Horde_Date_Recurrence('2008-03-14 12:00:00');
$r->setRecurType(HORDE_DATE_RECUR_MONTHLY_WEEKDAY);
$r->setRecurCount(2);
$ical = new Horde_iCalendar();
echo $r->toRRule10($ical) . "\n";
echo $r->toRRule20($ical) . "\n\n";

$r = new Horde_Date_Recurrence('2009-03-27 10:00:00');
$r->setRecurType(HORDE_DATE_RECUR_YEARLY_WEEKDAY);
$r->setRecurCount(1);
$ical = new Horde_iCalendar();
echo $r->toRRule20($ical) . "\n\n";

$rrule1 = array('D2 20070307',
                'D2 20070308T090000Z',
                'D2 #4',
                'W1 TH 20070329',
                'W1 TH 20070330T080000Z',
                'W1 SU MO TU WE TH FR SA 20070603T235959',
                'W1 TH #4',
                'W2 TH #4',
                'MD1 1 20070501',
                'MD1 1 20070502T080000Z',
                'MD1 1 #4',
                'MD2 1 #4',
                'MP1 1+ TH 20070501',
                'MP1 1+ TH 20070502T080000Z',
                'MP1 1+ TH #4',
                'YM1 3 20090301',
                'YM1 3 20090302T090000Z',
                'YM1 3 #4',
                'YD1 60 20090301',
                'YD1 60 20090302T090000Z',
                'YD1 60 #4');
foreach ($rrule1 as $rrule) {
    dump($rrule, 1);
}
$rrule2 = array('FREQ=DAILY;INTERVAL=2;UNTIL=20070307',
                'FREQ=DAILY;INTERVAL=2;UNTIL=20070308T090000Z',
                'FREQ=DAILY;INTERVAL=2;COUNT=4',
                'FREQ=WEEKLY;INTERVAL=1;BYDAY=TH;UNTIL=20070329',
                'FREQ=WEEKLY;INTERVAL=1;BYDAY=TH;UNTIL=20070330T080000Z',
                'FREQ=WEEKLY;INTERVAL=1;BYDAY=TH;COUNT=4',
                'FREQ=WEEKLY;INTERVAL=2;BYDAY=TH;COUNT=4',
                'FREQ=MONTHLY;INTERVAL=1;UNTIL=20070501',
                'FREQ=MONTHLY;INTERVAL=1;UNTIL=20070502T080000Z',
                'FREQ=MONTHLY;INTERVAL=1;COUNT=4',
                'FREQ=MONTHLY;INTERVAL=2;COUNT=4',
                'FREQ=MONTHLY;INTERVAL=1;BYDAY=1TH;UNTIL=20070501',
                'FREQ=MONTHLY;INTERVAL=1;BYDAY=1TH;UNTIL=20070502T080000Z',
                'FREQ=MONTHLY;INTERVAL=1;BYDAY=1TH;COUNT=4',
                'FREQ=YEARLY;INTERVAL=1;UNTIL=20090301',
                'FREQ=YEARLY;INTERVAL=1;UNTIL=20090302T090000Z',
                'FREQ=YEARLY;INTERVAL=1;COUNT=4',
                'FREQ=YEARLY;INTERVAL=1;BYYEARDAY=60;UNTIL=20090301',
                'FREQ=YEARLY;INTERVAL=1;BYYEARDAY=60;UNTIL=20090302T090000Z',
                'FREQ=YEARLY;INTERVAL=1;BYYEARDAY=60;COUNT=4',
                'FREQ=YEARLY;INTERVAL=1;BYDAY=1TH;BYMONTH=3;UNTIL=20090301',
                'FREQ=YEARLY;INTERVAL=1;BYDAY=1TH;BYMONTH=3;UNTIL=20090302T090000Z',
                'FREQ=YEARLY;INTERVAL=1;BYDAY=1TH;BYMONTH=3;COUNT=4');
foreach ($rrule2 as $rrule) {
    dump($rrule, 2);
}

?>
--EXPECT--
D2 20070308T090000Z
FREQ=DAILY;INTERVAL=2;UNTIL=20070308T090000Z
2007-03-01T10:00:00
2007-03-03T10:00:00
2007-03-05T10:00:00
2007-03-07T10:00:00
bool(false)

D2 #4
FREQ=DAILY;INTERVAL=2;COUNT=4
2007-03-01T10:00:00
2007-03-03T10:00:00
2007-03-05T10:00:00
2007-03-07T10:00:00
bool(false)

W1 TH 20070330T080000Z
FREQ=WEEKLY;INTERVAL=1;BYDAY=TH;UNTIL=20070330T080000Z
2007-03-01T10:00:00
2007-03-08T10:00:00
2007-03-15T10:00:00
2007-03-22T10:00:00
2007-03-29T10:00:00
bool(false)

W1 TH #4
FREQ=WEEKLY;INTERVAL=1;BYDAY=TH;COUNT=4
2007-03-01T10:00:00
2007-03-08T10:00:00
2007-03-15T10:00:00
2007-03-22T10:00:00
bool(false)

W2 TH #4
FREQ=WEEKLY;INTERVAL=2;BYDAY=TH;COUNT=4
2007-03-01T10:00:00
2007-03-15T10:00:00
2007-03-29T10:00:00
2007-04-12T10:00:00
bool(false)

MD1 1 20070502T080000Z
FREQ=MONTHLY;INTERVAL=1;UNTIL=20070502T080000Z
2007-03-01T10:00:00
2007-04-01T10:00:00
2007-05-01T10:00:00
bool(false)

MD1 1 #4
FREQ=MONTHLY;INTERVAL=1;COUNT=4
2007-03-01T10:00:00
2007-04-01T10:00:00
2007-05-01T10:00:00
2007-06-01T10:00:00
bool(false)

MD2 1 #4
FREQ=MONTHLY;INTERVAL=2;COUNT=4
2007-03-01T10:00:00
2007-05-01T10:00:00
2007-07-01T10:00:00
2007-09-01T10:00:00
bool(false)

MP1 1+ TH 20070502T080000Z
FREQ=MONTHLY;INTERVAL=1;BYDAY=1TH;UNTIL=20070502T080000Z
2007-03-01T10:00:00
2007-04-05T10:00:00
bool(false)

MP1 1+ TH #4
FREQ=MONTHLY;INTERVAL=1;BYDAY=1TH;COUNT=4
2007-03-01T10:00:00
2007-04-05T10:00:00
2007-05-03T10:00:00
2007-06-07T10:00:00
bool(false)

YM1 3 20090302T090000Z
FREQ=YEARLY;INTERVAL=1;UNTIL=20090302T090000Z
2007-03-01T10:00:00
2008-03-01T10:00:00
2009-03-01T10:00:00
bool(false)

YM1 3 #4
FREQ=YEARLY;INTERVAL=1;COUNT=4
2007-03-01T10:00:00
2008-03-01T10:00:00
2009-03-01T10:00:00
2010-03-01T10:00:00
bool(false)

YD1 60 20090302T090000Z
FREQ=YEARLY;INTERVAL=1;BYYEARDAY=60;UNTIL=20090302T090000Z
2007-03-01T10:00:00
2008-02-29T10:00:00
2009-03-01T10:00:00
bool(false)

YD1 60 #4
FREQ=YEARLY;INTERVAL=1;BYYEARDAY=60;COUNT=4
2007-03-01T10:00:00
2008-02-29T10:00:00
2009-03-01T10:00:00
2010-03-01T10:00:00
bool(false)


FREQ=YEARLY;INTERVAL=1;BYDAY=1TH;BYMONTH=3;UNTIL=20090302T090000Z
2007-03-01T10:00:00
2008-03-06T10:00:00
bool(false)


FREQ=YEARLY;INTERVAL=1;BYDAY=1TH;BYMONTH=3;COUNT=4
2007-03-01T10:00:00
2008-03-06T10:00:00
2009-03-05T10:00:00
2010-03-04T10:00:00
bool(false)

2009-04-25T12:00:00

MP1 2+ FR #2
FREQ=MONTHLY;INTERVAL=1;BYDAY=2FR;COUNT=2

FREQ=YEARLY;INTERVAL=1;BYDAY=4FR;BYMONTH=3;COUNT=1

int(1)
int(2)
NULL
NULL
2007-03-07T00:00:00

int(1)
int(2)
NULL
NULL
2007-03-08T00:00:00

int(1)
int(2)
NULL
int(4)

int(2)
int(1)
int(16)
NULL
2007-03-29T00:00:00

int(2)
int(1)
int(16)
NULL
2007-03-30T00:00:00

int(2)
int(1)
int(127)
NULL
2007-06-03T00:00:00

int(2)
int(1)
int(16)
int(4)

int(2)
int(2)
int(16)
int(4)

int(3)
int(1)
NULL
NULL
2007-05-01T00:00:00

int(3)
int(1)
NULL
NULL
2007-05-02T00:00:00

int(3)
int(1)
NULL
int(4)

int(3)
int(2)
NULL
int(4)

int(4)
int(1)
NULL
NULL
2007-05-01T00:00:00

int(4)
int(1)
NULL
NULL
2007-05-02T00:00:00

int(4)
int(1)
NULL
int(4)

int(5)
int(1)
NULL
NULL
2009-03-01T00:00:00

int(5)
int(1)
NULL
NULL
2009-03-02T00:00:00

int(5)
int(1)
NULL
int(4)

int(6)
int(1)
NULL
NULL
2009-03-01T00:00:00

int(6)
int(1)
NULL
NULL
2009-03-02T00:00:00

int(6)
int(1)
NULL
int(4)

int(1)
int(2)
NULL
NULL
2007-03-07T00:00:00

int(1)
int(2)
NULL
NULL
2007-03-08T00:00:00

int(1)
int(2)
NULL
int(4)

int(2)
int(1)
int(16)
NULL
2007-03-29T00:00:00

int(2)
int(1)
int(16)
NULL
2007-03-30T00:00:00

int(2)
int(1)
int(16)
int(4)

int(2)
int(2)
int(16)
int(4)

int(3)
int(1)
NULL
NULL
2007-05-01T00:00:00

int(3)
int(1)
NULL
NULL
2007-05-02T00:00:00

int(3)
int(1)
NULL
int(4)

int(3)
int(2)
NULL
int(4)

int(4)
int(1)
NULL
NULL
2007-05-01T00:00:00

int(4)
int(1)
NULL
NULL
2007-05-02T00:00:00

int(4)
int(1)
NULL
int(4)

int(5)
int(1)
NULL
NULL
2009-03-01T00:00:00

int(5)
int(1)
NULL
NULL
2009-03-02T00:00:00

int(5)
int(1)
NULL
int(4)

int(6)
int(1)
NULL
NULL
2009-03-01T00:00:00

int(6)
int(1)
NULL
NULL
2009-03-02T00:00:00

int(6)
int(1)
NULL
int(4)

int(7)
int(1)
NULL
NULL
2009-03-01T00:00:00

int(7)
int(1)
NULL
NULL
2009-03-02T00:00:00

int(7)
int(1)
NULL
int(4)
