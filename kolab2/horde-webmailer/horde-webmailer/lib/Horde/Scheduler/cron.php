<?php

require_once 'Horde/Scheduler.php';
require_once 'Horde/String.php';

/**
 * Horde_Scheduler_cron:: Sort of a cron replacement in a PHP cli
 * script.
 *
 * Date Syntax Examples.
 *
 * Remember:
 *   - Whitespace (space, tab, newline) delimited fields
 *   - Single values, sets, ranges, wildcards
 *
 * SECOND   MINUTE              HOUR        DAY     MONTH
 * *        *                   *           *       *       (every second)
 * 0,30     *                   *           *       *       (every 30 seconds)
 * 0        0,10,20,30,40,50    *           *       *       (every 10 minutes)
 * 0        0                   *           *       *       (beginning of every hour)
 * 0        0                   0,6,12,18   *       *       (at midnight, 6am, noon, 6pm)
 * 0        0                   0           1-7&Fri *       (midnight, first Fri of the month)
 * 0        0                   0           1-7!Fri *       (midnight, first Mon-Thu,Sat-Sun of the month)
 *
 *
 * Example usage:
 *
 * @set_time_limit(0);
 * require_once 'Horde/Scheduler.php';
 * $cron = Horde_Scheduler::factory('cron');
 *
 * // Run this command every 5 minutes.
 * $cron->addTask('perl somescript.pl', '0 0,5,10,15,20,25,30,35,40,45,50,55 * * *');
 *
 * // Run this command midnight of the first Friday of odd numbered months.
 * $cron->addTask('php -q somescript.php', '0 0 0 1-7&Fri 1,3,5,7,9,11');
 *
 * // Also run this command midnight of the second Thursday and Saturday of the even numbered months.
 * $cron->addTask('php -q somescript.php', '0 0 0 8-15&Thu,8-15&Sat 2,4,6,8,10,12');
 *
 * $cron->run();
 *
 * $Horde: framework/Scheduler/lib/Horde/Scheduler/cron.php,v 1.1.2.1 2007-12-20 13:49:37 jan Exp $
 *
 * @author  Ryan Flynn <ryan@ryanflynn.com>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @package Horde_Scheduler
 */
class Horde_Scheduler_cron extends Horde_Scheduler {

    var $_tasks = array();

    /**
     * Every time a task is added it will get a fresh uid even if
     * immediately removed.
     */
    var $_counter = 1;

    function addTask($cmd, $rules)
    {
        $ds = &new Horde_Scheduler_cronDate($rules);

        $this->_counter++;

        $this->_tasks[] =
            array(
                'uid' => $this->_counter,
                'rules' => $ds,
                'cmd' => $cmd
            );

        return $this->_counter;
    }

    function removeTask($uid)
    {
        $count = count($this->_tasks);
        for ($i = 0; $i < $count; $i++) {
            if ($this->_tasks['uid'] == $uid) {
                $found = $i;
                array_splice($this->_tasks, $i);
                return $i;
            }
        }

        return 0;
    }

    function run()
    {
        if (!count($this->_tasks)) {
            exit("crond: Nothing to schedule; exiting.\n");
        }

        while (true) {
            $t = time();

            // Check each task.
            foreach ($this->_tasks as $task) {
                if ($task['rules']->nowMatches()) {
                    $this->runcmd($task);
                }
            }

            // Wait until the next second.
            while (time() == $t) {
                $this->sleep(100000);
            }
        }
    }

    function runcmd(&$task)
    {
        Horde::logMessage('Horde_Scheduler_Cron::runcmd(): ' . $task['cmd'] . ' run by ' . $task['uid'], __FILE__, __LINE__, PEAR_LOG_INFO);
        return shell_exec($task['cmd']);
    }

}

/**
 * @package Horde_Scheduler
 */
class Horde_Scheduler_cronDate {

    var $legalDays = array('MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN');

