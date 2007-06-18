<?php
/**
 * The Kronolith_WeekView:: class provides an API for viewing weeks.
 *
 * $Horde: kronolith/lib/WeekView.php,v 1.78 2004/05/27 17:51:54 chuck Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>, Jan Schneider <jan@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Kronolith 0.1
 * @package Kronolith
 */
class Kronolith_WeekView {

    var $parsed = false;
    var $days = array();
    var $week = null;
    var $year = null;
    var $startDay = 0;
    var $endDay = 6;
    var $_sidebyside = false;
    var $_currentCalendars = array();

    function Kronolith_WeekView($week = null, $year = null, $startDay = null, $endDay = null)
    {
        if (empty($year)) {
            $year = date('Y');
        }
        if (empty($week)) {
            $week = Kronolith::weekOfYear(null, null, $year);
            if ($week == 1 && date('n') == 12) {
                $year++;
            }
        } else {
            if ($week < 1) {
                $year--;
                $week += Kronolith::weeksInYear($year);
            } elseif ($week > Kronolith::weeksInYear($year)) {
                $week -= Kronolith::weeksInYear($year);
                $year++;
            }
        }

        $this->year = $year;
        $this->week = $week;

        if (isset($startDay)) {
            $this->startDay = $startDay;
        }
        if (isset($endDay)) {
            $this->endDay = $endDay;
        }

        $firstDayOfWeek = Kronolith::firstDayOfWeek($week, $year);
        $firstDay = $firstDayOfWeek + Date_Calc::dateToDays(1, 1, $year) - 1;

        require_once KRONOLITH_BASE . '/lib/DayView.php';
        for ($i = $this->startDay; $i <= $this->endDay; $i++) {
            list($day, $month, $year) = explode('/', Date_Calc::daysToDate($firstDay + $i, '%d/%m/%Y'));
            $this->days[$i] = &new Kronolith_DayView($month, $day, $year, null, array());
        }

        list($sday, $smonth, $syear) = explode('/', Date_Calc::daysToDate($firstDay + $this->startDay, '%d/%m/%Y'));
        list($eday, $emonth, $eyear) = explode('/', Date_Calc::daysToDate($firstDay + $this->endDay, '%d/%m/%Y'));
        $startDate = Kronolith::timeStampToObject(mktime(0, 0, 0, $smonth, $sday, $syear));
        $endDate = Kronolith::timeStampToObject(mktime(23, 59, 59, $emonth, $eday, $eyear));
        $allevents = Kronolith::listEvents($startDate, $endDate, $GLOBALS['display_calendars']);
        for ($i = $this->startDay; $i <= $this->endDay; $i++) {
            $this->days[$i]->setEvents(isset($allevents[$this->days[$i]->getStamp()]) ?
                                       $allevents[$this->days[$i]->getStamp()] :
                                       array());
        }
        $this->_sidebyside = $this->days[$this->startDay]->_sidebyside;
        $this->_currentCalendars = $this->days[$this->startDay]->_currentCalendars;
    }

