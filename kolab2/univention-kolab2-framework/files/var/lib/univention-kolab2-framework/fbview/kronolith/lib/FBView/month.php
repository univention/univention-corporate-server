<?php
/**
 * This class represent a month fbview of multiple free busy information. It is basically
 * a ripoff of the week view
 *
 * Copyright 2004 Klaraelvdalens Datakonsult AB (Steffen Hansen <steffen@klaralvdalens-datakonsult.se>)
 * Copyright 2003-2004 Mike Cochrane <mike@graftonhall.co.nz>
 *
 * See the enclosed file COPYING for license information.
 *
 * $Horde: kronolith/lib/FBView/week.php,v 1.6 2004/05/25 08:34:22 stuart Exp $
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @package Kronolith
 */
class Kronolith_FreeBusy_View_month extends Kronolith_FreeBusy_View {

    var $_startStamp;
    var $_endStamp;

    function render($day = null)
    {
        global $prefs;

        require_once 'Date/Calc.php';

        if (is_null($day)) {
            list($startDate['year'], $startDate['month'], $startDate['mday']) = explode('-', Date_Calc::beginOfMonth(null, null, "%Y-%m-%d"));
            $day = mktime(0, 0, 1, $startDate['month'], $startDate['mday'], $startDate['year']);
        } else {
            list($startDate['year'], $startDate['month'], $startDate['mday']) = explode('-', Date_Calc::beginOfMonth(date('n', $day), date('Y', $day), "%Y-%m-%d"));
            $day = mktime(0, 0, 1, $startDate['month'], $startDate['mday'], $startDate['year']);
        }
	list($endDate['year'], $endDate['month'], $endDate['mday']) = explode('-', Date_Calc::beginOfNextMonth(date('j', $day), date('n', $day), date('Y', $day), "%Y-%m-%d"));
	$endday = mktime( 23,59,59,$endDate['month'], $endDate['mday'], $endDate['year'])-24*60*60;
        $this->_startStamp = mktime(0, 0, 1, date('n', $day), date('j', $day), date('Y', $day));
        $this->_endStamp   = mktime(23, 59, 59, date('n', $endday), date('j', $endday), date('Y', $endday));

	$prevMonth = mktime(0, 0, 0, date('n', $day), date('j', $day), date('Y', $day))-25*60*60;
	$nextMonth = mktime(0, 0, 0, date('n', $endday), date('j', $endday), date('Y', $endday))+25*60*60;

        require_once 'Horde/iCalendar.php';
        $vCal = &new Horde_iCalendar();
        $required = &Horde_iCalendar::newComponent('vfreebusy', $vCal);
        foreach ($this->_requiredMembers as $member) {
            $required->merge($member, false);
        }
        $required->simplify();

        $optional = &Horde_iCalendar::newComponent('vfreebusy', $vCal);
        foreach ($this->_optionalMembers as $member) {
            $optional->merge($member, false);
        }
        $optional->simplify();

        $optimal = &Horde_iCalendar::newComponent('vfreebusy', $vCal);
        $optimal->merge($required, false);
        $optimal->merge($optional);

        $base_url = Horde::selfUrl();
        $base_url = Util::removeParameter($base_url, 'date');
        $base_url = Util::removeParameter($base_url, 'fbview');
        $base_url = Util::addParameter($base_url, 'fbview', 'month');
        $template = &new Horde_Template();
        $template->set('title', strftime($prefs->getValue('date_format'), $this->_startStamp) . ' - ' .
                                strftime($prefs->getValue('date_format'), $this->_endStamp));

        $template->set('prev_url',
                       Horde::link('', _("Previous Month"), 'menuitem', null, 'return switchTimestamp(' . $prevMonth . ');') .
                       Horde::img('nav/left.gif', '<', null, $GLOBALS['registry']->getParam('graphics', 'horde')) . '</a>');

        $template->set('next_url',
                       Horde::link('', _("Next Month"), 'menuitem', null, 'return switchTimestamp(' . $nextMonth . ');') .
                       Horde::img('nav/right.gif', '>', null, $GLOBALS['registry']->getParam('graphics', 'horde')) . '</a>');

        $html = $template->fetch(KRONOLITH_TEMPLATES . '/fbview/header.tpl');

        $hours_html = '<table width="100%" cellpadding="0" cellspacing="0" style="text-align:center"><tr>';
        $dayWidth = 100 / 30;
        for ($i = 0; $i < 30; $i++) {
            $t = mktime(0, 0, 0, date('n', $day), date('j', $day) + $i, date('Y', $day));
            $day_label = strftime("&nbsp;%d&nbsp;", $t);
            if ($i > 0) {
                $hours_html .= "<td colspan=\"4\" style=\"white-space:nowrap;overflow:hidden;border-left:1px solid black;width:$dayWidth%\">$day_label</td>";
            } else {
                $hours_html .= "<td colspan=\"4\" style=\"white-space:nowrap;overflow:hidden;width:$dayWidth%\">$day_label</td>";
            }
        }

        $hours_html .= '</tr></table>';

        // Required to attend.
        if (count($this->_requiredMembers) > 0) {
            $template = &new Horde_Template();
            $rows = '';
            foreach ($this->_requiredMembers as $member) {
                $blocks = $this->_getBlocks($member, $member->getBusyPeriods(), 'busyblock.tpl', _("Busy"), $member->getExtraParams());
                $template = &new Horde_Template();
                $template->set('blocks', $blocks);
                $template->set('name', $member->getName());
                $rows .= $template->fetch(KRONOLITH_TEMPLATES . '/fbview/row.tpl');
            }

            $template = &new Horde_Template();
            $template->set('title', _("Required to attend"));
            $template->set('rows', $rows);
            $template->set('hours', $hours_html);
            $html .= $template->fetch(KRONOLITH_TEMPLATES . '/fbview/section.tpl');
        }

        // Optional to attend.
        if (count($this->_optionalMembers) > 0) {
            $template = &new Horde_Template();
            $rows = '';
            foreach ($this->_optionalMembers as $member) {
                $blocks = $this->_getBlocks($member, $member->getBusyPeriods(), 'busyblock.tpl', _("Busy"), $member->getExtraParams());
                $template = &new Horde_Template();
                $template->set('blocks', $blocks);
                $template->set('name', $member->getName());
                $rows .= $template->fetch(KRONOLITH_TEMPLATES . '/fbview/row.tpl');
            }

            $template = &new Horde_Template();
            $template->set('title', _("Optional to attend"));
            $template->set('rows', $rows);
            $template->set('hours', $hours_html);
            $html .= $template->fetch(KRONOLITH_TEMPLATES . '/fbview/section.tpl');
        }

        // possible meeting times.
        /*$optimal->setAttribute('ORGANIZER', _("All Attendees"));
        $blocks = $this->_getBlocks($optimal,
                                    $optimal->getFreePeriods($this->_startStamp, $this->_endStamp),
                                    'meetingblock.tpl', _("All Attendees"));

        $template = &new Horde_Template();
        $template->set('name', _("All Attendees"));
        $template->set('blocks', $blocks);
        $rows = $template->fetch(KRONOLITH_TEMPLATES . '/fbview/row.tpl');

        // possible meeting times.
        $required->setAttribute('ORGANIZER', _("Required Attendees"));
        $blocks = $this->_getBlocks($required,
                                    $required->getFreePeriods($this->_startStamp, $this->_endStamp),
                                    'meetingblock.tpl', _("Required Attendees"));

        $template = &new Horde_Template();
        $template->set('name', _("Required Attendees"));
        $template->set('blocks', $blocks);
        $rows .= $template->fetch(KRONOLITH_TEMPLATES . '/fbview/row.tpl');

        $template = &new Horde_Template();
        $template->set('title', _("Possible Meeting Times"));
        $template->set('rows', $rows);
        $template->set('hours', $hours_html);
        $html .= $template->fetch(KRONOLITH_TEMPLATES . '/fbview/section.tpl');*/

        if ($prefs->getValue('show_fb_legend')) {
            $legend_html = Util::bufferOutput('require' , KRONOLITH_TEMPLATES . '/fbview/legend.inc');
        } else {
            $legend_html = '';
        }

        return array($html, $legend_html);

    }

