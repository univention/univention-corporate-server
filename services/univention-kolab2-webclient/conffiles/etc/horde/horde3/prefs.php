<?php
// Warning: This file is auto-generated and might be overwritten by
//          univention-baseconfig.
//          Please edit the following file instead:
// Warnung: Diese Datei wurde automatisch generiert und kann durch
//          univention-baseconfig überschrieben werden.
//          Bitte bearbeiten Sie an Stelle dessen die folgende Datei:
//
// 	/etc/univention/templates/files/etc/horde/horde3/prefs.php
//

/**
 * $Horde: horde/config/prefs.php.dist,v 1.85.2.5 2005/12/27 17:00:10 chuck Exp $
 *
 * Preferences Information
 * =======================
 * Changes you make to the prefs.php file(s) will not be reflected until the
 * user logs out and logs in again.
 *
 * If you change these preferences in a production system, you will
 * need to delete any horde_prefs in your preferences database.
 *
 * prefGroups array
 * ----------------
 * $prefGroups are for display purposes when you press the options button.
 * The options choice will appear when you set your preferences driver
 * in the horde/config/conf.php file.
 *
 * $prefGroups array definition:
 *    column:  What column head this group will go under
 *     label:  Label for the group of settings
 *      desc:  Description that will show under label
 *   members:  List of preferences supported by this group
 *
 * _prefs array
 * ------------
 * The $_prefs array's are listed in the same order as listed in the
 * members element of $prefGroups.
 *
 *   value: This entry will either hold a number or a text value based on the
 *          preference type:
 *            implicit:  See Preference type
 *                text:  Text value
 *              number:  Number value
 *            checkbox:  Value should be 0 for unchecked, 1 for checked
 *              select:  Value associated with that selection list
 *
 *  locked: Allow preference to be changed from U
 *             true:  Do not show this preference in the U
 *            false:  Show this preference in the UI and allow changing
 *
 *  shared: Share with other horde apps
 *             true:  Share this pref with other Horde apps
 *            false:  Keep this pref local to the current app
 *
 *    type: Preference type
 *             special:  Provides a UI widget
 *              select:  Provides a selection list in the U
 *            checkbox:  Provides a checkbox
 *            implicit:  Provides storage for 'special' types
 *            password:  Provides a textbox for password entry.
 *                enum:  Use static list of elements...similar to 'select'
 *
 *    enum: Static list of elements.
 *
 * escaped: For an enum or a select, are the keys and values already html-escaped?
 *          Defaults to false if not present.
 *
 *    hook: Call a hook function for the value of this preference
 *             true:  Will call the function _prefs_hook_<prefname>
 *                    to fill in the value of this preference.
 *                    See hooks.php for more details.
 *            false:  Normal behaviour - no hook is called.
 */

$prefGroups['identities'] = array(
    'column' => _("Your Information"),
    'label' => _("Personal Information"),
    'desc' => _("Change the name and address that people see when they read and reply to your emails."),
    'members' => array('default_identity', 'identityselect', 'deleteidentity',
                       'id', 'fullname', 'from_addr')
);

$auth = &Auth::singleton($GLOBALS['conf']['auth']['driver']);
if (is_a($auth, 'Auth') && $auth->hasCapability('update')) {
    $prefGroups['forgotpass'] = array(
        'column' => _("Your Information"),
        'label' => _("Account Password"),
        'desc' => _("Set options to allow you to reset your password if you ever forget it."),
        'members' => array('security_question', 'security_answer', 'alternate_email')
    );
}

$prefGroups['language'] = array(
    'column' => _("Your Information"),
    'label' => _("Locale and Time"),
    'desc' => _("Set your preferred language, timezone and date options."),
    'members' => array('language', 'timezone', 'twentyFour', 'date_format')
);

$prefGroups['categories'] = array(
    'column' => _("Your Information"),
    'label' => _("Categories and Labels"),
    'desc' => _("Manage the list of categories you have to label items with, and colors associated with those categories."),
    'members' => array('categorymanagement')
);

$prefGroups['display'] = array(
    'column' => _("Other Information"),
    'label' => _("Display Options"),
    'desc' => _("Set your startup application, color scheme, page refreshing, and other display options."),
    'members' => array('initial_application', 'show_last_login', 'theme',
                       'summary_refresh_time', 'show_sidebar', 'sidebar_width',
                       'moz_sidebar', 'menu_view', 'menu_refresh_time',
                       'widget_accesskey', 'alpha_filter')
);

