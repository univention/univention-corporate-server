<?php
/**
 * $Horde: horde/services/portal/sidebar.php,v 1.4.2.20 2009-01-06 15:27:33 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Michael Pawlowsky <mikep@clearskymedia.ca>
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

/**
 * Determine if the current user can see an application.
 *
 * @param string $app         The application name.
 * @param array $params       The application's parameters.
 * @param array $hasChildren  Reference to an array to set children flags in.
 */
function canSee($app, $params, &$hasChildren)
{
    global $registry;

    static $cache = array();
    static $isAdmin;
    static $user;

    // If we have a cached value for this application, return it now.
    if (isset($cache[$app])) {
        return $cache[$app];
    }

    // Initialize variables we'll keep using in successive calls on
    // the first call.
    if (is_null($isAdmin)) {
        $isAdmin = Auth::isAdmin();
        $user = Auth::getAuth();
    }

    // Check if the current user has permisson to see this application, and if
    // the application is active. Headings are visible to everyone (but get
    // filtered out later if they have no children). Administrators always see
    // all applications except those marked 'inactive'. Anyone with SHOW
    // permissions can see an application, but READ is needed to actually use
    // the application. You can use this distinction to show applications to
    // guests that they need to log in to use. If you don't want them to see
    // apps they can't use, then don't give guests SHOW permissions to
    // anything.
    if (// Don't show applications that aren't installed, even if they're
        // configured.
        (isset($params['fileroot']) && !is_dir($params['fileroot'])) ||

        // Don't show blocks of applications that aren't installed.
        ($params['status'] == 'block' &&
         !is_dir($registry->get('fileroot', $params['app']))) ||

        // Filter out entries that are disabled, hidden or shouldn't show up
        // in the menu.
        $params['status'] == 'notoolbar' || $params['status'] == 'hidden' ||
        $params['status'] == 'inactive') {

        $cache[$app] = false;

    } elseif (// Headings can always be seen.
              ($params['status'] == 'heading') ||

              // Admins see everything that makes it to this point.
              ($isAdmin ||

               // Users who have SHOW permissions to active or block entries
               // see them.
               ($registry->hasPermission($app, PERMS_SHOW) &&
                ($params['status'] == 'active' ||
                 $params['status'] == 'block')))) {

        $cache[$app] = true;

        // Note that the parent node, if any, has children.
        if (isset($params['menu_parent'])) {
            $hasChildren[$params['menu_parent']] = true;
        }
    } else {
        // Catch anything that fell through, and don't show it.
        $cache[$app] = false;
    }

    return $cache[$app];
}

/**
 * Builds the menu structure depending on application permissions.
 */
