<?php
/**
 * $Horde: horde/config/prefs.php.dist,v 1.62 2004/05/19 19:04:03 chuck Exp $
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
 *  value: This entry will either hold a number or a text value based on the
 *         preference type:
 *           implicit:  See Preference type
 *               text:  Text value
 *             number:  Number value
 *           checkbox:  Value should be 0 for unchecked, 1 for checked
 *             select:  Value associated with that selection list
 *
 * locked: Allow preference to be changed from UI
 *            true:  Do not show this preference in the UI
 *           false:  Show this preference in the UI and allow changing
 *
 * shared: Share with other horde apps
 *            true:  Share this pref with other Horde apps
 *           false:  Keep this pref local to IMP
 *
 *   type: Preference type
 *            special:  Provides a UI widget
 *             select:  Provides a selection list in the UI
 *           checkbox:  Provides a checkbox
 *           implicit:  Provides storage for 'special' types
 *           password:  Provides a textbox for password entry.
 *               enum:  Use static list of elements...similar to 'select'
 *
 *   enum: Static list of elements.
 *
 *   hook: Call a hook function for the value of this preference
 *            true:  Will call the function _prefs_hook_<prefname>
 *                   to fill in the value of this preference.
 *                   See hooks.php for more details.
 *           false:  Normal behaviour - no hook is called.
 */

$prefGroups['identities'] = array(
    'column' => _("Your Information"),
    'label' => _("Personal Information"),
    'desc' => _("Change the name and address that people see when they read and reply to your emails."),
    'members' => array('default_identity', 'identityselect', 'deleteidentity',
                       'id', 'fullname', 'from_addr')
);

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
                       'summary_refresh_time', 'show_sidebar', 'moz_sidebar',
                       'menu_view', 'widget_accesskey')
);

$prefGroups['remote'] = array(
    'column' => _("Other Information"),
    'label' => _("Remote Servers"),
    'desc' => _("Set up remote servers that you want to access from your portal."),
    'url' => 'services/portal/rpcsum.php'
);

// For alternate IMSP authentication.
$prefGroups['imspauth'] = array(
    'column' => _("Other Information"),
    'label' => _("Alternate IMSP Login"),
    'desc' => _("Use if name/password is different for IMSP server."),
    'members' => array('imsp_auth_user', 'imsp_auth_pass')
);

// Personal Information preferences

// default identity
// Set locked to true if you don't want the users to have multiple identities.
$_prefs['default_identity'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => true,
    'type' => 'enum',
    'enum' => isset($identity) ? $identity->getAll('id') : array(),
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
$_prefs['id'] = array(
    'value' => '',
    'locked' => false,
    'shared' => true,
    'type' => 'text',
    'desc' => _("Identity's name:")
);

// user full name for From: line
$_prefs['fullname'] = array(
    'value' => '',
    'locked' => false,
    'shared' => true,
    'type' => 'text',
    'desc' => _("Your full name:")
);

// user preferred email address for From: line
$_prefs['from_addr'] = array(
    'value' => '',
    'locked' => false,
    'shared' => true,
    'type' => 'text',
    'desc' =>  _("Your From: address:")
);

// user language
$_prefs['language'] = array(
    'value' => '',
    'locked' => false,
    'shared' => true,
    'type' => 'select',
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
    'value' => 1,
    'locked' => false,
    'shared' => true,
    'type' => 'checkbox',
    'desc' => _("Display 24-hour times?")
);

// date format
$_prefs['date_format'] = array(
    'value' => '%A %B %d, %Y',
    'locked' => false,
    'shared' => true,
    'type' => 'enum',
    'enum' => array('%A %B %d, %Y' => strftime('%A %B %d, %Y'),
                    '%A, %d. %B %Y' => strftime('%A, %d. %B %Y'),
                    '%A, %d %B %Y' => strftime('%A, %d %B %Y'),
                    '%x' => strftime('%x')),
    'desc' => _("Choose how to display dates:")
);

// UI theme
$_prefs['theme'] = array(
    'value' => 'kolab',
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
    'value' => 0,
    'locked' => false,
    'shared' => true,
    'type' => 'checkbox',
    'desc' => sprintf(_("Show the %s Menu on the left?"), $GLOBALS['registry']->getParam('name', 'horde'))
);

$_prefs['moz_sidebar'] = array(
    'type' => 'link',
    'xurl' => sprintf('javascript:if (window.sidebar && window.sidebar.addPanel) window.sidebar.addPanel(\'%s\', \'%s\', \'%s\'); else alert(\'%s\');',
                      $GLOBALS['registry']->getParam('name', 'horde'),
                      Util::addParameter(Horde::url($GLOBALS['registry']->getParam('webroot', 'horde') . '/services/portal/menu.php', true, -1), 'mozbar', '1'),
                      Horde::url($GLOBALS['registry']->getParam('webroot', 'horde') . '/prefs.php', true, -1),
                      addslashes(_("Couldn't find the Mozilla Sidebar. Make sure the sidebar is open."))),
    'desc' => sprintf(_("Add the %s Menu as a Mozilla Sidebar"), $GLOBALS['registry']->getParam('name', 'horde'))
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

// perform maintenance operations?
$_prefs['do_maintenance'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => true,
    'type' => 'checkbox',
    'desc' => _("Perform maintenance operations on login?")
);

// confirm when doing maintenance operations? If false (0), they will
// be performed with no input from/check with the user.
$_prefs['confirm_maintenance'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => true,
    'type' => 'checkbox',
    'desc' => _("Ask for confirmation before doing maintenance operations?")
);

// what application should we go to after login?
$_prefs['initial_application'] = array(
    'value' => 'kronolith',
    'locked' => false,
    'shared' => true,
    'type' => 'select',
    'desc' => sprintf(_("What application should %s display after login?"), $GLOBALS['registry']->getParam('name'))
);

$_prefs['widget_accesskey'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => true,
    'type' => 'checkbox',
    'desc' => _("Should access keys be defined for most links?")
);

// the layout of the portal page.
$_prefs['portal_layout'] = array(
    'value' => 'a:0:{}',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit',
    'desc' => 'Layout of portal page'
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
// a value of 0 = no, 1 = yes
$_prefs['show_last_login'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => true,
    'type' => 'checkbox',
    'desc' => _("Show last login time when logging in?")
);

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
