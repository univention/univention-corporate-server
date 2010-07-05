<?php

define('HORDE_MENU_POS_LAST', 999);

define('HORDE_MENU_MASK_NONE',     0);
define('HORDE_MENU_MASK_HELP',     1);
define('HORDE_MENU_MASK_LOGIN',    2);
define('HORDE_MENU_MASK_PREFS',    4);
define('HORDE_MENU_MASK_PROBLEM',  8);
define('HORDE_MENU_MASK_ALL',     15);

/**
 * The Menu:: class provides standardized methods for creating menus in
 * Horde applications.
 *
 * $Horde: framework/Horde/Horde/Menu.php,v 1.35.2.17 2009-01-06 15:23:10 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jon Parise <jon@horde.org>
 * @since   Horde 1.3
 * @package Horde_Framework
 */
class Menu {

    /**
     * Menu array.
     *
     * @var array
     */
    var $_menu = array();

    /**
     * Mask defining what general Horde links are shown in this Menu.
     *
     * @var integer
     */
    var $_mask;

    /**
     * Constructor
     */
    function Menu($mask = HORDE_MENU_MASK_ALL)
    {
        /* Menuitem mask. */
        $this->_mask = $mask;

        /* Location of the menufile. */
        $this->_menufile = $GLOBALS['registry']->get('fileroot') . '/config/menu.php';
    }

    /**
     * Add an item to the menu array.
     *
     * @param string $url        String containing the value for the hyperlink.
     * @param string $text       String containing the label for this menu
     *                           item.
     * @param string $icon       String containing the filename of the image
     *                           icon to display for this menu item.
     * @param string $icon_path  If the icon lives in a non-default directory,
     *                           where is it?
     * @param string $target     If the link needs to open in another frame or
     *                           window, what is its name?
     * @param string $onclick    Onclick javascript, if desired.
     * @param string $class      CSS class for the menu item.
     *
     * @return integer  The id (NOT guaranteed to be an array index) of the
     *                  item just added to the menu.
     */
    function add($url, $text, $icon = '', $icon_path = null,
                 $target = '', $onclick = null, $class = null)
    {
        $pos = count($this->_menu);
        if (!$pos || ($pos - 1 != max(array_keys($this->_menu)))) {
            $pos = count($this->_menu);
        }

        $this->_menu[$pos] =
            array(
                'url' => $url,
                'text' => $text,
                'icon' => $icon,
                'icon_path' => $icon_path,
                'target' => $target,
                'onclick' => $onclick,
                'class' => $class
            );

        return $pos;
    }

    /**
     * Add an item to the menu array.
     *
     * @param string $url        String containing the value for the hyperlink.
     * @param string $text       String containing the label for this menu
     *                           item.
     * @param string $icon       String containing the filename of the image
     *                           icon to display for this menu item.
     * @param string $icon_path  If the icon lives in a non-default directory,
     *                           where is it?
     * @param string $target     If the link needs to open in another frame or
     *                           window, what is its name?
     * @param string $onclick    Onclick javascript, if desired.
     * @param string $class      CSS class for the menu item.
     *
     * @return integer  The id (NOT guaranteed to be an array index) of the item
     *                  just added to the menu.
     */
    function addArray($item)
    {
        $pos = count($this->_menu);
        if (!$pos || ($pos - 1 != max(array_keys($this->_menu)))) {
            $pos = count($this->_menu);
        }

        $this->_menu[$pos] = $item;

        return $pos;
    }

    function setPosition($id, $pos)
    {
        if (!isset($this->_menu[$id]) || isset($this->_menu[$pos])) {
            return false;
        }

        $item = $this->_menu[$id];
        unset($this->_menu[$id]);
        $this->_menu[$pos] = $item;

        return true;
    }

