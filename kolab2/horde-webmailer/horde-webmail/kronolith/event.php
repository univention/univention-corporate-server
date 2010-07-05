<?php
/**
 * $Horde: kronolith/event.php,v 1.10.2.3 2009-01-06 15:24:43 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

@define('KRONOLITH_BASE', dirname(__FILE__));
require_once KRONOLITH_BASE . '/lib/base.php';

$viewName = Util::getFormData('view', 'Event');
$view = Kronolith::getView($viewName);
if (is_a($view->event, 'PEAR_Error')) {
    $notification->push($view->event, 'horde.error');
    header('Location: ' . Horde::applicationUrl($prefs->getValue('defaultview') . '.php', true));
    exit;
}

switch ($viewName) {
case 'DeleteEvent':
    /* Shortcut when we're deleting events and don't want confirmation. */
    if (!$view->event->recurs() &&
        !($prefs->getValue('confirm_delete') ||
          Util::getFormData('confirm'))) {
        header('Location: ' . Horde::applicationUrl('delete.php?' . $_SERVER['QUERY_STRING'], true));
        exit;
    }
    break;

case 'EditEvent':
    if ($view->event->isPrivate() &&
        $view->event->getCreatorId() != Auth::getAuth()) {
        $url = Util::getFormData('url');
        if (empty($url)) {
            $url = Horde::applicationUrl($prefs->getValue('defaultview') . '.php', true);
        }
        header('Location: ' . Util::addParameter($url, 'unique', md5(microtime()), false));
        exit;
    }
    break;
}

$title = $view->getTitle();
$print_view = (bool)Util::getFormData('print');
if (!$print_view) {
    Horde::addScriptFile('popup.js', 'horde', true);
}
require KRONOLITH_TEMPLATES . '/common-header.inc';

if ($print_view) {
    require_once $registry->get('templates', 'horde') . '/javascript/print.js';
} else {
    require KRONOLITH_TEMPLATES . '/menu.inc';
}

echo '<div id="page">';
if (!$print_view) {
    Kronolith::eventTabs($viewName, $view->event);
}
$view->html();
echo '</div>';
require $registry->get('templates', 'horde') . '/common-footer.inc';
