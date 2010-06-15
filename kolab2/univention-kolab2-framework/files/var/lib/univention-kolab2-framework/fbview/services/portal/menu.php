<?php
/**
 * $Horde: horde/services/portal/menu.php,v 2.82 2004/05/26 17:29:56 eraserhd Exp $
 *
 * Copyright 1999-2004 Charles J. Hagenbuch <chuck@horde.org>
 * Copyright 1999-2004 Jon Parise <jon@horde.org>
 * Copyright 2003-2004 Michael Pawlowsky <mjpawlowsky@yahoo.com>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

/**
 * Builds the menu structure depending on application permissions.
 */
function buildMenu()
{
    global $registry, $perms;

    $children = array();
    foreach ($registry->applications as $app => $params) {
        if (isset($params['menu_parent'])) {
            /* Make sure the is a $children entry for each parent
             * group. */
            if (!isset($children[$params['menu_parent']])) {
                $children[$params['menu_parent']] = array();
            }
        }

        /* Don't show the application if it's not installed. */
        if (isset($params['fileroot']) && !is_dir($params['fileroot'])) {
            continue;
        }

        /* Check if the current user has permisson to see this
         * application, and if the application is
         * active. Administrators always see all applications. Anyone
         * with SHOW permissions can see an application, but READ is
         * needed to actually use the application. You can use this
         * distinction to show applications to guests that they need
         * to log in to use. If you don't want them to see apps they
         * can't use, then don't give guests SHOW permissions to
         * anything. */
        if ((Auth::isAdmin() &&
             ($params['status'] == 'active' ||
              $params['status'] == 'admin')) ||
            (($perms->exists($app) ? $perms->hasPermission($app, Auth::getAuth(), PERMS_SHOW) : Auth::getAuth()) &&
             $params['status'] == 'active')) {
            if (isset($params['menu_parent'])) {
                $children[$params['menu_parent']][$app] = $params;
            }
        } else {
            if ($params['status'] != 'heading') {
                $registry->applications[$app]['status'] = 'inactive';
            }
        }
    }

    $tmp = array();
    foreach ($registry->applications as $app => $params) {
        /* Filter out all parents without children. */
        if (isset($children[$app])) {
            if (count($children[$app])) {
                $tmp[$app] = $params;
                $tmp[$app]['children'] = true;
            }
        } else {
            $tmp[$app] = $params;
        }
    }

    $registry->applications = $tmp;
}

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__) . '/../..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Menu.php';
require_once 'Horde/Help.php';

if (!Auth::getAuth() && !$conf['menu']['always']) {
    Horde::authenticationFailureRedirect();
}

Horde::addScriptFile('menu.js');

if ($browser->hasQuirk('scrollbar_in_way')) {
    $notification->push('correctWidthForScrollbar()', 'javascript');
}
$bodyClass = 'sidebar';
if (Util::getFormData('mozbar')) {
    $target = '_content';
    $bodyClass .= ' nomargin';
} else {
    $target = 'horde_main';
}
require HORDE_TEMPLATES . '/common-header.inc';

// Build the array so we have parents and children all lined up.
buildMenu();

// Loop through the registry and create the <div>s.
$menutext = '';    // Variable for the HTML output.
$i = 0;            // Counter for looping through the registry.
$last_group = -1;  // To track groups of menus to make <div>s.
$last_parent = 0;  // Track the last parent we used.

foreach ($registry->applications as $app => $params) {
    /* Don't show the application if it's not installed. */
    if (isset($params['fileroot']) && !is_dir($params['fileroot'])) {
        continue;
    }

    $params['name'] = _($params['name']);
    if ($params['status'] == 'active' || $params['status'] == 'heading' ||
        ($params['status'] == 'admin' && Auth::isAdmin())) {
        $i++;
        $group = isset($params['menu_parent']) ? $params['menu_parent'] : null;
        $attr  = '';

        // When we switch groups close up the <div>.
        if (($i != 1) && ($group != $last_group)) {
            $menutext .= "</table></div>\n";
        }

        // Headings have no webroot; they're just containers for other
        // menu items.
        if ($params['status'] == 'heading' || !array_key_exists('webroot', $params)) {
            $url = '#';
        } else {
            $url = Horde::url($params['webroot'] . '/' . (isset($params['initial_page']) ? $params['initial_page'] : ''));
        }
        if (!array_key_exists('menu_parent', $params)) {
            // Standalone link or container heading.
            $menutext .= '<div class="head"><table border="0" cellpadding="0" cellspacing="0" width="100%">';
            if (array_key_exists('children', $params) && $params['status'] == 'heading') {
                $link = Horde::link($url, $params['name'], 'menuitem sidebaritem', $target,
                                    "toggle('" . $app . "'); this.blur(); return false;", $params['name']);
                $image = $link . Horde::img($params['icon'], $params['name'], '', '') . '</a>';
                $text = $link . $params['name'] . Horde::img('tree/arrow-collapsed.gif', '', 'id="arrow_' . $app . '"') . '</a>';
            } else {
                $link = Horde::link($url, $params['name'], 'menuitem sidebaritem', isset($params['target']) ? $params['target'] : $target, 'this.blur()', $params['name']);
                $image = $link . Horde::img($params['icon'], $params['name'], '', '') . '</a>';
                $text = $link . $params['name'] . '</a>';
            }
        } else {
            // Subitem.
            if ($group != $last_group) {
                $menutext .= '<div class="para" id="menu_' . $group . '"><table border="0" cellpadding="0" cellspacing="0" width="100%">';
                $last_group = $group;
            }

            $link  = Horde::link($url, $params['name'], 'menuitem sidebaritem', isset($params['target']) ? $params['target'] : $target, 'this.blur()', $params['name']);
            $image = Horde::img('tree/blank.gif', $params['name'], 'width="28" height="16"');
            $attr  = ' height="20" width="28" align="center"';
            $text  = $link . Horde::img($params['icon'], $params['name'], '', '') . '</a></td><td>';
            $text .= $link . $params['name'] . '</a>';
        }

        $menutext .= '<tr><td align="center" width="28" height="20">' . $image . '</td><td' . $attr . '>' . $text . '</td></tr>';
    }
}

