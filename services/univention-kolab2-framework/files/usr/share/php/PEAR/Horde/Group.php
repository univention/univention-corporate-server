<?php

require_once 'Horde/DataTree.php';
require_once 'Horde/History.php';

/**
 * The Group:: class provides the Horde groups system.
 *
 * $Horde: framework/Group/Group.php,v 1.63 2004/04/07 14:43:08 chuck Exp $
 *
 * Copyright 1999-2004 Stephane Huther <shuther@bigfoot.com>
 * Copyright 2001-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Stephane Huther <shuther@bigfoot.com>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.1
 * @package Horde_Group
 */
class Group {

    /**
     * Pointer to a DataTree instance to manage the different groups.
     * @var object DataTree $_datatree
     */
    var $_datatree;

    /**
     * Constructor
     */
    function Group()
    {
        global $conf;

        if (!isset($conf['datatree']['driver'])) {
            Horde::fatal('You must configure a DataTree backend to use Groups.');
        }

        $driver = $conf['datatree']['driver'];
        $this->_datatree = &DataTree::singleton($driver,
                                                array_merge(Horde::getDriverConfig('datatree', $driver),
                                                            array('group' => 'horde.groups')));
    }

    /**
     * Return a new group object.
     *
     * @param string $name The group's name.
     *
     * @return object DataTreeObject_Group A new group object.
     */
    function &newGroup($name)
    {
        if (empty($name)) {
            return PEAR::raiseError(_("Group names must be non-empty"));
        }
        $group = &new DataTreeObject_Group($name);
        $group->setGroupOb($this);
        return $group;
    }

    /**
     * Return a DataTreeObject_Group object corresponding to the named
     * group, with the users and other data retrieved appropriately.
     *
     * @param string $name The name of the group to retrieve.
     */
    function &getGroup($name)
    {
        /* cache of previous retrieved groups */
        static $groupCache;

        if (!is_array($groupCache)) {
            $groupCache = array();
        }

        if (!isset($groupCache[$name])) {
            $groupCache[$name] = $this->_datatree->getObject($name, 'DataTreeObject_Group');
            if (!is_a($groupCache[$name], 'PEAR_Error')) {
                $groupCache[$name]->setGroupOb($this);
            }
        }

        return $groupCache[$name];
    }

    /**
     * Return a DataTreeObject_Group object corresponding to the given
     * unique ID, with the users and other data retrieved
     * appropriately.
     *
     * @param string $cid  The unique ID of the group to retrieve.
     */
    function &getGroupById($cid)
    {
        $group = $this->_datatree->getObjectById($cid, 'DataTreeObject_Group');
        if (!is_a($group, 'PEAR_Error')) {
            $group->setGroupOb($this);
        }
        return $group;
    }

    /**
     * Get a globally unique ID for a group.
     *
     * @param object DataTreeObject_Group $group  The group.
     *
     * @return string  A GUID referring to $group.
     */
    function getGUID($group)
    {
        return 'horde:group:' . $this->getGroupId($group);
    }

    /**
     * Add a group to the groups system. The group must first be
     * created with Group::newGroup(), and have any initial users
     * added to it, before this function is called.
     *
     * @param object DataTreeObject_Group $group The new group object.
     */
    function addGroup($group)
    {
        if (!is_a($group, 'DataTreeObject_Group')) {
            return PEAR::raiseError('Groups must be DataTreeObject_Group objects or extend that class.');
        }
        $result = $this->_datatree->add($group);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        /* Log the addition of the group in the history log. */
        $history = &Horde_History::singleton();
        $history->log($this->getGUID($group), array('action' => 'add'), true);
        return $result;
    }