function buildMenu()
{
    global $conf, $registry;

    $apps = array();
    $children = array();
    foreach ($registry->applications as $app => $params) {
        if (canSee($app, $params, $children)) {
            $apps[$app] = $params;
        }
    }

    $menu = array();
    foreach ($apps as $app => $params) {
        // Filter out all headings without children.
        if ($params['status'] == 'heading' && empty($children[$app])) {
            continue;
        }

        $menu[$app] = $params;
    }

    // Add the administration menu if the user is an admin.
    if (Auth::isAdmin()) {
        $menu['administration'] = array('name' => _("Administration"),
                                        'icon' => $registry->getImageDir() . '/administration.png',
                                        'status' => 'heading');

        $list = $registry->callByPackage('horde', 'admin_list');
        if (!is_a($list, 'PEAR_Error')) {
            foreach ($list as $method => $vals) {
                $name = Horde::stripAccessKey($vals['name']);
                $icon = isset($vals['icon']) ? $registry->getImageDir() . '/' . $vals['icon'] : $registry->get('icon');

                $menu['administration_' . $method] = array(
                    'name' => $name,
                    'icon' => $icon,
                    'status' => 'active',
                    'menu_parent' => 'administration',
                    'url' => Horde::url($registry->applicationWebPath($vals['link'])),
                    );
            }
        }
    }

    if (Horde::showService('options') &&
        $conf['prefs']['driver'] != '' && $conf['prefs']['driver'] != 'none') {
        $menu['options'] = array('name' => _("Options"),
                                 'status' => 'active',
                                 'icon' => $registry->getImageDir() . '/prefs.png');

        /* Get a list of configurable applications. */
        $prefs_apps = array();
        foreach ($registry->applications as $application => $params) {
            if ($params['status'] == 'heading' ||
                $params['status'] == 'block' ||
                !file_exists($registry->get('fileroot', $application) . '/config/prefs.php')) {
                continue;
            }

            /* Check if the current user has permission to see this
             * application, and if the application is active.
             * Administrators always see all applications. */
            if ((Auth::isAdmin() && $params['status'] != 'inactive') ||
                ($registry->hasPermission($application) &&
                 ($params['status'] == 'active'))) {
                $prefs_apps[$application] = _($params['name']);
            }
        }

        if (!empty($prefs_apps['horde'])) {
            $menu['options_' . 'horde'] = array('name' => _("Global Options"),
                                                'status' => 'active',
                                                'menu_parent' => 'options',
                                                'icon' => $registry->get('icon', 'horde'),
                                                'url' => Horde::applicationUrl('services/prefs.php?app=horde'));
            unset($prefs_apps['horde']);
        }

        asort($prefs_apps);
        foreach ($prefs_apps as $app => $name) {
            $menu['options_' . $app] = array('name' => $name,
                                             'status' => 'active',
                                             'menu_parent' => 'options',
                                             'icon' => $registry->get('icon', $app),
                                             'url' => Horde::applicationUrl('services/prefs.php?app=' . $app));
        }
    }

    if (Auth::isAuthenticated()) {
        $menu['logout'] = array('name' => _("Log out"),
                                'status' => 'active',
                                'icon' => $registry->getImageDir() . '/logout.png',
                                'url' => Horde::getServiceLink('logout', 'horde', true),
                                'target' => '_parent');
    } else {
        $menu['login'] = array('name' => _("Log in"),
                               'status' => 'active',
                               'icon' => $registry->getImageDir() . '/login.png',
                               'url' => Horde::getServiceLink('login', 'horde', true, false));
    }

    return $menu;
}

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__) . '/../..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Tree.php';
require_once 'Horde/Block.php';
require_once 'Horde/Block/Collection.php';

if (!Auth::getAuth() && !$conf['menu']['always']) {
    Horde::authenticationFailureRedirect();
}

$is_mozbar = (bool)Util::getFormData('mozbar');

// Set up the tree.
$tree = &Horde_Tree::singleton('horde_menu', 'javascript');
$tree->setOption(array('target' => $is_mozbar ? '_content' : 'horde_main'));

$menu = buildMenu();
foreach ($menu as $app => $params) {
    if ($params['status'] == 'block') {
        if ($registry->get('status', $params['app']) == 'inactive') {
            continue;
        }
        $block = &Horde_Block_Collection::getBlock($params['app'], $params['blockname']);
        if (is_a($block, 'PEAR_Error')) {
            Horde::logMessage($block, __FILE__, __LINE__, PEAR_LOG_ERR);
            continue;
        }
        $block->buildTree($tree, 0,
                          isset($params['menu_parent']) ? $params['menu_parent'] : null);
    } else {
        // Need to run the name through gettext since the user's
        // locale may not have been loaded when registry.php was
        // parsed.
        $name = _($params['name']);

        // Headings have no webroot; they're just containers for other
        // menu items.
        if (isset($params['url'])) {
            $url = $params['url'];
        } elseif ($params['status'] == 'heading' || !isset($params['webroot'])) {
            $url = null;
        } else {
            $url = Horde::url($params['webroot'] . '/' . (isset($params['initial_page']) ? $params['initial_page'] : ''));
        }

        $node_params = array('url' => $url,
                             'target' => isset($params['target']) ? $params['target'] : null,
                             'icon' => isset($params['icon']) ? $params['icon'] : $registry->get('icon', $app),
                             'icondir' => '',
                             );
        $tree->addNode($app, !empty($params['menu_parent']) ? $params['menu_parent'] : null, $name, 0, false, $node_params);
    }
}

// If we're serving a request to the JS update client, just render the
// updated node javascript.
if (Util::getFormData('httpclient')) {
    header('Content-Type: text/javascript; charset=' . NLS::getCharset());
    echo $tree->renderNodeDefinitions();
    exit;
}

$rtl = isset($nls['rtl'][$language]);
$htmlId = 'sidebar-frame';
$bodyClass = 'sidebar';
if ($browser->hasQuirk('scrollbar_in_way')) {
    $bodyClass .= ' scrollbar-quirk';
}
Horde::addScriptFile('prototype.js', 'horde', true);
Horde::addScriptFile('sidebar.js', 'horde', true);
require HORDE_TEMPLATES . '/common-header.inc';
require HORDE_TEMPLATES . '/portal/sidebar.inc';