    function html($template_path = KRONOLITH_TEMPLATES)
    {
        global $prefs, $print_view, $cManager;

        $more_timeslots = $prefs->getValue('time_between_days');
        $include_all_events = !$prefs->getValue('show_shared_side_by_side');

        if (!$this->parsed) {
            $this->parse();
        }

        $hours = $this->days[$this->startDay]->hours;
        $cid = 0;
        if ($this->_sidebyside) {
            require $template_path . '/week/head_side_by_side.inc';
        } else {
            require $template_path . '/week/head.inc';
        }

        $event_count = 0;
        for ($j = $this->startDay; $j <= $this->endDay; $j++) {
            foreach ($this->_currentCalendars as $cid => $cal) {
                $event_count = max($event_count, count($this->days[$j]->_all_day_events[$cid]));
                reset($this->days[$j]->_all_day_events[$cid]);
            }
        }

        if ($more_timeslots) {
            $addeventurl = null;
        } else {
            $addeventurl = _("All day");
        }
        $rowspan = ' rowspan="1"';

        $first_row = true;
        $row = '';

        $colors = $cManager->colors();

        for ($j = $this->startDay; $j <= $this->endDay; $j++) {
            $row .= '<td class="hour" align="right">' . ($more_timeslots ? _("All day") : '&nbsp;') . '</td>';
            $row .= '<td colspan="' . $this->days[$j]->_totalspan . '" valign="top" style="padding:0px"><table border="0" width="100%" cellspacing="0" cellpadding="0">';
            if ($this->days[$j]->_all_day_maxrowspan > 0) {
                for ($k = 0; $k < $this->days[$j]->_all_day_maxrowspan; $k++) {
                    $row .= '<tr>';
                    foreach ($this->days[$j]->_currentCalendars as $cid => $cal) {
                        if (count($this->days[$j]->_all_day_events[$cid]) === $k) {
                            $row .= '<td rowspan="' . ($this->days[$j]->_all_day_maxrowspan - $k) . '" width="'. round(99/count($this->days[$j]->_currentCalendars)) . '%">&nbsp;</td>';
                        } elseif (count($this->days[$j]->_all_day_events[$cid]) > $k) {
                            $event = $this->days[$j]->_all_day_events[$cid][$k];
                            $categoryColor = isset($colors[$event->getCategory()]) ? $colors[$event->getCategory()] : '#ccffcc';
                            $row .= '<td class="week-eventbox" style="background-color: ' . $categoryColor . '; ';
                            $row .= 'border-color: ' . Kronolith::borderColor($categoryColor) . '" ';
                            $row .= 'onmouseover="javascript:style.backgroundColor=\'' . Kronolith::highlightColor($categoryColor) . '\'" ';
                            $row .= 'onmouseout="javascript:style.backgroundColor=\'' . $categoryColor . '\'" ';
                            $row .= 'width="' . round(99/count($this->days[$j]->_currentCalendars)) . '%" ';
                            $row .= 'valign="top">';
                            $row .= $event->getLink($this->days[$j]->getStamp());
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

        require $template_path . '/day/all_day.inc';

        $addeventurl = null;
        $rows = array();
        for ($i = 0; $i < 48; $i++) {
            if ($i >= $prefs->getValue('day_hour_end') && $i > $this->last) {
                break;
            }
            if ($i < $this->first && $i < $prefs->getValue('day_hour_start')) {
                continue;
            }

            if ($prefs->getValue('half') && $i % 2 != 0) {
                $time = ':30';
                $hourclass = 'halfhour';
            } else {
                $time = date(($prefs->getValue('twentyFour')) ? 'G' : 'ga', $hours[$i]['timestamp']);
                $hourclass = 'hour';
            }
            $style = ((($prefs->getValue('half')) ? $i : floor($i / 2)) % 2) ? 'item1' : 'item0';

            $row = '';
            for ($j = $this->startDay; $j <= $this->endDay; $j++) {
                // Add spacer between days, or timeslots.
                if ($more_timeslots) {
                    if ($prefs->getValue('half')) {
                        if ($i % 2 == 0) {
                            $row .= '<td align="right" class="hour">' . $time . '</td>';
                        } else {
                            $row .= '<td align="right" class="halfhour">' . $time . '</td>';
                        }
                    } else {
                        if ($i % 2 == 0) {
                            $row .= '<td rowspan="2" align="right" class="hour">' . $time . '</td>';
                        }
                    }
                } else {
                    $row .= '<td width="1%" class="text">&nbsp;</td>';
                }
                foreach ($this->_currentCalendars as $cid => $cal) {
                    $hspan = 0;
                    foreach ($this->days[$j]->_event_matrix[$cid][$i] as $key) {
                        $event = $this->days[$j]->_events[$key];
                        if ($include_all_events || $event->getCalendar() == $cid) {
                            $start = mktime(floor($i/2), ($i % 2) * 30, 0, $this->days[$j]->month, $this->days[$j]->mday, $this->days[$j]->year);

                            // Since we've made sure that this event's
                            // overlap is a factor of the total span,
                            // we get this event's individual span by
                            // dividing the total span by this event's
                            // overlap.
                            $span = $this->days[$j]->_span[$cid] / $event->overlap;
                            $hspan += $span;

                            $categoryColor = isset($colors[$event->getCategory()]) ? $colors[$event->getCategory()] : $colors['_default_'];
                            if ($event->startTimestamp >= $start && $event->startTimestamp < $start + 60 * 30 || $start == $this->days[$j]->getStamp()) {
                                $row .= '<td class="week-eventbox" style="background-color: ' . $categoryColor . '; ';
                                $row .= 'border-color: ' . Kronolith::borderColor($categoryColor) . '" ';
                                $row .= 'onmouseover="javascript:style.backgroundColor=\'' . Kronolith::highlightColor($categoryColor) . '\'" ';
                                $row .= 'onmouseout="javascript:style.backgroundColor=\'' . $categoryColor . '\'" ';
                                $row .= 'valign="top" ';
                                $row .= 'width="' . floor(((90 / count($this->days)) / count($this->_currentCalendars)) * ($span / $this->days[$j]->_span[$cid])) . '%"';
                                $row .= 'colspan="' . $span . '" rowspan="' . $event->rowspan . '">';
                                $row .= $event->getLink($this->days[$j]->getStamp());
                                $row .= '&nbsp;</td>';
                            }
                        }
                    }
                    $diff = $this->days[$j]->_span[$cid] - $hspan;

                    if ($diff > 0) {
                        for ($t = 0; $t < $diff; $t++) {
                            $row .= '<td colspan="1" class="' . $style . '">&nbsp;</td>';
                        }
                    }
                }
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
     * Parse all events for all of the days that we're handling; then
     * run through the results to get the total horizontal span for
     * the week, and the latest event of the week.
     *
     * @access public
     *
     * @return void
     */
    function parse()
    {
        for ($i = $this->startDay; $i <= $this->endDay; $i++) {
            $this->days[$i]->parse();
        }

        $this->totalspan = 0;
        $this->span = array();
        for ($i = $this->startDay; $i <= $this->endDay; $i++) {
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
        $this->first = 48;
        for ($i = $this->startDay; $i <= $this->endDay; $i++) {
            if ($this->days[$i]->last > $this->last) {
                $this->last = $this->days[$i]->last;
            }
            if ($this->days[$i]->first < $this->first) {
                $this->first = $this->days[$i]->first;
            }
        }
    }

    function link($offset = 0)
    {
        $scriptName = basename($_SERVER['PHP_SELF']);
        $week = $this->week + $offset;
        $year = $this->year;
        if ($week < 1) {
            $year--;
            $week += Kronolith::weeksInYear($year);
        } elseif ($week > Kronolith::weeksInYear($year)) {
            $week -= Kronolith::weeksInYear($year);
            $year++;
        }
        $url = Util::addParameter($scriptName, 'week', $week);
        $url = Util::addParameter($url, 'year', $year);
        return Horde::applicationUrl($url);
    }

}
