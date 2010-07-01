<?php

require_once KRONOLITH_BASE . '/lib/Day.php';

/**
 * The Kronolith_View_Month:: class provides an API for viewing
 * months.
 *
 * $Horde: kronolith/lib/Views/Month.php,v 1.17.2.3 2009-11-07 14:34:57 jan Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Kronolith 2.2
 * @package Kronolith
 */
class Kronolith_View_Month {

    var $month;
    var $year;
    var $_events = array();
    var $_currentCalendars = array();
    var $_daysInView;
    var $_startOfView;
    var $_startday;

    function Kronolith_View_Month($month = null, $year = null, $events = null)
    {
        global $prefs;

        if ($month === null) {
            $month = date('n');
        }
        if ($year === null) {
            $year = date('Y');
        }
        $this->month = $month;
        $this->year = $year;

        // Need to calculate the start and length of the view.
        $this->_startday = new Horde_Date(array('mday' => 1,
                                         'month' => $this->month,
                                         'year' => $this->year));
        $this->_startday = $this->_startday->dayOfWeek();
        $this->_daysInView = Date_Calc::weeksInMonth($this->month, $this->year) * 7;
        if (!$prefs->getValue('week_start_monday')) {
            $this->_startOfView = 1 - $this->_startday;

            // We may need to adjust the number of days in the view if
            // we're starting weeks on Sunday.
            if ($this->_startday == HORDE_DATE_SUNDAY) {
                $this->_daysInView -= 7;
            }
            $endday = new Horde_Date(array('mday' => Horde_Date::daysInMonth($this->month, $this->year),
                                           'month' => $this->month,
                                           'year' => $this->year));
            $endday = $endday->dayOfWeek();
            if ($endday == HORDE_DATE_SUNDAY) {
                $this->_daysInView += 7;
            }
        } else {
            if ($this->_startday == HORDE_DATE_SUNDAY) {
                $this->_startOfView = -5;
            } else {
                $this->_startOfView = 2 - $this->_startday;
            }
        }

        if ($events !== null) {
            $this->_events = $events;
        } else {
            $startDate = new Horde_Date(array('year' => $this->year,
                                              'month' => $this->month,
                                              'mday' => $this->_startOfView));
            $endDate = new Horde_Date(array('year' => $this->year,
                                            'month' => $this->month,
                                            'mday' => $this->_startOfView + $this->_daysInView,
                                            'hour' => 23,
                                            'min' => 59,
                                            'sec' => 59));
            $startDate->correct();
            $endDate->correct();
            $this->_events = Kronolith::listEvents($startDate, $endDate, $GLOBALS['display_calendars']);
            if ($prefs->getValue('show_shared_side_by_side')) {
                $allCalendars = Kronolith::listCalendars();
                $this->_currentCalendars = array();
                foreach ($GLOBALS['display_calendars'] as $id) {
                    $this->_currentCalendars[$id] = &$allCalendars[$id];
                }
            } else {
                $this->_currentCalendars = array(true);
            }
        }

        if (is_a($this->_events, 'PEAR_Error')) {
            $GLOBALS['notification']->push($this->_events, 'horde.error');
            $this->_events = array();
        }
        if (!is_array($this->_events)) {
            $this->_events = array();
        }
    }

