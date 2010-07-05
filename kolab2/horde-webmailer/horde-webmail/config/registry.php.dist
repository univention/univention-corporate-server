<?php
/**
 * registry.php -- Horde application registry.
 *
 * $Horde: horde/config/registry.php.dist,v 1.255.2.27 2009-07-24 08:58:06 jan Exp $
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
 * fileroot      string   The base filesystem path for the module's files.
 * webroot       string   The base URI for the module.
 * jsuri         string   The base URI for static javascript files.
 * jsfs          string   The base filesystem path for static javascript files.
 * themesuri     string   The base URI for the themes. This can be used to
 *                        serve all icons and style sheets from a separate
 *                        server.
 * themesfs      string   The base file system directory for the themes.
 * icon          string   The URI for an icon to show in menus for the module.
 *                        Setting this will override the default theme-based
 *                        logic in the code.
 * name          string   The name used in menus and descriptions for a module
 * status        string   'inactive', 'hidden', 'notoolbar', 'heading',
 *                        'block', 'admin', or 'active'.
 * provides      string   Service types the module provides.
 * initial_page  string   The initial (default) page (filename) for the module.
 * templates     string   The filesystem path to the templates directory.
 * menu_parent   string   The name of the 'heading' group that this app should
 *                        show up under.
 * target        string   The (optional) target frame for the link.
 * url           string   The (optional) URL of 'heading' entries.
 */

// We try to automatically determine the proper webroot for Horde here. This
// still assumes that applications live under horde/. If this results in
// incorrect results for you, simply change the 'webroot' setting in the
// 'horde' stanza below.

$this->applications['horde'] = array(
    'fileroot' => dirname(__FILE__) . '/..',
    'webroot' => _detect_webroot(),
    'initial_page' => 'login.php',
    'name' => _("Horde"),
    'status' => 'active',
    'templates' => dirname(__FILE__) . '/../templates',
    'provides' => 'horde',
);

$this->applications['mimp'] = array(
    'fileroot' => dirname(__FILE__) . '/../mimp',
    'webroot' => $this->applications['horde']['webroot'] . '/mimp',
    'name' => _("Mobile Mail"),
    'status' => 'notoolbar',
);

$this->applications['dimp'] = array(
    'fileroot' => dirname(__FILE__) . '/../dimp',
    'webroot' => $this->applications['horde']['webroot'] . '/dimp',
    'name' => _("Dynamic Mail"),
    'status' => 'notoolbar',
    'target' => '_parent',
);

$this->applications['imp'] = array(
    'fileroot' => dirname(__FILE__) . '/../imp',
    'webroot' => $this->applications['horde']['webroot'] . '/imp',
    'name' => _("Mail"),
    'status' => 'active',
    'provides' => array('mail', 'contacts/favouriteRecipients')
);

$this->applications['ingo'] = array(
    'fileroot' => dirname(__FILE__) . '/../ingo',
    'webroot' => $this->applications['horde']['webroot'] . '/ingo',
    'name' => _("Filters"),
    'status' => 'active',
    'provides' => array('filter', 'mail/blacklistFrom', 'mail/showBlacklist', 'mail/whitelistFrom', 'mail/showWhitelist', 'mail/applyFilters', 'mail/canApplyFilters', 'mail/showFilters'),
    'menu_parent' => 'imp'
);

$this->applications['sam'] = array(
    'fileroot' => dirname(__FILE__) . '/../sam',
    'webroot' => $this->applications['horde']['webroot'] . '/sam',
    'name' => _("Spam"),
    'status' => 'active',
    // Uncomment this line if you want Sam to handle the blacklist filter
    // instead of Ingo:
    // 'provides' => array('mail/blacklistFrom', 'mail/showBlacklist', 'mail/whitelistFrom', 'mail/showWhitelist'),
    'menu_parent' => 'imp'
);

$this->applications['forwards'] = array(
    'fileroot' => dirname(__FILE__) . '/../forwards',
    'webroot' => $this->applications['horde']['webroot'] . '/forwards',
    'name' => _("Forwards"),
    'status' => 'active',
    'provides' => 'forwards',
    'menu_parent' => 'imp',
);

$this->applications['vacation'] = array(
    'fileroot' => dirname(__FILE__) . '/../vacation',
    'webroot' => $this->applications['horde']['webroot'] . '/vacation',
    'name' => _("Vacation"),
    'status' => 'active',
    'provides' => 'vacation',
    'menu_parent' => 'imp'
);

$this->applications['imp-folders'] = array(
    'status' => 'block',
    'app' => 'imp',
    'blockname' => 'tree_folders',
    'menu_parent' => 'imp',
);