$menutext .= '</table></div>';

/* Add the administration link if the user is an admin. */
if (Auth::isAdmin()) {
    $menutext .= '<div class="head"><table border="0" cellpadding="0" cellspacing="0" width="100%">';
    $link = Horde::link('#', _("Administration"), 'menuitem sidebaritem', null,
                        "toggle('administration'); this.blur(); return false;", _("Administration"));
    $menutext .= '<tr><td align="center" width="28" height="20">' . $link . Horde::img('administration.gif', _("Administration")) . '</a></td><td>' . $link . _("Administration") . Horde::img('tree/arrow-collapsed.gif', '', 'id="arrow_administration"') . '</a></td></tr></table>';

    $menutext .= '<div class="para" id="menu_administration"><table border="0" cellpadding="0" cellspacing="0">';

    foreach ($registry->listApps() as $app) {
        if ($registry->hasMethod('admin_list', $app)) {
            $list = $registry->callByPackage($app, 'admin_list');
            if (!is_a($list, 'PEAR_Error')) {
                foreach ($list as $method => $vals) {
                    if ($app != 'horde') {
                        $name = $registry->getParam('name', $app);
                        if (!empty($vals['name'])) {
                            $name .= ' ' . $vals['name'];
                        }
                    } else {
                        $name = $vals['name'];
                    }
                    $img = isset($vals['icon']) ? $registry->getParam('graphics', $app) . '/' . $vals['icon'] : $registry->getParam('icon', $app);

                    $menutext .= '<tr><td align="center" width="28" height="20">' . Horde::img('tree/blank.gif', $name, 'width="16" height="16"') . '</td>';
                    $link = Horde::link(Horde::url($registry->applicationWebPath($vals['link'], $app)),
                                        $name, 'menuitem sidebaritem', $target, 'this.blur()', $name);
                    $menutext .= '<td width="28" align="center">' . $link . Horde::img($img, $name, '', '') . '</a></td><td>' . $link . $name . '</a></td></tr>';
                }
            }
        }
    }

    $menutext .= '</table></div></div>';
}

if (Auth::isAuthenticated()) {
    /* Add an options link. */
    $link = Horde::link(Horde::applicationUrl('services/prefs.php'), _("Options"), 'menuitem sidebaritem', $target,
                        null, _("Options"));
    $label = _("Options");
    $icon = 'prefs.gif';
    $menutext .= '<table border="0" cellpadding="0" cellspacing="0" width="100%"><tr><td align="center" width="28" height="20">' . $link . Horde::img($icon, $label) . '</a></td><td>' . $link . $label . '</a></td></tr></table>';

    /* Add a logout link. */
    $link = Horde::link(Auth::addLogoutParameters(Horde::applicationUrl('login.php'), AUTH_REASON_LOGOUT), _("Logout"), 'menuitem sidebaritem', $conf['menu']['always'] ? $target : '_parent',
                        null, sprintf(_("Log out of %s"), $registry->getParam('name')));
    $label = _("Logout");
    $icon = 'logout.gif';
} else {
    /* Add a login link. */
    $link = Horde::link(Horde::applicationUrl('login.php'), _("Login"), 'menuitem sidebaritem', $target,
                        null, sprintf(_("Log in to %s"), $registry->getParam('name')));
    $label = _("Login");
    $icon = 'login.gif';
}
$menutext .= '<table border="0" cellpadding="0" cellspacing="0" width="100%"><tr><td align="center" width="28" height="20">' . $link . Horde::img($icon, $label) . '</a></td><td>' . $link . $label . '</a></td></tr></table>';

require HORDE_TEMPLATES . '/horde/menu.inc';
require HORDE_TEMPLATES . '/common-footer.inc';
