<?php
/**
 * registry.php -- Horde application registry.
 *
 * $Horde: horde/config/registry.php.dist,v 1.219 2004/04/30 15:43:27 jan Exp $
 *
 * This configuration file is used by Horde to determine which Horde
 * applications are installed and where, as well as how they interact.
 *
 * Application registry
 * --------------------
 * The following settings register installed Horde applications.
 * By default, Horde assumes that the application directories live
 * inside the horde directory.
 *
 * Attribute     Type     Description
 * ---------     ----     -----------
 * fileroot      string   The base filesystem path for the module's files
 * webroot       string   The base URI for the module
 * graphics      string   The base URI for the module images
 * icon          string   The URI for an icon to show in menus for the module
 * name          string   The name used in menus and descriptions for a module
 * status        string   'inactive', 'hidden', 'notoolbar', 'heading', 'admin'
 *                        or 'active'.
 * provides      string   Service types the module provides.
 * initial_page  string   The initial (default) page (filename) for the module
 * templates     string   The filesystem path to the templates directory
 * menu_parent   string   The name of the 'heading' group that this app should
 *                        show up under.
 * target        string   The (optional) target frame for the link.
 */

// We try to automatically determine the proper webroot for Horde
// here. This still assumes that applications live under horde/. If
// this results in incorrect results for you, simply change the two
// uses of the $webroot variable in the 'horde' stanza below.
//
// Note for Windows users: the below assumes that your DOCUMENT_ROOT
// uses forward slashes. If it does not, you'll have to tweak this.

$this->applications['horde'] = array(
    'fileroot' => dirname(__FILE__) . '/..',
    'webroot' => '/fbview',
    'initial_page' => 'login.php',
    'icon' => '/fbview/graphics/horde.gif',
    'name' => _("Kolab Free/Busy View"),
    'status' => 'active',
    'templates' => dirname(__FILE__) . '/../templates',
    'provides' => 'horde'
);

if (Auth::getAuth()) {
    $this->applications['logout'] = array(
        'fileroot' => dirname(__FILE__) . '/..',
        'webroot' => $this->applications['horde']['webroot'],
        'initial_page' => 'login.php?' . AUTH_REASON_PARAM . '=' . AUTH_REASON_LOGOUT,
        'icon' => $this->applications['horde']['webroot'] . '/graphics/logout.gif',
        'name' => _("Logout"),
        'status' => 'notoolbar'
        );
} else {
    $this->applications['logout'] = array(
        'fileroot' => dirname(__FILE__) . '/..',
        'webroot' => $this->applications['horde']['webroot'],
        'initial_page' => 'login.php?url=' . urlencode(Horde::selfUrl(true)),
        'icon' => $this->applications['horde']['webroot'] . '/graphics/login.gif',
        'name' => _("Login"),
        'status' => 'notoolbar'
        );
}

$this->applications['kronolith'] = array(
    'fileroot' => dirname(__FILE__) . '/../kronolith',
    'webroot' => $this->applications['horde']['webroot'] . '/kronolith',
    'icon' => $this->applications['horde']['webroot'] . '/kronolith/graphics/kronolith.gif',
    'name' => _("Calendar"),
    'status' => 'active',
    'provides' => 'calendar',
);

//// Addressbook removed for Proko2
//$this->applications['turba'] = array(
//    'fileroot' => dirname(__FILE__) . '/../turba',
//    'webroot' => $this->applications['horde']['webroot'] . '/turba',
//    'icon' => $this->applications['horde']['webroot'] . '/turba/graphics/turba.gif',
//    'name' => _("Address Book"),
//    'status' => 'active',
//    'provides' => array('contacts', 'clients'),
//);
