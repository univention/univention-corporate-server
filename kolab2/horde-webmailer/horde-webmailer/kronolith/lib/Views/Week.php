<?php

require_once dirname(__FILE__) . '/Day.php';

/**
 * The Kronolith_View_Week:: class provides an API for viewing weeks.
 *
 * $Horde: kronolith/lib/Views/Week.php,v 1.24.2.7 2009-12-01 22:56:05 jan Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Kronolith 0.1
 * @package Kronolith
 */
class Kronolith_View_Week {

    var $parsed = false;
    var $days = array();
    var $week = null;
    var $year = null;
    var $startDay = null;
    var $endDay = null;
    var $_controller = 'week.php';
    var $_sidebyside = false;
    var $_currentCalendars = array();

    /**
     * How many time slots are we dividing each hour into?
     *
     * @var integer
     */
    var $_slotsPerHour = 2;

    /**
     * How many slots do we have per day? Calculated from $_slotsPerHour.
     *
     * @see $_slotsPerHour
     * @var integer
     */
    var $_slotsPerDay;

    function Kronolith_View_Week($week = null, $year = null, $startDay = null, $endDay = null)
    {
        if (empty($year)) {
            $year = date('Y');
        }
        if (empty($week)) {
            $date = new Horde_Date(array('year' => $year, 'month' => date('n'), 'mday' => date('j')));
            $week = $date->weekOfYear();
            if (!$GLOBALS['prefs']->getValue('week_start_monday') && $date->dayOfWeek() == HORDE_DATE_SUNDAY) {
                ++$week;
            }
            if ($week > 51 && $date->month == 1) {
                --$year;
            } elseif ($week == 1 && $date->month == 12) {
                ++$year;
            }
        } else {
            $weeksInYear = Horde_Date::weeksInYear($year);
            if ($week < 1) {
                --$year;
                $week += $weeksInYear;
            } elseif ($week > $weeksInYear) {
                $week -= $weeksInYear;
                ++$year;
            }
        }

        $this->year = $year;
        $this->week = $week;

        if ($startDay === null || $endDay === null) {
            if ($this->startDay === null) {
                if ($GLOBALS['prefs']->getValue('week_start_monday')) {
                    $this->startDay = HORDE_DATE_MONDAY;
                    $this->endDay = HORDE_DATE_SUNDAY + 7;
                } else {
                    $this->startDay = HORDE_DATE_SUNDAY;
                    $this->endDay = HORDE_DATE_SATURDAY;
                }
            }
        } else {
            $this->startDay = $startDay;
            $this->endDay = $endDay;
        }

        $firstDay = Horde_Date::firstDayOfWeek($week, $year) + Date_Calc::dateToDays(1, 1, $year) - 1;

        for ($i = $this->startDay; $i <= $this->endDay; ++$i) {
            list($day, $month, $year) = explode('/', Date_Calc::daysToDate($firstDay + $i, '%d/%m/%Y'));
            $this->days[$i] = new Kronolith_View_Day($month, $day, $year, array());
        }

        list($sday, $smonth, $syear) = explode('/', Date_Calc::daysToDate($firstDay + $this->startDay, '%d/%m/%Y'));
        list($eday, $emonth, $eyear) = explode('/', Date_Calc::daysToDate($firstDay + $this->endDay, '%d/%m/%Y'));
        $startDate = new Horde_Date(array('year' => $syear, 'month' => $smonth, 'mday' => $sday));
        $endDate = new Horde_Date(array('year' => $eyear, 'month' => $emonth, 'mday' => $eday,
                                        'hour' => 23, 'min' => 59, 'sec' => 59));
        $endDate->correct();
        $allevents = Kronolith::listEvents($startDate, $endDate, $GLOBALS['display_calendars']);
        if (is_a($allevents, 'PEAR_Error')) {
            $GLOBALS['notification']->push($allevents, 'horde.error');
            $allevents = array();
        }
        for ($i = $this->startDay; $i <= $this->endDay; ++$i) {
            $this->days[$i]->setEvents(isset($allevents[$this->days[$i]->getStamp()]) ?
                                       $allevents[$this->days[$i]->getStamp()] :
                                       array());
        }
        $this->_sidebyside = $this->days[$this->startDay]->_sidebyside;
        $this->_currentCalendars = $this->days[$this->startDay]->_currentCalendars;
        $this->_slotsPerHour = $this->days[$this->startDay]->_slotsPerHour;
        $this->_slotsPerDay = $this->days[$this->startDay]->_slotsPerDay;
        $this->_slotLength = $this->days[$this->startDay]->_slotLength;
    }