$prefGroups['logintasks'] = array(
    'column' => _("Other Information"),
    'label' => _("Login Tasks"),
    'desc' => sprintf(_("Customize tasks to run upon logon to %s."), $GLOBALS['registry']->get('name')),
    'members' => array('do_maintenance', 'confirm_maintenance')
);

$prefGroups['remote'] = array(
    'column' => _("Other Information"),
    'label' => _("Remote Servers"),
    'desc' => _("Set up remote servers that you want to access from your portal."),
    'url' => 'services/portal/rpcsum.php'
);

// For alternate IMSP authentication.
if (!empty($GLOBALS['conf']['imsp']['enabled'])) {
    $prefGroups['imspauth'] = array(
        'column' => _("Other Information"),
        'label' => _("Alternate IMSP Login"),
        'desc' => _("Use if name/password is different for IMSP server."),
        'members' => array('imsp_auth_user', 'imsp_auth_pass')
    );
}

// Determine functionality of richtext editor
$prefGroups['richtext'] = array(
    'column' => _("Other Information"),
    'label' => _("Rich Text Editor Options"),
    'desc' => _("Which plugins to enable for the Rich Text editor."),
    'members' => array('contextmenu', 'tableoperations', 'listtype'),
);
if ($registry->hasInterface('images')) {
    $prefGroups['richtext']['members'][] = 'anselimage';
}

$prefGroups['syncml'] = array(
    'column' => _("Other Information"),
    'label' => _("SyncML"),
    'desc' => _("Configuration for syncing with PDAs, Smartphones and Outlook."),
    'url' => 'services/portal/syncml.php',
    'members' => array()
);

// Personal Information preferences

// default identity
// Set locked to true if you don't want the users to have multiple identities.
$_prefs['default_identity'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => true,
    'type' => 'enum',
    'enum' => (isset($identity) && is_object($identity)) ? $identity->getAll('id') : array(),
    'desc' => _("Your default identity:")
);

// identities array
// Don't change anything here.
$_prefs['identities'] = array(
    'value' => 'a:0:{}',
    'locked' => false,
    'shared' => true,
    'type' => 'implicit'
);

// identity selection widget
$_prefs['identityselect'] = array(
    'shared' => true,
    'type' => 'special'
);

// delete button
$_prefs['deleteidentity'] = array(
    'type' => 'special',
    'shared' => true
);

// identity name
// If you lock this preference, you must specify a value or a hook for it in
// horde/config/hooks.php.
$_prefs['id'] = array(
    'value' => '',
    'locked' => false,
    'shared' => true,
    'type' => 'text',
    'desc' => _("Identity's name:")
);

// user full name for From: line
// If you lock this preference, you must specify a value or a hook for it in
// horde/config/hooks.php.
$_prefs['fullname'] = array(
    'value' => '',
    'locked' => false,
    'shared' => true,
    'type' => 'text',
    'desc' => _("Your full name:")
);

// user preferred email address for From: line
// If you lock this preference, you must specify a value or a hook for it in
// horde/config/hooks.php.
$_prefs['from_addr'] = array(
    'value' => '',
    'locked' => false,
    'shared' => true,
    'type' => 'text',
    'desc' =>  _("Your From: address:")
);

// user security question
$_prefs['security_question'] = array(
    'value' => '',
    'locked' => false,
    'shared' => true,
    'type' => 'text',
    'desc' => _("Enter a security question which you will be asked if you need to reset your password, e.g. 'what is the name of your pet?':")
);

// user security answer
$_prefs['security_answer'] = array(
    'value' => '',
    'locked' => false,
    'shared' => true,
    'type' => 'text',
    'desc' => _("Insert the required answer to the security question:")
);

// user alternate email
$_prefs['alternate_email'] = array(
    'value' => '',
    'locked' => false,
    'shared' => true,
    'type' => 'text',
    'desc' => _("Insert an email address to which you can receive the new password:")
);

// user language
$_prefs['language'] = array(
    'value' => '',
    'locked' => false,
    'shared' => true,
    'type' => 'select',
    'escaped' => true,
    'desc' => _("Select your preferred language:")
);

// user time zone
$_prefs['timezone'] = array(
    'value' => '',
    'locked' => false,
    'shared' => true,
    'type' => 'select',
    'desc' => _("Your current time zone:")
);

// time format
$_prefs['twentyFour'] = array(
    'value' => false,
    'locked' => false,
    'shared' => true,
    'type' => 'checkbox',
    'desc' => _("Display 24-hour times?")
);

