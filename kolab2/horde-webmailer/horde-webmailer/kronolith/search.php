<?php
/**
 * $Horde: kronolith/search.php,v 1.8.4.9 2009-01-06 15:24:43 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Meilof Veeningen <meilof@gmail.com>
 */

/**
 * Used with usort() to sort events based on their start times.
 */
function _sortEvents($a, $b)
{
    $start_a = $a->recurs() ? $a->recurrence->nextRecurrence($GLOBALS['event']->start) : $a->start;
    $start_b = $b->recurs() ? $b->recurrence->nextRecurrence($GLOBALS['event']->start) : $b->start;
    $diff = $start_a->timestamp() - $start_b->timestamp();
    if ($diff == 0) {
        return strcoll($a->title, $b->title);
    } else {
        return $diff;
    }
}

@define('KRONOLITH_BASE', dirname(__FILE__));
require_once KRONOLITH_BASE . '/lib/base.php';

/* Get search parameters. */
$search_mode = Util::getFormData('search_mode', 'basic');

if ($search_mode != 'basic') {
    /* Make a new empty event object with default values. */
    $event = &$kronolith_driver->getEvent();
    $event->title = $event->calendars = $event->category = $event->location =
    $event->status = $event->description = null;

    /* Set start on today, stop on tomorrow. */
    $event->start = &new Horde_Date(mktime(0, 0, 0));
    $event->end = &new Horde_Date(mktime(0, 0, 0, date('n'), date('j') + 1));

    /* We need to set the event to initialized, otherwise we will end up with
     * a default end date. */
    $event->initialized = true;

    $q_title = Util::getFormData('title');

    if (isset($q_title)) {
        /* We're returning from a previous search. */
        $event->readForm();
        if ($event->category == '__any') {
            $event->category = null;
        }
        if (Util::getFormData('status') == KRONOLITH_STATUS_NONE) {
            $event->status = null;
        }
    }
}

$desc = Util::getFormData('pattern_desc');
$title = Util::getFormData('pattern_title');
if ($desc || $title) {
    /* We're doing a simple search. */
    $event = &$kronolith_driver->getEvent();
    $event->setDescription($desc);
    $event->setTitle($title);
    $event->category = null;
    $event->status = null;

    $time1 = $_SERVER['REQUEST_TIME'];
    $range = Util::getFormData('range');
    if ($range == '+') {
        $event->start = new Horde_Date($time1);
        $event->end = null;
    } elseif ($range == '-') {
        $event->start = null;
        $event->end = new Horde_Date($time1);
    } else {
        $time2 = $time1 + $range;
        $event->start = new Horde_Date(min($time1, $time2));
        $event->end = new Horde_Date(max($time1, $time2));
    }
    $events = Kronolith::search($event);
} elseif (isset($q_title)) {
    /* Advanced search. */
    $events = Kronolith::search($event);
}

$title = _("Search");
Horde::addScriptFile('tooltip.js', 'horde', true);
require KRONOLITH_TEMPLATES . '/common-header.inc';
require KRONOLITH_TEMPLATES . '/menu.inc';

echo '<div id="page">';
if ($search_mode == 'basic') {
    require KRONOLITH_TEMPLATES . '/search/search.inc';
    $notification->push('document.eventform.pattern_title.focus()', 'javascript');
} else {
    require KRONOLITH_TEMPLATES . '/search/search_advanced.inc';
    $notification->push('document.eventform.title.focus()', 'javascript');
}

/* Display search results. */
if (isset($events)) {
    if (count($events)) {
        usort($events, '_sortEvents');

        require KRONOLITH_TEMPLATES . '/search/header.inc';
        require KRONOLITH_TEMPLATES . '/search/event_headers.inc';

        foreach ($events as $found) {
            $start = $found->recurs() ? $found->recurrence->nextRecurrence($event->start) : $found->start;
            $end = &new Horde_Date($start->timestamp() + $found->durMin * 60);
            require KRONOLITH_TEMPLATES . '/search/event_summaries.inc';
        }
        require KRONOLITH_TEMPLATES . '/search/event_footers.inc';
    } else {
        require KRONOLITH_TEMPLATES . '/search/empty.inc';
    }
}

echo '</div>';
require KRONOLITH_TEMPLATES . '/panel.inc';
require $registry->get('templates', 'horde') . '/common-footer.inc';
