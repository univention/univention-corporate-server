<?php
/**
 * The Perms_UI:: class provides UI methods for the Horde permissions
 * system.
 *
 * $Horde: framework/Perms/Perms/UI.php,v 1.27.2.23 2009-01-06 15:23:30 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 2.1
 * @package Horde_Perms
 */
class Perms_UI {

    /**
     * The Perms object we're displaying UI stuff for.
     *
     * @var Perms
     */
    var $_perms;

    /**
     * The Horde_Form object that will be used for displaying the edit form.
     *
     * @var Horde_Form
     */
    var $_form = null;

    /**
     * The Variables object used in Horde_Form.
     *
     * @var Variables
     */
    var $_vars = null;

    /**
     * The permission type.
     *
     * @var string
     */
    var $_type = 'matrix';

    /**
     * Constructor.
     *
     * @param Perms $perms  The Perms object to display UI stuff for.
     */
    function Perms_UI(&$perms)
    {
        $this->_perms = &$perms;
    }

    /**
     * Return a Horde_Tree representation of the permissions tree.
     *
     * @return string  The html showing the permissions as a Horde_Tree.
     */
    function renderTree($current = PERMS_ROOT)
    {
        global $registry;

        require_once 'Horde/Array.php';
        require_once 'Horde/Tree.php';

        /* Get the perms tree. */
        $nodes = &$this->_perms->getTree();

        $icondir = array('icondir' => $GLOBALS['registry']->getImageDir());
        $perms_node = $icondir + array('icon' => 'perms.png');
        $add = Horde::applicationUrl('admin/perms/addchild.php');
        $add_img = Horde::img('add_perm.png', _("Add Permission"));
        $edit = Horde::applicationUrl('admin/perms/edit.php');
        $delete = Horde::applicationUrl('admin/perms/delete.php');
        $edit_img = Horde::img('edit.png', _("Edit Permission"));
        $delete_img = Horde::img('delete.png', _("Delete Permission"));
        $blank_img = Horde::img('blank.gif', '', array('width' => 16, 'height' => 16));

        /* Set up the tree. */
        $tree = &Horde_Tree::singleton('perms_ui', 'javascript');
        $tree->setOption(array('alternate' => true, 'hideHeaders' => true));
        $tree->setHeader(array(array('width' => '50%')));

        foreach ($nodes as $perm_id => $node) {
            $node_class = ($current == $perm_id)
                ? array('class' => 'selected')
                : array();
            if ($perm_id == PERMS_ROOT) {
                $add_link = Horde::link(
                    Util::addParameter($add, 'perm_id', $perm_id),
                    _("Add New Permission"))
                    . $add_img . '</a>';
                $base_node_params = $icondir +
                    array('icon' => 'administration.png');

                $tree->addNode($perm_id, null, _("All Permissions"), 0, true,
                               $base_node_params + $node_class,
                               array($add_link));
            } else {
                $parent_id = $this->_perms->getParent($node);
                if (is_a($parent_id, 'PEAR_Error')) {
                    Horde::fatal($parent_id, __FILE__, __LINE__);
                }

                $perms_extra = array();
                $parents = explode(':', $node);

                if (!in_array($parents[0], $GLOBALS['registry']->listApps())) {
                    // This backend has permissions for an application that is
                    // not installed.  Perhaps the application has been removed
                    // or the backend is shared with other Horde installations.
                    // Skip this app and do not include it in the tree.
                    continue;
                }

                $app_perms = $this->_perms->getApplicationPermissions($parents[0]);
                if (is_a($app_perms, 'PEAR_Error')) {
                    $GLOBALS['notification']->push($app_perms);
                    continue;
                }
                if (isset($app_perms['tree']) &&
                    is_array(Horde_Array::getElement($app_perms['tree'], $parents))) {
                    $add_link = Horde::link(
                        Util::addParameter($add, 'perm_id', $perm_id),
                        _("Add Child Permission"))
                        . $add_img . '</a>';
                    $perms_extra[] = $add_link;
                } else {
                    $perms_extra[] = $blank_img;
                }

                $edit_link = Horde::link(
                    Util::addParameter($edit, 'perm_id', $perm_id),
                    _("Edit Permission"))
                    . $edit_img . '</a>';
                $perms_extra[] = $edit_link;
                $delete_link = Horde::link(
                    Util::addParameter($delete, 'perm_id', $perm_id),
                    _("Delete Permission"))
                    . $delete_img . '</a>';
                $perms_extra[] = $delete_link;
                $name = $this->_perms->getTitle($node);

                $expanded = isset($nodes[$current]) &&
                    strpos($nodes[$current], $node) === 0 &&
                    $nodes[$current] != $node;
                $tree->addNode($perm_id, $parent_id, $name,
                               substr_count($node, ':') + 1, $expanded,
                               $perms_node + $node_class, $perms_extra);
            }
        }

        $tree->sort('label');

        return $tree->renderTree();
    }