$this->applications['organizing'] = array(
    'name' => _("Organizing"),
    'status' => 'heading',
);

$this->applications['turba'] = array(
    'fileroot' => dirname(__FILE__) . '/../turba',
    'webroot' => $this->applications['horde']['webroot'] . '/turba',
    'name' => _("Address Book"),
    'status' => 'active',
    'provides' => array('contacts', 'clients/getClientSource', 'clients/clientFields', 'clients/getClient', 'clients/getClients', 'clients/addClient', 'clients/updateClient', 'clients/deleteClient', 'clients/searchClients'),
    'menu_parent' => 'organizing'
);

$this->applications['turba-menu'] = array(
    'status' => 'block',
    'app' => 'turba',
    'blockname' => 'tree_menu',
    'menu_parent' => 'turba',
);

$this->applications['kronolith'] = array(
    'fileroot' => dirname(__FILE__) . '/../kronolith',
    'webroot' => $this->applications['horde']['webroot'] . '/kronolith',
    'name' => _("Calendar"),
    'status' => 'active',
    'provides' => 'calendar',
    'menu_parent' => 'organizing'
);

$this->applications['kronolith-alarms'] = array(
    'status' => 'block',
    'app' => 'kronolith',
    'blockname' => 'tree_alarms',
    'menu_parent' => 'kronolith',
);

$this->applications['kronolith-menu'] = array(
    'status' => 'block',
    'app' => 'kronolith',
    'blockname' => 'tree_menu',
    'menu_parent' => 'kronolith',
);

$this->applications['nag'] = array(
    'fileroot' => dirname(__FILE__) . '/../nag',
    'webroot' => $this->applications['horde']['webroot'] . '/nag',
    'name' => _("Tasks"),
    'status' => 'active',
    'provides' => 'tasks',
    'menu_parent' => 'organizing'
);

$this->applications['nag-alarms'] = array(
    'status' => 'block',
    'app' => 'nag',
    'blockname' => 'tree_alarms',
    'menu_parent' => 'nag',
);

$this->applications['nag-menu'] = array(
    'status' => 'block',
    'app' => 'nag',
    'blockname' => 'tree_menu',
    'menu_parent' => 'nag',
);

$this->applications['mnemo'] = array(
    'fileroot' => dirname(__FILE__) . '/../mnemo',
    'webroot' => $this->applications['horde']['webroot'] . '/mnemo',
    'name' => _("Notes"),
    'status' => 'active',
    'provides' => 'notes',
    'menu_parent' => 'organizing'
);

$this->applications['mnemo-menu'] = array(
    'status' => 'block',
    'app' => 'mnemo',
    'blockname' => 'tree_menu',
    'menu_parent' => 'mnemo',
);

$this->applications['genie'] = array(
    'fileroot' => dirname(__FILE__) . '/../genie',
    'webroot' => $this->applications['horde']['webroot'] . '/genie',
    'name' => _("Wishlist"),
    'status' => 'active',
    'provides' => 'wishlist',
    'menu_parent' => 'organizing'
);

$this->applications['trean'] = array(
    'fileroot' => dirname(__FILE__) . '/../trean',
    'webroot' => $this->applications['horde']['webroot'] . '/trean',
    'name' => _("Bookmarks"),
    'status' => 'active',
    'provides' => 'bookmarks',
    'menu_parent' => 'organizing'
);

$this->applications['trean-menu'] = array(
    'status' => 'block',
    'app' => 'trean',
    'blockname' => 'tree_menu',
    'menu_parent' => 'trean',
);

$this->applications['devel'] = array(
    'name' => _("Development"),
    'status' => 'heading',
);

$this->applications['chora'] = array(
    'fileroot' => dirname(__FILE__) . '/../chora',
    'webroot' => $this->applications['horde']['webroot'] . '/chora',
    'name' => _("Version Control"),
    'status' => 'active',
    'menu_parent' => 'devel'
);

$this->applications['chora-menu'] = array(
    'status' => 'block',
    'app' => 'chora',
    'blockname' => 'tree_menu',
    'menu_parent' => 'chora',
);

$this->applications['whups'] = array(
    'fileroot' => dirname(__FILE__) . '/../whups',
    'webroot' => $this->applications['horde']['webroot'] . '/whups',
    'name' => _("Tickets"),
    'status' => 'active',
    'provides' => 'tickets',
    'menu_parent' => 'devel',
);

$this->applications['whups-menu'] = array(
    'status' => 'block',
    'app' => 'whups',
    'blockname' => 'tree_menu',
    'menu_parent' => 'whups',
);

