<?php
/**
 * $Horde: kronolith/attendees.php,v 1.7.8.23 2009-01-07 13:56:57 jan Exp $
 *
 * Copyright 2004-2007 Code Fusion  <http://www.codefusion.co.za/>
 * Copyright 2004-2007 Stuart Binge <s.binge@codefusion.co.za>
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

@define('KRONOLITH_BASE', dirname(__FILE__));
require_once KRONOLITH_BASE . '/lib/base.php';
require_once KRONOLITH_BASE . '/lib/FreeBusy.php';
require_once KRONOLITH_BASE . '/lib/FBView.php';
require_once KRONOLITH_BASE . '/lib/Imple.php';
require_once 'Horde/Identity.php';
require_once 'Horde/UI/Tabs.php';
require_once 'Horde/Variables.php';

// Get the current attendees array from the session cache.
$attendees = (isset($_SESSION['kronolith']['attendees']) &&
              is_array($_SESSION['kronolith']['attendees']))
    ? $_SESSION['kronolith']['attendees']
    : array();
$editAttendee = null;

// Get the action ID and value. This specifies what action the user initiated.
$actionID = Util::getFormData('actionID');
if (Util::getFormData('clearAll')) {
    $actionID =  'clear';
}
$actionValue = Util::getFormData('actionValue');

// Perform the specified action, if there is one.
switch ($actionID) {
case 'add':
    require_once 'Mail/RFC822.php';
    $parser = new Mail_RFC822;
    // Add new attendees. Multiple attendees can be seperated on a single line
    // by whitespace and/or commas.
    $newAttendees = trim(Util::getFormData('newAttendees'));
    if (empty($newAttendees)) {
        if (Util::getFormData('addNewClose')) {
            Util::closeWindowJS();
            exit;
        }
        break;
    }

    require_once 'Horde/MIME.php';
    foreach (MIME::rfc822Explode($newAttendees) as $newAttendee) {
        // Parse the address without validation to see what we can get out of
        // it. We allow email addresses (john@example.com), email address with
        // user information (John Doe <john@example.com>), and plain names
        // (John Doe).
        $newAttendeeParsed = $parser->parseAddressList($newAttendee, '', false,
                                                       false);

        // If we can't even get a mailbox out of the address, then it is
        // likely unuseable. Reject it entirely.
        if (is_a($newAttendeeParsed, 'PEAR_Error') ||
            !isset($newAttendeeParsed[0]) ||
            !isset($newAttendeeParsed[0]->mailbox)) {
            $notification->push(
                sprintf(_("Unable to recognize \"%s\" as an email address."),
                        $newAttendee),
                'horde.error');
            continue;
        }

        // Loop through any addresses we found.
        foreach ($newAttendeeParsed as $newAttendeeParsedPart) {
            // If there is only a mailbox part, then it is just a local name.
            if (empty($newAttendeeParsedPart->host)) {
                $attendees[] = array(
                    'attendance' => KRONOLITH_PART_REQUIRED,
                    'response'   => KRONOLITH_RESPONSE_NONE,
                    'name'       => $newAttendee,
                );
                continue;
            }

            // Build a full email address again and validate it.
            $name = empty($newAttendeeParsedPart->personal)
                ? ''
                : $newAttendeeParsedPart->personal;
            $newAttendeeParsedPartNew = MIME::encodeAddress(
                MIME::rfc822WriteAddress($newAttendeeParsedPart->mailbox,
                                         $newAttendeeParsedPart->host, $name));
            $newAttendeeParsedPartValidated = $parser->parseAddressList(
                $newAttendeeParsedPartNew, '', null, true);
            if (is_a($newAttendeeParsedPartValidated, 'PEAR_Error')) {
                $notification->push($newAttendeeParsedPartValidated,
                                    'horde.error');
            } else {
                $email = $newAttendeeParsedPart->mailbox . '@'
                    . $newAttendeeParsedPart->host;
                // Avoid overwriting existing attendees with the default
                // values.
                if (!isset($attendees[$email]))
                    $attendees[$email] = array(
                        'attendance' => KRONOLITH_PART_REQUIRED,
                        'response'   => KRONOLITH_RESPONSE_NONE,
                        'name'       => $name,
                    );
            }
        }
    }

    $_SESSION['kronolith']['attendees'] = $attendees;

    if (Util::getFormData('addNewClose')) {
        Util::closeWindowJS();
        exit;
    }
    break;

case 'edit':
    // Edit the specified attendee.
    if (isset($attendees[$actionValue])) {
        if (empty($attendees[$actionValue]['name'])) {
            $editAttendee = $actionValue;
        } else {
            require_once 'Horde/MIME.php';
            $editAttendee = MIME::trimEmailAddress(
                $attendees[$actionValue]['name']
                . (strpos($actionValue, '@') === false
                   ? ''
                   : ' <' . $actionValue . '>'));
        }
        unset($attendees[$actionValue]);
        $_SESSION['kronolith']['attendees'] = $attendees;
    }
    break;

case 'remove':
    // Remove the specified attendee.
    if (isset($attendees[$actionValue])) {
        unset($attendees[$actionValue]);
        $_SESSION['kronolith']['attendees'] = $attendees;
    }
    break;

case 'changeatt':
    // Change the attendance status of an attendee
    list($partval, $partname) = explode(' ', $actionValue, 2);
    if (isset($attendees[$partname])) {
        $attendees[$partname]['attendance'] = $partval;
        $_SESSION['kronolith']['attendees'] = $attendees;
    }
    break;

case 'changeresp':
    // Change the response status of an attendee
    list($partval, $partname) = explode(' ', $actionValue, 2);
    if (isset($attendees[$partname])) {
        $attendees[$partname]['response'] = $partval;
        $_SESSION['kronolith']['attendees'] = $attendees;
    }
    break;

case 'dismiss':
    // Close the attendee window.
    if ($browser->hasFeature('javascript')) {
        Util::closeWindowJS();
        exit;
    }

    $url = Util::getFormData('url');
    if (!empty($url)) {
        $location = Horde::applicationUrl($url, true);
    } else {
        $url = Util::addParameter($prefs->getValue('defaultview') . '.php',
                                  'month', Util::getFormData('month'));
        $url = Util::addParameter($url, 'year', Util::getFormData('year'));
        $location = Horde::applicationUrl($url, true);
    }

    // Make sure URL is unique.
    $location = Util::addParameter($location, 'unique', md5(microtime()));
    header('Location: ' . $location);
    exit;

case 'clear':
    // Remove all the attendees.
    $attendees = array();
    $_SESSION['kronolith']['attendees'] = $attendees;
    break;

case 'save':
    if (empty($attendees)) {
        break;
    }
    $savedattlist = unserialize($prefs->getValue('saved_attendee_list'));
    $savedattlist[] = array_keys($attendees);
    $prefs->setValue('saved_attendee_list', serialize($savedattlist));
    $notification->push(_('Successfully saved attendee list'), 'horde.success');
    break;
}

// Get the current Free/Busy view; default to the 'day' view if none specified.
$view = Util::getFormData('view', 'day');

// Pre-format our delete image/link.
$delimg = Horde::img('delete.png', _("Remove Attendee"), null,
                     $registry->getImageDir('horde'));

$ident = &Identity::singleton();
$identities = $ident->getAll('id');
$vars = Variables::getDefaultVariables();
$tabs = new Horde_UI_Tabs(null, $vars);
$tabs->addTab(_("Day"), 'javascript:switchView(\'day\')', 'day');
$tabs->addTab(_("Work Week"), 'javascript:switchView(\'workweek\')', 'workweek');
$tabs->addTab(_("Week"), 'javascript:switchView(\'week\')', 'week');
$tabs->addTab(_("Month"), 'javascript:switchView(\'month\')', 'month');

$attendee_view = &Kronolith_FreeBusy_View::singleton($view);

// Add the creator as a required attendee in the Free/Busy display
$cal = @unserialize($prefs->getValue('fb_cals'));
if (!is_array($cal)) {
    $cal = null;
}

// If the free/busy calendars preference is empty, default to the user's
// default_share preference, and if that's empty, to their username.
if (!$cal) {
    $cal = $prefs->getValue('default_share');
    if (!$cal) {
        $cal = Auth::getAuth();
    }
    $cal = array($cal);
}
$vfb = Kronolith_FreeBusy::generate($cal, null, null, true, Auth::getAuth());
if (!is_a($vfb, 'PEAR_Error')) {
    $attendee_view->addRequiredMember($vfb);
} else {
    $notification->push(
        sprintf(_("Error retrieving your free/busy information: %s"),
                $vfb->getMessage()));
}

// Add the Free/Busy information for each attendee.
foreach ($attendees as $email => $status) {
    if (strpos($email, '@') !== false &&
        ($status['attendance'] == KRONOLITH_PART_REQUIRED ||
         $status['attendance'] == KRONOLITH_PART_OPTIONAL)) {
        $vfb = Kronolith_Freebusy::get($email);
        if (!is_a($vfb, 'PEAR_Error')) {
            $organizer = $vfb->getAttribute('ORGANIZER');
            if (empty($organizer)) {
                $vfb->setAttribute('ORGANIZER', 'mailto:' . $email, array(),
                                   false);
            }
            if ($status['attendance'] == KRONOLITH_PART_REQUIRED) {
                $attendee_view->addRequiredMember($vfb);
            } else {
                $attendee_view->addOptionalMember($vfb);
            }
        } else {
            $notification->push(
                sprintf(_("Error retrieving free/busy information for %s: %s"),
                        $email, $vfb->getMessage()));
        }
    }
}

$timestamp = (int)Util::getFormData('timestamp');
if (!$timestamp) {
    $year = (int)Util::getFormData('year', date('Y'));
    $month = (int)Util::getFormData('month', date('n'));
    $day = (int)Util::getFormData('mday', date('d'));
    $timestamp = empty($year)
        ? $_SERVER['REQUEST_TIME']
        : mktime(0, 0, 0, $month, $day, $year);
}

$vfb_html = $attendee_view->render($timestamp);

// Add the ContactAutoCompleter
Imple::factory('ContactAutoCompleter', array('triggerId' => 'newAttendees'));

$title = _("Edit attendees");
require KRONOLITH_TEMPLATES . '/common-header.inc';

if ($browser->hasFeature('javascript')) {
    Horde::addScriptFile('open_savedattlist_win.js');
    $savedattlist_url = 'javascript:open_savedattlist_win();';
} else {
    $savedattlist_url = Horde::applicationUrl('savedattlist.php');
}

$notification->notify(array('status'));
require KRONOLITH_TEMPLATES . '/attendees/attendees.inc';
require $registry->get('templates', 'horde') . '/common-footer.inc';
