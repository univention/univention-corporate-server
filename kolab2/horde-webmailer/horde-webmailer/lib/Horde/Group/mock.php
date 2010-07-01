<?php
/**
 * The Group:: class provides the Horde groups system.
 *
 * $Horde: framework/Group/Group/mock.php,v 1.1.2.3 2009-01-06 15:23:08 jan Exp $
 *
 * Copyright 2008-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Duck <duck@obala.net>
 * @since   Horde 3.2
 * @package Horde_Group
 */
class Group_mock extends Group {

    /**
     * Constructor.
     */
    function Group_mock()
    {
    }

    /**
     * Initializes the object.
     */
    function __wakeup()
    {
    }

    /**
     * Returns a new group object.
     *
     * @param string $name    The group's name.
     * @param string $parent  The group's parent's name.
     *
     * @return DataTreeObject_Group  A new group object.
     */
    function &newGroup($name, $parent = GROUP_ROOT)
    {
        return PEAR::raiseError(_("Unsupported"));
    }

    /**
     * Returns a DataTreeObject_Group object corresponding to the named group,
     * with the users and other data retrieved appropriately.
     *
     * @param string $name The name of the group to retrieve.
     */
    function &getGroup($name)
    {
        return PEAR::raiseError(_("Unsupported"));
    }

    /**
     * Returns a DataTreeObject_Group object corresponding to the given unique
     * ID, with the users and other data retrieved appropriately.
     *
     * @param integer $cid  The unique ID of the group to retrieve.
     */
    function &getGroupById($cid)
    {
        return PEAR::raiseError(_("Unsupported"));
    }

    /**
     * Adds a group to the groups system. The group must first be created with
     * Group::newGroup(), and have any initial users added to it, before this
     * function is called.
     *
     * @param DataTreeObject_Group $group  The new group object.
     */
    function addGroup($group)
    {
        return PEAR::raiseError(_("Unsupported"));
    }

    /**
     * Stores updated data - users, etc. - of a group to the backend system.
     *
     * @param DataTreeObject_Group $group  The group to update.
     */
    function updateGroup($group)
    {
        return PEAR::raiseError(_("Unsupported"));
    }

    /**
     * Removes a group from the groups system permanently.
     *
     * @param DataTreeObject_Group $group  The group to remove.
     * @param boolean $force               Force to remove every child.
     */
    function removeGroup($group, $force = false)
    {
        return PEAR::raiseError(_("Unsupported"));
    }

    /**
     * Retrieves the name of a group.
     *
     * @param integer|DataTreeObject_Group $gid  The id of the group or the
     *                                           group object to retrieve the
     *                                           name for.
     *
     * @return string  The group's name.
     */
    function getGroupName($gid)
    {
        return '';
    }

    /**
     * Strips all parent references off of the given group name.
     *
     * @param string $group  Name of the group.
     *
     * @return The name of the group without parents.
     */
    function getGroupShortName($group)
    {
        return '';
    }

    /**
     * Retrieves the ID of a group.
     *
     * @param string|DataTreeObject_Group $group  The group name or object to
     *                                            retrieve the ID for.
     *
     * @return integer  The group's ID.
     */
    function getGroupId($group)
    {
        return '';
    }

    /**
     * Check if a group exists in the system.
     *
     * @param string $group  The group to check.
     *
     * @return boolean  True if the group exists, false otherwise.
     */
    function exists($group)
    {
        return false;
    }

    /**
     * Returns a tree of the parents of a child group.
     *
     * @param integer $gid  The id of the child group.
     *
     * @return array  The group parents tree, with groupnames as the keys.
     */
    function getGroupParents($gid)
    {
        return array();
    }

    /**
     * Returns the single parent ID of the given group.
     *
     * @param integer $gid  The DataTree ID of the child group.
     *
     * @return integer  The parent of the given group.
     */
    function getGroupParent($gid)
    {
        return null;
    }

    /**
     * Returns a flat list of the parents of a child group
     *
     * @param integer $gid  The id of the group.
     *
     * @return array  A flat list of all of the parents of $group, hashed in
     *                $id => $name format.
     */
    function getGroupParentList($gid)
    {
        return array();
    }

    /**
     * Returns a list of all groups, in the format id => groupname.
     *
     * @param boolean $refresh  If true, the cached value is ignored and the
     *                          group list is refreshed from the group backend.
     *
     * @return array  ID => groupname hash.
     */
    function listGroups($refresh = false)
    {
        return array();
    }

    /**
     * Get a list of every user that is a part of this group ONLY.
     *
     * @param integer $gid  The ID of the group.
     *
     * @return array  The user list.
     */
    function listUsers($gid)
    {
        return array();
    }

    /**
     * Get a list of every user that is part of the specified group
     * and any of its subgroups.
     *
     * @param integer $group  The ID of the parent group.
     *
     * @return array  The complete user list.
     */
    function listAllUsers($gid)
    {
        return array();
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
        return array();
    }

    /**
     * Say if a user is a member of a group or not.
     *
     * @param string $user        The name of the user.
     * @param integer $gid        The ID of the group.
     * @param boolean $subgroups  Return true if the user is in any subgroups
     *                            of group with ID $gid, also.
     *
     * @return boolean
     */
    function userIsInGroup($user, $gid, $subgroups = true)
    {
        return false;
    }

    /**
     * Returns the nesting level of the given group. 0 is returned for any
     * object directly below GROUP_ROOT.
     *
     * @param integer $gid  The ID of the group.
     *
     * @return The nesting level of the group.
     */
    function getLevel($gid)
    {
        return 0;
    }

    /**
     * Stores the object in the session cache.
     */
    function shutdown()
    {
    }

    /**
     * Returns the properties that need to be serialized.
     *
     * @return array  List of serializable properties.
     */
    function __sleep()
    {
    }

}
