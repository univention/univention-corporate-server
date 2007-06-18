<?php
/**
 * This class represent a single day fbview of mulitple free busy information.
 *
 * Copyright 2003-2004 Mike Cochrane <mike@graftonhall.co.nz>
 *
 * See the enclosed file COPYING for license information.
 *
 * $Horde: kronolith/lib/FBView/day.php,v 1.8 2004/05/25 08:34:22 stuart Exp $
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @package Kronolith
 */
class Kronolith_FreeBusy_View_day extends Kronolith_FreeBusy_View {

    var $_startStamp;
    var $_endStamp;

    function _getBlocks($member, $periods, $blockfile, $label, $extra = array())
    {
        $template = &new Horde_Template();

        $count = 0;
        $blocks = '';
        foreach ($periods as $start => $end) {
            if ($start < $this->_endStamp && $end > $this->_startStamp) {
                $left  = max(0, 100 * (($start - $this->_startStamp) / ($this->_endStamp - $this->_startStamp)));
                $right = max(0, 100 * (($end - $this->_startStamp) / ($this->_endStamp - $this->_startStamp)));
                $width = $right - $left;

                $template->set('left', $left);
                $template->set('width', min($width, 100 - $left) );
                $template->set('top', $count++ * 15);
                $template->set('evclick', '');
                $template->set('label', '');
                if (isset($extra[$start])) {
                    if (!empty($extra[$start]['X-UID'])) {
                        $link = "javascript:performAction(" . KRONOLITH_ACTIONID_VIEW . ", '" 
			  . addslashes($member->getName() . "#" 
				       . String::convertCharset(base64_decode($extra[$start]['X-UID']), 
								'UTF-8',NLS::getCharset())) . "')";
                        $template->set('evclick', $link);
                    }
                    if (!empty($extra[$start]['X-SUMMARY'])) {
                        $template->set('label', String::convertCharset(base64_decode($extra[$start]['X-SUMMARY']),'UTF-8',
				       NLS::getCharset()));
                    }
                }
                $blocks .= $template->fetch(KRONOLITH_TEMPLATES . '/fbview/' . $blockfile);
            }
        }

        if ($member->getEnd() < $this->_endStamp) {
            $left  = max(0, 100 * (($member->getEnd() - $this->_startStamp) / ($this->_endStamp - $this->_startStamp)));
            $right = 100;
            $width = $right - $left;

            $template->set('left', $left);
            $template->set('width', $width);
            $template->set('top', $count++ * 15);
            $template->set('label', _("Unknown"));
            $blocks .= $template->fetch(KRONOLITH_TEMPLATES . '/fbview/unknownblock.tpl');
        } else if ($member->getStart() > $this->_startStamp) {
            $left  = 0;
            $right = min(100, 100 * (($member->getStart() - $this->_startStamp) / ($this->_endStamp - $this->_startStamp)));
            $width = $right - $left;

            $template->set('left', $left);
            $template->set('width', $width);
            $template->set('top', $count++ * 15);
            $template->set('label', _("Unknown"));
            $blocks .= $template->fetch(KRONOLITH_TEMPLATES . '/fbview/unknownblock.tpl');
        }

        $template->set('top', $count++ * 15);
        $blocks .= $template->fetch(KRONOLITH_TEMPLATES . '/dayView/linesblock.tpl');

        return $blocks;
    }


    function render($day = null)
    {
        global $prefs;

        $startHour = 6;
        $endHour = 22;
        $title = 'today';

        if (is_null($day)) {
            $day = time();
        }
        $this->_startStamp = mktime($startHour, 0, 0, date('n', $day), date('j', $day), date('Y', $day));
        $this->_endStamp   = mktime($endHour, 0, 0, date('n', $day), date('j', $day), date('Y', $day));

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
        $template = &new Horde_Template();
        $template->set('title', strftime($prefs->getValue('date_format'), $this->_startStamp));
        $template->set('prev_url',
                       Horde::link('', _("Previous Day"), 'menuitem', null, 'return switchTimestamp(' . ($day - 86400) . ');') .
                       Horde::img('nav/left.gif', '<', null, $GLOBALS['registry']->getParam('graphics', 'horde')) . '</a>');

        $template->set('next_url',
                       Horde::link('', _("Next Day"), 'menuitem', null, 'return switchTimestamp(' . ($day + 86400) . ');') .
                       Horde::img('nav/right.gif', '>', null, $GLOBALS['registry']->getParam('graphics', 'horde')) . '</a>');

        $html = $template->fetch(KRONOLITH_TEMPLATES . '/fbview/header.tpl');

        $hours_html = '<table width="100%" cellpadding="0" cellspacing="0" style="text-align:center"><tr>';
        $step = 1;
        $width = 100 / ($endHour - $startHour);
        for ($i = $startHour; $i < $endHour; $i+= $step) {
            $t = mktime($i);
	    if( $prefs->getValue('twentyFour') ) {
	      $hour = intval(strftime("%H", $t));
	    } else {
	      $hour = intval(strftime("%I", $t)) . strftime(" %p", $t);
	    }
            if ($i > $startHour) {
                $hours_html .= "<td style=\"border-left:1px solid black;width:$width%\">$hour</td>";
            } else {
                $hours_html .= "<td style=\"width:$width%\">$hour</td>";
            }
        }
        $hours_html .= '</tr></table>';

        // Required attendees.
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

        // Optional attendees.
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

        // Possible meeting times for everyone.
        /*$optimal->setAttribute('ORGANIZER', _("All Attendees"));
        $blocks = $this->_getBlocks($optimal,
                                    $optimal->getFreePeriods($this->_startStamp, $this->_endStamp),
                                    'meetingblock.tpl', _("All Attendees"));

        $template = &new Horde_Template();
        $template->set('name', _("All Attendees"));
        $template->set('blocks', $blocks);
        $rows = $template->fetch(KRONOLITH_TEMPLATES . '/fbview/row.tpl');

        // Possible meeting times for required attendees.
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

}