    /**
     * Set an existing form object to use for the edit form.
     *
     * @param Horde_Form $form  An existing Horde_Form object to use.
     */
    function setForm(&$form)
    {
        $this->_form = &$form;
    }

    /**
     * Set an existing vars object to use for the edit form.
     *
     * @param Variables $vars  An existing Variables object to use.
     */
    function setVars(&$vars)
    {
        $this->_vars = &$vars;
    }

    /**
     * Create a form to add a permission.
     *
     * @param Perms $permission
     * @param string $force_choice  If the permission to be added can be one of
     *                              many, setting this will force the choice to
     *                              one particular.
     */
    function setupAddForm($permission, $force_choice = null)
    {
        /* Initialise form if required. */
        $this->_formInit();

        $this->_form->setTitle(sprintf(_("Add a child permission to \"%s\""), $this->_perms->getTitle($permission->getName())));
        $this->_form->setButtons(_("Add"));
        $this->_vars->set('perm_id', $this->_perms->getPermissionId($permission));
        $this->_form->addHidden('', 'perm_id', 'text', false);

        /* Set up the actual child adding field. */
        $child_perms = $this->_perms->getAvailable($permission->getName());
        if ($child_perms === false) {
            /* False, so no childs are to be added below this level. */
            $this->_form->addVariable(_("Permission"), 'child', 'invalid', true, false, null, array(_("No children can be added to this permission.")));
        } elseif (is_array($child_perms)) {
            if (!empty($force_choice)) {
                /* Choice array available, but choice being forced. */
                $this->_vars->set('child', $force_choice);
                $this->_form->addVariable(_("Permissions"), 'child', 'enum', true, true, null, array($child_perms));
            } else {
                /* Choice array available, so set up enum field. */
                $this->_form->addVariable(_("Permissions"), 'child', 'enum', true, false, null, array($child_perms));
            }
        }
    }

    /**
     * Function to validate any add form input.
     *
     * @return mixed  Either false if the form does not validate correctly or
     *                an array with all the form values.
     */
    function validateAddForm(&$info)
    {
        if (!$this->_form->validate($this->_vars)) {
            return false;
        }

        $this->_form->getInfo($this->_vars, $info);
        return true;
    }

