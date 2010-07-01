<?php

require_once 'Horde/Template.php';

/**
 * This class represent a view of multiple free busy information sets.
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information.
 *
 * $Horde: kronolith/lib/FBView.php,v 1.10.10.16 2009-01-06 15:24:45 jan Exp $
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @author  Jan Schneider <jan@horde.org>
 * @package Kronolith
 */
class Kronolith_FreeBusy_View {

    var $_requiredMembers = array();
    var $_optionalMembers = array();

    var $_startHour;
    var $_endHour;

    var $_startStamp;
    var $_endStamp;

    function addRequiredMember($vFreebusy)
    {
        $this->_requiredMembers[] = Util::cloneObject($vFreebusy);
    }

    function addOptionalMember($vFreebusy)
    {
        $this->_optionalMembers[] = Util::cloneObject($vFreebusy);
    }

    function render($day = null)
    {
        global $prefs;

        $this->_startHour = floor($prefs->getValue('day_hour_start') / 2);
        $this->_endHour = floor(($prefs->getValue('day_hour_end') + 1) / 2);

        $this->_render($day);

        require_once 'Horde/iCalendar.php';
        $vCal = new Horde_iCalendar();
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
        $base_url = Util::addParameter($base_url, 'fbview', $this->view);

        $template = &new Horde_Template();
        $template->set('title', $this->_title());

        $html = $template->fetch(KRONOLITH_TEMPLATES . '/fbview/header.html') .
            '<div class="fbgrid">';

        $hours_html = $this->_hours();

        // set C locale to avoid localized decimal separators during CSS width
        // calculation.
        $lc = setlocale(LC_NUMERIC, 0);
        setlocale(LC_NUMERIC, 'C');

        // Required to attend.
        if (count($this->_requiredMembers) > 0) {
            $template = new Horde_Template();
            $rows = '';
            foreach ($this->_requiredMembers as $member) {
                $member->simplify();
                $blocks = $this->_getBlocks($member, $member->getBusyPeriods(), 'busyblock.html', _("Busy"), $member->getExtraParams());
                $template = new Horde_Template();
                $template->set('blocks', $blocks);
                $template->set('name', $member->getName());
                $rows .= $template->fetch(KRONOLITH_TEMPLATES . '/fbview/row.html');
            }

            $template = new Horde_Template();
            $template->set('title', _("Required Attendees"));
            $template->set('rows', $rows);
            $template->set('span', count($this->_timeBlocks));
            $template->set('hours', $hours_html);
            $template->set('legend', '');
            $html .= $template->fetch(KRONOLITH_TEMPLATES . '/fbview/section.html');
        }

        // Optional to attend.
        if (count($this->_optionalMembers) > 0) {
            $template = new Horde_Template();
            $rows = '';
            foreach ($this->_optionalMembers as $member) {
                $member->simplify();
                $blocks = $this->_getBlocks($member, $member->getBusyPeriods(), 'busyblock.html', _("Busy"), $member->getExtraParams());
                $template = new Horde_Template();
                $template->set('blocks', $blocks);
                $template->set('name', $member->getName());
                $rows .= $template->fetch(KRONOLITH_TEMPLATES . '/fbview/row.html');
            }

            $template = new Horde_Template();
            $template->set('title', _("Optional Attendees"));
            $template->set('rows', $rows);
            $template->set('span', count($this->_timeBlocks));
            $template->set('hours', $hours_html);
            $template->set('legend', '');
            $html .= $template->fetch(KRONOLITH_TEMPLATES . '/fbview/section.html');
        }

	//**********
	//This has been disabled in kolab-fbview. Make this optional?

        // Possible meeting times.
        $optimal->setAttribute('ORGANIZER', _("All Attendees"));
        $blocks = $this->_getBlocks($optimal,
                                    $optimal->getFreePeriods($this->_startStamp, $this->_endStamp),
                                    'meetingblock.html', _("All Attendees"));

        $template = new Horde_Template();
        $template->set('name', _("All Attendees"));
        $template->set('blocks', $blocks);
        $rows = $template->fetch(KRONOLITH_TEMPLATES . '/fbview/row.html');

        // Possible meeting times.
        $required->setAttribute('ORGANIZER', _("Required Attendees"));
        $blocks = $this->_getBlocks($required,
                                    $required->getFreePeriods($this->_startStamp, $this->_endStamp),
                                    'meetingblock.html', _("Required Attendees"));

        $template = new Horde_Template();
        $template->set('name', _("Required Attendees"));
        $template->set('blocks', $blocks);
        $rows .= $template->fetch(KRONOLITH_TEMPLATES . '/fbview/row.html');

	//This has been disabled in kolab-fbview. Make this optional?
	//**********

        // Reset locale.
        setlocale(LC_NUMERIC, $lc);

        $template = new Horde_Template();
        $template->set('rows', $rows);
        $template->set('title', _("Overview"));
        $template->set('span', count($this->_timeBlocks));
        $template->set('hours', $hours_html);
        if ($prefs->getValue('show_fb_legend')) {
            $template->setOption('gettext', true);
            $template->set('legend', $template->fetch(KRONOLITH_TEMPLATES . '/fbview/legend.html'));
        } else {
            $template->set('legend', '');
        }

        return $html . $template->fetch(KRONOLITH_TEMPLATES . '/fbview/section.html') . '</div>';
    }

