<?php

require_once KRONOLITH_BASE . '/lib/Day.php';

/**
 * The Kronolith_View_Day:: class provides an API for viewing days.
 *
 * $Horde: kronolith/lib/Views/Day.php,v 1.29.2.3 2008-03-06 20:50:53 chuck Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Kronolith 0.1
 * @package Kronolith
 */
class Kronolith_View_Day extends Kronolith_Day {

    var $_events = array();
    var $_all_day_events = array();
    var $_event_matrix = array();
    var $_parsed = false;
    var $_span = array();
    var $_totalspan = 0;
    var $_sidebyside = false;
    var $_currentCalendars = array();

    function Kronolith_View_Day($month = null, $day = null, $year = null, $events = null)
    {
        parent::Kronolith_Day($month, $day, $year);

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

        if ($events === null) {
            $events = Kronolith::listEvents($this,
                                            new Horde_Date(array('year' => $this->year, 'month' => $this->month, 'mday' => $this->mday,
                                                                 'hour' => 23, 'min' => 59, 'sec' => 59)),
                                            $GLOBALS['display_calendars']);
            if (is_a($events, 'PEAR_Error')) {
                $this->_events = $events;
            } else {
                $this->_events = array_shift($events);
            }
        } else {
            $this->_events = $events;
        }

        if (is_a($this->_events, 'PEAR_Error')) {
            $GLOBALS['notification']->push($this->_events, 'horde.error');
            $this->_events = array();
        }
        if (!is_array($this->_events)) {
            $this->_events = array();
        }
    }

    function setEvents($events)
    {
        $this->_events = $events;
    }