    /**
     * Create a permission editing form.
     *
     * @param Horde_Permission $permission
     */
    function setupEditForm($permission)
    {
        global $registry;

        /* Initialise form if required. */
        $this->_formInit();

        $this->_form->setButtons(_("Update"), true);
        $perm_id = $this->_perms->getPermissionId($permission);
        $this->_form->addHidden('', 'perm_id', 'text', false);

        /* Get permission configuration. */
        $this->_type = $permission->get('type');
        $params = $permission->get('params');

        /* Default permissions. */
        $perm_val = $permission->getDefaultPermissions();
        $this->_form->setSection('default', _("All Authenticated Users"), Horde::img('perms.png', '', '', $registry->getImageDir('horde')), false);

        /* We MUST use 'deflt' for the variable name because 'default' is a
         * reserved word in JavaScript. */
        if ($this->_type == 'matrix') {
            /* Set up the columns for the permissions matrix. */
            $cols = Perms::getPermsArray();

            /* Define a single matrix row for default perms. */
            $matrix = array();
            $matrix[0] = Perms::integerToArray($perm_val);
            $this->_form->addVariable('', 'deflt', 'matrix', false, false, null, array($cols, array(0 => ''), $matrix));
        } else {
            $var = &$this->_form->addVariable('', 'deflt', $this->_type, false, false, null, $params);
            $var->setDefault($perm_val);
        }

        /* Guest permissions. */
        $perm_val = $permission->getGuestPermissions();
        $this->_form->setSection('guest', _("Guest Permissions"), '', false);

        if ($this->_type == 'matrix') {
            /* Define a single matrix row for guest perms. */
            $matrix = array();
            $matrix[0] = Perms::integerToArray($perm_val);
            $this->_form->addVariable('', 'guest', 'matrix', false, false, null, array($cols, array(0 => ''), $matrix));
        } else {
            $var = &$this->_form->addVariable('', 'guest', $this->_type, false, false, null, $params);
            $var->setDefault($perm_val);
        }

        /* Object creator permissions. */
        $perm_val = $permission->getCreatorPermissions();
        $this->_form->setSection('creator', _("Creator Permissions"), Horde::img('user.png', '', '', $registry->getImageDir('horde')), false);

        if ($this->_type == 'matrix') {
            /* Define a single matrix row for creator perms. */
            $matrix = array();
            $matrix[0] = Perms::integerToArray($perm_val);
            $this->_form->addVariable('', 'creator', 'matrix', false, false, null, array($cols, array(0 => ''), $matrix));
        } else {
            $var = &$this->_form->addVariable('', 'creator', $this->_type, false, false, null, $params);
            $var->setDefault($perm_val);
        }

        /* Users permissions. */
        $perm_val = $permission->getUserPermissions();
        $this->_form->setSection('users', _("Individual Users"), Horde::img('user.png', '', '', $registry->getImageDir('horde')), false);
        $auth = &Auth::singleton($GLOBALS['conf']['auth']['driver']);
        if ($auth->hasCapability('list')) {
            /* The auth driver has list capabilities so set up an array which
             * the matrix field type will recognise to set up an enum box for
             * adding new users to the permissions matrix. */
            $new_users = array();
            $user_list = $auth->listUsers();
            if (is_a($user_list, 'PEAR_Error')) {
                $new_users = true;
            } else {
                sort($user_list);
                foreach ($user_list as $user) {
                    if (!isset($perm_val[$user])) {
                        $new_users[$user] = $user;
                    }
                }
            }
        } else {
            /* No list capabilities, setting to true so that the matrix field
             * type will offer a text input box for adding new users. */
            $new_users = true;
        }

        if ($this->_type == 'matrix') {
            /* Set up the matrix array, breaking up each permission integer
             * into an array.  The keys of this array will be the row
             * headers. */
            $rows = array();
            $matrix = array();
            foreach ($perm_val as $u_id => $u_perms) {
                $rows[$u_id] = $u_id;
                $matrix[$u_id] = Perms::integerToArray($u_perms);
            }
            $this->_form->addVariable('', 'u', 'matrix', false, false, null, array($cols, $rows, $matrix, $new_users));
        } else {
            if ($new_users) {
                if (is_array($new_users)) {
                    $u_n = Util::getFormData('u_n');
                    $u_n = empty($u_n['u']) ? null : $u_n['u'];
                    $user_html = '<select name="u_n[u]"><option value="">' . _("-- select --") . '</option>';
                    foreach ($new_users as $new_user) {
                        $user_html .= '<option value="' . $new_user . '"';
                        $user_html .= $u_n == $new_user ? ' selected="selected"' : '';
                        $user_html .= '>' . htmlspecialchars($new_user) . '</option>';
                    }
                    $user_html .= '</select>';
                } else {
                    $user_html = '<input type="text" name="u_n[u]" />';
                }
                $this->_form->addVariable($user_html, 'u_n[v]', $this->_type, false, false, null, $params);
            }
            foreach ($perm_val as $u_id => $u_perms) {
                $var = &$this->_form->addVariable($u_id, 'u_v[' . $u_id . ']', $this->_type, false, false, null, $params);
                $var->setDefault($u_perms);
            }
        }

        /* Groups permissions. */
        $perm_val = $permission->getGroupPermissions();
        $this->_form->setSection('groups', _("Groups"), Horde::img('group.png', '', '', $registry->getImageDir('horde')), false);
        require_once 'Horde/Group.php';
        $groups = &Group::singleton();
        $group_list = $groups->listGroups();
        if (is_a($group_list, 'PEAR_Error')) {
            $GLOBALS['notification']->push($group_list);
            $group_list = array();
        }

        if (!empty($group_list)) {
            /* There is an available list of groups so set up an array which
             * the matrix field type will recognise to set up an enum box for
             * adding new groups to the permissions matrix. */
            $new_groups = array();
            foreach ($group_list as $groupId => $group) {
                if (!isset($perm_val[$groupId])) {
                    $new_groups[$groupId] = $group;
                }
            }
        } else {
            /* Do not offer a text box to add new groups. */
            $new_groups = false;
        }

        if ($this->_type == 'matrix') {
            /* Set up the matrix array, break up each permission integer into
             * an array. The keys of this array will be the row headers. */
            $rows = array();
            $matrix = array();
            foreach ($perm_val as $g_id => $g_perms) {
                $rows[$g_id] = isset($group_list[$g_id]) ? $group_list[$g_id] : $g_id;
                $matrix[$g_id] = Perms::integerToArray($g_perms);
            }
            $this->_form->addVariable('', 'g', 'matrix', false, false, null, array($cols, $rows, $matrix, $new_groups));
        } else {
            if ($new_groups) {
                if (is_array($new_groups)) {
                    $g_n = Util::getFormData('g_n');
                    $g_n = empty($g_n['g']) ? null : $g_n['g'];
                    $group_html = '<select name="g_n[g]"><option value="">' . _("-- select --") . '</option>';
                    foreach ($new_groups as $groupId => $group) {
                        $group_html .= '<option value="' . $groupId . '"';
                        $group_html .= $g_n == $groupId ? ' selected="selected"' : '';
                        $group_html .= '>' . htmlspecialchars($group) . '</option>';
                    }
                    $group_html .= '</select>';
                } else {
                    $group_html = '<input type="text" name="g_n[g]" />';
                }
                $this->_form->addVariable($group_html, 'g_n[v]', $this->_type, false, false, null, $params);
            }
            foreach ($perm_val as $g_id => $g_perms) {
                $var = &$this->_form->addVariable(isset($group_list[$g_id]) ? $group_list[$g_id] : $g_id, 'g_v[' . $g_id . ']', $this->_type, false, false, null, $params);
                $var->setDefault($g_perms);
            }
        }

        /* Set form title. */
        $this->_form->setTitle(sprintf(_("Edit permissions for \"%s\""), $this->_perms->getTitle($permission->getName())));
    }