$this->applications['luxor'] = array(
    'fileroot' => dirname(__FILE__) . '/../luxor',
    'webroot' => $this->applications['horde']['webroot'] . '/luxor',
    'name' => _("X-Ref"),
    'status' => 'active',
    'menu_parent' => 'devel'
);

$this->applications['info'] = array(
    'name' => _("Information"),
    'status' => 'heading',
);

$this->applications['klutz'] = array(
    'fileroot' => dirname(__FILE__) . '/../klutz',
    'webroot' => $this->applications['horde']['webroot'] . '/klutz',
    'name' => _("Comics"),
    'status' => 'active',
    'provides' => 'comics',
    'menu_parent' => 'info'
);

$this->applications['mottle'] = array(
    'fileroot' => dirname(__FILE__) . '/../mottle',
    'webroot' => $this->applications['horde']['webroot'] . '/mottle',
    'name' => _("MOTD"),
    'status' => 'active',
    'menu_parent' => 'info'
);

$this->applications['jonah'] = array(
    'fileroot' => dirname(__FILE__) . '/../jonah',
    'webroot' => $this->applications['horde']['webroot'] . '/jonah',
    'name' => _("News"),
    'status' => 'active',
    'provides' => 'news',
    'menu_parent' => 'info'
);

$this->applications['jonah-menu'] = array(
    'status' => 'block',
    'app' => 'jonah',
    'blockname' => 'tree_menu',
    'menu_parent' => 'jonah',
);

$this->applications['goops'] = array(
    'fileroot' => dirname(__FILE__) . '/../goops',
    'webroot' => $this->applications['horde']['webroot'] . '/goops',
    'name' => _("Search Engines"),
    'status' => 'active',
    'menu_parent' => 'info'
);

$this->applications['office'] = array(
    'name' => _("Office"),
    'status' => 'heading',
);

$this->applications['juno'] = array(
    'fileroot' => dirname(__FILE__) . '/../juno',
    'webroot' => $this->applications['horde']['webroot'] . '/juno',
    'name' => _("Accounting"),
    'status' => 'active',
    'menu_parent' => 'office'
);

$this->applications['midas'] = array(
    'fileroot' => dirname(__FILE__) . '/../midas',
    'webroot' => $this->applications['horde']['webroot'] . '/midas',
    'name' => _("Ads"),
    'status' => 'active',
    'menu_parent' => 'office'
);

$this->applications['sesha'] = array(
    'fileroot' => dirname(__FILE__) . '/../sesha',
    'webroot' => $this->applications['horde']['webroot'] . '/sesha',
    'name' => _("Inventory"),
    'status' => 'active',

    // Uncomment this line if you want Sesha to provide queue and version
    // names instead of Whups:
    // 'provides' => array('tickets/listQueues', 'tickets/getQueueDetails', 'tickets/listVersions', 'tickets/getVersionDetails'),
    'menu_parent' => 'office',
);

$this->applications['hermes'] = array(
    'fileroot' => dirname(__FILE__) . '/../hermes',
    'webroot' => $this->applications['horde']['webroot'] . '/hermes',
    'name' => _("Time Tracking"),
    'status' => 'active',
    'menu_parent' => 'office',
    'provides' => 'time'
);

$this->applications['hermes-stopwatch'] = array(
    'status' => 'block',
    'app' => 'hermes',
    'blockname' => 'tree_stopwatch',
    'menu_parent' => 'hermes',
);

$this->applications['hermes-menu'] = array(
    'status' => 'block',
    'app' => 'hermes',
    'blockname' => 'tree_menu',
    'menu_parent' => 'hermes',
);

$this->applications['myaccount'] = array(
    'name' => _("My Account"),
    'status' => 'heading',
);

$this->applications['gollem'] = array(
    'fileroot' => dirname(__FILE__) . '/../gollem',
    'webroot' => $this->applications['horde']['webroot'] . '/gollem',
    'name' => _("File Manager"),
    'status' => 'active',
    'menu_parent' => 'myaccount',
    'provides' => 'files',
);

$this->applications['gollem-menu'] = array(
    'status' => 'block',
    'app' => 'gollem',
    'blockname' => 'tree_menu',
    'menu_parent' => 'gollem',
);

$this->applications['passwd'] = array(
    'fileroot' => dirname(__FILE__) . '/../passwd',
    'webroot' => $this->applications['horde']['webroot'] . '/passwd',
    'name' => _("Password"),
    'status' => 'active',
    'menu_parent' => 'myaccount'
);

