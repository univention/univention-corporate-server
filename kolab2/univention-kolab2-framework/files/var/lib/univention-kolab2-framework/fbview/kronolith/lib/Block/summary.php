<?php
/**
 * Horde_Block_Kronolith_summary:: Implementation of the Horde_Block API
 * to display a summary of calendar items.
 *
 * $Horde: kronolith/lib/Block/summary.php,v 1.27 2004/05/27 17:51:54 chuck Exp $
 *
 * @package Horde_Block
 */
class Horde_Block_Kronolith_summary extends Horde_Block {

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

        $html  = Horde::link(Horde::url($registry->getInitialPage(), true), $registry->getParam('name'), 'header') . $registry->getParam('name') . '</a> :: ';
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
        global $registry, $prefs, $cManager;
        require_once dirname(__FILE__) . '/../base.php';
        require_once KRONOLITH_BASE . '/lib/Day.php';

        Horde::addScriptFile('tooltip.js', 'horde');

        $now = time();
        $today = date('j');
        $colors = $cManager->colors();
        $startDate = Kronolith::timestampToObject(mktime(0, 0, 0));
        $endDate = Kronolith::timestampToObject(mktime(0, 0, 0, date('n'), $today + $prefs->getValue('summary_days')));

        if (isset($this->_params['calendar']) && $this->_params['calendar'] != '__all') {
            $allevents = Kronolith::listEvents($startDate, $endDate, array($this->_params['calendar']));
        } else {
            $allevents = Kronolith::listEvents($startDate, $endDate, $GLOBALS['display_calendars']);
        }

        $html = '<table border="0" cellpadding="0" cellspacing="0" width="100%">';
        $iMax = $today + $prefs->getValue('summary_days');
        $firstday = true;
        for ($i = $today; $i < $today + $iMax; $i++) {
            $day = &new Kronolith_Day(date('n'), $i);
            if (empty($allevents[$day->getStamp()])) {
                continue;
            }

            $events = &$allevents[$day->getStamp()];
            $firstevent = true;
            $htmldays = array();

            $today12am = mktime(0, 0, 0, $day->month, $day->mday, $day->year);
            $tomorrow12am = mktime(0, 0, 0, $day->month, $day->mday + 1, $day->year);
            foreach ($events as $event) {
                if (!$event->hasRecurType(KRONOLITH_RECUR_NONE)) {
                    $event->startTimestamp = mktime($event->start->hour, $event->start->min, $event->start->sec, $day->month, $day->mday, $day->year);
                    $event->endTimestamp = $event->startTimestamp + $event->durMin * 60;
                } else {
                    if ($event->startTimestamp < $today12am) {
                        $event->startTimestamp = $today12am;
                    }
                    if ($event->endTimestamp >= $tomorrow12am) {
                        $event->endTimestamp = $tomorrow12am;
                    }
                }
                if ($event->endTimestamp < $now) continue;
                if ($prefs->getValue('summary_alarms') && !$event->alarm) continue;
                if ($firstevent) {
                    if (!$firstday) {
                        $html .= '<tr><td colspan="3" style="font-size:2px;">&nbsp;</td></tr>';
                    }
                    $html .= '<tr><td colspan="3" class="control"><b>';
                    if ($day->isToday()) {
                        $dayname = _("Today");
                    } elseif ($day->isTomorrow()) {
                        $dayname = _("Tomorrow");
                    } else {
                        $dayname = strftime($prefs->getValue('date_format'), $day->getStamp());
                    }
                    $daylink = Horde::applicationUrl('day.php');
                    $daylink = Util::addParameter($daylink, 'timestamp', $day->getStamp());
                    $html .= Horde::link($daylink, sprintf(_("Goto %s"), $dayname));
                    $html .= $dayname . '</a></b></td></tr>';
                    $firstevent = false;
                    $firstday = false;
                }
                $htmlday = '<tr><td class="text" nowrap="nowrap" valign="top">';
                if ($event->startTimestamp < $now && $event->endTimestamp > $now) {
                    $htmlday .= '<b>';
                }

                /* The following check to make sure the start time is
                 * not 12AM was changed to use the getStartDate
                 * function to get the startTimestamp hour and min
                 * instead of using start->hour and start->min. When
                 * using the SQL driver this change properly lists a
                 * multiday event as 'All day' if it spans the entire
                 * day. It shouldn't affect the MCAL driver since in
                 * the case of the MCAL driver the startTimestamp hour
                 * and min are the same as start->hour and
                 * start->min. */
                if ($event->getStartDate('G') != 0 ||
                    $event->getStartDate('i') != 0 ||
                    (($event->endTimestamp - $event->startTimestamp) % (24 * 60 * 60)) != 0) {
                    if ($prefs->getValue('twentyFour')) {
                        $time  = date('G:i', $event->startTimestamp) . '-';
                        $time .= date('G:i', $event->endTimestamp);
                    } else {
                        $time  = date('g:i A', $event->startTimestamp) . '-';
                        $time .= date('g:i A', $event->endTimestamp);
                    }
                } else {
                    $time = _("All day event");
                }

                $text = $event->getTitle();
                if ($location = $event->getLocation()) {
                    $text .= ' (' . $location . ')';
                }
                if (isset($event->taskID)) {
                    $htmlday .= Horde::link(Horde::url($registry->link('tasks/show',
                                                                       array('task' => $event->taskID,
                                                                             'tasklist' => $event->tasklistID)),
                                                       $event->title)) . $time . '</a>';
                } else {
                    $htmlday .= $time;
                }
                if ($event->startTimestamp < $now && $event->endTimestamp > $now) {
                    $htmlday .= '</b>';
                }

                $categoryColor = isset($colors[$event->getCategory()]) ? $colors[$event->getCategory()] : $colors['_default_'];
                $htmlday .= '</td><td class="text">&nbsp;&nbsp;&nbsp;</td>';
                $htmlday .= '<td class="block-eventbox" style="background-color: ' . $categoryColor . '; ';
                $htmlday .= 'border-color: ' . Kronolith::borderColor($categoryColor) . '" ';
                $htmlday .= 'onmouseover="javascript:style.backgroundColor=\'' . Kronolith::highlightColor($categoryColor) . '\'" ';
                $htmlday .= 'onmouseout="javascript:style.backgroundColor=\'' . $categoryColor . '\'" ';
                $htmlday .= 'valign="top">';

                if ($event->startTimestamp < $now && $event->endTimestamp > $now) {
                    $htmlday .= '<b>';
                }
                if (isset($event->eventID)) {
                    $htmlday .= $event->getLink(null, true);
                } elseif (isset($event->taskID)) {
                    $htmlday .= Horde::link(Horde::url($registry->link('tasks/show', array('task' => $event->taskID,
                                                                                           'tasklist' => $event->tasklistID)),
                                                       true), $event->title) . $text . '</a>';
                } else {
                    $htmlday .= $text;
                }
                if ($event->startTimestamp < $now && $event->endTimestamp > $now) {
                    $html .= '</b>';
                }
                $htmlday .= '</td></tr>';
                while (isset($htmldays[$event->startTimestamp])) {
                    $event->startTimestamp++;
                }
                $htmldays[$event->startTimestamp] = $htmlday;
            }
            ksort($htmldays);
            $html .= implode("\n", $htmldays);

        }

        if (empty($htmldays)) {
            $html .= '<i>' . _("No events to display") . '</i>';
        }
        return $html . '</table>';
    }

}