    /**
     * Store updated data - users, etc. - of a group to the backend
     * system.
     *
     * @param object DataTreeObject_Group $group   The group to update.
     */
    function updateGroup($group)
    {
        if (!is_a($group, 'DataTreeObject_Group')) {
            return PEAR::raiseError('Groups must be DataTreeObject_Group objects or extend that class.');
        }
        $result = $this->_datatree->updateData($group);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        /* Log the update of the group users on the history log. */
        $history = &Horde_History::singleton();
        $guid = $this->getGUID($group);
        foreach ($group->getAuditLog() as $userId => $action) {
            $history->log($guid, array('action' => $action, 'user' => $userId), true);
        }
        $group->clearAuditLog();

        /* Log the group modification. */
        $history->log($guid, array('action' => 'modify'), true);
        return $result;
    }

    /**
     * Change the name of a group without changing its contents or
     * where it is in the groups hierarchy.
     *
     * @param object DataTreeObject_Group $group   The group to rename.
     * @param string                      $newName The group's new name.
     */
    function renameGroup($group, $newName)
    {
        if (!is_a($group, 'DataTreeObject_Group')) {
            return PEAR::raiseError('Groups must be DataTreeObject_Group objects or extend that class.');
        }
        $result = $this->_datatree->rename($group, $newName);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        /* History Log the name change of the group. */
        $history = &Horde_History::singleton();
        $history->log($this->getGUID($group), array('action' => 'rename'), true);
        return $result;
    }

    /**
     * Remove a group from the groups system permanently.
     *
     * @param object DataTreeObject_Group $group  The group to remove.
     *
     * @param optional boolean force [default = false] Force to remove
     *                         every child
     */
    function removeGroup($group, $force = false)
    {
        if (!is_a($group, 'DataTreeObject_Group')) {
            return PEAR::raiseError('Groups must be DataTreeObject_Group objects or extend that class.');
        }

        $history = &Horde_History::singleton();
        $history->log($this->getGUID($group), array('action' => 'delete'), true);

        return $this->_datatree->remove($group, $force);
    }

    /**
     * Retrieve the name of a group.
     *
     * @param integer $groupId  The id of the group to retrieve the name for..
     *
     * @return string  The group's name.
     */
    function getGroupName($groupId)
    {
        if (is_a($groupId, 'DataTreeObject_Group')) {
            return $this->_datatree->getName($groupId->getId());
        } else {
            return $this->_datatree->getName($groupId);
        }
    }

    /**
     * Retrieve the ID of a group.
     *
     * @param string $group  The group to retrieve the ID for..
     *
     * @return integer  The group's ID.
     */
    function getGroupId($group)
    {
        if (is_a($group, 'DataTreeObject_Group')) {
            return $this->_datatree->getId($group->getName());
        } else {
            return $this->_datatree->getId($group);
        }
    }

    /**
     * Check if a group exists in the system.
     *
     * @param string $group           The group to check.
     *
     * @return boolean true if the group exists, false otherwise.
     */
    function exists($group)
    {
        return $this->_datatree->exists($group);
    }

    /**
     * Get a list of the parents of a child group.
     *
     * @param string $group The name of the child group.
     *
     * @return array
     */
    function getGroupParents($group)
    {
        return $this->_datatree->getParents($group);
    }

    /**
     * Get a list of every group, in the format cid => groupname.
     *
     * @return array  CID => groupname hash.
     */
    function listGroups()
    {
        static $groups;

        if (is_null($groups)) {
            $groups = $this->_datatree->get(DATATREE_FORMAT_FLAT, '-1', true);
            unset($groups['-1']);
        }

        return $groups;
    }

    /**
     * Get a list of every user that is a part of this group ONLY.
     *
     * @param string $group  The name of the group.
     *
     * @return array  The user list.
     * @access public
     */
    function listUsers($group)
    {
        $groupOb = &$this->getGroup($group);
        if (is_a($groupOb, 'PEAR_Error')) {
            return $groupOb;
        }

        if (!isset($groupOb->data['users']) ||
            !is_array($groupOb->data['users'])) {
            return array();
        }

        return array_keys($groupOb->data['users']);
    }

