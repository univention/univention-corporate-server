<?php
/**
 * The Perms_UI:: class provides UI methods for the Horde permissions
 * system.
 *
 * $Horde: framework/Perms/Perms/UI.php,v 1.15 2004/04/07 14:43:11 chuck Exp $
 *
 * Copyright 2001-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.1
 * @package Horde_Perms
 */
class Perms_UI {

    /**
     * The Perms object we're displaying UI stuff for.
     * @var object Perms $_perms
     */
    var $_perms;

    /**
     * The Horde_Form object that will be used for displaying the edit form.
     * @var object Horde_Form $_form
     */
    var $_form = null;

    /**
     * The Variables object used in Horde_Form.
     * @var object Variables $_vars
     */
    var $_vars = null;

    function Perms_UI(&$perms)
    {
        $this->_perms = &$perms;
    }

    /**
     * Return a Horde_Tree representation of the permissions tree.
     *
     * @return string  The html showing the permissions as a Horde_Tree.
     */
    function renderTree($current = -1)
    {
        require_once 'Horde/Tree.php';

        /* Get the perms tree. */
        $nodes = $this->_perms->_datatree->get(DATATREE_FORMAT_FLAT, -1, true);

        $spacer = '&nbsp;&nbsp;&nbsp;&nbsp;';
        $icondir = array('icondir' => $GLOBALS['registry']->getParam('graphics'));
        $perms_node = $icondir + array('icon' => 'perms.gif');
        $add = Horde::applicationUrl('admin/perms/addchild.php');
        $edit = Horde::applicationUrl('admin/perms/edit.php');
        $delete = Horde::applicationUrl('admin/perms/delete.php');
        $edit_img = Horde::img('edit.gif', _("Edit Permission"), 'hspace="2"');
        $delete_img = Horde::img('delete.gif', _("Delete Permission"), 'hspace="2"');

        /* Set up the tree. */
        $tree = &Horde_Tree::singleton('datatree', 'javascript');
        $tree->setOption(array('border' => '0', 'class' => 'item', 'cellpadding' => '0', 'cellspacing' => '0', 'alternate' => true));

        foreach ($nodes as $cid => $node) {
            $node_class = ($current == $cid) ? array('class' => 'selected') : array();
            if ($cid == -1) {
                $add_img = Horde::img('perms.gif', _("Add New Permission"), 'hspace="2"');
                $add_link = Horde::link(Util::addParameter($add, 'cid', $cid), _("Add New Permission")) . $add_img . '</a>';

                $base_node_params = $icondir + array('icon' => 'administration.gif');
                $tree->addNode($cid, null, _("All Permissions"), 0, true, $base_node_params + $node_class, array($spacer, $add_link));
            } else {
                $add_img = Horde::img('perms.gif', _("Add Child Permission"), 'hspace="2"');
                $add_link = Horde::link(Util::addParameter($add, 'cid', $cid), _("Add Child Permission")) . $add_img . '</a>';
                $edit_link = Horde::link(Util::addParameter($edit, 'cid', $cid), _("Edit Permission")) . $edit_img . '</a>';
                $delete_link = Horde::link(Util::addParameter($delete, 'cid', $cid), _("Delete Permission")) . $delete_img . '</a>';

                $parent_id = $this->_perms->_datatree->getParent($node);
                $perms_extra = array($spacer, $add_link, $edit_link, $delete_link);
                $tree->addNode($cid, $parent_id, DataTree::getShortName($node), substr_count($node, ':') + 1, false, $perms_node + $node_class, $perms_extra);
            }
        }

        return $tree->renderTree();
    }

    /**
     * Set an existing form object to use for the edit form.
     *
     * @access public
     *
     * @param object Horde_Form $form  An existing Horde_Form object to use.
     */
    function &setForm(&$form)
    {
        $this->_form = &$form;
    }
    
    /**
     * Set an existing vars object to use for the edit form.
     *
     * @access public
     *
     * @param object Variables $vars  An existing Variables object
     *                                      to use.
     */
    function &setVars(&$vars)
    {
        $this->_vars = &$vars;
    }

