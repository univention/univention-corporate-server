<?php
/**
 * $Horde: horde/admin/groups.php,v 1.41 2004/04/16 22:46:55 chuck Exp $
 *
 * Copyright 1999, 2000, 2001 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Menu.php';
require_once 'Horde/Group.php';
require_once 'Horde/Tree.php';

if (!Auth::isAdmin()) {
    Horde::authenticationFailureRedirect();
}

$groups = &Group::singleton();
$auth = &Auth::singleton($conf['auth']['driver']);

$form = null;
$reload = false;
$actionID = Util::getFormData('actionID');
switch ($actionID) {

case 'addchild':
    if (Util::getFormData('cid') == '-1') {
        $form = 'addchild.inc';
        $gname = _("All Groups");
    } else {
        $group = &$groups->getGroupById(Util::getFormData('cid'));
        if (!is_a($group, 'PEAR_Error')) {
            $gname = $group->getShortName();
            $form = 'addchild.inc';
        }
    }
    break;

case 'addchildform':
    $parent = Util::getFormData('cid');
    if ($parent == '-1') {
        $child = &$groups->newGroup(Util::getFormData('child'));
        $result = $groups->addGroup($child);
    } else {
        $pOb = &$groups->getGroupById($parent);
        $name = $pOb->getName() . ':' . DataTree::encodeName(Util::getFormData('child'));
        $child = &$groups->newGroup($name);
        $result = $groups->addGroup($child);
    }
    if (is_a($result, 'PEAR_Error')) {
        $notification->push(sprintf(_("'%s' was not created: %s."), $child->getShortName(), $result->getMessage()), 'horde.error');
    } else {
        $notification->push(sprintf(_("'%s' was added to the groups system."), $child->getShortName()), 'horde.success');
        $group = &$child;
        $form = 'edit.inc';
        $reload = true;
    }
    break;

case 'delete':
    $group = &$groups->getGroupById(Util::getFormData('cid'));
    if (!is_a($group, 'PEAR_Error')) {
        $form = 'delete.inc';
    }
    break;

case 'deleteform':
    if (Util::getFormData('confirm') == _("Delete")) {
        $group = &$groups->getGroupById(Util::getFormData('cid'));
        if (is_a($group, 'PEAR_Error')) {
            $notification->push(_("Attempt to delete a non-existent group."), 'horde.error');
        } else {
            $result = $groups->removeGroup($group, true);
            if (is_a($result, 'PEAR_Error')) {
                $notification->push(sprintf(_("Unable to delete '%s': %s."), $group->getShortName(), $result->getMessage()), 'horde.error');
             } else {
                $notification->push(sprintf(_("Successfully deleted '%s'."), $group->getShortName()), 'horde.success');
                $reload = true;
            }
        }
    }
    break;

case 'edit':
    $group = &$groups->getGroupById(Util::getFormData('cid'));
    if (!is_a($group, 'PEAR_Error')) {
        $form = 'edit.inc';
    } elseif (($category = Util::getFormData('category')) !== null) {
        $group = &$groups->getGroup($category);
        if (!is_a($group, 'PEAR_Error')) {
            $form = 'edit.inc';
        } elseif (Util::getFormData('autocreate')) {
            $parent = Util::getFormData('parent');
            $group = &$groups->newGroup($category);
            $result = $groups->addGroup($group, $parent);
            if (!is_a($result, 'PEAR_Error')) {
                $form = 'edit.inc';
            }
        }
    }
    break;

case 'editform':
    $group = &$groups->getGroupById(Util::getFormData('cid'));

    // Add any new users.
    $newuser = Util::getFormData('new_user');
    if (!empty($newuser)) {
        if (is_array($newuser)) {
            foreach ($newuser as $new) {
                $group->addUser($new, false);
            }
        } else {
            $group->addUser($newuser, false);
        }
    }

    // Remove any users marked for purging.
    $removes = Util::getFormData('remove');
    if (!empty($removes) && is_array($removes)) {
        foreach ($removes as $user => $junk) {
            $group->removeUser($user, false);
        }
    }

    // Set the email address of the group.
    $group->set('email', Util::getFormData('email'));

    // Save the group to the backend.
    $group->save();

    $notification->push(sprintf(_("Updated '%s'."), $group->getShortName()), 'horde.success');
    $form = 'edit.inc';
    $reload = true;
    break;
}

switch ($form) {
 case 'addchild.inc':
     $notification->push('document.add_child.child.focus()', 'javascript');
     break;
}

$title = _("Group Administration");
require HORDE_TEMPLATES . '/common-header.inc';
require HORDE_TEMPLATES . '/admin/common-header.inc';
$notification->notify(array('listeners' => 'status'));
if (!empty($form)) {
    include HORDE_TEMPLATES . '/admin/groups/' . $form;
}

/* Get the perms tree. */
$nodes = $groups->_datatree->get(DATATREE_FORMAT_FLAT, -1, true);

/* Set up some node params. */
$spacer = '&nbsp;&nbsp;&nbsp;&nbsp;';
$current = Util::getFormData('cid');
$icondir = array('icondir' => $registry->getParam('graphics'));
$group_node = $icondir + array('icon' => 'group.gif');
$add = Horde::applicationUrl('admin/groups.php?actionID=addchild');
$edit = Horde::applicationUrl('admin/groups.php?actionID=edit');
$delete = Horde::applicationUrl('admin/groups.php?actionID=delete');
$edit_img = Horde::img('edit.gif', _("Edit Group"), 'hspace="2"');
$delete_img = Horde::img('delete.gif', _("Delete Group"), 'hspace="2"');

/* Set up the tree. */
$tree = &Horde_Tree::singleton('datatree', 'javascript');
$tree->setOption(array('border' => '0', 'class' => 'item', 'cellpadding' => '0', 'cellspacing' => '0', 'alternate' => true));

$current_parents = $groups->_datatree->getParentList($current);

foreach ($nodes as $cid => $node) {
    $node_class = ($current == $cid) ? array('class' => 'selected') : array();
    if ($cid == -1) {
        $add_img = Horde::img('group.gif', _("Add New Group"), 'hspace="2"');
        $add_link = Horde::link(Util::addParameter($add, 'cid', $cid), _("Add New Group")) . $add_img . '</a>';

        $base_node_params = $icondir + array('icon' => 'administration.gif');
        $tree->addNode($cid, null, _("All Groups"), 0, true, $base_node_params + $node_class, array($spacer, $add_link));
    } else {
        $add_img = Horde::img('group.gif', _("Add Child Group"), 'hspace="2"');
        $add_link = Horde::link(Util::addParameter($add, 'cid', $cid), _("Add Child Group")) . $add_img . '</a>';
        $edit_link = Horde::link(Util::addParameter($edit, 'cid', $cid), _("Edit Group")) . $edit_img . '</a>';
        $delete_link = Horde::link(Util::addParameter($delete, 'cid', $cid), _("Delete Group")) . $delete_img . '</a>';

        $parent_id = $groups->_datatree->getParent($node);
        $group_extra = array($spacer, $add_link, $edit_link, $delete_link);
        $tree->addNode($cid, $parent_id, DataTree::getShortName($node), substr_count($node, ':') + 1, (isset($current_parents[$cid])) ? true : false, $group_node + $node_class, $group_extra);
    }
}

$tree->renderTree();
require HORDE_TEMPLATES . '/common-footer.inc';
