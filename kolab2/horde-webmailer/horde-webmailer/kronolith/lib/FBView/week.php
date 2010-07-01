<?php
/**
 * This class represent a week of free busy information sets.
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information.
 *
 * $Horde: kronolith/lib/FBView/week.php,v 1.11.4.14 2009-01-06 15:24:46 jan Exp $
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @author  Jan Schneider <jan@horde.org>
 * @package Kronolith
 */
class Kronolith_FreeBusy_View_week extends Kronolith_FreeBusy_View {

    var $view = 'week';
    var $_days = 7;
    var $_timeBlocks = array();

    function _title()
    {
        global $registry, $prefs;

        return Horde::link('#', _("Previous Week"), '', '', 'return switchTimestamp(' . ($this->_startStamp - 7 * 86400) . ');') .
            Horde::img('nav/left.png', '<', null, $registry->getImageDir('horde')) .
            '</a>' .
            strftime($prefs->getValue('date_format'), $this->_startStamp) .
            ' - ' .
            strftime($prefs->getValue('date_format'), $this->_startStamp + (($this->_days - 1) * 86400)) .
            Horde::link('#', _("Next Week"), '', '', 'return switchTimestamp(' . ($this->_startStamp + 7 * 86400) . ');') .
            Horde::img('nav/right.png', '>', null, $registry->getImageDir('horde')) .
            '</a>';
    }

    function _hours()
    {
        global $prefs;

        $hours_html = '';
        $dayWidth = round(100 / $this->_days);
        $span = floor(($this->_endHour - $this->_startHour) / 3);
        if (($this->_endHour - $this->_startHour) % 3) {
            $span++;
        }
        $date_format = $prefs->getValue('date_format');
        for ($i = 0; $i < $this->_days; $i++) {
            $t = mktime(0, 0, 0, date('n', $this->_startStamp), date('j', $this->_startStamp) + $i, date('Y', $this->_startStamp));
            $day_label = Horde::link('#', '', '', '', 'return switchDateView(\'day\',' . $t . ');') . strftime($date_format, $t) . '</a>';
            $hours_html .= sprintf('<th colspan="%d" width="%s%%">%s</th>',
                                   $span, $dayWidth, $day_label);
        }
        $hours_html .= '</tr><tr><td width="100" class="label">&nbsp;</td>';

        $width = round(100 / ($span * $this->_days));
        for ($i = 0; $i < $this->_days; $i++) {
            for ($h = $this->_startHour; $h < $this->_endHour; $h += 3) {
                $t = mktime($h, 0, 0, date('n', $this->_startStamp), date('j', $this->_startStamp) + $i, date('Y', $this->_startStamp));
                $this->_timeBlocks[$t] = mktime($h + 3, 0, 0, date('n', $this->_startStamp), date('j', $this->_startStamp) + $i, date('Y', $this->_startStamp)) - 1;

                $hour = date($prefs->getValue('twentyFour') ? 'G:00' : 'g:00', $t);
                $hours_html .= sprintf('<th width="%d%%">%s</th>',
                                       $width, $hour);
            }
        }

        return $hours_html;
    }

    function _render($day = null)
    {
        global $prefs;

        if (is_null($day)) {
            list($startDate['year'], $startDate['month'], $startDate['mday']) = explode('-', Date_Calc::beginOfWeek(null, null, null, "%Y-%m-%d"));
            $day = mktime(0, 0, 0, $startDate['month'], $startDate['mday'], $startDate['year']);
        } else {
            list($startDate['year'], $startDate['month'], $startDate['mday']) = explode('-', Date_Calc::beginOfWeek(date('j', $day), date('n', $day), date('Y', $day), "%Y-%m-%d"));
            $day = mktime(0, 0, 0, $startDate['month'], $startDate['mday'], $startDate['year']);
        }
        $this->_startStamp = mktime(0, 0, 0, date('n', $day), date('j', $day), date('Y', $day));
        $this->_endStamp   = mktime(23, 59, 59, date('n', $day) + $this->_days - 1, date('j', $day), date('Y', $day));
    }

}
