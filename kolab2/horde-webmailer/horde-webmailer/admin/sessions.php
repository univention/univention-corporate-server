<?php
/**
 * $Horde: horde/admin/sessions.php,v 1.2.2.8 2009-04-04 12:30:51 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

@define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/SessionHandler.php';

if (!Auth::isAdmin()) {
    Horde::authenticationFailureRedirect();
}

$type = !empty($conf['sessionhandler']['type']) ? $conf['sessionhandler']['type'] : 'none';
if ($type == 'external') {
    $notification->push(_("Cannot administer external session handlers."), 'horde.error');
} else {
    $sh = &SessionHandler::singleton($type);
}

$title = _("Session Admin");
Horde::addScriptFile('prototype.js', 'horde', true);
require HORDE_TEMPLATES . '/common-header.inc';
require HORDE_TEMPLATES . '/admin/menu.inc';

if (empty($sh)) {
    require HORDE_TEMPLATES . '/common-footer.inc';
    exit;
}

$session_info = $sh->getSessionsInfo();

echo '<h1 class="header">' . _("Current Sessions");
if (is_a($session_info, 'PEAR_Error')) {
    echo '</h1><p class="headerbox"><em>' . sprintf(_("Listing sessions failed: %s"), $session_info->getMessage()) . '</em></p>';
} else {
    echo ' (' . count($session_info) . ')</h1>' .
         '<ul class="headerbox linedRow">';

    $plus = Horde::img('tree/plusonly.png', _("Expand"), '', $GLOBALS['registry']->getImageDir('horde'));
    $minus = Horde::img('tree/minusonly.png', _("Collapse"), 'style="display:none"', $GLOBALS['registry']->getImageDir('horde'));

    $have_netdns = @include_once 'Net/DNS.php';
    if ($have_netdns) {
        $resolver = new Net_DNS_Resolver();
        $resolver->retry = isset($GLOBALS['conf']['dns']['retry']) ? $GLOBALS['conf']['dns']['retry'] : 1;
        $resolver->retrans = isset($GLOBALS['conf']['dns']['retrans']) ? $GLOBALS['conf']['dns']['retrans'] : 1;
    }

    foreach ($session_info as $id => $data) {
        $entry = array(
            _("Session Timestamp:") => date('r', $data['timestamp']),
            _("Browser:") => $data['browser'],
            _("Realm:") => empty($data['realm']) ? _("[None]") : $data['realm'],
            _("Remote Host:") => _("[Unknown]")
        );

        if (!empty($data['remote_addr'])) {
            if ($have_netdns) {
                $response = $resolver->query($data['remote_addr'], 'PTR');
                $host = $response ? $response->answer[0]->ptrdname : $data['remote_addr'];
            } else {
                $host = @gethostbyaddr($data['remote_addr']);
            }
            $entry[_("Remote Host:")] = $host . ' [' . $data['remote_addr'] . '] ' . NLS::generateFlagImageByHost($host);
        }

        echo '<li><div onclick="$(this).nextSiblings().invoke(\'toggle\'); $(this).immediateDescendants().invoke(\'toggle\');">' . $plus . $minus . htmlspecialchars($data['userid']) . ' [' . htmlspecialchars($id) . ']'
            . '</div><div style="padding-left:20px;display:none">';
        foreach ($entry as $key => $val) {
            echo '<div><strong>' . $key . '</strong> ' . $val . '</div>';
        }
        echo '</div></li>';
    }
    echo '</ul>';
}

require HORDE_TEMPLATES . '/common-footer.inc';
