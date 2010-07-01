<?php
/**
 * $Horde: imp/acl.php,v 1.23.10.15 2009-01-06 15:24:01 jan Exp $
 *
 * Copyright 2000-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Chris Hastie <imp@oak-wood.co.uk>
 * @author Eric Garrido <ekg2002@columbia.edu>
 */

@define('IMP_BASE', dirname(__FILE__));
require_once IMP_BASE . '/lib/base.php';
require_once IMP_BASE . '/lib/Folder.php';
require_once IMP_BASE . '/lib/IMAP/ACL.php';
require_once IMP_BASE . '/lib/Template.php';

$prefs_url = IMP::prefsURL(true);

/* Redirect back to the options screen if ACL is not enabled. */
if ($prefs->isLocked('acl') ||
    !(isset($_SESSION['imp']['acl']) && is_array($_SESSION['imp']['acl']))) {
    $notification->push(_("Folder sharing is not enabled."), 'horde.error');
    header('Location: ' . $prefs_url);
    exit;
}

$params = array(
    'hostspec' => $_SESSION['imp']['server'],
    'password' => Secret::read(Secret::getKey('imp'), $_SESSION['imp']['pass']),
    'port' => $_SESSION['imp']['port'],
    'protocol' => $_SESSION['imp']['protocol'],
    'username' => $_SESSION['imp']['user'],
);

if (isset($_SESSION['imp']['acl']['params'])) {
    $params = array_merge($params, $_SESSION['imp']['acl']['params']);
}

$ACLDriver = &IMP_IMAP_ACL::singleton($_SESSION['imp']['acl']['driver'], $params);

/* Check selected driver is supported. Redirect to options screen with
 * error message if not. */
$error = (!$ACLDriver->isSupported())
    ? _("This server does not support sharing folders.")
    : $ACLDriver->getError();

if ($error) {
    $notification->push($error, 'horde.error');
    header('Location: ' . $prefs_url);
    exit;
}

$acls = Util::getFormData('acl');
$folder = Util::getFormData('folder');
$new_user = Util::getFormData('new_user');
if ($new_user) {
    $new_acl = Util::getFormData('new_acl');
    /* check to see if $new_user already has an acl on the folder */
    if (isset($acls[$new_user])) {
        $acls[$new_user] = $new_acl;
        $new_user = '';
    }
}

$protected = $ACLDriver->getProtected();

/* Run through the action handlers. */
$actionID = Util::getFormData('actionID');
$ok_form = true;
switch ($actionID) {
case 'imp_acl_set':
    if (!$folder) {
        $notification->push(_("No folder selected."), 'horde.error');
        $ok_form = false;
    }

    if ($new_user) {
        /* Each ACL is submitted with the acl as the value. Reverse the hash
           mapping for createACL(). */
        $new_acl = array_flip($new_acl);
        $result = $ACLDriver->createACL($folder, $new_user, $new_acl);
        if (is_a($result, 'PEAR_Error')) {
            $notification->push($result);
        } elseif (!count($new_acl)) {
            $notification->push(sprintf(_("All rights on folder \"%s\" successfully removed for user \"%s\"."), $folder, $new_user), 'horde.success');
        } else {
            $notification->push(sprintf(_("User \"%s\" successfully given the specified rights for the folder \"%s\"."), $new_user, $folder), 'horde.success');
        }
    }

    if ($ok_form) {
        $current_acl = $ACLDriver->getACL($folder);
        foreach ($acls as $user => $acl) {
            if ($acl) {
                $acl = array_flip($acl);
                /* We had to have an empty value submitted to make sure all
                   users with acls were sent back, so we can remove those
                   without checkmarks. */
                unset($acl['']);
            } else {
                $acl = array();
            }

            if (!$user) {
                $notification->push(_("No user specified."), 'horde.error');
                continue;
            }

            if (in_array($user, $protected)) {
                if ($acl) {
                    $notification->push(sprintf(_("Rights for user \"%s\" cannot be modified."), $user), 'horde.error');
                }
                continue;
            }

            /* Check to see if ACL didn't change */
            if ((isset($current_acl[$user])) &&
                (array_keys($current_acl[$user]) == array_keys($acl))) {
                continue;
            }

            $result = $ACLDriver->editACL($folder, $user, $acl);
            if (is_a($result, 'PEAR_Error')) {
                $notification->push($result);
            } elseif (!count($acl)) {
                $notification->push(sprintf(_("All rights on folder \"%s\" successfully removed for user \"%s\"."), $folder, $user), 'horde.success');
            } else {
                $notification->push(sprintf(_("User \"%s\" successfully given the specified rights for the folder \"%s\"."), $user, $folder), 'horde.success');
            }
        }
    }
    break;
}