    /**
     * Get a list of every user that is part of the specified group
     * and any of its subgroups.
     *
     * @access public
     *
     * @param string $group  The name of the parent group.
     *
     * @return array  The complete user list.
     */
    function listAllUsers($group)
    {
        // Get a list of every group that is a sub-group of $group.
        $groups = $this->_datatree->get(DATATREE_FORMAT_FLAT, $group, true);
        if (is_a($groups, 'PEAR_Error')) {
            return $groups;
        }

        $groups = array($group) + $groups;
        $users = array();
        foreach ($groups as $group) {
            $users = array_merge($users, $this->listUsers($group));
        }
        return array_values(array_flip(array_flip($users)));
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
        static $cache;

        if (empty($cache[$user])) {
            $criteria = array(
                'AND' => array(
                    array('field' => 'name', 'op' => '=', 'test' => 'user'),
                    array('field' => 'key', 'op' => '=', 'test' => $user)));
            $groups = $this->_datatree->getByAttributes($criteria);

            if (is_a($groups, 'PEAR_Error')) {
                return $groups;
            }

            if ($parentGroups) {
                foreach ($groups as $id => $g) {
                    $parents = $this->_datatree->getParentList($id);
                    if (is_a($parents, 'PEAR_Error')) {
                        return $parents;
                    }
                    $groups += $parents;
                }
            }

            $cache[$user] = $groups;
        }

        return $cache[$user];
    }

    /**
     * Say if a user is a member of a group or not.
     *
     * @param          string  $user       The name of the user.
     * @param          string  $group      The name of the group.
     * @param optional boolean $subgroups  Return true if the user is in any subgroups
     *                                     of $group, also.
     *
     * @return boolean
     * @access public
     */
    function userIsInGroup($user, $group, $subgroups = true)
    {
        if (!$this->exists($group)) {
            return false;
        } elseif ($subgroups) {
            $groups = $this->getGroupMemberships($user, true);
            if (is_a($groups, 'PEAR_Error')) {
                return $groups;
            }

            return !empty($groups[$this->getGroupId($group)]);
        } else {
            $users = $this->listUsers($group);
            if (is_a($users, 'PEAR_Error')) {
                return $users;
            }
            return in_array($user, $users);
        }
    }

    /**
     * Attempts to return a concrete Group instance based on $driver.
     *
     * @access public
     *
     * @param mixed $driver           The type of concrete Group subclass to
     *                                return. The code is dynamically
     *                                included.
     * @param optional array $params  A hash containing any additional
     *                                configuration or connection parameters a
     *                                subclass might need.
     *
     * @return object Group   The newly created concrete Group instance, or a
     *                        PEAR_Error object on an error.
     */
    function &factory($driver = '', $params = null)
    {
        $driver = basename($driver);

        if (@file_exists(dirname(__FILE__) . '/Group/' . $driver . '.php')) {
            require_once dirname(__FILE__) . '/Group/' . $driver . '.php';
        } else {
            @include_once 'Horde/Group/' . $driver . '.php';
        }
        $class = 'Group_' . $driver;
        if (class_exists($class)) {
            return $ret = &new $class($params);
        } else {
            return PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }
    }

    /**
     * Attempts to return a reference to a concrete Group instance.
     * It will only create a new instance if no Group instance
     * currently exists.
     *
     * This method must be invoked as: $var = &Group::singleton()
     *
     * @return object Group  The concrete Group reference, or false on an
     *                       error.
     */
    function &singleton()
    {
        static $group;

        if (!isset($group)) {
            global $conf;

            require_once 'Horde/Auth.php';
            $auth = &Auth::singleton($conf['auth']['driver']);
            if ($auth->hasCapability('groups')) {
                $group = &Group::factory($auth->getDriver(), $auth);
            } elseif (!empty($conf['group']['driver']) && $conf['group']['driver'] != 'datatree') {
                $group = &Group::factory($conf['group']['driver']);
            } else {
                $group = new Group();
            }
        }

        return $group;
    }

}