    /**
     * Function to validate any edit form input.
     *
     * @return mixed  Either false if the form does not validate correctly or
     *                an array with all the form values.
     */
    function validateEditForm(&$info)
    {
        if (!$this->_form->validate($this->_vars)) {
            return false;
        }

        $this->_form->getInfo($this->_vars, $info);

        if ($this->_type == 'matrix') {
            /* Collapse the array for default/guest/creator. */
            $info['deflt'] = isset($info['deflt'][0]) ? $info['deflt'][0] : null;
            $info['guest']   = isset($info['guest'][0]) ? $info['guest'][0] : null;
            $info['creator'] = isset($info['creator'][0]) ? $info['creator'][0] : null;
        } else {
            $u_n = $this->_vars->get('u_n');
            $info['u'] = array();
            if (!empty($u_n['u'])) {
                $info['u'][$u_n['u']] = $info['u_n']['v'];
            }
            unset($info['u_n']);
            if (isset($info['u_v'])) {
                $info['u'] += $info['u_v'];
                unset($info['u_v']);
            }
            $g_n = $this->_vars->get('g_n');
            $info['g'] = array();
            if (!empty($g_n['g'])) {
                $info['g'][$g_n['g']] = $info['g_n']['v'];
            }
            unset($info['g_n']);
            if (isset($info['g_v'])) {
                $info['g'] += $info['g_v'];
                unset($info['g_v']);
            }
        }
        $info['default'] = $info['deflt'];
        unset($info['deflt']);

        return true;
    }

    /**
     * Create a permission deleting form.
     *
     * @param object $permission
     */
    function setupDeleteForm($permission)
    {
        /* Initialise form if required. */
        $this->_formInit();

        $this->_form->setTitle(sprintf(_("Delete permissions for \"%s\""), $this->_perms->getTitle($permission->getName())));
        $this->_form->setButtons(array(_("Delete"), _("Do not delete")));
        $this->_form->addHidden('', 'perm_id', 'text', false);
        $this->_form->addVariable(sprintf(_("Delete permissions for \"%s\" and any sub-permissions?"), $this->_perms->getTitle($permission->getName())), 'prompt', 'description', false);

    }

    /**
     * Function to validate any delete form input.
     *
     * @return mixed  If the delete button confirmation has been pressed return
     *                true, if any other submit button has been pressed return
     *                false. If form did not validate return null.
     */
    function validateDeleteForm(&$info)
    {
        $form_submit = $this->_vars->get('submitbutton');

        if ($form_submit == _("Delete")) {
            if ($this->_form->validate($this->_vars)) {
                $this->_form->getInfo($this->_vars, $info);
                return true;
            }
        } elseif (!empty($form_submit)) {
            return false;
        }

        return null;
    }

    /**
     * Renders the edit form.
     */
    function renderForm($form_script = 'edit.php')
    {
        require_once 'Horde/Form/Renderer.php';
        $renderer = &new Horde_Form_Renderer();
        $this->_form->renderActive($renderer, $this->_vars, $form_script, 'post');
    }

    /**
     * Creates any form objects if they have not been initialised yet.
     *
     * @access private
     */
    function _formInit()
    {
        if (is_null($this->_vars)) {
            /* No existing vars set, get them now. */
            require_once 'Horde/Variables.php';
            $this->_vars = &Variables::getDefaultVariables();
        }

        if (!is_a($this->_form, 'Horde_Form')) {
            /* No existing valid form object set so set up a new one. */
            require_once 'Horde/Form.php';
            $this->_form = new Horde_Form($this->_vars);
        }
    }

}