$imp_folder = &IMP_Folder::singleton();
$rights = $ACLDriver->getRights();
$rightsTitles = $ACLDriver->getRightsTitles();

if (empty($folder)) {
    $folder = 'INBOX';
}

$curr_acl = $ACLDriver->getACL($folder);
$canEdit = $ACLDriver->canEdit($folder, $_SESSION['imp']['user']);

if (is_a($curr_acl, 'PEAR_Error')) {
    $notification->push($curr_acl, 'horde_error');
    $curr_acl = array();
}

require_once 'Horde/Prefs/UI.php';
if (is_callable(array('Horde', 'loadConfiguration'))) {
    $result = Horde::loadConfiguration('prefs.php', array('prefGroups', '_prefs'), 'imp');
    if (!is_a($result, 'PEAR_Error')) {
        extract($result);
    }
} else {
    require IMP_BASE . '/config/prefs.php';
}
$app = 'imp';
$chunk = Util::nonInputVar('chunk');
if ($_SESSION['imp']['default_view'] != 'dimp') {
    Prefs_UI::generateHeader(null, $chunk);
} else {
    require $registry->get('templates', $app) . '/common-header.inc';
    $GLOBALS['notification']->notify(array('listeners' => 'status'));
}

/* Set up template. */
$t = new IMP_Template();
$t->setOption('gettext', true);
$t->set('aclurl', Horde::applicationUrl('acl.php'));
$t->set('forminput', Util::formInput());
$t->set('imp_view', $_SESSION['imp']['default_view'] != 'dimp');
if ($_SESSION['imp']['default_view'] != 'dimp') {
    $t->set('aclnavcell', Util::bufferOutput(array('Prefs_UI', 'generateNavigationCell'), 'acl'));
}
$t->set('changefolder', Horde::link('#', _("Change Folder"), 'smallheader', '', 'ACLFolderChange(true); return false;'));
$t->set('sharedimg', Horde::img('shared.png', _("Change Folder")));
$t->set('options', IMP::flistSelect('', true, array(), $folder));
$t->set('current', sprintf(_("Current access to %s"), IMP::displayFolder($folder)));
$t->set('folder', $folder);
$t->set('noacl', !count($curr_acl));
$t->set('maxrule', 1);
if (!$t->get('noacl')) {
    $i = 0;
    $cval = array();
    foreach ($curr_acl as $index => $rule) {
        $entry = array(
            'i' => ++$i,
            'num_val' => ($i - 1),
            'disabled' => in_array($index, $protected) || !$canEdit,
            'index' => $index
        );
        /* Create table of each ACL option for each user granted permissions,
         * enabled indicates the right has been given to the user */
        foreach (array_keys($rights) as $val) {
            $entry['rule'][] = array('val' => $val, 'enabled'=> isset($rule{$val}));
        }
        $cval[] = $entry;
    }
    $t->set('curr_acl', $cval);
    $t->set('maxval', count($curr_acl));
    /* number of individual ACL options, for table rendering */
    $t->set('maxrule', count($rights));
}
$t->set('canedit', $canEdit);
if (empty($_SESSION['imp']['admin'])) {
    $new_user_field = '<input id="new_user" type="text" name="new_user"/>';
} else {
    require_once IMP_BASE . '/lib/api.php';
    $current_users = array_keys($curr_acl);
    $new_user_field = '<select id="new_user" name="new_user">';
    foreach (_imp_userList() as $user) {
        if (in_array($user, $current_users)) {
            continue;
        }
        $new_user_field .= "\n" . '<option>' . htmlspecialchars($user)
            . '</option>';
    }
    $new_user_field .= "\n</select>";
}
$t->set('new_user', $new_user_field);
$rightsTitlesval = array();
foreach ($rightsTitles as $right => $desc) {
    $rightsval[] = array(
        'right' => $right,
        'desc' => $desc
    );
}
$t->set('rights', $rightsval);
$t->set('width', round(100 / (count($rightsval) + 1)) . '%');
$t->set('prefsurl', $prefs_url);

Horde::addScriptFile('prototype.js', 'imp', true);
Horde::addScriptFile('acl.js', 'imp', true);
echo $t->fetch(IMP_TEMPLATES . '/acl/acl.html');
if (!$chunk) {
    require $registry->get('templates', 'horde') . '/common-footer.inc';
}
