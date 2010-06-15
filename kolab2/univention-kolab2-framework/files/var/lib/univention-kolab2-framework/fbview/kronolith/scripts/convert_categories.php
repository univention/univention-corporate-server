#!/usr/local/bin/php
<?php
/**
 * $Horde: kronolith/scripts/convert_categories.php,v 1.4 2004/05/19 20:26:24 chuck Exp $
 *
 * Copyright 2004 Charles J. Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (GPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

@define('AUTH_HANDLER', true);
@define('KRONOLITH_BASE', dirname(__FILE__) . '/..');
require_once KRONOLITH_BASE . '/lib/base.php';

// Run through every calendar.
$cals = $kronolith_shares->listAllShares();
foreach ($cals as $calid => $calshare) {
    echo "Converting categories for $calid ...\n";

    if ($kronolith->getCalendar() != $calid) {
        $kronolith->close();
        $kronolith->open($calid);
    }

    $categories = listCategories($calid);

    // List all events.
    $events = $kronolith->listEvents();
    foreach ($events as $eventId) {
        $event = &$kronolith->getEvent($eventId);
        if (isset($categories[$event->getCategory()])) {
            $event->setCategory($categories[$event->getCategory()]);
            $result = $event->save();
            if (is_a($result, 'PEAR_Error')) {
                Horde::fatal($result);
            }
        }
    }
}

echo "\n** Categories successfully converted ***\n";
exit;

function listCategories($calendar = null)
{
    global $prefs;

    static $catString, $categories;

    $cur = getPrefByShare('event_categories', $calendar);
    if (is_null($catString) || $catString != $cur) {
        $categories = array(0 => _("Unfiled"));

        $catString = $cur;
        if (empty($catString)) {
            return $categories;
        }

        $cats = explode('|', $catString);
        foreach ($cats as $cat) {
            list($key, $val) = explode(':', $cat);
            $categories[$key] = _($val);
        }
    }

    asort($categories);
    return $categories;
}

function getPrefByShare($pref, $share = null)
{
    if (!is_a($share, 'DataTreeObject_Share')) {
        $share = $GLOBALS['kronolith_shares']->getShare($share);
        if (is_a($share, 'PEAR_Error')) {
            return null;
        }
    }

    $owner = $share->get('owner');
    $userprefs = &Prefs::singleton($GLOBALS['conf']['prefs']['driver'],
                                   $GLOBALS['registry']->getApp(),
                                   $owner, '', null, false);
    $userprefs->retrieve();
    return $userprefs->getValue($pref);
}