    function html()
    {
        global $prefs;

        $more_timeslots = $prefs->getValue('time_between_days');
        $include_all_events = !$prefs->getValue('show_shared_side_by_side');
        $showLocation = Kronolith::viewShowLocation();
        $showTime = Kronolith::viewShowTime();

        if (!$this->parsed) {
            $this->parse();
        }

        $slots = $this->days[$this->startDay]->slots;
        $cid = 0;
        require KRONOLITH_TEMPLATES . '/week/head.inc';
        if ($this->_sidebyside) {
            require KRONOLITH_TEMPLATES . '/week/head_side_by_side.inc';
        }
        echo '</thead><tbody>';

        $event_count = 0;
        for ($j = $this->startDay; $j <= $this->endDay; ++$j) {
            foreach ($this->_currentCalendars as $cid => $cal) {
                $event_count = max($event_count, count($this->days[$j]->_all_day_events[$cid]));
                reset($this->days[$j]->_all_day_events[$cid]);
            }
        }

        if ($more_timeslots) {
            $newEventUrl = null;
        } else {
            $newEventUrl = _("All day");
        }

        $eventCategories = array();

        $row = '';
        for ($j = $this->startDay; $j <= $this->endDay; ++$j) {
            $row .= '<td class="hour rightAlign daySpacer">' . ($more_timeslots ? _("All day") : '&nbsp;') . '</td>' .
                '<td colspan="' . $this->days[$j]->_totalspan . '" valign="top"><table width="100%" cellspacing="0">';
            if ($this->days[$j]->_all_day_maxrowspan > 0) {
                for ($k = 0; $k < $this->days[$j]->_all_day_maxrowspan; ++$k) {
                    $row .= '<tr>';
                    foreach ($this->days[$j]->_currentCalendars as $cid => $cal) {
                        if (count($this->days[$j]->_all_day_events[$cid]) === $k) {
                            $row .= '<td rowspan="' . ($this->days[$j]->_all_day_maxrowspan - $k) . '" width="'. round(99 / count($this->days[$j]->_currentCalendars)) . '%">&nbsp;</td>';
                        } elseif (count($this->days[$j]->_all_day_events[$cid]) > $k) {
                            $event = $this->days[$j]->_all_day_events[$cid][$k];
                            if ($event->hasPermission(PERMS_READ)) {
                                $eventCategories[$event->getCategory()] = true;
                            }

                            $row .= '<td class="week-eventbox category' . md5($event->getCategory()) . '" '
                                . 'width="' . round(99 / count($this->days[$j]->_currentCalendars)) . '%" '
                                . 'valign="top">'
                                . $event->getLink($this->days[$j]->getStamp(), true, $this->link(0, true));
                            if ($showLocation) {
                                $row .= '<div class="event-location">' . htmlspecialchars($event->getLocation()) . '</div>';
                            }
                            $row .= '</td>';
                        }
                    }
                    $row .= '</tr>';
                }
            } else {
                $row .= '<tr><td colspan="' . count($this->_currentCalendars) . '">&nbsp;</td></tr>';
            }
            $row .= '</table></td>';
        }

        $rowspan = '';
        $first_row = true;
        require KRONOLITH_TEMPLATES . '/day/all_day.inc';

        $twenty_four = $prefs->getValue('twentyFour');
        $day_hour_force = $prefs->getValue('day_hour_force');
        $day_hour_start = $prefs->getValue('day_hour_start') / 2 * $this->_slotsPerHour;
        $day_hour_end = $prefs->getValue('day_hour_end') / 2 * $this->_slotsPerHour;
        $rows = array();
        $covered = array();

        for ($i = 0; $i < $this->_slotsPerDay; ++$i) {
            if ($i >= $day_hour_end && $i > $this->last) {
                break;
            }
            if ($i < $this->first && $i < $day_hour_start) {
                continue;
            }

            if (($m = $i % $this->_slotsPerHour) != 0) {
                $time = ':' . $m * $this->_slotLength;
                $hourclass = 'halfhour';
            } else {
                $time = date($twenty_four ? 'G' : 'ga', $slots[$i]['timestamp']);
                $hourclass = 'hour';
            }

            $row = '';
            for ($j = $this->startDay; $j <= $this->endDay; ++$j) {
                // Add spacer between days, or timeslots.
                if ($more_timeslots) {
                    $row .= '<td align="right" class="' . $hourclass . ' daySpacer">' . $time . '</td>';
                } else {
                    $row .= '<td class="daySpacer">&nbsp;</td>';
                }

                if (!count($this->_currentCalendars)) {
                    $row .= '<td>&nbsp;</td>';
                }

                foreach ($this->_currentCalendars as $cid => $cal) {
                     // Width (sum of colspans) of events for the current time
                     // slot.
                    $hspan = 0;
                     // $hspan + count of empty TDs in the current timeslot.
                    $current_indent = 0;

                    // $current_indent is initialized to the position of the
                    // first available cell of the day.
                    for (; isset($covered[$j][$i][$current_indent]); ++$current_indent);

                    foreach ($this->days[$j]->_event_matrix[$cid][$i] as $key) {
                        $event = &$this->days[$j]->_events[$key];
                        if ($include_all_events || $event->getCalendar() == $cid) {
                            // Since we've made sure that this event's
                            // overlap is a factor of the total span,
                            // we get this event's individual span by
                            // dividing the total span by this event's
                            // overlap.
                            $span = $this->days[$j]->_span[$cid] / $event->overlap;

                            // Store the indent we're starting this event at
                            // for future use.
                            if (!isset($event->indent)) {
                                $event->indent = $current_indent;
                            }

                            // If $event->span is set this mean than we
                            // already calculated the width of the event.
                            if (!isset($event->span)) {
                                // If the first node that we would cover is
                                // already covered, we can assume that table
                                // rendering will take care of pushing the
                                // event over. However, if the first node
                                // _isn't_ covered but any others that we
                                // would covered _are_, we only cover the
                                // available nodes.
                                if (!isset($covered[$j][$i][$event->indent])) {
                                    $collision = false;
                                    $available = 0;
                                    for ($y = $event->indent; $y < ($span + $event->indent); ++$y) {
                                        if (isset($covered[$j][$i][$y])) {
                                            $collision = true;
                                            break;
                                        }
                                        $available++;
                                    }

                                    if ($collision) {
                                        $span = $available;
                                    }
                                }

                                // We need to store the computed event span
                                // because in some cases it might not be
                                // possible to compute it again (when only the
                                // first half of the event is in colision).
                                // ceil() is needed because of some float
                                // values (bug ?)
                                $event->span = ceil($span);
                            }

                            $hspan          += $event->span;
                            $current_indent += $event->span;

                            $start = mktime(floor($i / $this->_slotsPerHour), ($i % $this->_slotsPerHour) * $this->_slotLength, 0,
                                            $this->days[$j]->month, $this->days[$j]->mday, $this->days[$j]->year);
                            if (((!$day_hour_force || $i >= $day_hour_start) &&
                                 $event->start->timestamp() >= $start &&
                                 $event->start->timestamp() < $start + 60 * $this->_slotLength ||
                                 $start == $this->days[$j]->getStamp()) ||
                                ($day_hour_force &&
                                 $i == $day_hour_start &&
                                 $event->start->timestamp() < $start)) {
                                if ($event->hasPermission(PERMS_READ)) {
                                    $eventCategories[$event->getCategory()] = true;
                                }

                                // Store the nodes that we're covering for
                                // this event in the coverage graph.
                                for ($x = $i; $x < ($i + $event->rowspan); ++$x) {
                                    for ($y = $event->indent; $y < $current_indent; ++$y) {
                                        $covered[$j][$x][$y] = true;
                                    }
                                }

                                $row .= '<td class="week-eventbox category' . md5($event->getCategory()) . '" '
                                    . 'valign="top" '
                                    . 'width="' . floor(((90 / count($this->days)) / count($this->_currentCalendars)) * ($span / $this->days[$j]->_span[$cid])) . '%" '
                                    . 'colspan="' . $event->span . '" rowspan="' . $event->rowspan . '">'
                                    . $event->getLink($this->days[$j]->getStamp(), true, $this->link(0, true));
                                if ($showTime) {
                                    $row .= '<div class="event-time">' . htmlspecialchars($event->getTimeRange()) . '</div>';
                                }
                                if ($showLocation) {
                                    $row .= '<div class="event-location">' . htmlspecialchars($event->getLocation()) . '</div>';
                                }
                                $row .= '</td>';
                            }
                        }
                    }

                    $diff = $this->days[$j]->_span[$cid] - $hspan;
                    if ($diff > 0) {
                        $row .= str_repeat('<td>&nbsp;</td>', $diff);
                    }
                }
            }

            $rows[] = array('row' => $row, 'slot' => '<span class="' . $hourclass . '">' . $time . '</span>');
        }

        require_once 'Horde/Template.php';
        $template = new Horde_Template();
        $template->set('row_height', round(20 / $this->_slotsPerHour));
        $template->set('rows', $rows);
        $template->set('show_slots', !$more_timeslots, true);
        echo $template->fetch(KRONOLITH_TEMPLATES . '/day/rows.html')
            . '</tbody></table>';

        require KRONOLITH_TEMPLATES . '/category_legend.inc';
    }