/**
 * Extension of the DataTreeObject class for storing Group information
 * in the Categories driver. If you want to store specialized Group
 * information, you should extend this class instead of extending
 * DataTreeObject directly.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.1
 * @package Horde_Group
 */
class DataTreeObject_Group extends DataTreeObject {

    /**
     * The Group object which this group is associated with - needed
     * for updating data in the backend to make changes stick, etc.
     *
     * @var object Group $_groupOb
     */
    var $_groupOb;

    /**
     * This variable caches the users added or removed from the group
     * for History logging of user-groups relationship.
     *
     * @var array $_auditLog
     */
    var $_auditLog = array();

    /**
     * The DataTreeObject_Group constructor. Just makes sure to call
     * the parent constructor so that the group's name is set
     * properly.
     *
     * @param string $name The name of the group.
     */
    function DataTreeObject_Group($name)
    {
        parent::DataTreeObject($name);
    }

    /**
     * Associates a Group object with this group.
     *
     * @param object Group $groupOb The Group object.
     */
    function setGroupOb(&$groupOb)
    {
        $this->_groupOb = &$groupOb;
    }

    /**
     * Fetch the ID of this group
     *
     * @return string The group's ID
     */
    function getId()
    {
        return $this->_groupOb->getGroupId($this);
    }

    /**
     * Save any changes to this object to the backend permanently.
     */
    function save()
    {
        $this->_groupOb->updateGroup($this);
    }

    /**
     * Adds a user to this group, and makes sure that the backend is
     * updated as well.
     *
     * @param string $username The user to add.
     */
    function addUser($username, $update = true)
    {
        $this->data['users'][$username] = 1;
        $this->_auditLog[$username] = 'addUser';
        if ($update && $this->_groupOb->_datatree->exists($this->getName())) {
            $this->save();
        }
    }

    /**
     * Removes a user from this group, and makes sure that the backend
     * is updated as well.
     *
     * @param string $username The user to remove.
     */
    function removeUser($username, $update = true)
    {
        unset($this->data['users'][$username]);
        $this->_auditLog[$username] = 'deleteUser';
        if ($update) {
            $this->save();
        }
    }

    /**
     * Get a list of every user that is a part of this group
     * (and only this group)
     *
     * @return array The user list
     * @access public
     */
    function listUsers()
    {
        return $this->_groupOb->listUsers($this->name);
    }

    /**
     * Get a list of every user that is a part of this group and
     * any of it's subgroups
     *
     * @return array The complete user list
     * @access public
     */
    function listAllUsers()
    {
        return $this->_groupOb->listAllUsers($this->name);
    }

    /**
     * Get all the users recently added or removed from the group.
     */
    function getAuditLog()
    {
        return $this->_auditLog;
    }

    /**
     * Clears the audit log. To be called after group update.
     */
    function clearAuditLog()
    {
        $this->_auditLog = array();
    }

    /**
     * Map this object's attributes from the data array into a format
     * that we can store in the attributes storage backend.
     *
     * @return array  The attributes array.
     */
    function _toAttributes()
    {
        // Default to no attributes.
        $attributes = array();

        // Loop through all users, if any.
        if (isset($this->data['users']) && is_array($this->data['users']) && count($this->data['users'])) {
            foreach ($this->data['users'] as $user => $active) {
                $attributes[] = array('name' => 'user',
                                      'key' => $user,
                                      'value' => $active);
            }
        }
        $attributes[] = array('name' => 'email',
                              'key' => '',
                              'value' => $this->get('email'));

        return $attributes;
    }

    /**
     * Take in a list of attributes from the backend and map it to our
     * internal data array.
     *
     * @param array $attributes  The list of attributes from the
     *                           backend (attribute name, key, and value).
     */
    function _fromAttributes($attributes)
    {
        // Initialize data array.
        $this->data['users'] = array();

        foreach ($attributes as $attr) {
            if ($attr['name'] == 'user') {
                $this->data['users'][$attr['key']] = $attr['value'];
            } else {
                $this->data[$attr['name']] = $attr['value'];
            }
        }
    }

}
