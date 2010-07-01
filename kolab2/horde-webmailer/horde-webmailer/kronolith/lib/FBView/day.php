<?php
/**
 * This class represent a single day of free busy information sets.
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information.
 *
 * $Horde: kronolith/lib/FBView/day.php,v 1.13.4.11 2009-01-06 15:24:46 jan Exp $
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @author  Jan Schneider <jan@horde.org>
 * @package Kronolith
 */
class Kronolith_FreeBusy_View_day extends Kronolith_FreeBusy_View {

    var $view = 'day';
    var $_timeBlocks = array();

    function _title()
    {
        global $registry, $prefs;

        return Horde::link('#', _("Previous Day"), '', '', 'return switchTimestamp(' . ($this->_startStamp - 86400) . ');') .
            Horde::img('nav/left.png', '<', null, $registry->getImageDir('horde')) .
            '</a>' .
            strftime($prefs->getValue('date_format'), $this->_startStamp) .
            Horde::link('#', _("Next Day"), '', '', 'return switchTimestamp(' . ($this->_startStamp + 86400) . ');') .
            Horde::img('nav/right.png', '>', null, $registry->getImageDir('horde')) .
            '</a>';
    }

    function _hours()
    {
        global $prefs;

        $hours_html = '';
        $width = round(100 / ($this->_endHour - $this->_startHour + 1));
        for ($i = $this->_startHour; $i < $this->_endHour; $i++) {
            $t = mktime($i, 0, 0, date('n', $this->_startStamp), date('j', $this->_startStamp), date('Y', $this->_startStamp));
            $this->_timeBlocks[$t] = mktime($i + 1, 0, 0, date('n', $this->_startStamp), date('j', $this->_startStamp), date('Y', $this->_startStamp)) - 1;
            $hours_html .= '<th width="' . $width . '%">' . date($prefs->getValue('twentyFour') ? 'G:00' : 'g:00', $t) . '</th>';
        }

        return $hours_html;
    }

    function _render($day = null)
    {
        global $prefs;

        if (is_null($day)) {
            $day = $_SERVER['REQUEST_TIME'];
        }
        $this->_startStamp = mktime($this->_startHour, 0, 0, date('n', $day), date('j', $day), date('Y', $day));
        $this->_endStamp = mktime($this->_endHour, 0, 0, date('n', $day), date('j', $day), date('Y', $day));
    }

}
