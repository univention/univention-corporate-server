<?php
/**
 * The Menu:: class provides standardized methods for creating menus in
 * Horde applications.
 *
 * $Horde: framework/Menu/Menu.php,v 1.67 2004/04/17 14:06:27 jan Exp $
 *
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 * Copyright 1999-2004 Jon Parise <jon@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jon Parise <jon@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_Framework
 */
class Menu {

    /**
     * Show help option?
     *
     * @var boolean $_with_help
     */
    var $_with_help;

    /**
     * Show login option?
     *
     * @var boolean $_with_login
     */
    var $_with_login;

    /**
     * Show preferences option?
     *
     * @var boolean $_with_prefs
     */
    var $_with_prefs;

    /**
     * The location of the menufile.
     *
     * @var boolean $_menufile
     */
    var $_menufile;

    /**
     * Constructor
     *
     * @access public
     */
    function Menu($with_help = true, $with_login = null, $with_prefs = true)
    {
        /* Default to false if help turned off or no javascript support. */
        if (!empty($GLOBALS['conf']['user']['online_help']) &&
            $GLOBALS['browser']->hasFeature('javascript')) {
            $with_help = false;
        }
        $this->_with_help = $with_help;
        $this->_with_prefs = $with_prefs;

        /* If no setting specified for login button, default to true if no
           Horde frameset and false if there is a Horde frameset. */
        $this->_with_login = (is_null($with_login)) ? !$GLOBALS['conf']['menu']['display'] : $with_login;

        /* Location of the menufile. */
        $this->_menufile = $GLOBALS['registry']->getParam('fileroot') . '/config/menu.php';
    }

    /**
     * Generates the HTML for an item on the menu bar.
     *
     * @param string $url                  String containing the value for
     *                                     the hyperlink.
     * @param string $text                 String containing the label for
     *                                     this menu item.
     * @param optional string $icon        String containing the filename of
     *                                     the image icon to display for this
     *                                     menu item.
     * @param optional string $icon_path   If the icon lives in a non-default
     *                                     directory, where is it?
     * @param optional string $target      If the link needs to open in
     *                                     another frame or window, what is
     *                                     its name?
     * @param optional string $onclick     Onclick javascript, if desired.
     * @param optional string $cell_class  CSS class for the table cell.
     * @param optional string $link_class  CSS class for the item link.
     *
     * @return string  String containing the HTML to display this menu item.
     */
    function createItem($url, $text, $icon = '', $icon_path = null,
                        $target = '', $onclick = null, $cell_class = null,
                        $link_class = 'menuitem')
    {
        global $conf, $prefs;

        if (is_null($cell_class)) {
            /* Try to match the item's path against the current script
             * filename as well as other possible URLs to this script. */
            if (Menu::isSelected($url)) {
                $cell_class = 'menuselected';
            }
        }
        if ($cell_class === '__noselection') {
            $cell_class = null;
        }

        $accesskey = Horde::getAccessKey($text);
        $plaintext = preg_replace('/_([A-Za-z])/', '\\1', $text);
        $menu_view = $prefs->getValue('menu_view');

        $html = '<td align="center" nowrap="nowrap" style="cursor:pointer;" valign="';
        $html .= (($menu_view == 'icon') ? 'middle' : 'bottom') . '"';

        /* Handle javascript URLs. */
        if (strstr($url, 'javascript:')) {
            $html .= ' onclick="' . str_replace('javascript:', '', $url) . '"';
        } elseif (!$url) {
            if ($onclick) {
                $html .= ' onclick="' . $onclick . '";';
            }
        } else {
            $html .= ' onclick="document.location=\'' . addslashes($url) . '\';"';
        }
        $html .= (!empty($cell_class)) ? " class=\"$cell_class\">" : '>';

        if (strstr($url, 'javascript:')) {
            if (!strstr($onclick, 'return false;')) {
                $onclick .= 'return false;';
            }
            $html .= Horde::link('', $plaintext, $link_class, $target, $onclick, '', $accesskey);
        } else {
            $html .= Horde::link($url, $plaintext, $link_class, $target, $onclick, '', $accesskey);
        }

        if (!empty($icon) &&
            (($menu_view == 'icon') || ($menu_view == 'both'))) {
            $html .= Horde::img($icon, $plaintext, ($menu_view == 'icon') ? 'hspace="5" vspace="5"' : '', $icon_path);
            if ($menu_view == 'both') {
                $html .= '<br />';
            }
        }

        if ($menu_view != 'icon') {
            $html .= Horde::highlightAccessKey($text, $accesskey);
        }

        $html .= "</a>&nbsp;</td>\n";

        return $html;
    }

