<?php
/**
 * $Horde: kronolith/attendeeshandler.php,v 1.1 2004/05/25 08:34:21 stuart Exp $
 *
 * Copyright 2004 Code Fusion  <http://www.codefusion.co.za/>
 *                Stuart Binge <s.binge@codefusion.co.za>
 *
 * See the enclosed file COPYING for license information (GPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

@define('KRONOLITH_BASE', dirname(__FILE__));
require_once KRONOLITH_BASE . '/lib/base.php';
require_once KRONOLITH_BASE . '/lib/FBView.php';

// Get the current attendees array from the session cache.
$attendees = ((array_key_exists('attendees', $_SESSION) && is_array($_SESSION['attendees'])) ? $_SESSION['attendees'] : array());

// Get our Action ID & Value. This specifies what action the user initiated.
$actionID = Util::getFormData('actionID', false);
$actionValue = Util::getFormData('actionValue', false);
if (!$actionID) {
    $actionID = (Util::getFormData('addNew', false) ? KRONOLITH_ACTIONID_ADD : false);
    $actionValue = Util::getFormData('newAttendees', '');
}
$viewEventUID = NULL;

// Get the current Free/Busy view; default to the 'day' view if none specified.
$view = Util::getFormData('view', 'day');

// Preformat our delete image/link.
$delimg = Horde::img('delete.gif', _("Remove Attendee"), null, $registry->getParam('graphics', 'horde'));

// Perform the specified action, if there is one.
switch ($actionID) {
case KRONOLITH_ACTIONID_ADD:
    // Add new attendees. Multiple attendees can be seperated on a single line by whitespace and/or commas
    $new = preg_split('/[\s,]+/', $actionValue, -1, PREG_SPLIT_NO_EMPTY);
    if (is_array($new)) {
        foreach ($new as $newattendee) {
            // Avoid overwriting existing attendees with the default values
            if (!array_key_exists($newattendee, $attendees))
                $attendees[$newattendee] = array('attendance' => KRONOLITH_PART_REQUIRED, 'response' => KRONOLITH_RESPONSE_NONE);
        }
    }

    $_SESSION['attendees'] = $attendees;
    break;

case KRONOLITH_ACTIONID_REMOVE:
    // Remove the specified attendee
    if (array_key_exists($actionValue, $attendees)) {
        unset($attendees[$actionValue]);
        $_SESSION['attendees'] = $attendees;
    }

    break;

case KRONOLITH_ACTIONID_CLEAR:
    // Clear the attendee array
    $attendees = array();
    $_SESSION['attendees'] = $attendees;

    break;

case KRONOLITH_ACTIONID_CHANGEATT:
    // Change the attendance status of an attendee
    list($partval, $partname) = preg_split('/\s+/', $actionValue, 2, PREG_SPLIT_NO_EMPTY);
    if (array_key_exists($partname, $attendees)) {
        $attendees[$partname]['attendance'] = $partval;
        $_SESSION['attendees'] = $attendees;
    }

    break;

case KRONOLITH_ACTIONID_DISMISS:
    // Make sure we're actually allowed to dismiss
    if (!$allow_dismiss) break;

    // Close the attendee window
    global $browser;

    if ($browser->hasFeature('javascript')) {
        Util::closeWindowJS();
    } else {
        $url = Util::getFormData('url');

        if (!empty($url)) {
            $location = Horde::applicationUrl($url, true);
        } else {
            $url = Util::addParameter($prefs->getValue('defaultview') . '.php', 'month', Util::getFormData('month'));
            $url = Util::addParameter($url, 'year', Util::getFormData('year'));
            $location = Horde::applicationUrl($url, true);
        }

        // Make sure URL is unique.
        $location = Util::addParameter($location, 'unique', md5(microtime()));

        header('Location: ' . $location);
    }
    break;

case KRONOLITH_ACTIONID_SAVE:
    if (empty($attendees)) {
        break;
    }
    $savedattlist = unserialize($_COOKIE['saved_attendee_list']);
    //$savedattlist = unserialize($GLOBALS['prefs']->getValue('saved_attendee_list'));
    $savedattlist[] = array_keys($attendees);
    //$GLOBALS['prefs']->setValue('saved_attendee_list', serialize($savedattlist));
    setCookie('saved_attendee_list', serialize($savedattlist), time()+60*60*24*365 /*one year*/, '/fbview' );
    $notification->push(_('Successfully saved attendee list'), 'horde.success');

    break;

case KRONOLITH_ACTIONID_VIEW:
    // View the specified event
    list($viewEventUser, $viewEventUID) = preg_split('/#/', $actionValue, -1, PREG_SPLIT_NO_EMPTY);;

    break;
}
