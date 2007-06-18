<?php
/**
 * Horde_Block_Kronolith_month:: Implementation of the Horde_Block API
 * to display a mini month view of calendar items.
 *
 * $Horde: kronolith/lib/Block/month.php,v 1.8 2004/04/26 16:55:54 chuck Exp $
 *
 * @package Horde_Block
 */
class Horde_Block_Kronolith_month extends Horde_Block {

    var $_app = 'kronolith';

    function getParams()
    {
        @define('KRONOLITH_BASE', dirname(__FILE__) . '/..');
        require_once KRONOLITH_BASE . '/lib/base.php';

        $params = array('calendar' => array('name' => _("Calendar"),
                                            'type' => 'enum',
                                            'default' => '__all'));
        $params['calendar']['values']['__all'] = _("All Visible");
        foreach (Kronolith::listCalendars() as $id => $cal) {
            $params['calendar']['values'][$id] = $cal->get('name');
        }

        $GLOBALS['registry']->popApp();
        return $params;
    }

    /**
     * The title to go in this block.
     *
     * @return string   The title text.
     */
    function _title()
    {
        global $registry;

        $title = strftime('%B, %G');
        $html  = Horde::link(Horde::url($registry->getInitialPage(), true), $title, 'header') . $title . '</a> :: ';
        $html .= Horde::link(Horde::applicationUrl('addevent.php', true), _("New Event"), 'smallheader') . Horde::img('new.gif', _("New Event"), 'align="middle"', Horde::url($registry->getParam('graphics'), true, -1)) . ' ' . _("New Event") . '</a>';

        return $html;
    }

    /**
     * The content to go in this block.
     *
     * @return string   The content
     */
    function _content()
    {
        global $prefs;
        require_once dirname(__FILE__) . '/../base.php';
        require_once KRONOLITH_BASE . '/lib/Day.php';

        Horde::addScriptFile('tooltip.js', 'horde');

        $year = date('Y');
        $month = date('m');
        $today = mktime(0, 0, 0, date('n'), date('j'), date('Y'));

        $startday = Kronolith::dayOfWeek($prefs->getValue('week_start_monday') ? 1 : 2, $month, $year);
        $daysInMonth = Date_Calc::weeksInMonth($month, $year) * 7;

        $startStamp = mktime(0, 0, 0, $month, 1 - $startday, $year);
        $startDate = Kronolith::timestampToObject($startStamp);
        $endStamp = mktime(23, 59, 59, $month, (1 - $startday) + $daysInMonth, $year);
        $endDate = Kronolith::timestampToObject($endStamp);

        /* Table start. and current month indicator. */
        $html = '<table border="0" cellpadding="1" cellspacing="1" class="monthgrid" width="100%">';

        /* Set up the weekdays. */
        $weekdays = array(_("Mo"), _("Tu"), _("We"), _("Th"), _("Fr"), _("Sa"));
        if (!$prefs->getValue('week_start_monday')) {
            array_unshift($weekdays, _("Su"));
        } else {
            array_push($weekdays, _("Su"));
        }
        foreach ($weekdays as $weekday) {
            $html .= '<th class="item">' . $weekday . '</th>';
        }

        if (isset($this->_params['calendar']) && $this->_params['calendar'] != '__all') {
            $all_events = Kronolith::listEvents($startDate, $endDate, array($this->_params['calendar']));
        } else {
            $all_events = Kronolith::listEvents($startDate, $endDate, $GLOBALS['display_calendars']);
        }

        $weeks = array();
        $weekday = 0;
        $week = -1;
        for ($day = (1 - $startday); $day < (1 - $startday) + $daysInMonth; $day++) {
            $dayStamp = mktime(0, 0, 0, $month, $day, $year);

            if ($weekday == 7) {
                $weekday = 0;
            }
            if ($weekday == 0) {
                $week++;
                $html .= '</tr><tr>';
            }

            if (mktime(0, 0, 0) == $dayStamp) {
                $td_class = 'today';
            } elseif (date('n', $dayStamp) != $month) {
                $td_class = 'othermonth';
            } elseif (date('w', $dayStamp) == 0 || date('w', $dayStamp) == 6) {
                $td_class = 'weekend';
            } else {
                $td_class = 'text';
            }
            $html .= '<td align="center" class="' . $td_class . '">';

            /* Set up the link to the day view. */
            $url = Horde::applicationUrl('day.php', true);
            $url = Util::addParameter($url, array('timestamp' => $dayStamp));

            if (!empty($all_events[$dayStamp])) {
                /* There are events; create a cell with tooltip to
                 * list them. */
                $day_events = '';
                foreach ($all_events[$dayStamp] as $event) {
                    $day_events .= date($prefs->getValue('twentyFour') ? 'G:i' : 'g:ia', $event->getStartTimestamp()) . ' - ' . date($prefs->getValue('twentyFour') ? 'G:i' : 'g:ia', $event->getEndTimestamp());
                    $day_events .= ($event->getLocation()) ? ' (' . $event->getLocation() . ')' : '';
                    $day_events .= ' ' . $event->getTitle() . "\n";
                }
                $cell = Horde::linkTooltip($url, _("View Day"), '', '', '', $day_events) . date('j', $dayStamp) . '</a>';
            } else {
                /* No events, plain link to the day. */
                $cell = Horde::linkTooltip($url, _("View Day")) . date('j', $dayStamp) . '</a>';
            }

            /* Bold the cell if there are events. */
            if (!empty($all_events[$dayStamp])) {
                $cell = '<b>' . $cell . '</b>';
            }

            $html .= $cell . '</td>';
            $weekday++;
        }

        $html .= '</tr><tr><td colspan="7" class="control" align="center">';
        $url = Horde::applicationUrl('day.php', true);
        $url = Util::addParameter($url, array('timestamp' => time()));
        $today_link = strftime($prefs->getValue('date_format'), time());
        $today_link = Horde::link($url) . $today_link . '</a>';

        $html .= sprintf(_("Today is %s"), $today_link);
        $html .= '</td></tr></table>';

        return $html;
    }

}
