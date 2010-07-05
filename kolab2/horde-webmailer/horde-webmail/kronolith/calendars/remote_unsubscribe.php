<?php
/**
 * $Horde: kronolith/calendars/remote_unsubscribe.php,v 1.1.2.3 2009-01-06 15:24:44 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

@define('KRONOLITH_BASE', dirname(dirname(__FILE__)));
require_once KRONOLITH_BASE . '/lib/base.php';
require_once KRONOLITH_BASE . '/lib/Forms/UnsubscribeRemoteCalendar.php';

// Exit if this isn't an authenticated user or if the user can't
// subscribe to remote calendars (remote_cals is locked).
if (!Auth::getAuth() || $prefs->isLocked('remote_cals')) {
    header('Location: ' . Horde::applicationUrl($prefs->getValue('defaultview') . '.php', true));
    exit;
}

$vars = Variables::getDefaultVariables();
$url = $vars->get('url');

$remote_calendar = null;
$remote_calendars = unserialize($GLOBALS['prefs']->getValue('remote_cals'));
foreach ($remote_calendars as $key => $calendar) {
    if ($calendar['url'] == $url) {
        $remote_calendar = $calendar;
        break;
    }
}
if (is_null($remote_calendar)) {
    $notification->push(_("The remote calendar was not found."), 'horde.error');
    header('Location: ' . Horde::applicationUrl('calendars/', true));
    exit;
}

$form = new Kronolith_UnsubscribeRemoteCalendarForm($vars, $remote_calendar);

// Execute if the form is valid (must pass with POST variables only).
if ($form->validate(new Variables($_POST))) {
    $result = $form->execute();
    if (is_a($result, 'PEAR_Error')) {
        $notification->push($result, 'horde.error');
    } elseif ($result) {
        $notification->push(sprintf(_("You have been unsubscribed from \"%s\" (%s)."), $calendar['name'], $calendar['url']), 'horde.success');
    }

    header('Location: ' . Horde::applicationUrl('calendars/', true));
    exit;
}

$vars->set('url', $calendar['url']);
$title = $form->getTitle();
require KRONOLITH_TEMPLATES . '/common-header.inc';
require KRONOLITH_TEMPLATES . '/menu.inc';
echo $form->renderActive($form->getRenderer(), $vars, 'remote_unsubscribe.php', 'post');
require $registry->get('templates', 'horde') . '/common-footer.inc';
