<?php
/**
 * $Horde: horde/index.php,v 2.105.4.13 2009-01-06 15:13:50 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__));
$horde_configured = (is_readable(HORDE_BASE . '/config/conf.php') &&
                     is_readable(HORDE_BASE . '/config/mime_drivers.php') &&
                     is_readable(HORDE_BASE . '/config/nls.php') &&
                     is_readable(HORDE_BASE . '/config/prefs.php') &&
                     is_readable(HORDE_BASE . '/config/registry.php'));

if (!$horde_configured) {
    require HORDE_BASE . '/lib/Test.php';
    Horde_Test::configFilesMissing('Horde', HORDE_BASE, 'prefs.php',
        array('conf.php' => 'This is the main Horde configuration file. It contains paths and basic items that apply to the core framework and all Horde applications.',
              'mime_drivers.php' => 'This file controls the global set of MIME drivers for the Horde framework, allowing applications to make use of programs such as enscript or mswordview to render content into HTML for viewing in a browser.',
              'nls.php' => 'This file provides localisation support for the Horde framework.',
              'registry.php' => 'The registry is how Horde applications find out how to talk to each other. You should list any installed Horde applications that you have here.'));
}

require_once HORDE_BASE . '/lib/base.php';

$main_page = Util::getFormData('url');

// Break up the requested URL in $main_page and run some sanity checks
// on it to prevent phishing and XSS attacks. If any of the checks
// fail, $main_page will be set to null.
if (!empty($main_page)) {
    // Mute errors in case of unparseable URLs
    $req = @parse_url($main_page);

    // We assume that any valid redirect URL will be in the same
    // cookie domain. This helps prevent rogue off-site Horde installs
    // from mimicking the real server.
    if (isset($req['host'])) {
        $qcookiedom = preg_quote($conf['cookie']['domain']);
        if (!preg_match('/' . $qcookiedom . '$/', $req['host'])) {
            $main_page = null;
        }
    }

    // Protocol whitelist: If the URL is fully qualified, make sure it
    // is either http or https.
    $allowed_protocols = array('http', 'https');
    if (empty($req['scheme']) ||
        !in_array($req['scheme'], $allowed_protocols)) {
        $main_page = null;
    }
}

if ($browser->isMobile()) {
    if ($main_page) {
        header('Location: ' . $main_page);
    } else {
        require HORDE_BASE . '/services/portal/mobile.php';
    }
    exit;
}

if (!$main_page) {
    $initial_app = $prefs->getValue('initial_application');
    if (!empty($initial_app) && $registry->hasPermission($initial_app)) {
        $main_page = Horde::url($registry->getInitialPage($initial_app), true);
    } elseif (isset($registry->applications['horde']['initial_page'])) {
        $main_page = Horde::applicationUrl($registry->applications['horde']['initial_page'], true);
    } elseif (Auth::getAuth()) {
        $main_page = Horde::applicationUrl('services/portal/', true);
    } else {
        $main_page = Horde::applicationUrl('login.php', true);
    }
}

if (!Util::getFormData('frameset_loaded') &&
    ($conf['menu']['always'] ||
     (Auth::getAuth() && $prefs->getValue('show_sidebar')))) {
    if ($browser->hasQuirk('scrollbar_in_way')) {
        $scrollbar = 'yes';
    } else {
        $scrollbar = 'auto';
    }
    require HORDE_TEMPLATES . '/index/frames_index.inc';
} else {
    header('Location: ' . $main_page);
}
