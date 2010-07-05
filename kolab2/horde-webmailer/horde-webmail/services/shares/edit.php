<?php
/**
 * $Horde: horde/services/shares/edit.php,v 1.26.10.20 2009-11-07 13:20:19 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

$fieldsList['show'] = 0;
$fieldsList['read'] = 1;
$fieldsList['edit'] = 2;
$fieldsList['delete'] = 3;

@define('HORDE_BASE', dirname(__FILE__) . '/../..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Share.php';
require_once 'Horde/Group.php';

// Exit if the user shouldn't be able to change share permissions.
if (!empty($conf['share']['no_sharing'])) {
    exit('permission denied');
}

$app = Util::getFormData('app');
$shares = &Horde_Share::singleton($app);
$groups = &Group::singleton();
$auth = &Auth::singleton($conf['auth']['driver']);
if ($registry->hasMethod('shareHelp', $app)) {
    require_once 'Horde/Help.php';
    $help = $registry->callByPackage($app, 'shareHelp');
} else {
    $help = null;
}

$form = null;
$reload = false;
$actionID = Util::getFormData('actionID', 'edit');
switch ($actionID) {
case 'edit':
    $share = &$shares->getShareById(Util::getFormData('cid'));
    if (!is_a($share, 'PEAR_Error')) {
        $form = 'edit.inc';
        $perm = &$share->getPermission();
    } elseif (($category = Util::getFormData('share')) !== null) {
        $share = &$shares->getShare($category);
        if (!is_a($share, 'PEAR_Error')) {
            $form = 'edit.inc';
            $perm = &$share->getPermission();
        }
    }
    if (is_a($share, 'PEAR_Error')) {
        $notification->push($share, 'horde.error');
    } elseif (isset($share) && Auth::getAuth() != $share->get('owner')) {
        exit('permission denied');
    }
    break;

case 'editform':
    $share = &$shares->getShareById(Util::getFormData('cid'));
    if (is_a($share, 'PEAR_Error')) {
        $notification->push(_("Attempt to edit a non-existent share."), 'horde.error');
    } else {
        if (Auth::getAuth() != $share->get('owner')) {
            exit('permission denied');
        }
        $perm = &$share->getPermission();

        // Process owner and owner permissions.
        $old_owner = $share->get('owner');
        $new_owner_backend = Util::getFormData('owner_select', Util::getFormData('owner_input', $old_owner));
        $new_owner = Auth::addHook($new_owner_backend);
        if ($old_owner !== $new_owner && !empty($new_owner)) {
            if ($old_owner != Auth::getAuth() && !Auth::isAdmin()) {
                $notification->push(_("Only the owner or system administrator may change ownership or owner permissions for a share"), 'horde.error');
            } elseif ($auth->hasCapability('list') && !$auth->exists($new_owner_backend)) {
                $notification->push(sprintf(_("The user \"%s\" does not exist."), $new_owner_backend), 'horde.error');
            } else {
                $share->set('owner', $new_owner);
                $share->save();
            }
        }

        // Process default permissions.
        if (Util::getFormData('default_show')) {
            $perm->addDefaultPermission(PERMS_SHOW, false);
        } else {
            $perm->removeDefaultPermission(PERMS_SHOW, false);
        }
        if (Util::getFormData('default_read')) {
            $perm->addDefaultPermission(PERMS_READ, false);
        } else {
            $perm->removeDefaultPermission(PERMS_READ, false);
        }
        if (Util::getFormData('default_edit')) {
            $perm->addDefaultPermission(PERMS_EDIT, false);
        } else {
            $perm->removeDefaultPermission(PERMS_EDIT, false);
        }
        if (Util::getFormData('default_delete')) {
            $perm->addDefaultPermission(PERMS_DELETE, false);
        } else {
            $perm->removeDefaultPermission(PERMS_DELETE, false);
        }

        // Process guest permissions.
        if (Util::getFormData('guest_show')) {
            $perm->addGuestPermission(PERMS_SHOW, false);
        } else {
            $perm->removeGuestPermission(PERMS_SHOW, false);
        }
        if (Util::getFormData('guest_read')) {
            $perm->addGuestPermission(PERMS_READ, false);
        } else {
            $perm->removeGuestPermission(PERMS_READ, false);
        }
        if (Util::getFormData('guest_edit')) {
            $perm->addGuestPermission(PERMS_EDIT, false);
        } else {
            $perm->removeGuestPermission(PERMS_EDIT, false);
        }
        if (Util::getFormData('guest_delete')) {
            $perm->addGuestPermission(PERMS_DELETE, false);
        } else {
            $perm->removeGuestPermission(PERMS_DELETE, false);
        }

        // Process creator permissions.
        if (Util::getFormData('creator_show')) {
            $perm->addCreatorPermission(PERMS_SHOW, false);
        } else {
            $perm->removeCreatorPermission(PERMS_SHOW, false);
        }
        if (Util::getFormData('creator_read')) {
            $perm->addCreatorPermission(PERMS_READ, false);
        } else {
            $perm->removeCreatorPermission(PERMS_READ, false);
        }
        if (Util::getFormData('creator_edit')) {
            $perm->addCreatorPermission(PERMS_EDIT, false);
        } else {
            $perm->removeCreatorPermission(PERMS_EDIT, false);
        }
        if (Util::getFormData('creator_delete')) {
            $perm->addCreatorPermission(PERMS_DELETE, false);
        } else {
            $perm->removeCreatorPermission(PERMS_DELETE, false);
        }

        // Process user permissions.
        $u_names = Util::getFormData('u_names');
        $u_show = Util::getFormData('u_show');
        $u_read = Util::getFormData('u_read');
        $u_edit = Util::getFormData('u_edit');
        $u_delete = Util::getFormData('u_delete');

        foreach ($u_names as $key => $user_backend) {
            // Apply backend hooks
            $user = Auth::addHook($user_backend);
            // If the user is empty, or we've already set permissions
            // via the owner_ options, don't do anything here.
            if (empty($user) || $user == $new_owner) {
                continue;
            }
            if ($auth->hasCapability('list') && !$auth->exists($user_backend)) {
                $notification->push(sprintf(_("The user \"%s\" does not exist."), $user_backend), 'horde.error');
                continue;
            }

            if (!empty($u_show[$key])) {
                $perm->addUserPermission($user, PERMS_SHOW, false);
            } else {
                $perm->removeUserPermission($user, PERMS_SHOW, false);
            }
            if (!empty($u_read[$key])) {
                $perm->addUserPermission($user, PERMS_READ, false);
            } else {
                $perm->removeUserPermission($user, PERMS_READ, false);
            }
            if (!empty($u_edit[$key])) {
                $perm->addUserPermission($user, PERMS_EDIT, false);
            } else {
                $perm->removeUserPermission($user, PERMS_EDIT, false);
            }
            if (!empty($u_delete[$key])) {
                $perm->addUserPermission($user, PERMS_DELETE, false);
            } else {
                $perm->removeUserPermission($user, PERMS_DELETE, false);
            }
        }

        // Process group permissions.
        $g_names = Util::getFormData('g_names');
        $g_show = Util::getFormData('g_show');
        $g_read = Util::getFormData('g_read');
        $g_edit = Util::getFormData('g_edit');
        $g_delete = Util::getFormData('g_delete');

        foreach ($g_names as $key => $group) {
            if (empty($group)) {
                continue;
            }

            if (!empty($g_show[$key])) {
                $perm->addGroupPermission($group, PERMS_SHOW, false);
            } else {
                $perm->removeGroupPermission($group, PERMS_SHOW, false);
            }
            if (!empty($g_read[$key])) {
                $perm->addGroupPermission($group, PERMS_READ, false);
            } else {
                $perm->removeGroupPermission($group, PERMS_READ, false);
            }
            if (!empty($g_edit[$key])) {
                $perm->addGroupPermission($group, PERMS_EDIT, false);
            } else {
                $perm->removeGroupPermission($group, PERMS_EDIT, false);
            }
            if (!empty($g_delete[$key])) {
                $perm->addGroupPermission($group, PERMS_DELETE, false);
            } else {
                $perm->removeGroupPermission($group, PERMS_DELETE, false);
            }
        }

        $result = $share->setPermission($perm, false);
        if (is_a($result, 'PEAR_Error')) {
            $notification->push($result, 'horde.error');
        } else {
            $result = $share->save();
            if (is_a($result, 'PEAR_Error')) {
                $notification->push($result, 'horde.error');
            } else {
                if (Util::getFormData('save_and_finish')) {
                    Util::closeWindowJS();
                    exit;
                }
                $notification->push(sprintf(_("Updated \"%s\"."), $share->get('name')), 'horde.success');
            }
        }

        $form = 'edit.inc';
    }
    break;
}

if (is_a($share, 'PEAR_Error')) {
    $title = _("Edit permissions");
} else {
    $title = sprintf(_("Edit permissions for \"%s\""), $share->get('name'));
}

if ($auth->hasCapability('list')) {
    $userList = $auth->listUsers();
    if (is_a($userList, 'PEAR_Error')) {
        Horde::logMessage($userList, __FILE__, __LINE__, PEAR_LOG_ERR);
        $userList = array();
    }
    sort($userList);
} else {
    $userList = array();
}

if (!empty($conf['share']['any_group'])) {
    $groupList = $groups->listGroups();
} else {
    $groupList = $groups->getGroupMemberships(Auth::getAuth(), true);
}
if (is_a($groupList, 'PEAR_Error')) {
    Horde::logMessage($groupList, __FILE__, __LINE__, PEAR_LOG_NOTICE);
    $groupList = array();
}
asort($groupList);

require HORDE_TEMPLATES . '/common-header.inc';
$notification->notify(array('listeners' => 'status'));
if (!empty($form)) {
    require HORDE_TEMPLATES . '/shares/' . $form;
}

require HORDE_TEMPLATES . '/common-footer.inc';
