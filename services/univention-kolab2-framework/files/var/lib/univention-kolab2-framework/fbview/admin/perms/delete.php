<?php
/**
 * $Horde: horde/admin/perms/delete.php,v 1.16 2004/04/07 14:43:01 chuck Exp $
 *
 * Copyright 1999, 2000, 2001 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

define('HORDE_BASE', dirname(__FILE__) . '/../..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Menu.php';
require_once 'Horde/Group.php';
require_once 'Horde/Tree.php';

/* Form libraries. */
require_once 'Horde/Form.php';
require_once 'Horde/Form/Renderer.php';
require_once 'Horde/Variables.php';

if (!Auth::isAdmin()) {
    Horde::authenticationFailureRedirect();
}

$groups = &Group::singleton();
$auth = &Auth::singleton($conf['auth']['driver']);

/* Set up the form variables. */
$vars = &Variables::getDefaultVariables();
$cid = $vars->get('cid');
$category = $vars->get('category');
$permission = &$perms->getPermissionById($cid);
$form_submit = $vars->get('submitbutton');

/* If the permission fetched is an error return to permissions list. */
if (is_a($permission, 'PEAR_Error')) {
    $notification->push(_("Attempt to delete a non-existent permission."), 'horde.error');
    $url = Horde::applicationUrl('admin/perms/index.php', true);
    header('Location: ' . $url);
    exit;
}

$form = &Horde_Form::singleton('', $vars);

$form->setButtons(array(_("Delete"), _("Do not delete")));
$form->addHidden('', 'cid', 'text', false);
$form->addVariable(_("Delete this permission and any sub-permissions?"), 'prompt', 'description', false);

$form->setTitle(Horde::img('delete.gif') . ' ' . sprintf(_("Delete permissions for '%s'"), $perms->getTitle($permission->getName())));

if ($form_submit == _("Delete")) {
    $form->validate($vars);
    if ($form->isValid()) {
        $form->getInfo($vars, $info);

        $result = $perms->removePermission($permission, true);
        if (is_a($result, 'PEAR_Error')) {
            $notification->push(sprintf(_("Unable to delete '%s': %s."), $permission->getShortName(), $result->getMessage()), 'horde.error');
        } else {
            $notification->push(sprintf(_("Successfully deleted '%s'."), $permission->getShortName()), 'horde.success');
            $url = Horde::applicationUrl('admin/perms/index.php', true);
            header('Location: ' . $url);
            exit;
        }
    }
} elseif (!empty($form_submit)) {
    $notification->push(sprintf(_("Permission '%s' not deleted."), $permission->getShortName()), 'horde.success');
    $url = Horde::applicationUrl('admin/perms/index.php', true);
    header('Location: ' . $url);
    exit;
}

$title = _("Permissions Administration");
require HORDE_TEMPLATES . '/common-header.inc';
require HORDE_TEMPLATES . '/admin/common-header.inc';
$notification->notify(array('listeners' => 'status'));

/* Render the form. */
$renderer = &new Horde_Form_Renderer();
$form->renderActive($renderer, $vars, 'delete.php', 'post');

echo '<br />';

require_once 'Horde/Perms/UI.php';
$ui = &new Perms_UI($perms);
$ui->renderTree($cid);

require HORDE_TEMPLATES . '/common-footer.inc';
