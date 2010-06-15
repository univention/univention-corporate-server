<?php
/**
 * $Horde: horde/index.php,v 2.95 2004/04/07 14:43:00 chuck Exp $
 *
 * Copyright 1999-2004 Charles J. Hagenbuch <chuck@horde.org>
 * Copyright 1999-2004 Jon Parise <jon@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

// Check for a prior definition of HORDE_BASE (perhaps by an
// auto_prepend_file definition for site customization).
if (!defined('HORDE_BASE')) {
    @define('HORDE_BASE', dirname(__FILE__));
}
$horde_configured = (@file_exists(HORDE_BASE . '/config/conf.php') &&
                     @file_exists(HORDE_BASE . '/config/html.php') &&
                     @file_exists(HORDE_BASE . '/config/mime_drivers.php') &&
                     @file_exists(HORDE_BASE . '/config/prefs.php') &&
                     @file_exists(HORDE_BASE . '/config/registry.php'));

if ($horde_configured) {
    @define('AUTH_HANDLER', true);
    require_once HORDE_BASE . '/lib/base.php';

    if ($browser->isMobile()) {
        require HORDE_BASE . '/services/portal/mobile.php';
        exit;
    } else {
        $url = Util::getFormData('url');
        $initial_app = $prefs->getValue('initial_application');

        if (!empty($url)) {
            $main_page = $url;
        } elseif (!empty($initial_app) && ($GLOBALS['perms']->exists($initial_app) ?
                                           $GLOBALS['perms']->hasPermission($initial_app, Auth::getAuth(), PERMS_READ) :
                                           Auth::getAuth())) {
            $main_page = Horde::url($registry->getInitialPage($initial_app));
        } elseif (isset($registry->applications['horde']['initial_page'])) {
            $main_page = Horde::applicationUrl($registry->applications['horde']['initial_page']);
        } elseif (Auth::getAuth()) {
            $main_page = Horde::applicationUrl('services/portal/');
        } else {
            $main_page = Horde::applicationUrl('login.php');
        }

        if (!Util::getFormData('frameset') &&
            ($conf['menu']['always'] ||
             ($conf['menu']['display'] && Auth::getAuth() && $prefs->getValue('show_sidebar')))) {
            if ($browser->hasQuirk('scrollbar_in_way')) {
                $scrollbar = 'yes';
            } else {
                $scrollbar = 'auto';
            }
            $main_page = Util::addParameter($main_page, 'frameset', 1);
            require HORDE_TEMPLATES . '/index/frames_index.inc';
        } else {
            header('Location: ' . $main_page);
            exit;
        }
    }
} else {
    require HORDE_BASE . '/lib/Test.php';
    Horde_Test::configFilesMissing('Horde', HORDE_BASE, 'prefs.php',
        array('conf.php' => 'This is the main Horde configuration file. It contains paths and basic items that apply to the core framework and all Horde applications.',
              'html.php' => 'This file controls the stylesheet that is used to set colors and fonts for the Horde framework and all applications that do not provide their own settings.',
              'mime_drivers.php' => 'This file controls the global set of MIME drivers for the Horde framework, allowing applications to make use of programs such as enscript or mswordview to render content into HTML for viewing in a browser.',
              'registry.php' => 'The registry is how Horde applications find out how to talk to each other. You should list any installed Horde applications that you have here.'));
}
