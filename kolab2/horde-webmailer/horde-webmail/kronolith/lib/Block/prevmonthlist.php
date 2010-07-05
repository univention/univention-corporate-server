<?php

$block_name = _("Prior Events");

/**
 * Horde_Block_Kronolith_monthlist:: Implementation of the Horde_Block
 * API to display a list of previous calendar items grouped by month.
 *
 * $Horde: kronolith/lib/Block/prevmonthlist.php,v 1.15.2.14 2009-01-13 22:44:45 mrubinsk Exp $
 *
 * @package Horde_Block
 */
class Horde_Block_Kronolith_prevmonthlist extends Horde_Block {

    var $_app = 'kronolith';

    function _params()
    {
        require_once dirname(__FILE__) . '/../base.php';

        $params = array('calendar' => array('name' => _("Calendar"),
                                            'type' => 'enum',
                                            'default' => '__all'),
                        'months' => array('name' => _("Months Before"),
                                          'type' => 'int',
                                          'default' => 2));
        $params['calendar']['values']['__all'] = _("All Visible");
        foreach (Kronolith::listCalendars() as $id => $cal) {
            $params['calendar']['values'][$id] = $cal->get('name');
        }

        return $params;
    }

    /**
     * The title to go in this block.
     *
     * @return string   The title text.
     */
    function _title()
    {
        if (isset($this->_params['calendar']) && $this->_params['calendar'] != '__all') {
            $url_params = array('display_cal' => $this->_params['calendar']);
        } else {
            $url_params = array();
        }
        return Horde::link(Horde::url(Util::addParameter($GLOBALS['registry']->getInitialPage(), $url_params), true)) . _("Prior Events") . '</a>';
    }

    /**
     * The content to go in this block.
     *
     * @return string   The content
     */
    function _content()
    {
        require_once dirname(__FILE__) . '/../base.php';
        require_once KRONOLITH_BASE . '/lib/Day.php';

        global $registry, $prefs;

        Horde::addScriptFile('tooltip.js', 'horde', true);

        $startDate = new Horde_Date(array('year' => date('Y'), 'month' => date('n') - $this->_params['months'], 'mday' => date('j')));
        $startDate->correct();
        $endDate = new Horde_Date(array('year' => date('Y'), 'month' => date('n'), 'mday' => date('j') - 1));
        $endDate->correct();

        $now = $startDate->timestamp();
        $current_month = '';

        if (isset($this->_params['calendar']) && $this->_params['calendar'] != '__all') {
            $calendar = $GLOBALS['kronolith_shares']->getShare($this->_params['calendar']);
            if (!is_a($calendar, 'PEAR_Error') && !$calendar->hasPermission(Auth::getAuth(), PERMS_SHOW)) {
                return _("Permission Denied");
            }
            $all_events = Kronolith::listEvents($startDate, $endDate, array($this->_params['calendar']), true, false, false);
        } else {
            $all_events = Kronolith::listEvents($startDate, $endDate, $GLOBALS['display_calendars']);
        }
        if (is_a($all_events, 'PEAR_Error')) {
            return '<em>' . $all_events->getMessage() . '</em>';
        }

        $html = '<link href="' . Horde::applicationUrl('themes/categoryCSS.php', true) . '" rel="stylesheet" type="text/css" />';

        /* How many days do we need to check. */
        $days = Date_Calc::dateDiff($startDate->mday, $startDate->month, $startDate->year,
                                    $endDate->mday, $endDate->month, $endDate->year);

        /* Loop through the days. */
        for ($i = 0; $i < $days; ++$i) {
            $day = new Kronolith_Day($startDate->month, $startDate->mday + $i, $startDate->year);
            $today_stamp = $day->getStamp();
            if (empty($all_events[$today_stamp])) {
                continue;
            }

            $events = &$all_events[$today_stamp];
            $firstevent = true;

            /* Output month header. */
            if ($current_month != $day->month) {
                $current_month = strftime('%m', $today_stamp);
                $html .= '<tr><td colspan="4" class="control"><strong>' . strftime('%B', $today_stamp) . '</strong></td></tr>';
            }

            $today12am = mktime(0, 0, 0, $day->month, $day->mday, $day->year);
            $tomorrow12am = mktime(0, 0, 0, $day->month, $day->mday + 1, $day->year);
            foreach ($events as $event) {

                if ($event->start->timestamp() < $today12am) {
                    $event->start = new Horde_Date($today12am);
                }
                if ($event->end->timestamp() >= $tomorrow12am) {
                    $event->end = new Horde_Date($tomorrow12am);
                }

                if ($event->end->timestamp() < $now) {
                    continue;
                }

                if ($prefs->getValue('summary_alarms') && !$event->alarm) {
                    continue;
                }
                if ($firstevent) {
                    $html .= '<tr><td class="text" valign="top" align="right"><strong>';
                    if ($day->isToday()) {
                        $html .= _("Today");
                    } elseif ($day->isTomorrow()) {
                        $html .= _("Tomorrow");
                    } else {
                        $html .= date('j', $today_stamp);
                    }
                    $html .= '</strong>&nbsp;</td>';
                    $firstevent = false;
                } else {
                    $html .= '<tr><td class="text">&nbsp;</td>';
                }

                $html .= '<td class="text" nowrap="nowrap" valign="top">';
                if ($event->start->timestamp() < $now && $event->end->timestamp() > $now) {
                    $html .= '<strong>' . $event->getLocation() . '</strong>';
                } else {
                    $html .= $event->getLocation();
                }

                $html .= '</td><td class="text">&nbsp;&nbsp;&nbsp;</td>' .
                    '<td class="block-eventbox category' . md5($event->getCategory()) . '" valign="top">';

                if ($event->start->timestamp() < $now && $event->end->timestamp() > $now) {
                    $html .= '<strong>';
                }
                if (isset($event->eventID)) {
                    $html .= $event->getLink(null, true, null, true);
                } elseif (isset($this->external)) {
                    $html .= Horde::link(Horde::url($registry->link($this->external . '/show', $event->external_params),
                                                    true), $event->getTitle()) . $event->getTitle() . '</a>';
                } else {
                    $html .= $event->getTitle();
                }
                if ($event->start->timestamp() < $now && $event->end->timestamp() > $now) {
                    $html .= '</strong>';
                }
                $html .= '</td></tr>';
            }
        }

        if (empty($html)) {
            return '<em>' . _("No events to display") . '</em>';
        }

        return '<table cellspacing="0" width="100%">' . $html . '</table>';
    }

}