    /**
     * Return the unordered list representing the list of menu items. Styling
     * is done through CSS.
     *
     * @return string  An unordered list of menu elements that can be entirely
     *                 styled with CSS.
     */
    function render()
    {
        global $conf, $registry, $prefs;

        $graphics = $registry->getImageDir('horde');
        $app = $registry->getApp();

        if ($this->_mask !== HORDE_MENU_MASK_NONE) {
            /* Add any custom menu items. */
            $this->addSiteLinks();

            /* Add any app menu items. */
            $this->addAppLinks();
        }

        /* Add settings link. */
        if ($this->_mask & HORDE_MENU_MASK_PREFS && $url = Horde::getServiceLink('options', $app)) {
            $this->add($url, _("_Options"), 'prefs.png', $graphics);
        }

        /* Add problem link. */
        if ($this->_mask & HORDE_MENU_MASK_PROBLEM && $problem_link = Horde::getServiceLink('problem', $app)) {
            $this->add($problem_link, _("Problem"), 'problem.png', $graphics);
        }

        /* Add help link. */
        require_once 'Horde/Help.php';
        if ($this->_mask & HORDE_MENU_MASK_HELP && $help_link = Horde::getServiceLink('help', $app)) {
            $this->add($help_link, _("Help"), 'help_index.png', $graphics, 'help', 'popup(this.href); return false;', 'helplink');
        }

        /* Login/Logout. */
        if ($this->_mask & HORDE_MENU_MASK_LOGIN) {
            /* If the sidebar isn't always shown, but is sometimes
             * shown, then logout links should be to the parent
             * frame. */
            $auth_target = null;
            if ($conf['menu']['always'] || $prefs->getValue('show_sidebar')) {
                $auth_target = '_parent';
            }

            if (Auth::getAuth()) {
                if ($logout_link = Horde::getServiceLink('logout', $app, !$prefs->getValue('show_sidebar'))) {
                    $this->add($logout_link, _("_Log out"), 'logout.png', $graphics, $auth_target, null, '__noselection');
                }
            } else {
                if ($login_link = Horde::getServiceLink('login', $app)) {
                    $this->add($login_link, _("_Log in"), 'login.png', $graphics, $auth_target, null, '__noselection');
                }
            }
        }

        /* No need to return an empty list if there are no menu
         * items. */
        if (!count($this->_menu)) {
            return '';
        }

        /* Sort to match explicitly set positions. */
        ksort($this->_menu);
        if (!empty($GLOBALS['nls']['rtl'][$GLOBALS['language']]))  {
            $this->_menu = array_reverse($this->_menu) ;
        }

        $menu_view = $prefs->getValue('menu_view');
        $output = '<ul>';
        foreach ($this->_menu as $m) {
            /* Check for separators. */
            if ($m == 'separator') {
                $output .= "\n<li class=\"separator\">&nbsp;</li>";
                continue;
            }

            /* Item class and selected indication. */
            if (!isset($m['class'])) {
                /* Try to match the item's path against the current
                 * script filename as well as other possible URLs to
                 * this script. */
                if (Menu::isSelected($m['url'])) {
                    $m['class'] = 'current';
                }
            } elseif ($m['class'] === '__noselection') {
                unset($m['class']);
            }

            /* Icon. */
            $icon = '';
            if ($menu_view == 'icon' || $menu_view == 'both') {
                if (!isset($m['icon_path'])) {
                    $m['icon_path'] = null;
                }
                $icon = Horde::img($m['icon'], Horde::stripAccessKey($m['text']), '', $m['icon_path']) . '<br />';
            }

            /* Link. */
            $accesskey = Horde::getAccessKey($m['text']);
            $link = Horde::link($m['url'], ($menu_view == 'icon') ? Horde::stripAccessKey($m['text']) : '',
                                isset($m['class']) ? $m['class'] : '',
                                isset($m['target']) ? $m['target'] : '',
                                isset($m['onclick']) ? $m['onclick'] : '',
                                '', $accesskey);

            $output .= sprintf("\n<li>%s%s%s</a></li>",
                               $link, $icon, ($menu_view != 'icon') ? Horde::highlightAccessKey($m['text'], $accesskey) : '');
        }

        return $output . '</ul>';
    }

    /**
     * Any links to other Horde applications defined in an application's config
     * file by the $conf['menu']['apps'] array are added to the menu array.
     */
    function addAppLinks()
    {
        global $conf, $registry;

        if (isset($conf['menu']['apps']) && is_array($conf['menu']['apps'])) {
            foreach ($conf['menu']['apps'] as $app) {
                if ($registry->get('status', $app) != 'inactive' && $registry->hasPermission($app, PERMS_SHOW)) {
                    $url = $registry->getInitialPage($app);
                    if (!is_a($url, 'PEAR_Error')) {
                        $this->add(Horde::url($url), $registry->get('name', $app), $registry->get('icon', $app), '');
                    }
                }
            }
        }
    }

    /**
     * Add any other links found in $this->_menufile to be included in the
     * menu.
     */
    function addSiteLinks()
    {
        if (is_readable($this->_menufile)) {
            include $this->_menufile;
            if (isset($_menu) && is_array($_menu)) {
                foreach ($_menu as $menuitem) {
                    $this->addArray($menuitem);
                }
            }
        }
    }

    /**
     * Checks to see if the current url matches the given url.
     *
     * @return boolean  Whether the given URL is the current location.
     */
    function isSelected($url)
    {
        $server_url = parse_url($_SERVER['PHP_SELF']);
        $check_url = parse_url($url);

        /* Try to match the item's path against the current script
           filename as well as other possible URLs to this script. */
        if (isset($check_url['path']) &&
            (($check_url['path'] == $server_url['path']) ||
             ($check_url['path'] . 'index.php' == $server_url['path']) ||
             ($check_url['path'] . '/index.php' == $server_url['path']))) {
            return true;
        }

        return false;
    }

}