    function html()
    {
        global $prefs;

        if (!$this->_parsed) {
            $this->parse();
        }

        $started = false;
        $first_row = true;
        $addLinks = Kronolith::getDefaultCalendar(PERMS_EDIT) &&
            (!empty($GLOBALS['conf']['hooks']['permsdenied']) ||
             Kronolith::hasPermission('max_events') === true ||
             Kronolith::hasPermission('max_events') > Kronolith::countEvents());
        $showLocation = Kronolith::viewShowLocation();
        $showTime = Kronolith::viewShowTime();

        require KRONOLITH_TEMPLATES . '/day/head.inc';
        if ($this->_sidebyside) {
            require KRONOLITH_TEMPLATES . '/day/head_side_by_side.inc';
        }
        echo '<tbody>';

        $eventCategories = array();

        if ($addLinks) {
            $newEventUrl = Util::addParameter('new.php', array('timestamp' => $this->slots[0]['timestamp'],
                                                               'allday' => 1,
                                                               'url' => $this->link(0, true)));
            $newEventUrl = Horde::link(Horde::applicationUrl($newEventUrl), _("Create a New Event"), 'hour') . _("All day") .
                Horde::img('new_small.png', '+', array('class' => 'iconAdd')) . '</a>';
        } else {
            $newEventUrl = '<span class="hour">' . _("All day") . '</span>';
        }

        /* The all day events are not listed in different columns, but in
         * different rows.  In side by side view we do not spread an event
         * over multiple rows if there are different numbers of all day events
         * for different calendars.  We just put one event in a single row
         * with no rowspan.  We put in a rowspan in the row after the last
         * event to fill all remaining rows. */
        $row = '';
        $rowspan = ($this->_all_day_maxrowspan) ? ' rowspan="' . $this->_all_day_maxrowspan . '"' : '';
        for ($k = 0; $k < $this->_all_day_maxrowspan; ++$k) {
            $row = '';
            foreach ($this->_currentCalendars as $cid => $cal) {
                if (count($this->_all_day_events[$cid]) === $k) {
                    // There are no events or all events for this calendar
                    // have already been printed.
                    $row .= '<td class="allday" width="1%" rowspan="' . ($this->_all_day_maxrowspan - $k) . '" colspan="'.  $this->_span[$cid] . '">&nbsp;</td>';
                } elseif (count($this->_all_day_events[$cid]) > $k) {
                    // We have not printed every all day event yet. Put one
                    // into this row.
                    $event = $this->_all_day_events[$cid][$k];
                    if ($event->hasPermission(PERMS_READ)) {
                        $eventCategories[$event->getCategory()] = true;
                    }

                    $row .= '<td class="day-eventbox category' . md5($event->getCategory()) . '" '
                        . 'width="' . round(90 / count($this->_currentCalendars))  . '%" '
                        . 'valign="top" colspan="' . $this->_span[$cid] . '">'
                        . $event->getLink($this->getStamp(), true, $this->link(0, true));
                    if ($showLocation) {
                        $row .= '<div class="event-location">' . htmlspecialchars($event->getLocation()) . '</div>';
                    }
                    $row .= '</td>';
                }
            }
            require KRONOLITH_TEMPLATES . '/day/all_day.inc';
            $first_row = false;
        }

        if ($first_row) {
            $row .= '<td colspan="' . $this->_totalspan . '" width="100%">&nbsp;</td>';
            require KRONOLITH_TEMPLATES . '/day/all_day.inc';
        }

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

            $row = '';
            if (($m = $i % $this->_slotsPerHour) != 0) {
                $time = ':' . $m * $this->_slotLength;
                $hourclass = 'halfhour';
            } else {
                $time = date($twenty_four ? 'G' : 'ga', $this->slots[$i]['timestamp']);
                $hourclass = 'hour';
            }

            if (!count($this->_currentCalendars)) {
                $row .= '<td>&nbsp;</td>';
            }

            foreach ($this->_currentCalendars as $cid => $cal) {
                $hspan = 0;
                foreach ($this->_event_matrix[$cid][$i] as $key) {
                    $event = &$this->_events[$key];

                    // Since we've made sure that this event's overlap is a
                    // factor of the total span, we get this event's
                    // individual span by dividing the total span by this
                    // event's overlap.
                    $span = $this->_span[$cid] / $event->overlap;

                    // Store the indent we're starting this event at
                    // for future use.
                    if (!isset($event->indent)) {
                        $event->indent = $hspan;
                    }

                    // If the first node that we would cover is
                    // already covered, we can assume that table
                    // rendering will take care of pushing the event
                    // over. However, if the first node _isn't_
                    // covered but any others that we would cover
                    // _are_, we only cover the available nodes.
                    if (!isset($covered[$i][$event->indent])) {
                        $collision = false;
                        $available = 0;
                        for ($y = $event->indent; $y < ($span + $event->indent); ++$y) {
                            if (isset($covered[$i][$y])) {
                                $collision = true;
                                break;
                            }
                            $available++;
                        }

                        if ($collision) {
                            $span = $available;
                        }
                    }

                    $hspan += $span;

                    $start = mktime(floor($i / $this->_slotsPerHour), ($i % $this->_slotsPerHour) * $this->_slotLength, 0,
                                    $this->month, $this->mday, $this->year);
                    if (((!$day_hour_force || $i >= $day_hour_start) &&
                         $event->start->timestamp() >= $start &&
                         $event->start->timestamp() < $start + 60 * $this->_slotLength ||
                         $start == $this->getStamp()) ||
                        ($day_hour_force &&
                         $i == $day_hour_start &&
                         $event->start->timestamp() < $start)) {
                        if ($event->hasPermission(PERMS_READ)) {
                            $eventCategories[$event->getCategory()] = true;
                        }

                        // Store the nodes that we're covering for
                        // this event in the coverage graph.
                        for ($x = $i; $x < ($i + $event->rowspan); ++$x) {
                            for ($y = $event->indent; $y < $hspan; ++$y) {
                                $covered[$x][$y] = true;
                            }
                        }

                        $row .= '<td class="day-eventbox category' . md5($event->getCategory()) . '" '
                            . 'width="' . round((90 / count($this->_currentCalendars)) * ($span / $this->_span[$cid]))  . '%" '
                            . 'valign="top" colspan="' . $span . '" rowspan="' . $event->rowspan . '">'
                            . $event->getLink($this->getStamp(), true, $this->link(0, true));
                        if ($showTime) {
                            $row .= '<div class="event-time">' . htmlspecialchars($event->getTimeRange()) . '</div>';
                        }
                        if ($showLocation) {
                            $row .= '<div class="event-location">' . htmlspecialchars($event->getLocation()) . '</div>';
                        }
                        $row .= '</td>';
                    }
                }

                $diff = $this->_span[$cid] - $hspan;
                if ($diff > 0) {
                    $row .= str_repeat('<td>&nbsp;</td>', $diff);
                }
            }

            if ($addLinks) {
                $newEventUrl = Util::addParameter('new.php',
                                                  array('timestamp' => $this->slots[$i]['timestamp'],
                                                        'url' => $this->link(0, true)));
                $newEventUrl = Horde::link(Horde::applicationUrl($newEventUrl), _("Create a New Event"), $hourclass) .
                    $time . Horde::img('new_small.png', '+', array('class' => 'iconAdd')) . '</a>';
            } else {
                $newEventUrl = '<span class="' . $hourclass . '">' . $time . '</span>';
            }

            $rows[] = array('row' => $row, 'slot' => $newEventUrl);
        }

        require_once 'Horde/Template.php';
        $template = new Horde_Template();
        $template->set('row_height', round(20 / $this->_slotsPerHour));
        $template->set('rows', $rows);
        $template->set('show_slots', true, true);
        echo $template->fetch(KRONOLITH_TEMPLATES . '/day/rows.html')
            . '</tbody></table>';