// date format
$_prefs['date_format'] = array(
    'value' => '%x',
    'locked' => false,
    'shared' => true,
    'type' => 'enum',
    'enum' => array(
        '%x' => strftime('%x'),
        '%Y-%m-%d' => strftime('%Y-%m-%d'),
        '%A %B %d, %Y' => strftime('%A %B %d, %Y'),
        '%A, %d. %B %Y' => strftime('%A, %d. %B %Y'),
        '%A, %d %B %Y' => strftime('%A, %d %B %Y'),
        '%a, %b %e, %Y' => strftime('%a, %b %e, %Y'),
        '%a, %b %e, %y' => strftime('%a, %b %e, %y'),
        '%a, %b %e' => strftime('%a, %b %e'),
        '%a, %e %b %Y' => strftime('%a, %e %b %Y'),
        '%a, %e %b %y' => strftime('%a, %e %b %y'),
        '%a %d %b %Y' => strftime ('%a %d %b %Y'),
        '%a %x' => strftime ('%a %x'),
        '%a %Y-%m-%d' => strftime ('%a %Y-%m-%d'),
        '%e %b %Y' => strftime('%e %b %Y'),
        '%e. %b %Y' => strftime('%e. %b %Y'),
        '%e. %m %Y' => strftime('%e %m %Y'),
        '%e. %m.' => strftime('%e. %m.'),
        '%e. %B' => strftime('%e. %B'),
        '%e. %B %Y' => strftime('%e. %B %Y'),
        '%e. %B %y' => strftime('%e. %B %y'),
        '%B %e, %Y' => strftime('%B %e, %Y'),
    ),
    'desc' => _("Choose how to display dates:"));

// UI theme
$_prefs['theme'] = array(
    'value' => 'univention',
    'locked' => false,
    'shared' => true,
    'type' => 'select',
    'desc' => _("Select your color scheme.")
);

// categories
$_prefs['categories'] = array(
    'value' => '',
    'locked' => false,
    'shared' => true,
    'type' => 'implicit'
);

// category colors
$_prefs['category_colors'] = array(
    'value' => '',
    'locked' => false,
    'shared' => true,
    'type' => 'implicit'
);

// UI for category management.
$_prefs['categorymanagement'] = array(
    'type' => 'special'
);

$_prefs['summary_refresh_time'] = array(
    'value' => 300,
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array(0 => _("Never"),
                    30 => _("Every 30 seconds"),
                    60 => _("Every minute"),
                    300 => _("Every 5 minutes"),
                    900 => _("Every 15 minutes"),
                    1800 => _("Every half hour")),
    'desc' => _("Refresh Portal View:")
);

$_prefs['show_sidebar'] = array(
    'value' => true,
    'locked' => false,
    'shared' => true,
    'type' => 'checkbox',
    'desc' => sprintf(_("Show the %s Menu on the left?"), $GLOBALS['registry']->get('name', 'horde'))
);

$_prefs['sidebar_width'] = array(
    'value' => 150,
    'locked' => false,
    'shared' => false,
    'type' => 'number',
    'desc' => sprintf(_("Width of the %s menu on the left (takes effect on next log-in):"), $GLOBALS['registry']->get('name', 'horde'))
);

$_prefs['moz_sidebar'] = array(
    'type' => 'link',
    'xurl' => sprintf('javascript:if (window.sidebar && window.sidebar.addPanel) window.sidebar.addPanel(\'%s\', \'%s\', \'%s\'); else alert(\'%s\');',
                      $GLOBALS['registry']->get('name', 'horde'),
                      Util::addParameter(Horde::url($GLOBALS['registry']->get('webroot', 'horde') . '/services/portal/sidebar.php', true, -1), 'mozbar', '1'),
                      Horde::url($GLOBALS['registry']->get('webroot', 'horde') . '/prefs.php', true, -1),
                      addslashes(_("Couldn't find the Mozilla Sidebar. Make sure the sidebar is open."))),
    'desc' => sprintf(_("Add the %s Menu as a Mozilla Sidebar"), $GLOBALS['registry']->get('name', 'horde'))
);

$_prefs['menu_view'] = array(
    'value' => 'both',
    'locked' => false,
    'shared' => true,
    'type' => 'enum',
    'enum' => array('text' => _("Text Only"),
                    'icon' => _("Icons Only"),
                    'both' => _("Icons with text")),
    'desc' => _("Menu mode:")
);

