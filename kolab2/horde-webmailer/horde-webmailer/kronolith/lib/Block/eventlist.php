<?php

$block_name = _("Calendar List View");

/**
 * Horde_Block_Kronolith_eventlist:: Implementation of the Horde_Block API to
 * display a list of events.
 *
 * $Horde: kronolith/lib/Block/summary.php,v 1.41.2.14 2008/08/21 00:31:03 mrubinsk Exp $
 *
 * @package Horde_Block
 */
class Horde_Block_Kronolith_eventlist extends Horde_Block {

    var $_app = 'kronolith';

    function _params()
    {
        @define('KRONOLITH_BASE', dirname(__FILE__) . '/../..');
        require_once KRONOLITH_BASE . '/lib/base.php';

        $params = array('days' => array('name' => _("Days"),
                                        'type' => 'int',
                                        'default' => 42),
                        'maxevents' => array('name' => _("Maximum number of events to display (0 = no limit)"),
                                             'type' => 'int',
                                             'default' => 0));

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
        return '';
    }

    /**
     * The content to go in this block.
     *
     * @return string   The content
     */
    function _content()
    {
        global $kronolith_driver, $registry, $prefs;
        require_once dirname(__FILE__) . '/../base.php';
        require_once KRONOLITH_BASE . '/lib/Day.php';
        require_once 'Horde/Prefs/CategoryManager.php';
        require_once 'Horde/Text/Filter.php';

        if (!empty($this->_params['days'])) {
            $span = $this->_params['days'];
        } else {
            $span = 42;
        }

        $now = $_SERVER['REQUEST_TIME'];
        $today = date('j');

        $startDate = new Horde_Date(array('year' => date('Y'), 'month' => date('n'), 'mday' => date('j')));
        $endDate = new Horde_Date(array('year' => date('Y'), 'month' => date('n'), 'mday' => date('j') + $span));
        $endDate->correct();

        if (isset($this->_params['calendar']) &&
            $this->_params['calendar'] != '__all') {

            $calendar = $GLOBALS['kronolith_shares']->getShare($this->_params['calendar']);
            if (!is_a($calendar, 'PEAR_Error') && !$calendar->hasPermission(Auth::getAuth(), PERMS_SHOW)) {
                return _("Permission Denied");
            }

            $all_events = Kronolith::listEvents($startDate,
                                                $endDate,
                                                array($this->_params['calendar']));
        } else {
            $calendars = Kronolith::listCalendars(false, PERMS_SHOW);
            $all_events = Kronolith::listEvents($startDate,
                                                $endDate,
                                                array_keys($calendars));
        }
        if (is_a($all_events, 'PEAR_Error')) {
            return '<em>' . $all_events->getMessage() . '</em>';
        }

        $iMax = $today + $span;

        $html = '';
        $firstday = true;
        $olddayname = '';
        $totalevents = 0;

        $displayed = array();

        for ($i = $today; $i < $iMax; ++$i) {
            $day = new Kronolith_Day(date('n'), $i);

            if ($day->isToday()) {
                $dayname = _("Today");
            } elseif ($day->isTomorrow()) {
                $dayname = _("Tomorrow");
            } elseif ($day->weekOfYear() == $startDate->weekOfYear()) {
                $dayname = _("This week");
            } elseif ($day->month == $startDate->month) {
                if ($day->weekOfYear() == $startDate->weekOfYear() + 1) {
                    $dayname = _("Next week");
                } elseif ($day->weekOfYear() == $startDate->weekOfYear() + 2) {
                    $dayname = _("Two weeks from now");
                } elseif ($day->weekOfYear() == $startDate->weekOfYear() + 3) {
                    $dayname = _("Three weeks from now");
                } elseif ($day->weekOfYear() == $startDate->weekOfYear() + 4) {
                    $dayname = _("Four weeks from now");
                } elseif ($day->weekOfYear() == $startDate->weekOfYear() + 5) {
                    $dayname = _("Five weeks from now");
                }
            } elseif ($day->month - 1 == $startDate->month
                      || ($day->month == 1 && $startDate->month == 12)) {
                $dayname = _("Next month");
            } elseif ($day->year == $startDate->year) {
                $dayname = $day->format('F');
            } elseif ($day->year - 1 == $startDate->year) {
                $dayname = _("Next year");
            } else {
                $dayname = _("After the next year");
            }

            if (empty($all_events[$day->getStamp()])) {
                continue;
            }

            $events = &$all_events[$day->getStamp()];

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

                if ($event->end->timestamp() < $now) {
                    continue;
                }
                if ($dayname != $olddayname) {
                    if (!$firstday) {
                        $html .= '<tr><td colspan="3">&nbsp;</td></tr>';
                    }
                    $html .= '<tr align="center"><td colspan="3" class="section">';
                    $html .= $dayname . '</td></tr>';
                    $olddayname = $dayname;
                    $firstday = false;
                }

                if (in_array($event->getId(), $displayed)) {
                    continue;
                }

                $category = $event->getCategory();
                if (!empty($category)) {
                    $ctd = '<td class="category_bar category' . md5($category) . '" width="1%" />';
                } else {
                    $ctd = '<td />';
                }

                if ($event->isAllDay()) {
                    $format = 'D, d M Y';
                } else {
                    $format = 'G:i T D, d M Y';
                }

                if ($event->start->timestamp() < $now) {
                    $time = _('until') . date($format, $event->end->timestamp());
                } else {
                    $time = date($format, $event->start->timestamp()) . _(' to ') .
                        date($format, $event->end->timestamp());
                }

                $html .= '<tr>' . $ctd . '<td class="event" style="vertical-align:top;"><div class="time">';

                if ($event->start->timestamp() < $now &&
                    $event->end->timestamp() > $now) {
                    $html .= '<strong>';
                }

                $html .= $time;

                if ($event->start->timestamp() < $now &&
                    $event->end->timestamp() > $now) {
                    $html .= '</strong>';
                }

                $html .= '</div><div class="location" style="vertical-align:top">';
                $html .= $event->getLocation();
                $html .= '</div></td><td style="vertical-align:top;" class="event"><div class="eventtitle">';
                $html .= $event->getTitle();
                $html .= '</div>';

                $html .= '<div class="description">';
                $desc = Text_Filter::filter($event->getDescription(), 'text2html', array('parselevel' => TEXT_HTML_MICRO, 'class' => 'text'));
                $html .= strtr($desc, array("\n" => " ", "\r" => " "));
                $html .= '</div>';

                $html .= '</td></tr>';

                $html .= '<tr>' . $ctd . '<td  class="linedRow"/><td class="linedRow annotation">';

                if (!empty($category)) {
                    $html .= '<div style="text-align:right;float:left;">';
                    $html .= _("Category") . ': ' . $category;
                    $html .= '</div>';
                }

                $html .= '<div style="text-align:right">';
                $html .= _("Calendar") . ': ' . urldecode($event->getCalendar());
                $html .= '</div>';

                $html .= '</td></tr>';

                $totalevents++;

                $displayed[] = $event->getId();
            }
        }

        if (empty($html)) {
            return '<em>' . _("No events to display") . '</em>';
        }

        return '<link href="' . Horde::applicationUrl('themes/categoryCSS.php') . '" rel="stylesheet" type="text/css" /><table cellspacing="0" width="100%">' . $html . '</table>';
    }

}
