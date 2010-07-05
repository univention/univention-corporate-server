<?php
/**
 * $Horde: horde/admin/perms/edit.php,v 1.38.2.9 2009-01-06 15:22:10 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 * @author Jan Schneider <jan@horde.org>
 */

@define('HORDE_BASE', dirname(__FILE__) . '/../..');
require_once HORDE_BASE . '/lib/base.php';

if (!Auth::isAdmin()) {
    Horde::authenticationFailureRedirect();
}

/* Set up the form variables. */
require_once 'Horde/Variables.php';
$vars = &Variables::getDefaultVariables();
$perm_id = $vars->get('perm_id');
$category = $vars->get('category');

/* See if we need to (and are supposed to) autocreate the permission. */
if ($category !== null) {
    $permission = &$perms->getPermission($category);
    if (is_a($permission, 'PEAR_Error') && Util::getFormData('autocreate')) {

        /* Check to see if the permission we are copying from exists before we
         * autocreate. */
        $copyFrom = Util::getFormData('autocreate_copy');
        if ($copyFrom && !$perms->exists($copyFrom)) {
            $copyFrom = null;
        }

        $parent = $vars->get('parent');
        $permission = &$perms->newPermission($category);
        $result = $perms->addPermission($permission, $parent);
        if (!is_a($result, 'PEAR_Error')) {
            $form = 'edit.inc';
            $perm_id = $perms->getPermissionId($permission);
        }

        if ($copyFrom) {
            /* We have autocreated the permission and we have been told to
             * copy an existing permission for the defaults. */
            $copyFromObj = &$perms->getPermission($copyFrom);
            $permission->addGuestPermission($copyFromObj->getGuestPermissions(), false);
            $permission->addDefaultPermission($copyFromObj->getDefaultPermissions(), false);
            $permission->addCreatorPermission($copyFromObj->getCreatorPermissions(), false);
            foreach ($copyFromObj->getUserPermissions() as $user => $uperm) {
                $permission->addUserPermission($user, $uperm, false);
            }
            foreach ($copyFromObj->getGroupPermissions() as $group => $gperm) {
                $permission->addGroupPermission($group, $gperm, false);
            }
        } else {
            /* We have autocreated the permission and we don't have an
             * existing permission to copy.  See if some defaults were
             * supplied. */
            $addPerms = Util::getFormData('autocreate_guest');
            if ($addPerms) {
                $permission->addGuestPermission($addPerms, false);
            }
            $addPerms = Util::getFormData('autocreate_default');
            if ($addPerms) {
                $permission->addDefaultPermission($addPerms, false);
            }
            $addPerms = Util::getFormData('autocreate_creator');
            if ($addPerms) {
                $permission->addCreatorPermission($addPerms, false);
            }
        }
        $permission->save();
    } else {
        $perm_id = $perms->getPermissionId($permission);
    }
    $vars->set('perm_id', $perm_id);
} else {
    $permission = &$perms->getPermissionById($perm_id);
}

/* If the permission fetched is an error return to the permissions list. */
if (is_a($permission, 'PEAR_Error')) {
    $notification->push(_("Attempt to edit a non-existent permission."), 'horde.error');
    $url = Horde::applicationUrl('admin/perms/index.php', true);
    header('Location: ' . $url);
    exit;
}

require_once 'Horde/Perms/UI.php';
$ui = &new Perms_UI($perms);
$ui->setVars($vars);
$ui->setupEditForm($permission);

if ($ui->validateEditForm($info)) {
    /* Update and save the permissions. */
    $permission->updatePermissions($info);
    $permission->save();
    $notification->push(sprintf(_("Updated \"%s\"."), $perms->getTitle($permission->getName())), 'horde.success');
    $url = Util::addParameter('admin/perms/edit.php', 'perm_id', $permission->getId());
    $url = Horde::applicationUrl($url, true);
    header('Location: ' . $url);
    exit;
}

$title = _("Permissions Administration");
require HORDE_TEMPLATES . '/common-header.inc';
require HORDE_TEMPLATES . '/admin/menu.inc';

/* Render the form and tree. */
$ui->renderForm('edit.php');
echo '<br />';
$ui->renderTree($perm_id);

require HORDE_TEMPLATES . '/common-footer.inc';