$this->applications['jeta'] = array(
    'fileroot' => dirname(__FILE__) . '/../jeta',
    'webroot' => $this->applications['horde']['webroot'] . '/jeta',
    'name' => _("SSH"),
    'status' => 'active',
    'menu_parent' => 'myaccount'
);

$this->applications['website'] = array(
    'name' => _("Web Site"),
    'status' => 'heading',
);

$this->applications['agora'] = array(
    'fileroot' => dirname(__FILE__) . '/../agora',
    'webroot' => $this->applications['horde']['webroot'] . '/agora',
    'name' => _("Forums"),
    'status' => 'active',
    'provides' => 'forums',
    'menu_parent' => 'website'
);

$this->applications['ulaform'] = array(
    'fileroot' => dirname(__FILE__) . '/../ulaform',
    'webroot' => $this->applications['horde']['webroot'] . '/ulaform',
    'name' => _("Forms"),
    'status' => 'active',
    'menu_parent' => 'website'
);

$this->applications['volos'] = array(
    'fileroot' => dirname(__FILE__) . '/../volos',
    'webroot' => $this->applications['horde']['webroot'] . '/volos',
    'name' => _("Guestbook"),
    'status' => 'active',
    'menu_parent' => 'website'
);

$this->applications['ansel'] = array(
    'fileroot' => dirname(__FILE__) . '/../ansel',
    'webroot' => $this->applications['horde']['webroot'] . '/ansel',
    'name' => _("Photos"),
    'status' => 'active',
    'provides' => 'images',
    'menu_parent' => 'website'
);

$this->applications['scry'] = array(
    'fileroot' => dirname(__FILE__) . '/../scry',
    'webroot' => $this->applications['horde']['webroot'] . '/scry',
    'name' => _("Polls"),
    'status' => 'active',
    'provides' => 'polls',
    'menu_parent' => 'website'
);

$this->applications['merk'] = array(
    'fileroot' => dirname(__FILE__) . '/../merk',
    'webroot' => $this->applications['horde']['webroot'] . '/merk',
    'name' => _("Shopping"),
    'status' => 'active',
    'provides' => 'shop',
    'menu_parent' => 'website'
);

$this->applications['wicked'] = array(
    'fileroot' => dirname(__FILE__) . '/../wicked',
    'webroot' => $this->applications['horde']['webroot'] . '/wicked',
    'name' => _("Wiki"),
    'status' => 'active',
    'provides' => 'wiki',
    'menu_parent' => 'website'
);

$this->applications['vilma'] = array(
    'fileroot' => dirname(__FILE__) . '/../vilma',
    'webroot' => $this->applications['horde']['webroot'] . '/vilma',
    'name' => _("Mail Admin"),
    'status' => 'active',
    'menu_parent' => 'administration'
);

$this->applications['nic'] = array(
    'fileroot' => dirname(__FILE__) . '/../nic',
    'webroot' => $this->applications['horde']['webroot'] . '/nic',
    'name' => _("Network Tools"),
    'status' => 'active',
    'menu_parent' => 'administration'
);

function _detect_webroot()
{
    // Note for Windows users: the below assumes that your PHP_SELF variable
    // uses forward slashes. If it does not, you'll have to tweak this.
    if (isset($_SERVER['SCRIPT_URL']) || isset($_SERVER['SCRIPT_NAME'])) {
        $path = empty($_SERVER['SCRIPT_URL']) ?
            $_SERVER['SCRIPT_NAME'] :
            $_SERVER['SCRIPT_URL'];
        $hordedir = str_replace(DIRECTORY_SEPARATOR, '/', __FILE__);
        $hordedir = basename(preg_replace(';/config/registry.php$;', '', $hordedir));
        if (preg_match(';/' . $hordedir . ';', $path)) {
            $webroot = preg_replace(';/' . $hordedir . '.*;', '/' . $hordedir, $path);
        } else {
            $webroot = '';
        }
    } elseif (isset($_SERVER['PHP_SELF'])) {
        $webroot = preg_split(';/;', $_SERVER['PHP_SELF'], 2, PREG_SPLIT_NO_EMPTY);
        $webroot = strstr(dirname(__FILE__), DIRECTORY_SEPARATOR . array_shift($webroot));
        if ($webroot !== false) {
            $webroot = preg_replace(array('/\\\\/', ';/config$;'), array('/', ''), $webroot);
        } elseif ($webroot === false) {
            $webroot = '';
        } else {
            $webroot = '/horde';
        }
    } else {
        $webroot = '/horde';
    }

    return $webroot;
}