    /**
     * Create a form to add a permission.
     *
     * @access public
     *
     * @param object $permission
     * @param optional string $force_choice  If the permission to be added
     *                                       can be one of many, setting this
     *                                       will force the choice to one
     *                                       particular.
     */
    function setupAddForm($permission, $force_choice = null)
    {
        /* Initialise form if required. */
        $this->_formInit();

        $this->_form->setTitle(Horde::img('perms.gif', '', '', $GLOBALS['registry']->getParam('graphics', 'horde')) . ' ' . sprintf(_("Add a child permission to '%s'"), $permission->getName()));
        $this->_form->setButtons(_("Add"), true);
        $this->_vars->set('parent_perm_id', $this->_perms->getPermissionId($permission));
        $this->_form->addHidden('', 'parent_perm_id', 'text', false);

        /* Set up the actual child adding field. */
        $child_perms = $this->_perms->getAvailable($permission->getName());
        if ($child_perms === false) {
            /* False, so no childs are to be added below this level. */
            $this->_form->addVariable(_("No child permissions are to be added below this level."), 'child', 'description', false);
        } elseif (is_array($child_perms)) {
            if (!empty($force_choice)) {
                /* Choice array available, but choice being forced. */
                $this->_vars->set('child', $force_choice);
                $this->_form->addVariable(_("Permissions for"), 'child', 'enum', true, true, null, array($child_perms));
            } else {
                /* Choice array available, so set up enum field. */
                $this->_form->addVariable(_("Permissions for"), 'child', 'enum', true, false, null, array($child_perms));
            }
        } else {
            /* No choices returned, so give a free form text field. */
            $this->_form->addVariable(_("Permissions for"), 'child', 'text', true);
        }

    }

    /**
     * Function to validate any add form input.
     *
     * @access public
     *
     * @returns mixed  Either false if the form does not validate correctly
     *                 or an array with all the form values.
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
     * @access public
     *
     * @param object $permission
     */
    function setupEditForm($permission)
    {
        /* Initialise form if required. */
        $this->_formInit();

        $this->_form->setButtons(_("Update"), true);
        $perm_id = $this->_perms->getPermissionId($permission);
        $this->_form->addHidden('', 'perm_id', 'text', false);

        /* Set up the columns for the permissions matrix. */
        $cols = Perms::getPermsArray();

        /* Default permissions. */
        $perm_val = $permission->getDefaultPermissions();

        /* Define a single matrix row for default perms. */
        $matrix = array();
        $matrix[0] = Perms::integerToArray($perm_val);
        $this->_form->setSection('default', Horde::img('perms.gif', '', '', $GLOBALS['registry']->getParam('graphics', 'horde')) . ' ' . _("Default Permissions"), false);
        $this->_form->addVariable(_("Default permissions"), 'default', 'matrix', false, false, null, array($cols, array(0 => ''), $matrix));

        /* Guest permissions. */
        $perm_val = $permission->getGuestPermissions();

        /* Define a single matrix row for guest perms. */
        $matrix = array();
        $matrix[0] = Perms::integerToArray($perm_val);
        $this->_form->setSection('guest', Horde::img('guest.gif', '', '', $GLOBALS['registry']->getParam('graphics', 'horde')) . ' ' . _("Guest Permissions"), false);
        $this->_form->addVariable(_("Guest permissions"), 'guest', 'matrix', false, false, null, array($cols, array(0 => ''), $matrix));

        /* Object creator permissions. */
        $perm_val = $permission->getCreatorPermissions();

        /* Define a single matrix row for creator perms. */
        $matrix = array();
        $matrix[0] = Perms::integerToArray($perm_val);
        $this->_form->setSection('creator', Horde::img('user.gif', '', '', $GLOBALS['registry']->getParam('graphics', 'horde')) . ' ' . _("Creator Permissions"), false);
        $this->_form->addVariable(_("Object creator permissions"), 'creator', 'matrix', false, false, null, array($cols, array(0 => ''), $matrix));

        /* Users permissions. */
        $perm_val = $permission->getUserPermissions();
        $this->_form->setSection('users', Horde::img('user.gif', '', '', $GLOBALS['registry']->getParam('graphics', 'horde')) . ' ' . _("Users"), false);
        $auth = &Auth::singleton($GLOBALS['conf']['auth']['driver']);
        if ($auth->hasCapability('list')) {
            /* The auth driver has list capabilities so set up an array which
             * the matrix field type will recognise to set up an enum box for
             * adding new users to the permissions matrix. */
            $new_users = array();
            $user_list = $auth->listUsers();
            foreach ($user_list as $user) {
                if (!isset($perm_val[$user])) {
                    $new_users[$user] = $user;
                }
            }
        } else {
            /* No list capabilities, setting to true so that the matrix field
             * type will offer a text input box for adding new users. */
            $new_users = true;
        }

        /* Set up the matrix array, breaking up each permission integer into
         * an array.  The keys of this array will be the row headers. */
        $rows = array();
        $matrix = array();
        foreach ($perm_val as $u_id => $u_perms) {
            $rows[$u_id] = $u_id;
            $matrix[$u_id] = Perms::integerToArray($u_perms);
        }
        $this->_form->addVariable(_("User permissions"), 'u', 'matrix', false, false, null, array($cols, $rows, $matrix, $new_users));

        /* Groups permissions. */
        $perm_val = $permission->getGroupPermissions();
        $this->_form->setSection('groups', Horde::img('group.gif', '', '', $GLOBALS['registry']->getParam('graphics', 'horde')) . ' ' . _("Groups"), false);
        require_once 'Horde/Group.php';
        $groups = &Group::singleton();
        $group_list = $groups->listGroups();
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

        /* Set up the matrix array, break up each permission integer into an
         * array. The keys of this array will be the row headers. */
        $rows = array();
        $matrix = array();
        foreach ($perm_val as $g_id => $g_perms) {
            $rows[$g_id] = isset($group_list[$g_id]) ? $group_list[$g_id] : $g_id;
            $matrix[$g_id] = Perms::integerToArray($g_perms);
        }
        $this->_form->addVariable(_("Group permissions"), 'g', 'matrix', false, false, null, array($cols, $rows, $matrix, $new_groups));

        /* Set form title. */
        $this->_form->setTitle(Horde::img('edit.gif', '', '', $GLOBALS['registry']->getParam('graphics', 'horde')) . ' ' . sprintf(_("Edit permissions for '%s'"), $this->_perms->getTitle($permission->getName())));
    }