    /**
     * Creates a menu string from a custom menu item.  Custom menu items
     * can either define a new menu item or a menu separate (spacer).
     *
     * A custom menu item consists of a hash with the following properties:
     *
     *  'url'       The URL value for the menu item.
     *  'text'      The text to accompany the menu item.
     *  'icon'      The filename of an icon to use for the menu item.
     *  'icon_path' The path to the icon if it doesn't exist in the graphics/
     *              directory.
     *  'target'    The "target" of the link (e.g. '_top', '_blank').
     *  'onclick'   Any onclick javascript.
     *
     * A menu separator item is simply a string set to 'separator'.
     *
     * @param mixed $item  Mixed parameter containing the custom menu item.
     *
     * @return string  The resulting HTML to display the menu item.
     */
    function customItem($item)
    {
        $text = '';

        if (is_array($item)) {
            $text = Menu::createItem($item['url'], $item['text'],
                                     @$item['icon'], @$item['icon_path'],
                                     @$item['target'], @$item['onclick']);
        } else {
            if (strcasecmp($item, 'separator') == 0) {
                $text = '<td>&nbsp;</td>';
            }
        }

        return $text;
    }

    /**
     * Print out any site-specific links for the current application
     * that have been defined in application/config/menu.php.
     */
    function siteLinks()
    {
        $menufile = $GLOBALS['registry']->getParam('fileroot') . '/config/menu.php';
        if (@is_readable($menufile)) {
            include_once $menufile;
            if (isset($_menu) && is_array($_menu)) {
                foreach ($_menu as $item) {
                    echo Menu::customItem($item);
                }
            }
        }
    }

    /**
     * Print out any links to other Horde applications that are
     * defined in $conf['menu']['apps'].
     */
    function appLinks()
    {
        global $conf, $registry;
        if (isset($conf['menu']['apps']) && is_array($conf['menu']['apps'])) {
            foreach ($conf['menu']['apps'] as $app) {
                if ($registry->getParam('status', $app) != 'inactive') {
                    $url = $registry->getInitialPage($app);
                    if (!is_a($url, 'PEAR_Error')) {
                        echo Menu::createItem(Horde::url($url), $registry->getParam('name', $app), $registry->getParam('icon', $app), '');
                    }
                }
            }
        }
    }

