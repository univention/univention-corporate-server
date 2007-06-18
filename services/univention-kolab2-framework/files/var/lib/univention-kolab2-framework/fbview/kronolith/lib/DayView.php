<?php

require_once KRONOLITH_BASE . '/lib/Day.php';

/**
 * The Kronolith_DayView:: class provides an API for viewing days.
 *
 * $Horde: kronolith/lib/DayView.php,v 1.129 2004/05/27 17:51:54 chuck Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Kronolith 0.1
 * @package Kronolith
 */
class Kronolith_DayView extends Kronolith_Day {

    var $_events = array();
    var $_all_day_events = array();
    var $_event_matrix = array();
    var $_parsed = false;
    var $_span = array();
    var $_totalspan = 0;
    var $_sidebyside = false;
    var $_currentCalendars = array();

    function Kronolith_DayView($month = null, $day = null, $year = null,
                               $timestamp = null, $events = null)
    {
        parent::Kronolith_Day($month, $day, $year, $timestamp);

        global $prefs;
        $this->_sidebyside = $prefs->getValue('show_shared_side_by_side');
        if ($this->_sidebyside) {
            $allCalendars = Kronolith::listCalendars();
            foreach ($GLOBALS['display_calendars'] as $cid) {
                 $this->_currentCalendars[$cid] = &$allCalendars[$cid];
                 $this->_all_day_events[$cid] = array();
            }
        } else {
            $this->_currentCalendars = array(0);
        }

        if (is_null($events)) {
            $events = Kronolith::listEvents($this,
                                            Kronolith::timestampToObject(mktime(23, 59, 59, $this->month, $this->mday, $this->year)),
                                            $GLOBALS['display_calendars']);
            $this->_events = array_pop($events);
        } else {
            $this->_events = $events;
        }
        if (!is_array($this->_events)) {
            $this->_events = array();
        }
    }

    function setEvents($events)
    {
        $this->_events = $events;
    }

