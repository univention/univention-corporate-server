<?php
/**
 * Horde_Block_Kronolith_monthlist:: Implementation of the Horde_Block API
 * to display a list of calendar items grouped by month.
 *
 * $Horde: kronolith/lib/Block/monthlist.php,v 1.12 2004/05/27 17:51:54 chuck Exp $
 *
 * @package Horde_Block
 */
class Horde_Block_Kronolith_monthlist extends Horde_Block {

    var $_app = 'kronolith';

    function getParams()
    {
        @define('KRONOLITH_BASE', dirname(__FILE__) . '/..');
        require_once KRONOLITH_BASE . '/lib/base.php';

        $params = array('calendar' => array('name' => _("Calendar"),
                                            'type' => 'enum',
                                            'default' => '__all'),
                        'months'   => array('name' => _("Months Ahead"),
                                            'type' => 'int',
                                            'default' => '2'));
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

        $html  = Horde::link(Horde::url($registry->getInitialPage(), true), _("Monthly Events List"), 'header') . _("Monthly Events List") . '</a> :: ';
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
        $current_month = '';
        $colors = $cManager->colors();

        /* Get timestamps. */
        $startDate = mktime(0, 0, 0, date('n'), 1);
        $endDate = mktime(0, 0, 0, date('n') + $this->_params['months'], $today);

        /* Get Kronolith objects from timestamps. */
        $startDate_object = Kronolith::timestampToObject($startDate);
        $endDate_object = Kronolith::timestampToObject($endDate);

        if (isset($this->_params['calendar']) && $this->_params['calendar'] != '__all') {
            $allevents = Kronolith::listEvents($startDate_object, $endDate_object, array($this->_params['calendar']));
        } else {
            $allevents = Kronolith::listEvents($startDate_object, $endDate_object, $GLOBALS['display_calendars']);
        }

        $html = '<table border="0" cellpadding="0" cellspacing="0" width="100%">';

        /* How many days do we need to check. */
        $iMax = ($endDate - $startDate) / 86400;

        /* Loop through the days. */
        for ($i = $today; $i < $iMax; $i++) {
            $day = &new Kronolith_Day(date('n'), $i);
            $today_stamp = $day->getStamp();
            if (empty($allevents[$today_stamp])) {
                continue;
            }

            $events = &$allevents[$today_stamp];
            $firstevent = true;
            $htmldays = array();

            /* Output month header. */
            if ($current_month != $day->month) {
                $current_month = strftime('%m', $today_stamp);
                $html .= '<tr><td colspan="4" class="control"><b>' . strftime('%B', $today_stamp) . '</b></td></tr>';
            }

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
                    $html .= '<tr><td class="text" valign="top" align="right"><b>';
                    if ($day->isToday()) {
                        $html .= _("Today");
                    } elseif ($day->isTomorrow()) {
                        $html .= _("Tomorrow");
                    } else {
                        $html .= strftime('%e', $today_stamp);
                    }
                    $html .= '</b>&nbsp;</td>';
                    $htmlday = '';
                    $firstevent = false;
                } else {
                    $htmlday = '<tr><td class="text">&nbsp;</td>';
                }

                $htmlday .= '<td class="text" nowrap="nowrap" valign="top">';
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
                    $htmlday .= $location;
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
            $html .= sprintf('<i>%s</i>', _("No events to display"));
        }
        return $html . '</table>';
    }

}