    /**
     * Attempts to return a concrete Kronolith_FreeBusy_View instance based on
     * $view.
     *
     * @param string $view  The type of concrete Kronolith_FreeBusy_View
     *                      subclass to return.
     *
     * @return mixed  The newly created concrete Kronolith_FreeBusy_View
     *                instance, or false on an error.
     */
    function &factory($view)
    {
        $driver = basename($view);
        require_once dirname(__FILE__) . '/FBView/' . $driver . '.php';
        $class = 'Kronolith_FreeBusy_View_' . $driver;
        if (class_exists($class)) {
            $fbview = new $class($user, $params);
        } else {
            $fbview = false;
        }

        return $fbview;
    }

    /**
     * Attempts to return a reference to a concrete Kronolith_FreeBusy_View
     * instance based on $view.  It will only create a new instance if no
     * Kronolith_FreeBusy_View instance with the same parameters currently
     * exists.
     *
     * This method must be invoked as:
     * $var = &Kronolith_FreeBusy_View::singleton()
     *
     * @param string $view  The type of concrete Kronolith_FreeBusy_View
     *                      subclass to return.
     *
     * @return mixed  The created concrete Kronolith_FreeBusy_View instance, or
     *                false on an error.
     */
    function &singleton($view)
    {
        static $instances = array();

        if (!isset($instances[$view])) {
            $instances[$view] = &Kronolith_FreeBusy_View::factory($view);
        }

        return $instances[$view];
    }

    function _getBlocks($member, $periods, $blockfile, $label, $extra = array())
    {
        $template = new Horde_Template();
        $template->set('label', $label);

        reset($periods);
        list($periodStart, $periodEnd) = each($periods);

        $blocks = '';
        foreach ($this->_timeBlocks as $start => $end) {
            if ($member->getStart() > $start ||
                $member->getEnd() < $end) {
                $blocks .= $template->fetch(KRONOLITH_TEMPLATES . '/fbview/unknownblock.html');
                continue;
            }

            while ($start > $periodEnd &&
                   list($periodStart, $periodEnd) = each($periods));

            if (($periodStart <= $start && $periodEnd >= $start) ||
                ($periodStart <= $end && $periodEnd >= $end) ||
                ($periodStart <= $start && $periodEnd >= $end) ||
                ($periodStart >= $start && $periodEnd <= $end)) {

                $l_start = ($periodStart < $start) ? $start : $periodStart;
                $l_end = ($periodEnd > $end) ? $end : $periodEnd;
                $plen = ($end - $start) / 100.0;

                $left = ($l_start - $start) / $plen;
                $width = ($l_end - $l_start) / $plen;

                $template->set('left', $left . '%');
                $template->set('width', $width . '%');
                $template->set('evclick', '');

                if (isset($extra[$periodStart])) {
                    if (!empty($extra[$periodStart]['X-UID'])) {
                        $link = "javascript:performAction('viewaction', '" 
			  . addslashes($member->getName() . "#" 
				       . String::convertCharset(base64_decode($extra[$periodStart]['X-UID']), 
								'UTF-8',NLS::getCharset())) . "')";
                        $template->set('evclick', $link);
                    }
                    if (!empty($extra[$periodStart]['X-SUMMARY'])) {
                        $template->set('label', String::convertCharset(base64_decode($extra[$periodStart]['X-SUMMARY']),'UTF-8',
				       NLS::getCharset()));
                    }
                }

                $blocks .= $template->fetch(KRONOLITH_TEMPLATES . '/fbview/' . $blockfile);
            } else {
                $blocks .= $template->fetch(KRONOLITH_TEMPLATES . '/fbview/emptyblock.html');
            }
        }

        return $blocks;
    }

}
