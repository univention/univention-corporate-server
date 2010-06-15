<?php
/**
 * $Horde: horde/admin/perms/addchild.php,v 1.20 2004/04/07 14:43:01 chuck Exp $
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

$form = &Horde_Form::singleton('', $vars);

/* Depending on what level set relative title and type of child to add. */
if ($cid == '-1') {
    $pname = _("All Permissions");
    $cid_name = '';
} else {
    $permission = &$perms->getPermissionById($cid);
    if (is_a($permission, 'PEAR_Error')) {
        $notification->push(_("Invalid parent permission."), 'horde.error');
        $url = Horde::applicationUrl('admin/perms/index.php', true);
        header('Location: ' . $url);
        exit;
    }
    $pname = $perms->getTitle($permission->getName());
    $cid_name = $permission->getName();
}

/* Set up form. */
$form->setTitle(Horde::img('perms.gif') . ' ' . sprintf(_("Add a child permission to '%s'"), $pname));
$form->setButtons(_("Add"), true);
$form->addHidden('', 'cid', 'text', false);

/* Set up the actual child adding field. */
$child_perms = $perms->getAvailable($cid_name);
if ($child_perms === false) {
    /* False, so no childs are to be added below this level. */
    $form->addVariable(_("No child permissions are to be added below this level."), 'child', 'description', false);
} elseif (is_array($child_perms)) {
    /* Choice array available, so set up enum field. */
    $form->addVariable(_("Permission"), 'child', 'enum', true, false, null, array($child_perms));
} else {
    /* No choices returned, so give a free form text field. */
    $form->addVariable(_("Permission"), 'child', 'text', true);
}

if ($form->validate($vars)) {
    $form->getInfo($vars, $info);

    if ($info['cid'] == '-1') {
        $child = &$perms->newPermission($info['child']);
        $result = $perms->addPermission($child);
    } else {
        $pOb = &$perms->getPermissionById($info['cid']);
        $name = $pOb->getName() . ':' . DataTree::encodeName($info['child']);
        $child = &$perms->newPermission($name);
        $result = $perms->addPermission($child);
    }
    if (is_a($result, 'PEAR_Error')) {
        $notification->push(sprintf(_("'%s' was not created: %s."), $child->getShortName(), $result->getMessage()), 'horde.error');
    } else {
        $notification->push(sprintf(_("'%s' was added to the permissions system."), $child->getShortName()), 'horde.success');
        $permission = &$child;
        $url = Horde::applicationUrl('admin/perms/edit.php', true);
        $url = Util::addParameter($url, 'cid', $permission->getId());
        header('Location: ' . $url);
        exit;
    }
}

$title = _("Permissions Administration");
require HORDE_TEMPLATES . '/common-header.inc';
require HORDE_TEMPLATES . '/admin/common-header.inc';
$notification->notify(array('listeners' => 'status'));

/* Render the form. */
$renderer = &new Horde_Form_Renderer();
$form->renderActive($renderer, $vars, 'addchild.php', 'post');

echo '<br />';

require_once 'Horde/Perms/UI.php';
$ui = &new Perms_UI($perms);
$ui->renderTree($cid);

require HORDE_TEMPLATES . '/common-footer.inc';