    /**
     * Function to validate any edit form input.
     *
     * @access public
     *
     * @returns mixed  Either false if the form does not validate correctly
     *                 or an array with all the form values.
     */
    function validateEditForm(&$info)
    {
        if (!$this->_form->validate($this->_vars)) {
            return false;
        }

        $this->_form->getInfo($this->_vars, $info);

        /* Collapse the array for default/guest/creator. */
        $info['default'] = isset($info['default'][0]) ? $info['default'][0] : null;
        $info['guest']   = isset($info['guest'][0]) ? $info['guest'][0] : null;
        $info['creator'] = isset($info['creator'][0]) ? $info['creator'][0] : null;
        return true;
    }

    /**
     * Create a permission deleting form.
     *
     * @access public
     *
     * @param object $permission
     */
    function setupDeleteForm($permission)
    {
        /* Initialise form if required. */
        $this->_formInit();

        $this->_form->setTitle(Horde::img('delete.gif', '', '', $GLOBALS['registry']->getParam('graphics', 'horde')) . ' ' . sprintf(_("Delete permissions for '%s'"), $this->_perms->getTitle($permission->getName())));
        $this->_form->setButtons(array(_("Delete"), _("Do not delete")));
        $this->_form->addHidden('', 'perm_id', 'text', false);
        $this->_form->addVariable(sprintf(_("Delete permissions for '%s' and any sub-permissions?"), $this->_perms->getTitle($permission->getName())), 'prompt', 'description', false);

    }

    /**
     * Function to validate any delete form input.
     *
     * @access public
     *
     * @returns mixed  If the delete button confirmation has been pressed
     *                 return true, if any other submit button has been
     *                 pressed return false. If form did not validate return
     *                 null.
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
     *
     * @access public
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
            $this->_form = &Horde_Form::singleton('', $this->_vars);
        }
    }

}