    function html($template_path = KRONOLITH_TEMPLATES)
    {
        global $prefs, $print_view, $cManager;

        if (!$this->_parsed) {
            $this->parse();
        }

        $hours = $this->hours;
        $started = false;
        $first_row = true;

        $colors = $cManager->colors();

        if ($this->_sidebyside) {
            require $template_path . '/day/head_side_by_side.inc';
        } else {
            require $template_path . '/day/head.inc';
        }
        $row = '';
        if (Kronolith::getDefaultCalendar(PERMS_EDIT)) {
            $addeventurl = Horde::applicationUrl('addevent.php');
            $addeventurl = Util::addParameter($addeventurl, 'timestamp', $hours[0]['timestamp']);
            $addeventurl = Util::addParameter($addeventurl, 'allday', '1');
            $addeventurl = Util::addParameter($addeventurl, 'url', Horde::selfUrl(true));
            $addeventurl = Horde::link($addeventurl, _("Create a New Event"), 'hour') . _("All day") . '</a>';
        } else {
            $addeventurl = '<span class="hour">' . _("All day") . '</span>';
        }

        /* The all day events are not listed in different columns, but
         * in different rows.  In side by side view we do not spread
         * an event over multiple rows if there are different numbers
         * of all day events for different calendars.  We just put one
         * event in a single row with no rowspan.  We put in a rowspan
         * in the row after the last event to fill all remaining
         * rows. */
        $rowspan = ($this->_all_day_maxrowspan) ? ' rowspan="' . $this->_all_day_maxrowspan . '" ' : '';
        for ($k = 0; $k < $this->_all_day_maxrowspan; $k++) {
            $row = '';
            foreach ($this->_currentCalendars as $cid => $cal) {
                if (count($this->_all_day_events[$cid]) === $k) {
                    // There are no events or all events for this
                    // calendar have already been printed.
                    $row .= '<td class="allday" width="1%" rowspan="' . ($this->_all_day_maxrowspan - $k) . '" colspan="'.  $this->_span[$cid] . '">&nbsp;</td>';
                } elseif (count($this->_all_day_events[$cid]) > $k) {
                    // We have not printed every all day event
                    // yet. Put one into this row.
                    $event = $this->_all_day_events[$cid][$k];
                    $categoryColor = isset($colors[$event->getCategory()]) ? $colors[$event->getCategory()] : '#ccffcc';
                    $row .= '<td class="day-eventbox" style="background-color: ' . $categoryColor . '; ';
                    $row .= 'border-color:' . Kronolith::borderColor($categoryColor) . '" ';
                    $row .= 'onmouseover="javascript:style.backgroundColor=\'' . Kronolith::highlightColor($categoryColor) . '\'" ';
                    $row .= 'onmouseout="javascript:style.backgroundColor=\'' . $categoryColor . '\'" ';
                    $row .= 'valign="top" colspan="' . $this->_span[$cid] . '">';
                    $row .= $event->getLink($this->getStamp());
                    $row .= '</td>';
                }
            }
            require $template_path . '/day/all_day.inc';
            $first_row = false;
        }

        if ($first_row) {
            $row .= '<td colspan="' . $this->_totalspan. '">&nbsp;</td>';
            require $template_path . '/day/all_day.inc';
        }

        $first_row = true;
        for ($i = 0; $i < 48; $i++) {
            if ($i >= $prefs->getValue('day_hour_end') && $i > $this->last) {
                break;
            }
            if ($i < $this->first && $i < $prefs->getValue('day_hour_start')) {
                continue;
            }

            $row = '';
            $hspan = 0;
            if ($prefs->getValue('half') && $i % 2 != 0) {
                $time = ':30';
                $hourclass = 'halfhour';
            } else {
                $time = date(($prefs->getValue('twentyFour')) ? 'G' : 'ga', $hours[$i]['timestamp']);
                $hourclass = 'hour';
            }
            $style = ((($prefs->getValue('half')) ? $i : floor($i / 2)) % 2) ? 'item1' : 'item0';

            foreach ($this->_currentCalendars as $cid => $cal) {
                foreach ($this->_event_matrix[$cid][$i] as $key) {
                    $event = $this->_events[$key];
                    $start = mktime(floor($i / 2), ($i % 2) * 30, 0, $this->month, $this->mday, $this->year);

                    // Since we've made sure that this event's overlap
                    // is a factor of the total span, we get this
                    // event's individual span by dividing the total
                    // span by this event's overlap.
                    $span = $this->_span[$cid] / $event->overlap;
                    $hspan += $span;

                    $categoryColor = isset($colors[$event->getCategory()]) ? $colors[$event->getCategory()] : $colors['_default_'];
                    if ($event->startTimestamp >= $start && $event->startTimestamp < $start + 60 * 30 || $start == $this->getStamp()) {
                        $row .= '<td class="day-eventbox" style="background-color: ' . $categoryColor . '; ';
                        $row .= 'border-color:' . Kronolith::borderColor($categoryColor) . '" ';
                        $row .= 'onmouseover="javascript:style.backgroundColor=\'' . Kronolith::highlightColor($categoryColor) . '\'" ';
                        $row .= 'onmouseout="javascript:style.backgroundColor=\'' . $categoryColor . '\'" ';
                        $row .= 'width="' . round((90 / count($this->_currentCalendars)) * ($span / $this->_span[$cid]))  . '%" ';
                        $row .= 'valign="top" colspan="' . $span . '" rowspan="' . $event->rowspan . '">';
                        $row .= $event->getLink($this->getStamp());
                        $row .= '&nbsp;</td>';
                    }
                }

                $diff = $this->_span[$cid] - $hspan;
                if ($diff > 0) {
                    for ($t = 0; $t < $diff; $t ++) {
                        $row .= '<td colspan="1" class="' . $style . '">&nbsp;</td>';
                    }
                }
            }

            if (Kronolith::getDefaultCalendar(PERMS_EDIT)) {
                $addeventurl = Horde::applicationUrl('addevent.php');
                $addeventurl = Util::addParameter($addeventurl, 'timestamp', $hours[$i]['timestamp']);
                $addeventurl = Util::addParameter($addeventurl, 'url', Horde::selfUrl(true));
                $addeventurl = Horde::link($addeventurl, _("Create a New Event"), $hourclass);
            } else {
                $addeventurl = '';
            }

            if ($prefs->getValue('half')) {
                $rowspan = false;
                require $template_path . '/day/row.inc';
            } else {
                $rowspan = true;
                if ($i % 2) {
                    require $template_path . '/day/row_half.inc';
                } else {
                    require $template_path . '/day/row.inc';
                }
            }

            $first_row = false;
        }
        require $template_path . '/day/foot.inc';
    }

