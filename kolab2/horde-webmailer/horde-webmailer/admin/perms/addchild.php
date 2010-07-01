<?php
/**
 * $Horde: horde/admin/perms/addchild.php,v 1.27.2.9 2009-01-06 15:22:10 jan Exp $
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

$permission = &$perms->getPermissionById($perm_id);
if (is_a($permission, 'PEAR_Error')) {
    $notification->push(_("Invalid parent permission."), 'horde.error');
    $url = Horde::applicationUrl('admin/perms/index.php', true);
    header('Location: ' . $url);
    exit;
}

/* Set up form. */
require_once 'Horde/Perms/UI.php';
$ui = &new Perms_UI($perms);
$ui->setVars($vars);
$ui->setupAddForm($permission);

if ($ui->validateAddForm($info)) {
    if ($info['perm_id'] == PERMS_ROOT) {
        $child = &$perms->newPermission($info['child']);
        $result = $perms->addPermission($child);
    } else {
        $pOb = &$perms->getPermissionById($info['perm_id']);
        $name = $pOb->getName() . ':' . str_replace(':', '.', $info['child']);
        $child = &$perms->newPermission($name);
        $result = $perms->addPermission($child);
    }
    if (is_a($result, 'PEAR_Error')) {
        $notification->push(sprintf(_("\"%s\" was not created: %s."), $perms->getTitle($child->getName()), $result->getMessage()), 'horde.error');
    } else {
        $notification->push(sprintf(_("\"%s\" was added to the permissions system."), $perms->getTitle($child->getName())), 'horde.success');
        $url = Horde::applicationUrl('admin/perms/edit.php', true);
        $url = Util::addParameter($url, 'perm_id', $child->getId(), false);
        header('Location: ' . $url);
        exit;
    }
}

$title = _("Permissions Administration");
require HORDE_TEMPLATES . '/common-header.inc';
require HORDE_TEMPLATES . '/admin/menu.inc';

/* Render the form and tree. */
$ui->renderForm('addchild.php');
echo '<br />';
$ui->renderTree($perm_id);

require HORDE_TEMPLATES . '/common-footer.inc';
