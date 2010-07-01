<?php

$block_name = _("Calendar Summary");

/**
 * Horde_Block_Kronolith_summary:: Implementation of the Horde_Block API to
 * display a summary of calendar items.
 *
 * $Horde: kronolith/lib/Block/summary.php,v 1.41.2.18 2009-01-13 22:44:45 mrubinsk Exp $
 *
 * @package Horde_Block
 */
class Horde_Block_Kronolith_summary extends Horde_Block {

    var $_app = 'kronolith';

    function _params()
    {
        @define('KRONOLITH_BASE', dirname(__FILE__) . '/../..');
        require_once KRONOLITH_BASE . '/lib/base.php';

        $params = array('calendar' => array('name' => _("Calendar"),
                                            'type' => 'enum',
                                            'default' => '__all'),
                        'maxevents' => array('name' => _("Maximum number of events to display (0 = no limit)"),
                                             'type' => 'int',
                                             'default' => 0));
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
        global $registry;

        if (isset($this->_params['calendar']) && $this->_params['calendar'] != '__all') {
            $url_params = array('display_cal' => $this->_params['calendar']);
        } else {
            $url_params = array();
        }
        return Horde::link(Horde::url(Util::addParameter($registry->getInitialPage(), $url_params), true)) . htmlspecialchars($registry->get('name')) . '</a>';
    }

    /**
     * The content to go in this block.
     *
     * @return string   The content
     */
    function _content()
    {
        global $registry, $prefs;
        require_once dirname(__FILE__) . '/../base.php';
        require_once KRONOLITH_BASE . '/lib/Day.php';
        require_once 'Horde/Prefs/CategoryManager.php';

        Horde::addScriptFile('tooltip.js', 'horde', true);

        $now = $_SERVER['REQUEST_TIME'];
        $today = date('j');

        $startDate = new Horde_Date(array('year' => date('Y'), 'month' => date('n'), 'mday' => date('j')));
        $endDate = new Horde_Date(array('year' => date('Y'), 'month' => date('n'), 'mday' => date('j') + $prefs->getValue('summary_days')));
        $endDate->correct();

        if (isset($this->_params['calendar']) &&
            $this->_params['calendar'] != '__all') {

            $calendar = $GLOBALS['kronolith_shares']->getShare($this->_params['calendar']);
            if (!is_a($calendar, 'PEAR_Error') && !$calendar->hasPermission(Auth::getAuth(), PERMS_SHOW)) {
                return _("Permission Denied");
            }

            $all_events = Kronolith::listEvents($startDate,
                                                $endDate,
                                                array($this->_params['calendar']),
                                                true, false, false);
        } else {
            $all_events = Kronolith::listEvents($startDate,
                                                $endDate,
                                                $GLOBALS['display_calendars']);
        }
        if (is_a($all_events, 'PEAR_Error')) {
            return '<em>' . $all_events->getMessage() . '</em>';
        }

        $html = '';
        $iMax = $today + $prefs->getValue('summary_days');
        $firstday = true;
        $totalevents = 0;
        for ($i = $today; $i < $iMax; ++$i) {
            $day = new Kronolith_Day(date('n'), $i);
            if (empty($all_events[$day->getStamp()])) {
                continue;
            }

            $events = &$all_events[$day->getStamp()];
            $firstevent = true;

            $today12am = mktime(0, 0, 0,
                                $day->month,
                                $day->mday,
                                $day->year);
            $tomorrow12am = mktime(0, 0, 0,
                                   $day->month,
                                   $day->mday + 1,
                                   $day->year);
            foreach ($events as $event) {

                if (!empty($this->_params['maxevents']) &&
                    $totalevents >= $this->_params['maxevents']) {
                    break 2;
                }

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
                    if (!$firstday) {
                        $html .= '<tr><td colspan="3" style="line-height:2px">&nbsp;</td></tr>';
                    }
                    $html .= '<tr><td colspan="3" class="control"><strong>';
                    if ($day->isToday()) {
                        $dayname = _("Today");
                    } elseif ($day->isTomorrow()) {
                        $dayname = _("Tomorrow");
                    } elseif ($day->diff() < 7) {
                        $dayname = strftime('%A', $day->getStamp());
                    } else {
                        $dayname = strftime($prefs->getValue('date_format'),
                                            $day->getStamp());
                    }
                    $url_params = array('timestamp' => $day->getStamp());
                    if (isset($this->_params['calendar']) && $this->_params['calendar'] != '__all') {
                        $url_params['display_cal'] = $this->_params['calendar'];
                    }
                    $daylink = Horde::applicationUrl('day.php', true);
                    $daylink = Util::addParameter($daylink, $url_params);
                    
                    $html .= Horde::link($daylink, sprintf(_("Goto %s"),
                                                           $dayname));
                    $html .= $dayname . '</a></strong></td></tr>';
                    $firstevent = false;
                    $firstday = false;
                }
                $html .= '<tr class="linedRow"><td class="text nowrap" valign="top">';
                if ($event->start->timestamp() < $now &&
                    $event->end->timestamp() > $now) {
                    $html .= '<strong>';
                }

                if ($event->isAllDay()) {
                    $time = _("All day event");
                } else {
                    if ($prefs->getValue('twentyFour')) {
                        $time = date('G:i', $event->start->timestamp()) . '-' .
                            date('G:i', $event->end->timestamp());
                    } else {
                        $time = date('g:i A', $event->start->timestamp()) . '-' .
                            date('g:i A', $event->end->timestamp());
                    }
                }

                $text = $event->getTitle();
                if ($location = $event->getLocation()) {
                    $text .= ' (' . $location . ')';
                }
                $html .= $time;
                if ($event->start->timestamp() < $now &&
                    $event->end->timestamp() > $now) {
                    $html .= '</strong>';
                }

                $html .= '</td><td class="text">&nbsp;&nbsp;&nbsp;</td>' .
                    '<td class="block-eventbox category' . md5($event->getCategory()) . '" valign="top">';

                if ($event->start->timestamp() < $now &&
                    $event->end->timestamp() > $now) {
                    $html .= '<strong>';
                }
                $html .= $event->getLink(null, true, null, true);
                if ($event->start->timestamp() < $now &&
                    $event->end->timestamp() > $now) {
                    $html .= '</strong>';
                }
                $html .= '</td></tr>';
                $totalevents++;
            }
        }

        if (empty($html)) {
            return '<em>' . _("No events to display") . '</em>';
        }

        return '<link href="' . Horde::applicationUrl('themes/categoryCSS.php', true) . '" rel="stylesheet" type="text/css" /><table cellspacing="0" width="100%">' . $html . '</table>';
    }

}
