<?php
/**
 * This class represent a month of free busy information sets.
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information.
 *
 * $Horde: kronolith/lib/FBView/month.php,v 1.4.2.3 2009-01-06 15:24:46 jan Exp $
 *
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @author  Jan Schneider <jan@horde.org>
 * @package Kronolith
 */
class Kronolith_FreeBusy_View_month extends Kronolith_FreeBusy_View {

    var $view = 'month';
    var $_timeBlocks = array();
    var $_days = 30;

    function _title()
    {
        global $registry, $prefs;

        return Horde::link('#', _("Previous Month"), '', '', 'return switchTimestamp(' . ($this->_startStamp - 1) . ');') .
            Horde::img('nav/left.png', '<', null, $registry->getImageDir('horde')) .
            '</a>' .
            strftime($prefs->getValue('date_format'), $this->_startStamp) .
            ' - ' .
            strftime($prefs->getValue('date_format'), $this->_startStamp + (($this->_days - 1) * 86400)) .
            Horde::link('#', _("Next Month"), '', '', 'return switchTimestamp(' . ($this->_endStamp + 1) . ');') .
            Horde::img('nav/right.png', '>', null, $registry->getImageDir('horde')) .
            '</a>';
    }

    function _hours()
    {
        global $prefs;

        $hours_html = '';
        $dayWidth = round(100 / $this->_days);
        $date_format = $prefs->getValue('date_format');

        $week = Date_Calc::weekOfYear(1, date('n', $this->_startStamp), date('Y', $this->_startStamp));
        $span = (7 - Date_Calc::dayOfWeek(1, date('n', $this->_startStamp), date('Y', $this->_startStamp))) % 7 + 1;
        $span_left = $this->_days;
        $t = $this->_startStamp;
        while ($span_left > 0) {
            $span_left -= $span;
            $week_label = Horde::link('#', '', '', '', 'return switchDateView(\'week\',' . $t . ');') . ("Week") . ' ' . $week . '</a>';
            $hours_html .= sprintf('<th colspan="%d" width="%s%%">%s</th>',
                                   $span, $dayWidth, $week_label);
            $week++;
            $t += 7 * 24 * 3600;
            $span = min($span_left, 7);
        }
        $hours_html .= '</tr><tr><td width="100" class="label">&nbsp;</td>';

        for ($i = 0; $i < $this->_days; $i++) {
            $t = mktime(0, 0, 0, date('n', $this->_startStamp), date('j', $this->_startStamp) + $i, date('Y', $this->_startStamp));
            $day_label = Horde::link('#', '', '', '', 'return switchDateView(\'day\',' . $t . ');') . sprintf("%s.", $i + 1) . '</a>';
            $hours_html .= sprintf('<th width="%s%%">%s</th>',
                                   $dayWidth, $day_label);
        }

        for ($i = 0; $i < $this->_days; $i++) {
            $t = mktime($this->_startHour, 0, 0, date('n', $this->_startStamp), date('j', $this->_startStamp) + $i, date('Y', $this->_startStamp));
            $this->_timeBlocks[$t] = mktime($this->_endHour, 0, 0, date('n', $this->_startStamp), date('j', $this->_startStamp) + $i, date('Y', $this->_startStamp));
        }

        return $hours_html;
    }

    function _render($day = null)
    {
        global $prefs;

        if (is_null($day)) {
            list($startDate['year'], $startDate['month'], $startDate['mday']) = explode('-', Date_Calc::beginOfMonthBySpan(0, null, null, "%Y-%m-%d"));
            $day = mktime(0, 0, 0, $startDate['month'], $startDate['mday'], $startDate['year']);
        } else {
            list($startDate['year'], $startDate['month'], $startDate['mday']) = explode('-', Date_Calc::beginOfMonthBySpan(0, date('n', $day), date('Y', $day), "%Y-%m-%d"));
            $day = mktime(0, 0, 0, $startDate['month'], $startDate['mday'], $startDate['year']);
        }
        $this->_startStamp = mktime(0, 0, 0, date('n', $day), date('j', $day), date('Y', $day));
        $this->_days = Date_Calc::daysInMonth($startDate['month'], $startDate['year']);
        $this->_endStamp   = mktime(23, 59, 59, date('n', $day), date('j', $day) + $this->_days - 1, date('Y', $day));
    }

}
