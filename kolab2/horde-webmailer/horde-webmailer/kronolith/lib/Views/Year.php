<?php

require_once KRONOLITH_BASE . '/lib/Day.php';

/**
 * The Kronolith_View_Year:: class provides an API for viewing years.
 *
 * $Horde: kronolith/lib/Views/Year.php,v 1.12.2.3 2008-09-17 08:52:02 jan Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Kronolith 2.2
 * @package Kronolith
 */
class Kronolith_View_Year {

    var $year;
    var $_events = array();

    function Kronolith_View_Year($year = null, $events = null)
    {
        if ($year === null) {
            $year = date('Y');
        }
        $this->year = $year;

        if ($events !== null) {
            $this->_events = $events;
        } else {
            $startDate = new Horde_Date(array('year' => $year,
                                              'month' => 1,
                                              'mday' => 1));
            $endDate = new Horde_Date(array('year' => $year,
                                            'month' => 12,
                                            'mday' => 31,
                                            'hour' => 23,
                                            'min' => 59,
                                            'sec' => 59));
            $startDate->correct();
            $endDate->correct();

            $this->_events = Kronolith::listEvents($startDate, $endDate, $GLOBALS['display_calendars']);
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

        $today = mktime(0, 0, 0);
        $timestamp = mktime(1, 1, 1, 1, 1, $this->year);
        $prevstamp = mktime(1, 1, 1, 1, 1, $this->year - 1);
        $nextstamp = mktime(1, 1, 1, 1, 1, $this->year + 1);

        require KRONOLITH_TEMPLATES . '/year/head.inc';

        $html = '<table class="nopadding" cellspacing="5" width="100%"><tr>';
        for ($month = 1; $month <= 12; ++$month) {
            $html .= '<td valign="top">';

            // Heading for each month.
            $mtitle = strftime('%B', mktime(1, 1, 1, $month, 1, $this->year));
            $url = Util::addParameter(Horde::applicationUrl('month.php'), array('month' => $month, 'year' => date('Y', $timestamp)));
            $html .= '<h2 class="smallheader"><a class="smallheader" href="' . $url . '">' . $mtitle . '</a></h2>' .
                '<table class="nopadding monthgrid" cellspacing="0" width="100%"><thead><tr class="item">';
            if (!$prefs->getValue('week_start_monday')) {
                $html .= '<th>' . _("Su"). '</th>';
            }
            $html .= '<th>' . _("Mo") . '</th>' .
                '<th>' . _("Tu") . '</th>' .
                '<th>' . _("We") . '</th>' .
                '<th>' . _("Th") . '</th>' .
                '<th>' . _("Fr") . '</th>' .
                '<th>' . _("Sa") . '</th>';
            if ($prefs->getValue('week_start_monday')) {
                $html .= '<th>' . _("Su") . '</th>';
            }
            $html .= '</tr></thead><tbody><tr>';

            $startday = new Horde_Date(array('mday' => 1,
                                             'month' => $month,
                                             'year' => $this->year));
            $startday = $startday->dayOfWeek();

            $daysInView = Date_Calc::weeksInMonth($month, $this->year) * 7;
            if (!$prefs->getValue('week_start_monday')) {
                $startOfView = 1 - $startday;

                // We may need to adjust the number of days in the
                // view if we're starting weeks on Sunday.
                if ($startday == HORDE_DATE_SUNDAY) {
                    $daysInView -= 7;
                }
                $endday = new Horde_Date(array('mday' => Horde_Date::daysInMonth($month, $this->year),
                                               'month' => $month,
                                               'year' => $this->year));
                $endday = $endday->dayOfWeek();
                if ($endday == HORDE_DATE_SUNDAY) {
                    $daysInView += 7;
                }
            } else {
                if ($startday == HORDE_DATE_SUNDAY) {
                    $startOfView = -5;
                } else {
                    $startOfView = 2 - $startday;
                }
            }

            $currentCalendars = array(true);
            $eventCategories = array();

            foreach ($currentCalendars as $id => $cal) {
                $cell = 0;
                for ($day = $startOfView; $day < $startOfView + $daysInView; ++$day) {
                    $date = new Horde_Date(array('year' => $this->year, 'month' => $month, 'mday' => $day));
                    $daystamp = $date->timestamp();
                    $date->hour = $prefs->getValue('twentyFour') ? 12 : 6;
                    $timestamp = $date->timestamp();
                    $week = $date->weekOfYear();

                    if ($cell % 7 == 0 && $cell != 0) {
                        $html .= "</tr>\n<tr>";
                    }
                    if (date('n', $daystamp) != $month) {
                        $style = 'monthgrid';
                    } elseif (date('w', $daystamp) == 0 || date('w', $daystamp) == 6) {
                        $style = 'weekend';
                    } else {
                        $style = 'text';
                    }

                    /* Set up the link to the day view. */
                    $url = Horde::applicationUrl('day.php', true);
                    $url = Util::addParameter($url, array('timestamp' => $daystamp));

                    if (date('n', $daystamp) != $month) {
                        $cellday = '&nbsp;';
                    } elseif (!empty($this->_events[$daystamp])) {
                        /* There are events; create a cell with tooltip to list
                         * them. */
                        $day_events = '';
                        foreach ($this->_events[$daystamp] as $event) {
                            if ($event->getStatus() == KRONOLITH_STATUS_CONFIRMED) {
                                /* Set the background color to distinguish the
                                 * day */
                                $style = 'year-event';
                            }

                            if ($event->isAllDay()) {
                                $day_events .= _("All day");
                            } else {
                                $day_events .= $event->start->strftime($prefs->getValue('twentyFour') ? '%R' : '%I:%M%p') . '-' . $event->end->strftime($prefs->getValue('twentyFour') ? '%R' : '%I:%M%p');
                            }
                            $day_events .= ':'
                                . (($event->getLocation()) ? ' (' . $event->getLocation() . ')' : '')
                                . ' ' . $event->getTitle() . "\n";
                        }
                        /* Bold the cell if there are events. */
                        $cellday = '<strong>' . Horde::linkTooltip($url, _("View Day"), '', '', '', $day_events) . date('j', $daystamp) . '</a></strong>';
                    } else {
                        /* No events, plain link to the day. */
                        $cellday = Horde::linkTooltip($url, _("View Day")) . date('j', $daystamp) . '</a>';
                    }
                    if ($today == $daystamp && date('n', $daystamp) == $month) {
                        $style .= ' today';
                    }

                    $html .= '<td align="center" class="' . $style . '" height="10" width="5%" valign="top">' .
                        $cellday . '</td>';
                    ++$cell;
                }
            }

            $html .= '</tr></tbody></table></td>';
            if ($month % 3 == 0 && $month != 12) {
                $html .= '</tr><tr>';
            }
        }

        echo $html . '</tr></table>';
    }

    function link($offset = 0, $full = false)
    {
        return Horde::applicationUrl(Util::addParameter('year.php', 'year', $this->year + $offset), $full);
    }

    function getName()
    {
        return 'Year';
    }

}