    var $sec;
    var $min;
    var $hour;
    var $day;
    var $month;

    function Horde_Scheduler_cronDate($raw)
    {
        $this->parse(String::upper($raw));
    }

    function nowMatches()
    {
        return $this->scheduledAt(time());
    }

    function scheduledAt($ts = null)
    {
        if ($ts === null) {
            $ts = time();
        }
        return ($this->monthMatches($ts) &&
                $this->monthMatches($ts) &&
                $this->dayMatches($ts) &&
                $this->hourMatches($ts) &&
                $this->minMatches($ts) &&
                $this->secMatches($ts));
    }

    function monthMatches($ts)
    {
        if ($this->month == '*') {
            return true;
        }

        $currentmonth = '-' . date('n', $ts) . '-';

        return (bool)strpos($this->month, $currentmonth);
    }

    function dayMatches($ts)
    {
        if (!empty($this->day['value']) && $this->day['value'] == '*') {
            return true;
        }

        $currentdaynum = '-' . date('j', $ts) . '-';
        $currentdaytxt = String::upper(date('D'));

        foreach ($this->day as $day) {
            if (@strpos($day['not'], $currentdaytxt) === false) {
                $v1 = (@strpos($day['value'], $currentdaynum) !== false);
                $v2 = (@strpos($day['and'], $currentdaytxt) !== false);

                if (!empty($day['and']) && ($v1 && $v2)) {
                    return true;
                } elseif (empty($day['and']) && $v1) {
                    return true;
                }
            }
        }

        return false;
    }

    function hourMatches($ts)
    {
        if ($this->hour == '*') {
            return true;
        }

        $currenthour = '-' . date('G', $ts) . '-';

        return (strpos($this->hour, $currenthour) !== false);
    }

    function minMatches($ts)
    {
        if ($this->min == '*') {
            return true;
        }

        $currentmin = '-' . intval(date('i', $ts)) . '-';

        return (strpos($this->min, $currentmin) !== false);
    }

    function secMatches($ts)
    {
        if ($this->sec == '*') {
            return true;
        }

        $currentsec = '-' . intval(date('s', $ts)) . '-';

        return (strpos($this->sec, $currentsec) !== false);
    }

    function parse($str)
    {
        $s = array();

        list($s['sec'], $s['min'], $s['hour'], $s['day'], $s['month']) = preg_split('|[\n\t ]+|', $str);

        foreach ($s as $k => $v) {
            if (strpos($v, '*') !== false) {
                $s[$k] = array('*');
            } elseif (!$this->generallyDecentSyntax($v)) {
                die("Illegal syntax in '$v'\n");
            } else {
                $s[$k] = explode(',', $s[$k]);
            }
        }

        if ($s['sec'][0] == '*') {
            $this->sec = '*';
        } else {
            for ($i = 0; $i < sizeof($s['sec']); $i++) {
                if ($this->isRange($s['sec'][$i])) {
                    $s['sec'][$i] = $this->expandRange($this->rangeVals($s['sec'][$i]));
                }
            }
            $this->sec = '-' . join('-', $s['sec']) . '-';
        }

        if ($s['min'][0] == '*') {
            $this->min = '*';
        } else {
            for ($i = 0; $i < sizeof($s['min']); $i++) {
                if ($this->isRange($s['min'][$i])) {
                    $s['min'][$i] = $this->expandRange($this->rangeVals($s['min'][$i]));
                }
            }
            $this->min = '-' . join('-', $s['min']) . '-';
        }

        if ($s['hour'][0] == '*') {
            $this->hour = '*';
        } else {
            for ($i = 0; $i < sizeof($s['hour']); $i++) {
                if ($this->isRange($s['hour'][$i])) {
                    $s['hour'][$i] = $this->expandRange($this->rangeVals($s['hour'][$i]));
                }
            }
            $this->hour = '-' . join('-', $s['hour']) . '-';
        }

        if ($s['day'][0] == '*') {
            $this->day = '*';
        } else {
            for ($i = 0; $i < sizeof($s['day']); $i++) {
                $tmp = array();
                if (($char = $this->isCond($s['day'][$i])) !== false) {
                    if ($char == '&') {
                        list($tmp['value'], $tmp['and']) = explode($char, $s['day'][$i]);
                        if ($this->isRange($tmp['and'])) {
                            $tmp['and'] = $this->expandRange($this->rangeVals($tmp['and']));
                        }
                    } else {
                        list($tmp['value'], $tmp['not']) = explode($char, $s['day'][$i]);
                        if ($this->isRange($tmp['not'])) {
                            $tmp['not'] = $this->expandRange($this->rangeVals($tmp['not']));
                        }
                    }
                } else {
                    $tmp = array('value' => $s['day'][$i]);
                }

                $s['day'][$i] = $tmp;

                if ($this->isRange($s['day'][$i]['value'])) {
                    $s['day'][$i]['value'] = $this->expandRange($this->rangeVals($s['day'][$i]['value']));
                }
            }

            $this->day = $s['day'];
        }

        if ($s['month'][0] == '*') {
            $this->month = '*';
        } else {
            for ($i = 0; $i < sizeof($s['month']); $i++) {
                if ($this->isRange($s['month'][$i])) {
                    $s['month'][$i] = $this->expandRange($this->rangeVals($s['month'][$i]));
                }
            }
            $this->month = '-' . join('-', $s['month']) . '-';
        }
    }