    function _getBlocks($member, $periods, $blockfile, $label, $extra = array())
    {
        $template = &new Horde_Template();

        $count = 0;
        $blocks = '';
        $dayWidth = 100 / 30;
        foreach ($periods as $start => $end) {
            if ($start < $this->_endStamp && $end > $this->_startStamp) {

                $start_day = floor(($start - $this->_startStamp) / (24 * 3600));
                $start_hour = intval(strftime('%H', $start));
                $start_min = intval(strftime('%M', $start));

                $left = $dayWidth * $start_day;
                if ($start_hour >= 9 && $start_hour < 18) {
                    $left += ($start_hour - 9) * ($dayWidth / 9);
                    $left += ($start_min / 60) * ($dayWidth / 9);
                } elseif ($start_hour >= 18) {
                    $left += $dayWidth;
                }
                $left = min(100, max(0, $left));

                $end_day = floor(($end - $this->_startStamp) / (24 * 3600));
                $end_hour = intval(strftime('%H', $end));
                $end_min = intval(strftime('%M', $end));

                $right = $dayWidth * $end_day;
                if ($end_hour >= 9 && $end_hour < 18) {
                    $right += ($end_hour - 9) * ($dayWidth / 9);
                    $right += ($end_min / 60) * ($dayWidth / 9);
                } elseif ($end_hour >= 18) {
                    $right += $dayWidth;
                }
                $right = min(100, $right);

		if( $left == $right ) { 
		  // This is the minimum interval we can display
		  if( $left > 0 ) {
		    $left -= 1;
		  } else {
		    $right += 1;
		  }
		}
                if (($right - $left) != 0) {
                    $template->set('left', $left);
                    $template->set('width', $right - $left);
                    $template->set('top', $count++ * 15);
                    $template->set('label', $label);
                    $template->set('evclick', '');
                    $template->set('label', '');
                    if (isset($extra[$start])) {
                        if (!empty($extra[$start]['X-UID'])) {
                            $link = "javascript:performAction(" . KRONOLITH_ACTIONID_VIEW . ", '" 
			      . addslashes($member->getName() . "#" 
					   . String::convertCharset(base64_decode($extra[$start]['X-UID']), 
								    'UTF-8', NLS::getCharset())) . "')";
                            $template->set('evclick', $link);
                        }
                        if (!empty($extra[$start]['X-SUMMARY'])) {
                            $template->set('label', String::convertCharset(base64_decode($extra[$start]['X-SUMMARY']),
									   'UTF-8', NLS::getCharset()));
                        }
                    }
                    $blocks .= $template->fetch(KRONOLITH_TEMPLATES . '/fbview/' . $blockfile);
                }
            }
        }

        // Indicate if we don't know the free busy info for any periods
        $start = $member->getStart();
        $end   = $member->getEnd();
        if ($start > $this->_startStamp) {
            if ($start >= $this->_endStamp) {
                $right = 100;
            } else {
                $start_day = floor(($start - $this->_startStamp) / (24 * 3600));
                $start_hour = intval(strftime('%H', $start));
                $start_min = intval(strftime('%M', $start));

                $right = $dayWidth * $start_day;
                if ($start_hour >= 9 && $start_hour < 18) {
                    $right += ($start_hour - 9) * ($dayWidth / 9);
                    $right += ($start_min / 60) * ($dayWidth / 9);
                } elseif ($start_hour >= 18) {
                    $right += $dayWidth;
                }
            }
            $left  = 0;

            $template->set('left', $left);
            $template->set('width', min($right - $left, 100));
            $template->set('top', $count++ * 15);

            $blocks .= $template->fetch(KRONOLITH_TEMPLATES . '/fbview/unknownblock.tpl');
        } else if ($end <= $this->_endStamp) {
            if ($end <= $this->_startStamp) {
                $left = 0;
            } else {
                $end_day = floor(($end - $this->_startStamp) / (24 * 3600));
                $end_hour = intval(strftime('%H', $end));
                $end_min = intval(strftime('%M', $end));

                $left = $dayWidth * $end_day;
                if ($end_hour >= 9 && $end_hour < 18) {
                    $left += ($end_hour - 9) * ($dayWidth / 9);
                    $left += ($end_min / 60) * ($dayWidth / 9);
                } elseif ($end_hour >= 18) {
                    $left += $dayWidth;
                }
                $left = min(100, $left);
            }
            $right  = 100;

            $template->set('left', $left);
            $template->set('width', min($right - $left, 100));
            $template->set('top', $count++ * 15);

            $blocks .= $template->fetch(KRONOLITH_TEMPLATES . '/fbview/unknownblock.tpl');
        }

        // overlay the grid
        $template->set('top', $count++ * 15);
        $blocks .= $template->fetch(KRONOLITH_TEMPLATES . '/weekView/linesblock.tpl');

        return $blocks;
    }

}
