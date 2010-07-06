<?php
/**
 * $Horde: dimp/config/prefs.php.dist,v 1.14.2.5 2008-05-20 05:27:36 slusarz Exp $
 *
 * See horde/config/prefs.php for documentation on the structure of this file.
 */

$prefGroups['login'] = array(
    'column' => _("General Options"),
    'label' => _("Login Tasks"),
    'desc' => sprintf(_("Customize tasks to run upon logon to %s."), $GLOBALS['registry']->get('name')),
    'members' => array('login_view')
);

// Login preferences
$_prefs['login_view'] = array(
    'value' => 'portal',
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array('portal' => _("Portal"),
                    'inbox' => _("Inbox")),
    'desc' => _("The page to view immediately after login.")
);

// Other Implicit preferences
$_prefs['show_preview'] = array(
    'value' => true,
    'locked' => false,
    'shared' => false,
    'type' => 'implicit',
);
