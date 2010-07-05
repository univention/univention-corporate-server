<?php
/**
 * $Horde: kronolith/feed/index.php,v 1.3.2.2 2009-01-06 15:24:45 jan Exp $
 *
 * Copyright 2008-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Jan Schneider <jan@horde.org>
 */

function _no_access($status, $reason, $body)
{
    header('HTTP/1.0 ' . $status . ' ' . $reason);
    echo "<!DOCTYPE HTML PUBLIC \"-//IETF//DTD HTML 2.0//EN\">
<html><head>
<title>$status $reason</title>
</head><body>
<h1>$reason</h1>
<p>$body</p>
</body></html>";
    exit;
}

$session_control = 'readonly';
@define('AUTH_HANDLER', true);
@define('KRONOLITH_BASE', dirname(__FILE__) . '/..');
require_once KRONOLITH_BASE . '/lib/base.php';
require_once KRONOLITH_BASE . '/lib/version.php';
require_once 'Horde/Identity.php';
require_once 'Horde/MIME.php';
require_once 'Horde/Template.php';

$calendar = Util::getFormData('c');
$share = $kronolith_shares->getShare($calendar);
if (is_a($share, 'PEAR_Error')) {
    _no_access(404, 'Not Found',
               sprintf(_("The requested feed (%s) was not found on this server."),
                       htmlspecialchars($calendar)));
}
if (!$share->hasPermission(Auth::getAuth(), PERMS_READ)) {
    if (Auth::getAuth()) {
        _no_access(403, 'Forbidden',
                   sprintf(_("Permission denied for the requested feed (%s)."),
                           htmlspecialchars($calendar)));
    } else {
        $auth = &Auth::singleton($conf['auth']['driver']);
        if (isset($_SERVER['PHP_AUTH_USER'])) {
            $user = $_SERVER['PHP_AUTH_USER'];
            $pass = $_SERVER['PHP_AUTH_PW'];
        } elseif (isset($_SERVER['Authorization'])) {
            $hash = str_replace('Basic ', '', $_SERVER['Authorization']);
            $hash = base64_decode($hash);
            if (strpos($hash, ':') !== false) {
                list($user, $pass) = explode(':', $hash, 2);
            }
        }

        if (!isset($user) ||
            !$auth->authenticate($user, array('password' => $pass))) {
            header('WWW-Authenticate: Basic realm="' . $registry->get('name') . ' Feeds"');
            _no_access(401, 'Unauthorized',
                       sprintf(_("Login required for the requested feed (%s)."),
                               htmlspecialchars($calendar)));
        }
    }
}

$feed_type = basename(Util::getFormData('type'));
if (empty($feed_type)) {
    // If not specified, default to Atom.
    $feed_type = 'atom';
}

$startDate = new Horde_Date(array('year' => date('Y'), 'month' => date('n'), 'mday' => date('j')));
$events = Kronolith::listEvents($startDate,
                                new Horde_Date($startDate),
                                array($calendar));
if (is_a($events, 'PEAR_Error')) {
    Horde::logMessage($events, __FILE__, __LINE__, PEAR_LOG_ERR);
    $events = array();
}

if (isset($conf['urls']['pretty']) && $conf['urls']['pretty'] == 'rewrite') {
    $self_url = 'feed/' . $calendar;
} else {
    $self_url = Util::addParameter('feed/index.php', 'c', $calendar);
}
$self_url = Horde::applicationUrl($self_url, true, -1);

$owner = $share->get('owner');
$identity = Identity::factory('none', $owner);
$history = &Horde_History::singleton();
$now = new Horde_Date(time());

$template = new Horde_Template();
$template->set('charset', NLS::getCharset());
$template->set('updated', $now->iso8601DateTime());
$template->set('kronolith_name', 'Kronolith');
$template->set('kronolith_version', KRONOLITH_VERSION);
$template->set('kronolith_uri', 'http://www.horde.org/kronolith/');
$template->set('kronolith_icon', Horde::url($registry->getImageDir() . '/kronolith.png', true, -1));
$template->set('xsl', $registry->get('themesuri') . '/feed-rss.xsl');
$template->set('calendar_name', @htmlspecialchars($share->get('name'), ENT_COMPAT, NLS::getCharset()));
$template->set('calendar_desc', @htmlspecialchars($share->get('desc'), ENT_COMPAT, NLS::getCharset()), true);
$template->set('calendar_owner', @htmlspecialchars($identity->getValue('fullname'), ENT_COMPAT, NLS::getCharset()));
$template->set('calendar_email', @htmlspecialchars($identity->getValue('from_addr'), ENT_COMPAT, NLS::getCharset()), true);
$template->set('self_url', $self_url);

$entries = array();
foreach ($events as $day_events) {
    foreach ($day_events as $id => $event) {
        /* Modification date. */
        $modified = $history->getActionTimestamp('kronolith:' . $calendar . ':'
                                                 . $event->getUID(), 'modify');
        if (!$modified) {
            $modified = $history->getActionTimestamp('kronolith:' . $calendar . ':'
                                                     . $event->getUID(), 'add');
        }
        $modified = new Horde_Date($modified);
        /* Description. */
        $desc = @htmlspecialchars($event->getDescription(), ENT_COMPAT, NLS::getCharset());
        if (strlen($desc)) {
            $desc .= '<br /><br />';
        }
        /* Time. */
        $desc .= _("When:") . ' ' . $event->start->strftime($prefs->getValue('date_format')) . ' ' . date($prefs->getValue('twentyFor') ? 'H:i' : 'h:i a', $event->start->timestamp()) . _(" to ");
        if ($event->start->compareDate($event->end->timestamp()) == 0) {
            $desc .= date($prefs->getValue('twentyFor') ? 'H:i' : 'h:i a', $event->end->timestamp());
        } else {
            $desc .= $event->end->strftime($prefs->getValue('date_format')) . ' ' . date($prefs->getValue('twentyFor') ? 'H:i' : 'h:i a', $event->end->timestamp());
        }
        /* Attendees. */
        $attendees = array();
        foreach ($event->getAttendees() as $attendee => $status) {
            $attendees[] = empty($status['name']) ? $attendee : MIME::trimEmailAddress($status['name'] . (strpos($attendee, '@') === false ? '' : ' <' . $attendee . '>'));
        }
        if (count($attendees)) {
            $desc .= '<br />' . _("Who:") . ' ' . @htmlspecialchars(implode(', ', $attendees), ENT_COMPAT, NLS::getCharset());
        }
        if (strlen($event->getLocation())) {
            $desc .= '<br />' . _("Where:") . ' ' . @htmlspecialchars($event->getLocation(), ENT_COMPAT, NLS::getCharset());
        }
        $desc .= '<br />' . _("Event Status:") . ' ' . Kronolith::statusToString($event->getStatus());

        $entries[$id]['title'] = @htmlspecialchars($event->getTitle(), ENT_COMPAT, NLS::getCharset());
        $entries[$id]['desc'] = @htmlspecialchars($desc, ENT_COMPAT, NLS::getCharset());
        $entries[$id]['url'] = htmlspecialchars(Horde::url($event->getViewUrl(), true, -1));
        $entries[$id]['modified'] = $modified->iso8601DateTime();
        $entries[$id]['category'] = $event->getCategory();
    }
}
$template->set('entries', $entries, true);

$browser->downloadHeaders($calendar . '.xml', 'text/xml', true);
echo $template->fetch(KRONOLITH_TEMPLATES . '/feeds/' . $feed_type . '.xml');
