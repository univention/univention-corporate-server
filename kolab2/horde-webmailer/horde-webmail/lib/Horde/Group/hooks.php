<?php
/**
 * The Group_hooks:: class provides the Horde groups system with the
 * addition of adding support for hook functions to define if a user
 * is in a group.
 *
 * $Horde: framework/Group/Group/hooks.php,v 1.7.2.16 2009-01-06 15:23:08 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jason Rust <jrust@rustyparts.com>
 * @since   Horde 3.0
 * @package Horde_Group
 */
class Group_hooks extends Group {

    var $_hookFunction = false;

    /**
     * Constructor.
     */
    function Group_hooks($params)
    {
        parent::Group($params);
        Horde::loadConfiguration('hooks.php', null, 'horde');
        $this->_hookFunction = function_exists('_group_hook');
    }

    /**
     * Get a list of every group that $user is in.
     *
     * @param string  $user          The user to get groups for.
     * @param boolean $parentGroups  Also return the parents of any groups?
     *
     * @return array  An array of all groups the user is in.
     */
    function getGroupMemberships($user, $parentGroups = false)
    {
        $memberships = parent::getGroupMemberships($user, $parentGroups);
        if (!$this->_hookFunction) {
            return $memberships;
        }

        $groups = $this->listGroups();
        foreach ($groups as $gid => $groupName) {
            if (empty($memberships[$gid]) && _group_hook($groupName, $user)) {
                $memberships += array($gid => $groupName);
            }

            if ($parentGroups) {
                $parents = $this->getGroupParentList($gid);
                if (is_a($parents, 'PEAR_Error')) {
                    return $parents;
                }

                $memberships += $parents;
            }
        }

        return $memberships;
    }

    /**
     * Say if a user is a member of a group or not.
     *
     * @param string  $user       The name of the user.
     * @param integer $gid        The ID of the group.
     * @param boolean $subgroups  Return true if the user is in any subgroups
     *                            of $group, also.
     *
     * @return boolean
     */
    function userIsInGroup($user, $gid, $subgroups = true)
    {
        $inGroup = ($this->_hookFunction && _group_hook($this->getGroupName($gid), $user));
        return ($inGroup || parent::userIsInGroup($user, $gid, $subgroups));
    }

}