    function html()
    {
        global $prefs;

        $sidebyside = $prefs->getValue('show_shared_side_by_side');
        $twentyFour = $prefs->getValue('twentyFour');
        $addLinks = Kronolith::getDefaultCalendar(PERMS_EDIT) &&
            (!empty($GLOBALS['conf']['hooks']['permsdenied']) ||
             Kronolith::hasPermission('max_events') === true ||
             Kronolith::hasPermission('max_events') > Kronolith::countEvents());

        if ($sidebyside) {
            require KRONOLITH_TEMPLATES . '/month/head_side_by_side.inc';
        } else {
            require KRONOLITH_TEMPLATES . '/month/head.inc';
        }

        $eventCategories = array();

        $html = '';
        if (!$sidebyside && count($this->_currentCalendars)) {
            $html .= '<tr>';
        }

        $showLocation = Kronolith::viewShowLocation();
        $showTime = Kronolith::viewShowTime();
        $day_url = Horde::applicationUrl('day.php');
        $this_link = $this->link(0, true);
        $new_url = Util::addParameter(Horde::applicationUrl('new.php'), 'url', $this_link);
        $new_img = Horde::img('new_small.png', '+');

        foreach ($this->_currentCalendars as $id => $cal) {
            if ($sidebyside) {
                $html .= '<tr>';
            }

            $cell = 0;
            for ($day = $this->_startOfView; $day < $this->_startOfView + $this->_daysInView; ++$day) {
                $date = new Horde_Date(array('year' => $this->year, 'month' => $this->month, 'mday' => $day));
                $daystamp = $date->timestamp();
                $date->hour = $twentyFour ? 12 : 6;
                $timestamp = $date->timestamp();
                $week = $date->weekOfYear();

                if ($cell % 7 == 0 && $cell != 0) {
                    if ($sidebyside) {
                        $html .= '<td>' . htmlspecialchars($cal->get('name')) . '</td>';
                    } else {
                        $html .= "</tr>\n<tr>";
                    }
                }
                if (mktime(0, 0, 0) == $daystamp) {
                    $style = 'today';
                } elseif (date('n', $daystamp) != $this->month) {
                    $style = 'othermonth';
                } elseif (date('w', $daystamp) == 0 || date('w', $daystamp) == 6) {
                    $style = 'weekend';
                } else {
                    $style = 'text';
                }

                $html .= '<td class="' . $style . '" height="70" width="14%" valign="top"><div>';

                $url = Util::addParameter($day_url, 'timestamp', $daystamp);
                $html .= '<a class="day" href="' . $url . '">' . date('j', $daystamp) . '</a>';

                if ($addLinks) {
                    $url = Util::addParameter($new_url, 'timestamp', $timestamp);
                    if ($sidebyside) {
                        $url = Util::addParameter($url, 'calendar', $id);
                    }
                    $html .= Horde::link($url, _("Create a New Event"), 'newEvent') .
                        $new_img . '</a>';
                }

                if ($date->dayOfWeek() == HORDE_DATE_MONDAY) {
                    $url = Util::addParameter('week.php', 'week', $week);
                    if ($this->month == 12 && $week == 1) {
                        $url = Util::addParameter($url, 'year', $this->year + 1);
                    } elseif ($this->month == 1 && $week > 51) {
                        $url = Util::addParameter($url, 'year', $this->year - 1);
                    } else {
                        $url = Util::addParameter($url, 'year', $this->year);
                    }
                    $html .= Horde::link(Horde::applicationUrl($url), '', 'week') . sprintf(_("Week %d"), $week) . '</a>';
                }

                $html .= '</div><div class="clear">&nbsp;</div>';

                if (!empty($this->_events[$daystamp]) &&
                    count($this->_events[$daystamp])) {
                    foreach ($this->_events[$daystamp] as $event) {
                        if (!$sidebyside || $event->getCalendar() == $id) {
                            if ($event->hasPermission(PERMS_READ)) {
                                $eventCategories[$event->getCategory()] = true;
                            }
                            $html .= '<div class="month-eventbox category' . md5($event->getCategory()) . '">'
                                . $event->getLink($timestamp, true, $this_link);
                            if ($showTime) {
                                $html .= '<div class="event-time">' . htmlspecialchars($event->getTimeRange()) . '</div>';
                            }
                            if ($showLocation) {
                                $html .= '<div class="event-location">' . htmlspecialchars($event->getLocation()) . '</div>';
                            }
                            $html .= '</div>';
                        }
                    }
                }

                $html .= "</td>\n";
                ++$cell;
            }

            if ($sidebyside) {
                $html .= '</tr>';
            }
        }
        if (!$sidebyside && count($this->_currentCalendars)) {
            $html .= '</tr>';
        }

        echo $html . '</tbody></table>';
        require KRONOLITH_TEMPLATES . '/category_legend.inc';
    }

    function getStamp($offset = 0)
    {
        return @mktime(1, 1, 1, $this->month + $offset, 1, $this->year);
    }

    function getMonth($offset = 0)
    {
        $stamp = $this->getStamp($offset);
        return array('month' => date('n', $stamp),
                     'year' => date('Y', $stamp));
    }

    function link($offset = 0, $full = false)
    {
        $month = $this->getMonth($offset);
        return Horde::applicationUrl(Util::addParameter('month.php',
                                                        array('month' => $month['month'],
                                                              'year' => $month['year'])), $full);
    }

    function getName()
    {
        return 'Month';
    }

}