    /**
     * Parse all events for all of the days that we're handling; then
     * run through the results to get the total horizontal span for
     * the week, and the latest event of the week.
     */
    function parse()
    {
        for ($i = $this->startDay; $i <= $this->endDay; ++$i) {
            $this->days[$i]->parse();
        }

        $this->totalspan = 0;
        $this->span = array();
        for ($i = $this->startDay; $i <= $this->endDay; ++$i) {
            $this->totalspan += $this->days[$i]->_totalspan;
            foreach ($this->_currentCalendars as $cid => $key) {
                if (isset($this->span[$cid])) {
                    $this->span[$cid] += $this->days[$i]->_span[$cid];
                } else {
                    $this->span[$cid] = $this->days[$i]->_span[$cid];
                }
            }
        }

        $this->last = 0;
        $this->first = $this->_slotsPerDay;
        for ($i = $this->startDay; $i <= $this->endDay; ++$i) {
            if ($this->days[$i]->last > $this->last) {
                $this->last = $this->days[$i]->last;
            }
            if ($this->days[$i]->first < $this->first) {
                $this->first = $this->days[$i]->first;
            }
        }
    }

    function getWeek($offset = 0)
    {
        $week = $this->week + $offset;
        $year = $this->year;
        $weeksInYear = Horde_Date::weeksInYear($year);
        if ($week < 1) {
            --$year;
            // We need last year's number of weeks.
            $week += Horde_Date::weeksInYear($year);
        } elseif ($week > $weeksInYear) {
            $week -= $weeksInYear;
            ++$year;
        }

        return array('week' => $week,
                     'year' => $year);
    }

    function link($offset = 0, $full = false)
    {
        $pair = $this->getWeek($offset);
        return Horde::applicationUrl(Util::addParameter($this->_controller,
                                                        array('week' => $pair['week'],
                                                              'year' => $pair['year'])),
                                     $full);
    }

    function getName()
    {
        return 'Week';
    }

}