    /**
     * This function runs through the events and tries to figure out
     * what should be on each line of the output table. This is a
     * little tricky.
     *
     * @access public
     */
    function parse()
    {
        global $prefs;

        $tmp = array();
        $this->_all_day_maxrowspan = 0;

        // Separate out all day events and do some initialization/prep
        // for parsing.
        foreach ($this->_currentCalendars as $cid => $cal) {
            $this->_all_day_events[$cid] = array();
            $this->_all_day_rowspan[$cid] = 0;
        }

        foreach ($this->_events as $key => $event) {
            // If we have side_by_side we only want to include the
            // event in the proper calendar.
            if ($this->_sidebyside) {
                $cid = $event->getCalendar();
            } else {
                $cid = 0;
            }

            // All day events are easy; store them seperately.
            if ($event->isAllDay()) {
                $this->_all_day_events[$cid][] = $event;
                $this->_all_day_rowspan[$cid]++;
                $this->_all_day_maxrowspan = max($this->_all_day_maxrowspan, $this->_all_day_rowspan[$cid]);
            } else {
                // Initialize the number of events that this event
                // overlaps with.
                $event->overlap = 0;

                // Initialize this event's vertical span.
                $event->rowspan = 0;

                // Make sure that we're using the current date for
                // recurring events.
                if (!$event->hasRecurType(KRONOLITH_RECUR_NONE)) {
                    $event->start->mday = $this->mday;
                    $event->start->month = $this->month;
                    $event->start->year = $this->year;
                    $event->setStartTimestamp(Kronolith::objectToTimestamp($event->start));
                    $event->setEndTimestamp($event->startTimestamp + $event->durMin * 60);
                }
                $tmp[] = $event;
            }
        }
        $this->_events = $tmp;

        // Initialize the set of different rowspans needed.
        $spans = array(1 => true);

        // Track the last half-hour in which we have an event.
        $this->last = 0;
        $this->first = 48;

        // Run through every half-hour slot, adding in entries for
        // every event that we have here.
        for ($i = 0; $i < 48; $i++) {
            // Initialize this slot in the event matrix.
            foreach ($this->_currentCalendars as $cid => $cal) {
                $this->_event_matrix[$cid][$i] = array();
            }

            // Calculate the start and end timestamps for this slot.
            $start = mktime(floor($i / 2), ($i % 2) * 30, 0, $this->month, $this->mday, $this->year);
            $end = $start + (60 * 30);

            // Search through our events.
            foreach ($this->_events as $key => $event) {
                // If we have side_by_side we only want to include the
                // event in the proper calendar.
                if ($this->_sidebyside) {
                    $cid = $event->getCalendar();
                } else {
                    $cid = 0;
                }

                // If the event falls anywhere inside this slot, add
                // it, make sure other events know that they overlap
                // it, and increment the event's vertical span.
                if (($event->endTimestamp > $start && $event->startTimestamp < $end ) ||
                    ($event->endTimestamp == $event->startTimestamp && $event->startTimestamp == $start)) {

                    // Make sure we keep the latest hour than an event
                    // reaches up-to-date.
                    if ($i > $this->last) {
                        $this->last = $i;
                    }

                    // Make sure we keep the first hour than an event
                    // reaches up-to-date.
                    if ($i < $this->first) {
                        $this->first = $i;
                    }

                    // Add this event to the events which are in this
                    // row.
                    $this->_event_matrix[$cid][$i][] = $key;

                    // Increment the event's vertical span.
                    $this->_events[$key]->rowspan++;
                }
            }

            foreach ($this->_currentCalendars as $cid => $cal) {
                // Update the number of events that events in this row
                // overlap with.
                foreach ($this->_event_matrix[$cid][$i] as $ev) {
                    $this->_events[$ev]->overlap = max($this->_events[$ev]->overlap,
                                                    count($this->_event_matrix[$cid][$i]));
                }

                // Update the set of rowspans to include the value for
                // this row.
                $spans[$cid][count($this->_event_matrix[$cid][$i])] = true;
            }
        }

        foreach ($this->_currentCalendars as $cid => $cal) {
            // Sort every row by event duration, so that longer events are
            // farther to the left.
            for ($i = 0; $i <= $this->last; $i++) {
                if (count($this->_event_matrix[$cid][$i])) {
                    usort($this->_event_matrix[$cid][$i], array($this, '_sortByDuration'));
                }
            }

            // Now that we have the number of events in each row, we
            // can calculate the total span needed.
            $span[$cid] = 1;

            // Turn keys into array values.
            $spans[$cid] = array_keys($spans[$cid]);

            // Start with the biggest one first.
            rsort($spans[$cid]);
            foreach ($spans[$cid] as $s) {
                // If the number of events in this row doesn't divide
                // cleanly into the current total span, we need to
                // multiply the total span by the number of events in
                // this row.
                if ($span[$cid] % $s != 0) {
                    $span[$cid] *= $s;
                }
            }
            $this->_totalspan += $span[$cid];
        }
        // Set the final span.
        $this->_span = $span;

        // We're now parsed and ready to go.
        $this->_parsed = true;
    }

    function link($offset = 0)
    {
        $url = Horde::applicationUrl('day.php');
        $url = Util::addParameter($url, 'month', $this->getTime('%m', $offset));
        $url = Util::addParameter($url, 'mday', ltrim($this->getTime('%d', $offset)));
        $url = Util::addParameter($url, 'year', $this->getTime('%Y', $offset));

        return $url;
    }

    function _sortByDuration($evA, $evB)
    {
        $durA = $this->_events[$evA]->rowspan;
        $durB = $this->_events[$evB]->rowspan;

        if ($durA > $durB) {
            return -1;
        } elseif ($durA == $durB) {
            return 0;
        } else {
            return 1;
        }
    }

}
