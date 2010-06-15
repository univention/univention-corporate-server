<?php
/**
 * The Group_hooks:: class provides the Horde groups system with the
 * addition of adding support for hook functions to define if a user
 * is in a group.
 *
 * $Horde: framework/Group/Group/hooks.php,v 1.5 2004/02/21 19:49:08 chuck Exp $
 *
 * Copyright 2003-2004 Jason Rust <jrust@rustyparts.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jason Rust <jrust@rustyparts.com>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Group
 */
class Group_hooks extends Group {

    /**
     * Constructor.
     */
    function Group_hooks()
    {
        parent::Group();
        require $GLOBALS['registry']->getParam('fileroot', 'horde') . '/config/hooks.php';
    }

    /**
     * Get a list of every group that $user is in.
     *
     * @param string $user  The user to get groups for.
     *
     * @return array  An array of all groups the user is in.
     */
    function getGroupMemberships($user)
    {
        $memberships = parent::getGroupMemberships($user);
        $funcs = get_defined_functions();
        foreach ($funcs['user'] as $funcName) {
            if (strpos($funcName, '_group_hook_') === 0) {
                $groupName = substr($funcName, 12);
                if (!in_array($groupName, $memberships) &&
                    $this->exists($groupName) &&
                    call_user_func($funcName, $user)) {
                    $memberships[] = $groupName;
                }
            }
        }

        return $memberships;
    }

    /**
     * Say if a user is a member of a group or not.
     *
     * @param          string  $user       The name of the user.
     * @param          string  $group      The name of the group.
     * @param optional boolean $subgroups  Return true if the user is in any subgroups
     *                                     of $group, also.
     *
     * @access public
     * @return boolean
     */
    function userIsInGroup($user, $group, $subgroups = false)
    {
        if ($this->hasHook($group)) {
            if (call_user_func($this->_getGroupHookName($group), $user)) {
                $inGroup = true;
            } else {
                $inGroup = false;
            }
        } else {
            $inGroup = false;
        }

        if ($inGroup || parent::userIsInGroup($user, $group, $subgroups)) {
            return true;
        } else {
            return false;
        }
    }

    /**
     * Determines if a group has a hook associated with it.
     *
     * @param string $name  The group name.
     *
     * @access public
     * @return boolean  True if the group has a hook, false otherwise
     */
    function hasHook($name)
    {
        return function_exists($this->_getGroupHookName($name));
    }

    /**
     * Returns the name of the hook function.
     *
     * @param string $name  The group name.
     *
     * @access public
     * @return string  The function name for the hook for this group
     */
    function _getGroupHookName($name)
    {
        return '_group_hook_' . str_replace(':', '__', $name);
    }

}