$_prefs['menu_refresh_time'] = array(
    'value' => 300,
    'locked' => false,
    'shared' => true,
    'type' => 'enum',
    'enum' => array(0 => _("Never"),
                    30 => _("Every 30 seconds"),
                    60 => _("Every minute"),
                    120 => _("Every 2 minutes"),
                    300 => _("Every 5 minutes")),
    'desc' => _("Refresh Dynamic Menu Elements:")
);


// Login/Maintenance Tasks preferences

// To disable maintenance entirely, set 'value' = false and
// 'locked' = true for all of these. To just turn it off by default,
// set 'value' false for do_maintenance.
// perform maintenance operations?
$_prefs['do_maintenance'] = array(
    'value' => true,
    'locked' => false,
    'shared' => true,
    'type' => 'checkbox',
    'desc' => _("Perform maintenance operations on login?"),
    'help' => 'prefs-do_maintenance');

// last time maintenance was run.
// value is a UNIX timestamp of the last time maintenance ran for the user.
$_prefs['last_maintenance'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => true,
    'type' => 'implicit'
);

// confirm when doing maintenance operations? If false, they will
// be performed with no input from/check with the user.
$_prefs['confirm_maintenance'] = array(
    'value' => true,
    'locked' => false,
    'shared' => true,
    'type' => 'checkbox',
    'desc' => _("Ask for confirmation before doing maintenance operations?"),
    'help' => 'prefs-confirm_maintenance');

// End Login/Maintenance preferences


// what application should we go to after login?
$_prefs['initial_application'] = array(
    'value' => 'horde',
    'locked' => false,
    'shared' => true,
    'type' => 'select',
    'desc' => sprintf(_("What application should %s display after login?"), $GLOBALS['registry']->get('name'))
);

// should we create access keys?
$_prefs['widget_accesskey'] = array(
    'value' => true,
    'locked' => false,
    'shared' => true,
    'type' => 'checkbox',
    'desc' => _("Should access keys be defined for most links?")
);

// should we not use the alpha image loader for IE?
$_prefs['alpha_filter'] = array(
    'value' => false,
    'locked' => true,
    'shared' => true,
    'type' => 'checkbox',
    'desc' => _("If you don't see any icons using Internet Explorer, you may need to check this box to turn off PNG transparency.")
);

// the layout of the portal page.
$_prefs['portal_layout'] = array(
    'value' => 'a:0:{}',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit'
);

// the remote servers.
$_prefs['remote_summaries'] = array(
    'value' => 'a:0:{}',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit'
);

// last login time of user
// value is a serialized array of the UNIX timestamp of the last
// login, and the host that the last login was from.
$_prefs['last_login'] = array(
    'value' => 'a:0:{}',
    'locked' => false,
    'shared' => true,
    'type' => 'implicit'
);

// show the last login time of user
$_prefs['show_last_login'] = array(
    'value' => true,
    'locked' => false,
    'shared' => true,
    'type' => 'checkbox',
    'desc' => _("Show last login time when logging in?")
);

if (!empty($GLOBALS['conf']['imsp']['enabled'])) {
    $_prefs['imsp_auth_user'] = array(
        'value' => '',
        'locked' => false,
        'shared' => false,
        'type' => 'text',
        'desc' => _("Alternate IMSP Username")
    );

    $_prefs['imsp_auth_pass'] = array(
        'value' => '',
        'locked' => false,
        'shared' => false,
        'type' => 'password',
        'desc' => _("Alternate IMSP Password")
    );
}

// Rich Text Editor preferences.

$_prefs['contextmenu'] = array(
    'value' => true,
    'locked' => false,
    'shared' => true,
    'type' => 'checkbox',
    'desc' => _("Enable right click context menu?")
);

$_prefs['tableoperations'] = array(
    'value' => false,
    'locked' => false,
    'shared' => true,
    'type' => 'checkbox',
    'desc' => _("Show table operations menu bar?")
);

$_prefs['listtype'] = array(
    'value' => true,
    'locked' => false,
    'shared' => true,
    'type' => 'checkbox',
    'desc' => _("Allow setting of ordered list type?")
);

if ($registry->hasInterface('images')) {
    $_prefs['anselimage'] = array(
        'value' => true,
        'locked' => false,
        'shared' => true,
        'type' => 'checkbox',
        'desc' => _("Enable insertion of images from Photo Galleries in text?")
    );
}

// End Rich Text Editor preferences.