    /**
     * Used in Horde_Template situations to return an array of menu elements
     * for a page.
     *
     * @access public
     *
     * @return array  An array of menu elements.
     */
    function getMenu()
    {
        /* Cache the menu generation. */
        static $menu = array();

        /* Return the menu array if already generated. */
        if (!empty($menu)) {
            return $menu;
        }

        global $conf, $registry, $prefs;

        $graphics = $registry->getParam('graphics', 'horde');

        /* Get the menu array from the current app. */
        $app = $registry->getApp();
        $function = 'get' . $app . 'Menu';
        if (is_callable(array($app, $function))) {
            $menu = call_user_func(array($app, $function));
        }
 
        /* Add settings item. */
        if ($this->_with_prefs &&
            ($conf['prefs']['driver'] != '') &&
            ($conf['prefs']['driver'] != 'none')) {
            $url = Horde::url($registry->getParam('webroot', 'horde') . '/services/prefs.php');
            $url = Util::addParameter($url, 'app', $app);
            $menu[] = array('url' => $url, 'text' => _("Options"), 'icon' => 'prefs.gif', 'icon_path' => $graphics);
        }

        /* Add any app menu items. */
        $this->addAppLinks($menu);

        /* Add any custom menu items. */
        $this->addSiteLinks($menu);

        /* Add help item. */
        require_once 'Horde/Help.php';
        if ($help_link = Help::listLink($app)) {
            Help::javascript();
            $menu[] = array('url' => $help_link, 'text' => _("Help"), 'icon' => 'manual.gif', 'icon_path' => $graphics);
        }

        /* Login/Logout. */
        if (Auth::getAuth() && $this->_with_login) {
            $url = Horde::url($registry->getParam('webroot', 'horde') . '/login.php');
            $url = Auth::addLogoutParameters($url, AUTH_REASON_LOGOUT);
            $menu[] = array('url' => $url, 'text' => _("Logout"), 'icon' => 'logout.gif', 'icon_path' => $graphics);
        } elseif ($this->_with_login) {
            $url = Auth::getLoginScreen('', Horde::selfUrl());
            $menu[] = array('url' => $url, 'text' => _("Login"), 'icon' => 'login.gif', 'icon_path' => $graphics);
        }

        /* Loop through the menu and set up necessary elements. */
        $menu_view = $prefs->getValue('menu_view');
        foreach ($menu as $k => $item) {
            /* Access keys. */
            $item['accesskey'] = Horde::getAccessKey($item['text']);
            $item['text_accesskey'] = Horde::highlightAccessKey($item['text'], $item['accesskey']);

            /* Cell class and selected indication. */
            if (Menu::isSelected($item['url']) &&
                (!isset($item['cell_class']) ||
                 ($item['cell_class'] != '__noselection'))) {
                $item['status'] = 'menuselected';
            } else {
                $item['status'] = '';
            }
            if (isset($item['cell_class'])) {
                unset($item['cell_class']);
            }
            $item['onclick'] = (isset($item['onclick'])) ? $item['onclick'] : '';
            $item['target'] = (isset($item['target'])) ? $item['target'] : '';

            /* The actual button of the menu. */
            $item['button'] = '';
            if (!empty($item['icon']) &&
                (($menu_view == 'icon') || ($menu_view == 'both'))) {
                /* Icon available and requested in prefs, so set up icon. */
                $item['button'] .= Horde::img($item['icon'], $item['text'], ($menu_view == 'icon') ? 'hspace="5" vspace="5"' : '', $item['icon_path']);
                if ($menu_view == 'both') {
                    $item['button'] .= '<br />';
                }
            }

            /* If no icon-only preference then set text. */
            if ($menu_view != 'icon') {
                $item['button'] .= Horde::highlightAccessKey($item['text'], $item['accesskey']);
            }

            $menu[$k] = $item;
        }

        return $menu;
    }

    /**
     * Any links to other Horde applications defined in an application's
     * config file by the $conf['menu']['apps'] array are added to the menu
     * array for use in Horde_Template pages.
     *
     * @access public
     *
     * @param array &$menu  TODO
     */
    function addAppLinks(&$menu)
    {
        global $conf, $registry;

        if (isset($conf['menu']['apps']) && is_array($conf['menu']['apps'])) {
            foreach ($conf['menu']['apps'] as $app) {
                if ($registry->getParam('status', $app) != 'inactive') {
                    $url = $registry->getInitialPage($app);
                    if (!is_a($url, 'PEAR_Error')) {
                        $menu[] = array('url' => $url, 'text' => $registry->getParam('name', $app), 'icon' => $registry->getParam('icon', $app), 'icon_path' => '');
                    }
                }
            }
        }
    }

    /**
     * Any other links usually found in the /config/menu.php file that need
     * to be included in the menu as handled by Horde_Template are done here.
     *
     * @access public
     *
     * @param array &$menu  TODO
     */
    function addSiteLinks(&$menu)
    {
        if (@is_readable($this->_menufile)) {
            include $this->_menufile;
            if (isset($_menu) && is_array($_menu)) {
                foreach ($_menu as $menuitem) {
                    $menu[] = $menuitem;
                }
            }
        }
    }

    /**
     * Checks to see if the current url matches the given url.
     *
     * @access public
     *
     * @return bool  True or false whether given url is the current one.
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
