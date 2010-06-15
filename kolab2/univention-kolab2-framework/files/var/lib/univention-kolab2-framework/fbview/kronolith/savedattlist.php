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

$title = _('Load Attendee List');

Horde::addScriptFile('tooltip.js', 'horde');
require KRONOLITH_TEMPLATES . '/common-header.inc';

// Get our list of saved attendees
$savedattlist = unserialize($_COOKIE['saved_attendee_list']);

// Preformat our image urls
$delimg = Horde::img('delete.gif', _("Remove List"), null, $registry->getParam('graphics', 'horde'));
$loadimg = Horde::img('tick.gif', _("Load List"), null, $registry->getParam('graphics', 'horde'));

// Get our Action ID & Value. This specifies what action the user initiated.
$actionID = Util::getFormData('actionID', false);
$actionValue = Util::getFormData('actionValue', false);
if (!$actionID) {
    $actionID = (Util::getFormData('addNew', false) ? KRONOLITH_ACTIONID_ADD : false);
    $actionValue = Util::getFormData('newAttendees', '');
}

// Perform the specified action, if there is one.
switch ($actionID) {
case KRONOLITH_ACTIONID_REMOVE:
    // Remove the specified attendee
    if (array_key_exists($actionValue, $savedattlist)) {
        unset($savedattlist[$actionValue]);
	//$GLOBALS['prefs']->setValue('saved_attendee_list', serialize($savedattlist));
	setCookie('saved_attendee_list', serialize($savedattlist), time()+60*60*24*365 /*one year*/ );
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
}

$form_handler = Horde::applicationUrl('savedattlist.php');
require KRONOLITH_TEMPLATES . '/savedattlist/savedattlist.inc';
require $registry->getParam('templates', 'horde') . '/common-footer.inc';