    function isCond($s)
    {
        if (strpos($s, '&') !== false) {
            return '&';
        } elseif (strpos($s, '!') !== false) {
            return '!';
        } else {
            return false;
        }
    }

    function isRange($s)
    {
        return preg_match('/^\w+\-\w+/', $s);
    }

    function isCondRange($s)
    {
        return (isCond($s) && isRange($s));
    }

    function isCondVal($s)
    {
        return (isCond($s) && !isRange($s));
    }

    function rangeVals($s)
    {
        return explode('-', $s);
    }

    function expandRange($l, $h = '')
    {
        // Expand range from 1-5 -> '-1-2-3-4-5-'.
        if (is_array($l)) {
            $h = $l[1];
            $l = $l[0];
        }

        if ($this->isDigit($l)) {
            if (!$this->isDigit($h)) {
                die("Invalid value '$h' in range '$l-$h'");
            }

            // Currently there is no possible reason to need to do a
            // range beyond 0-59 for anything.
            if ($l < 0) {
                $l = 0;
            } elseif ($l > 59) {
                $l = 59;
            }

            if ($h < 0) {
                $h = 0;
            } elseif ($h > 59) {
                $h = 59;
            }

            if ($l > $h) {
                $tmp = $l;
                $l = $h;
                $h = $tmp;
                unset($tmp);
            }

            // For some reason range() doesn't work w/o the explicit
            // intval() calls.
            return '-' . join('-', range(intval($l), intval($h))) . '-';
        } else {
            // Invalid.
            die("Invalid value '$l' in range '$l-$h'");
        }
    }

    function dayValue($s)
    {
        for ($i = 0; $i < count($this->legalDays); $i++) {
            if ($this->legalDays[$i] == $s) {
                return $i;
            }
        }

        return -1;
    }

    function isDigit($s)
    {
        return preg_match('/^\d+$/', $s);
    }

    function isAlpha($s)
    {
        return $this->isLegalDay($s);
    }

    function isLegalDay($s)
    {
        return in_array($s, $this->legalDays);
    }

    function generallyDecentSyntax($s)
    {
        return ($s == '*' ||
                preg_match('/^\d+(-\d+)?([!&][A-Z\*]+(-[A-Z\*]+)?)?(,\d+(-\d+)?([!&][A-Z\*]+(-[A-Z\*]+)?)?)*$/', $s));
    }

}