        require KRONOLITH_TEMPLATES . '/category_legend.inc';
    }

    /**
     * This function runs through the events and tries to figure out
     * what should be on each line of the output table. This is a
     * little tricky.
     */
    function parse()
    {
        global $prefs;

        $tmp = array();
        $this->_all_day_maxrowspan = 0;
        $day_hour_force = $prefs->getValue('day_hour_force');
        $day_hour_start = $prefs->getValue('day_hour_start') / 2 * $this->_slotsPerHour;
        $day_hour_end = $prefs->getValue('day_hour_end') / 2 * $this->_slotsPerHour;

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
                $this->_all_day_events[$cid][] = &Util::cloneObject($event);
                ++$this->_all_day_rowspan[$cid];
                $this->_all_day_maxrowspan = max($this->_all_day_maxrowspan, $this->_all_day_rowspan[$cid]);
            } else {
                // Initialize the number of events that this event
                // overlaps with.
                $event->overlap = 0;

                // Initialize this event's vertical span.
                $event->rowspan = 0;

                $tmp[] = &Util::cloneObject($event);
            }
        }
        $this->_events = $tmp;

        // Initialize the set of different rowspans needed.
        $spans = array(1 => true);

        // Track the first and last slots in which we have an event
        // (they each start at the other end of the day and move
        // towards/past each other as we find events).
        $this->first = $this->_slotsPerDay;
        $this->last = 0;

        // Run through every slot, adding in entries for every event
        // that we have here.
        for ($i = 0; $i < $this->_slotsPerDay; ++$i) {
            // Initialize this slot in the event matrix.
            foreach ($this->_currentCalendars as $cid => $cal) {
                $this->_event_matrix[$cid][$i] = array();
            }

            // Calculate the start and end timestamps for this slot.
            $start = mktime(floor($i / $this->_slotsPerHour), ($i % $this->_slotsPerHour) * $this->_slotLength, 0,
                            $this->month, $this->mday, $this->year);
            $end = $start + (60 * $this->_slotLength);

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
                if (($event->end->timestamp() > $start && $event->start->timestamp() < $end) ||
                    ($event->end->timestamp() == $event->start->timestamp() && $event->start->timestamp() == $start)) {

                    // Make sure we keep the latest hour that an event
                    // reaches up-to-date.
                    if ($i > $this->last &&
                        (!$day_hour_force || $i <= $day_hour_end)) {
                        $this->last = $i;
                    }

                    // Make sure we keep the first hour that an event
                    // reaches up-to-date.
                    if ($i < $this->first &&
                        (!$day_hour_force || $i >= $day_hour_start)) {
                        $this->first = $i;
                    }

                    if (!$day_hour_force ||
                        ($i >= $day_hour_start && $i <= $day_hour_end)) {
                        // Add this event to the events which are in this row.
                        $this->_event_matrix[$cid][$i][] = $key;

                        // Increment the event's vertical span.
                        ++$this->_events[$key]->rowspan;
                    }
                }
            }

            foreach (array_keys($this->_currentCalendars) as $cid) {
                // Update the number of events that events in this row
                // overlap with.
                $max = 0;
                $count = count($this->_event_matrix[$cid][$i]);
                foreach ($this->_event_matrix[$cid][$i] as $ev) {
                    $this->_events[$ev]->overlap = max($this->_events[$ev]->overlap, $count);
                    $max = max($max, $this->_events[$ev]->overlap);
                }

                // Update the set of rowspans to include the value for
                // this row.
                $spans[$cid][$max] = true;
            }
        }

        foreach (array_keys($this->_currentCalendars) as $cid) {
            // Sort every row by start time so that events always show
            // up here in the same order.
            for ($i = $this->first; $i <= $this->last; ++$i) {
                if (count($this->_event_matrix[$cid][$i])) {
                    usort($this->_event_matrix[$cid][$i], array($this, '_sortByStart'));
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
                if ($s != 0 && $span[$cid] % $s != 0) {
                    $span[$cid] *= $s;
                }
            }
            $this->_totalspan += $span[$cid];
        }
        // Set the final span.
        if (isset($span)) {
            $this->_span = $span;
        } else {
            $this->_totalspan = 1;
        }

        // We're now parsed and ready to go.
        $this->_parsed = true;
    }

    function link($offset = 0, $full = false)
    {
        return Horde::applicationUrl(
            Util::addParameter('day.php',
                               array('month' => $this->getTime('%m', $offset),
                                     'mday' => ltrim($this->getTime('%d', $offset)),
                                     'year' => $this->getTime('%Y', $offset))),
            $full);
    }

    function getName()
    {
        return 'Day';
    }

    function _sortByStart($evA, $evB)
    {
        $sA = $this->_events[$evA]->start;
        $sB = $this->_events[$evB]->start;

        return $sB->compareTime($sA);
    }

}
