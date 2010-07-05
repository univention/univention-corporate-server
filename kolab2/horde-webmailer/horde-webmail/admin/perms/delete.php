<?php
/**
 * $Horde: horde/admin/perms/delete.php,v 1.19.8.8 2009-01-06 15:22:10 jan Exp $
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
$permission = &$perms->getPermissionById($perm_id);

/* If the permission fetched is an error return to permissions list. */
if (is_a($permission, 'PEAR_Error')) {
    $notification->push(_("Attempt to delete a non-existent permission."), 'horde.error');
    $url = Horde::applicationUrl('admin/perms/index.php', true);
    header('Location: ' . $url);
    exit;
}

/* Set up form. */
require_once 'Horde/Perms/UI.php';
$ui = &new Perms_UI($perms);
$ui->setVars($vars);
$ui->setupDeleteForm($permission);

if ($confirmed = $ui->validateDeleteForm($info)) {
    $result = $perms->removePermission($permission, true);
    if (is_a($result, 'PEAR_Error')) {
        $notification->push(sprintf(_("Unable to delete \"%s\": %s."), $perms->getTitle($permission->getName()), $result->getMessage()), 'horde.error');
    } else {
        $notification->push(sprintf(_("Successfully deleted \"%s\"."), $perms->getTitle($permission->getName())), 'horde.success');
        $url = Horde::applicationUrl('admin/perms/index.php', true);
        header('Location: ' . $url);
        exit;
    }
} elseif ($confirmed === false) {
    $notification->push(sprintf(_("Permission \"%s\" not deleted."), $perms->getTitle($permission->getName())), 'horde.success');
    $url = Horde::applicationUrl('admin/perms/index.php', true);
    header('Location: ' . $url);
    exit;
}

$title = _("Permissions Administration");
require HORDE_TEMPLATES . '/common-header.inc';
require HORDE_TEMPLATES . '/admin/menu.inc';

/* Render the form and tree. */
$ui->renderForm('delete.php');
echo '<br />';
$ui->renderTree($perm_id);

require HORDE_TEMPLATES . '/common-footer.inc';
