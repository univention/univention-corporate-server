<?php
// Warning: This file is auto-generated and might be overwritten by
//          univention-baseconfig.
//          Please edit the following file instead:
// Warnung: Diese Datei wurde automatisch generiert und kann durch
//          univention-baseconfig überschrieben werden.
//          Bitte bearbeiten Sie an Stelle dessen die folgende Datei:
//
// 	/etc/univention/templates/files/etc/horde/horde3/registry.php
//

/**
 * registry.php -- Horde application registry.
 *
 * $Horde: horde/config/registry.php.dist,v 1.255.2.17 2006/07/21 15:49:46 jan Exp $
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

// We try to automatically determine the proper webroot for Horde
// here. This still assumes that applications live under horde3/. If
// this results in incorrect results for you, simply change the
// use of the $webroot variable in the 'horde' stanza below.
//
// Note for Windows users: the below assumes that your PHP_SELF
// variable uses forward slashes. If it does not, you'll have to tweak
// this.
if (isset($_SERVER['PHP_SELF'])) {
    $webroot = preg_split(';/;', $_SERVER['PHP_SELF'], 2, PREG_SPLIT_NO_EMPTY);
    $webroot = strstr(dirname(__FILE__), DIRECTORY_SEPARATOR . array_shift($webroot));
    if ($webroot !== false) {
        $webroot = preg_replace(array('/\\\\/', ';/config$;'), array('/', ''), $webroot);
    } elseif ($webroot === false) {
        $webroot = '';
    } else {
        $webroot = '/horde3';
    }
} else {
    $webroot = '/horde3';
}

$this->applications['horde'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/..',
    'webroot' => $webroot,
    'initial_page' => 'login.php',
    'name' => _("Horde"),
    'status' => 'active',
    'templates' => '/usr/share/horde3/lib' . '/../templates',
    'provides' => 'horde'
);

$this->applications['mimp'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../mimp',
    'webroot' => $this->applications['horde']['webroot'] . '/mimp',
    'name' => _("Mobile Mail"),
    'status' => 'notoolbar'
);

@!@
if not baseConfig.has_key('horde/application/imp') or not baseConfig['horde/application/imp'].lower() in [ 'no', 'false' ]:
	print "$this->applications['imp'] = array("
	print "    'fileroot' => '/usr/share/horde3/lib' . '/../imp',"
	print "    'webroot' => $this->applications['horde']['webroot'] . '/imp',"
	print "    'name' => _(\"Mail\"),"
	print "    'status' => 'active',"
	print "    'provides' => 'mail',"
	print ");"
	print ""
	if not baseConfig.has_key('horde/application/ingo') or not baseConfig['horde/application/ingo'].lower() in [ 'no', 'false' ]:
		print "$this->applications['ingo'] = array("
		print "    'fileroot' => '/usr/share/horde3/lib' . '/../ingo',"
		print "    'webroot' => $this->applications['horde']['webroot'] . '/ingo',"
		print "    'name' => _(\"Filters\"),"
		print "    'status' => 'active',"
		print "    'provides' => array('mail/blacklistFrom', 'mail/showBlacklist', 'mail/whitelistFrom', 'mail/showWhitelist', 'mail/applyFilters', 'mail/canApplyFilters', 'mail/showFilters'),"
		print "    'menu_parent' => 'imp'"
		print ");"
		print ""
	print "$this->applications['sam'] = array("
	print "    'fileroot' => '/usr/share/horde3/lib' . '/../sam',"
	print "    'webroot' => $this->applications['horde']['webroot'] . '/sam',"
	print "    'name' => _(\"Spam\"),"
	print "    'status' => 'inactive',"
	print "    // Uncomment this line if you want Sam to handle the blacklist filter"
	print "    // instead of Ingo:"
	print "    // 'provides' => array('mail/blacklistFrom', 'mail/showBlacklist', 'mail/whitelistFrom', 'mail/showWhitelist'),"
	print "    'menu_parent' => 'imp'"
	print ");"
	print ""
	print "$this->applications['forwards'] = array("
	print "    'fileroot' => '/usr/share/horde3/lib' . '/../forwards',"
	print "    'webroot' => $this->applications['horde']['webroot'] . '/forwards',"
	print "    'name' => _(\"Forwards\"),"
	print "    'status' => 'active',"
	print "    'provides' => 'forwards',"
	print "    'menu_parent' => 'imp',"
	print ");"
	print ""
	print "$this->applications['vacation'] = array("
	print "    'fileroot' => '/usr/share/horde3/lib' . '/../vacation',"
	print "    'webroot' => $this->applications['horde']['webroot'] . '/vacation',"
	print "    'name' => _(\"Vacation\"),"
	print "    'status' => 'active',"
	print "    'provides' => 'vacation',"
	print "    'menu_parent' => 'imp'"
	print ");"
	print ""
	print "$this->applications['imp-folders'] = array("
	print "    'status' => 'block',"
	print "    'app' => 'imp',"
	print "    'blockname' => 'tree_folders',"
	print "    'menu_parent' => 'imp',"
	print ");"
@!@

$this->applications['organizing'] = array(
    'name' => _("Organizing"),
    'status' => 'heading',
);

@!@
if not baseConfig.has_key('horde/application/turba') or not baseConfig['horde/application/turba'].lower() in [ 'no', 'false' ]:
	print "$this->applications['turba'] = array("
	print "    'fileroot' => '/usr/share/horde3/lib' . '/../turba',"
	print "    'webroot' => $this->applications['horde']['webroot'] . '/turba',"
	print "    'name' => _(\"Address Book\"),"
	print "    'status' => 'active',"
	print "    'provides' => array('contacts', 'clients'),"
	print "    'menu_parent' => 'organizing'"
	print ");"
	print ""
	print "$this->applications['turba-menu'] = array("
	print "    'status' => 'block',"
	print "    'app' => 'turba',"
	print "    'blockname' => 'tree_menu',"
	print "    'menu_parent' => 'turba',"
	print ");"

if not baseConfig.has_key('horde/application/kronolith') or not baseConfig['horde/application/kronolith'].lower() in [ 'no', 'false' ]:
	print "$this->applications['kronolith'] = array("
	print "    'fileroot' => '/usr/share/horde3/lib' . '/../kronolith',"
	print "    'webroot' => $this->applications['horde']['webroot'] . '/kronolith',"
	print "    'name' => _(\"Calendar\"),"
	print "    'status' => 'active',"
	print "    'provides' => 'calendar',"
	print "    'menu_parent' => 'organizing'"
	print ");"
	print ""
	print "$this->applications['kronolith-alarms'] = array("
	print "    'status' => 'block',"
	print "    'app' => 'kronolith',"
	print "    'blockname' => 'tree_alarms',"
	print "    'menu_parent' => 'kronolith',"
	print ");"
	print ""
	print "$this->applications['kronolith-menu'] = array("
	print "    'status' => 'block',"
	print "    'app' => 'kronolith',"
	print "    'blockname' => 'tree_menu',"
	print "    'menu_parent' => 'kronolith',"
	print ");"

if not baseConfig.has_key('horde/application/mnemo') or not baseConfig['horde/application/mnemo'].lower() in [ 'no', 'false' ]:
	print "$this->applications['mnemo'] = array("
	print "    'fileroot' => '/usr/share/horde3/lib' . '/../mnemo',"
	print "    'webroot' => $this->applications['horde']['webroot'] . '/mnemo',"
	print "    'name' => _(\"Notes\"),"
	print "    'status' => 'active',"
	print "    'provides' => 'notes',"
	print "    'menu_parent' => 'organizing'"
	print ");"

if not baseConfig.has_key('horde/application/nag') or not baseConfig['horde/application/nag'].lower() in [ 'no', 'false' ]:
	print "$this->applications['nag'] = array("
	print "    'fileroot' => '/usr/share/horde3/lib' . '/../nag',"
	print "    'webroot' => $this->applications['horde']['webroot'] . '/nag',"
	print "    'name' => _(\"Tasks\"),"
	print "    'status' => 'active',"
	print "    'provides' => 'tasks',"
	print "    'menu_parent' => 'organizing'"
	print ");"
@!@

$this->applications['genie'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../genie',
    'webroot' => $this->applications['horde']['webroot'] . '/genie',
    'name' => _("Wishlist"),
    'status' => 'inactive',
    'provides' => 'wishlist',
    'menu_parent' => 'organizing'
);

$this->applications['trean'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../trean',
    'webroot' => $this->applications['horde']['webroot'] . '/trean',
    'name' => _("Bookmarks"),
    'status' => 'inactive',
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
    'fileroot' => '/usr/share/horde3/lib' . '/../chora',
    'webroot' => $this->applications['horde']['webroot'] . '/chora',
    'name' => _("Version Control"),
    'status' => 'active',
    'menu_parent' => 'devel'
);

$this->applications['whups'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../whups',
    'webroot' => $this->applications['horde']['webroot'] . '/whups',
    'name' => _("Tickets"),
    'status' => 'inactive',
    'provides' => 'tickets',
    'menu_parent' => 'devel'
);

$this->applications['luxor'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../luxor',
    'webroot' => $this->applications['horde']['webroot'] . '/luxor',
    'name' => _("X-Ref"),
    'status' => 'inactive',
    'menu_parent' => 'devel'
);

$this->applications['nic'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../nic',
    'webroot' => $this->applications['horde']['webroot'] . '/nic',
    'name' => _("Network"),
    'status' => 'inactive',
    'menu_parent' => 'devel'
);

$this->applications['info'] = array(
    'name' => _("Information"),
    'status' => 'heading',
);

$this->applications['klutz'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../klutz',
    'webroot' => $this->applications['horde']['webroot'] . '/klutz',
    'name' => _("Comics"),
    'status' => 'inactive',
    'provides' => 'comics',
    'menu_parent' => 'info'
);

$this->applications['occam'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../occam',
    'webroot' => $this->applications['horde']['webroot'] . '/occam',
    'name' => _("Courses"),
    'status' => 'inactive',
    'menu_parent' => 'info'
);

$this->applications['mottle'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../mottle',
    'webroot' => $this->applications['horde']['webroot'] . '/mottle',
    'name' => _("MOTD"),
    'status' => 'inactive',
    'menu_parent' => 'info'
);

$this->applications['jonah'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../jonah',
    'webroot' => $this->applications['horde']['webroot'] . '/jonah',
    'name' => _("News"),
    'status' => 'inactive',
    'provides' => 'news',
    'menu_parent' => 'info'
);

$this->applications['jonah-menu'] = array(
    'status' => 'block',
    'app' => 'jonah',
    'blockname' => 'tree_menu',
    'menu_parent' => 'jonah',
);

$this->applications['troll'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../troll',
    'webroot' => $this->applications['horde']['webroot'] . '/troll',
    'name' => _("Newsgroups"),
    'status' => 'inactive',
    'menu_parent' => 'info'
);

$this->applications['troll-menu'] = array(
    'status' => 'block',
    'app' => 'troll',
    'blockname' => 'tree_menu',
    'menu_parent' => 'troll',
);

$this->applications['goops'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../goops',
    'webroot' => $this->applications['horde']['webroot'] . '/goops',
    'name' => _("Search Engines"),
    'status' => 'inactive',
    'menu_parent' => 'info'
);

$this->applications['office'] = array(
    'name' => _("Office"),
    'status' => 'heading',
);

$this->applications['juno'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../juno',
    'webroot' => $this->applications['horde']['webroot'] . '/juno',
    'name' => _("Accounting"),
    'status' => 'inactive',
    'menu_parent' => 'office'
);

$this->applications['midas'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../midas',
    'webroot' => $this->applications['horde']['webroot'] . '/midas',
    'name' => _("Ads"),
    'status' => 'inactive',
    'menu_parent' => 'office'
);

$this->applications['hylax'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../hylax',
    'webroot' => $this->applications['horde']['webroot'] . '/hylax',
    'name' => _("Faxes"),
    'status' => 'inactive',
    'menu_parent' => 'office',
);

$this->applications['sesha'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../sesha',
    'webroot' => $this->applications['horde']['webroot'] . '/sesha',
    'name' => _("Inventory"),
    'status' => 'inactive',

    // Uncomment this line if you want Sesha to provide queue and version
    // names instead of Whups:
    // 'provides' => array('tickets/listQueues', 'tickets/getQueueDetails', 'tickets/listVersions', 'tickets/getVersionDetails'),
    'menu_parent' => 'office',
);

$this->applications['thor'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../thor',
    'webroot' => $this->applications['horde']['webroot'] . '/thor',
    'name' => _("Projects"),
    'status' => 'inactive',
    'provides' => 'projects',
    'menu_parent' => 'office'
);

$this->applications['rakim'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../rakim',
    'webroot' => $this->applications['horde']['webroot'] . '/rakim',
    'name' => _("Support"),
    'status' => 'inactive',
    'menu_parent' => 'office'
);

$this->applications['hermes'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../hermes',
    'webroot' => $this->applications['horde']['webroot'] . '/hermes',
    'name' => _("Time Tracking"),
    'status' => 'inactive',
    'menu_parent' => 'office',
    'provides' => 'time'
);

$this->applications['hermes-watch'] = array(
    'status' => 'block',
    'app' => 'hermes',
    'blockname' => 'stopwatch',
    'menu_parent' => 'hermes',
);

$this->applications['myaccount'] = array(
    'name' => _("My Account"),
    'status' => 'heading',
);

@!@
if not baseConfig.has_key('horde/application/gollem') or not baseConfig['horde/application/gollem'].lower() in [ 'no', 'false' ]:
	print "$this->applications['gollem'] = array("
	print "    'fileroot' => '/usr/share/horde3/lib' . '/../gollem',"
	print "    'webroot' => $this->applications['horde']['webroot'] . '/gollem',"
	print "    'name' => _(\"File Manager\"),"
	print "    'status' => 'active',"
	print "    'menu_parent' => 'myaccount',"
	print "    'provides' => 'files',"
	print ");"
	print ""
	print "$this->applications['gollem-menu'] = array("
	print "    'status' => 'block',"
	print "    'app' => 'gollem',"
	print "    'blockname' => 'tree_menu',"
	print "    'menu_parent' => 'gollem',"
	print ");"
@!@

$this->applications['passwd'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../passwd',
    'webroot' => $this->applications['horde']['webroot'] . '/passwd',
    'name' => _("Password"),
    'status' => 'active',
    'menu_parent' => 'myaccount'
);

$this->applications['jeta'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../jeta',
    'webroot' => $this->applications['horde']['webroot'] . '/jeta',
    'name' => _("SSH"),
    'status' => 'inactive',
    'menu_parent' => 'myaccount'
);

$this->applications['website'] = array(
    'name' => _("Web Site"),
    'status' => 'heading',
);

$this->applications['giapeto'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../giapeto',
    'webroot' => $this->applications['horde']['webroot'] . '/giapeto',
    'name' => _("CMS"),
    'status' => 'inactive',
    'provides' => 'cms',
    'menu_parent' => 'website'
);

$this->applications['agora'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../agora',
    'webroot' => $this->applications['horde']['webroot'] . '/agora',
    'name' => _("Forums"),
    'status' => 'inactive',
    'provides' => 'forums',
    'menu_parent' => 'website'
);

$this->applications['ulaform'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../ulaform',
    'webroot' => $this->applications['horde']['webroot'] . '/ulaform',
    'name' => _("Forms"),
    'status' => 'inactive',
    'menu_parent' => 'website'
);

$this->applications['volos'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../volos',
    'webroot' => $this->applications['horde']['webroot'] . '/volos',
    'name' => _("Guestbook"),
    'status' => 'inactive',
    'menu_parent' => 'website'
);

$this->applications['ansel'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../ansel',
    'webroot' => $this->applications['horde']['webroot'] . '/ansel',
    'name' => _("Photos"),
    'status' => 'inactive',
    'provides' => 'images',
    'menu_parent' => 'website'
);

$this->applications['scry'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../scry',
    'webroot' => $this->applications['horde']['webroot'] . '/scry',
    'name' => _("Polls"),
    'status' => 'inactive',
    'provides' => 'polls',
    'menu_parent' => 'website'
);

$this->applications['merk'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../merk',
    'webroot' => $this->applications['horde']['webroot'] . '/merk',
    'name' => _("Shopping"),
    'status' => 'inactive',
    'menu_parent' => 'website'
);

$this->applications['swoosh'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../swoosh',
    'webroot' => $this->applications['horde']['webroot'] . '/swoosh',
    'name' => _("SMS Messaging"),
    'status' => 'inactive',
    'provides' => 'sms',
    'menu_parent' => 'website'
);

$this->applications['wicked'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../wicked',
    'webroot' => $this->applications['horde']['webroot'] . '/wicked',
    'name' => _("Wiki"),
    'status' => 'inactive',
    'provides' => 'wiki',
    'menu_parent' => 'website'
);

$this->applications['vilma'] = array(
    'fileroot' => '/usr/share/horde3/lib' . '/../vilma',
    'webroot' => $this->applications['horde']['webroot'] . '/vilma',
    'name' => _("Mail Admin"),
    'status' => 'inactive',
    'menu_parent' => 'administration'
);
