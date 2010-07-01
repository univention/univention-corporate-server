<?php

require_once 'Horde/Auth.php';
require_once 'Horde/DataTree.php';
require_once 'Horde/History.php';
require_once 'Horde/SessionObjects.php';

/** The parent Group node */
define('GROUP_ROOT', -1);

/**
 * The Group:: class provides the Horde groups system.
 *
 * $Horde: framework/Group/Group.php,v 1.67.2.22 2009-01-06 15:23:08 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Stephane Huther <shuther1@free.fr>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 2.1
 * @package Horde_Group
 */
class Group {

    /**
     * Group driver parameters
     *
     * @var array
     */
    var $_params;

    /**
     * Pointer to a DataTree instance to manage the different groups.
     *
     * @var DataTree
     */
    var $_datatree;

    /**
     * Cache of previously retrieved group objects.
     *
     * @var array
     */
    var $_groupCache = array();

    /**
     * Id-name-map of already cached group objects.
     *
     * @var array
     */
    var $_groupMap = array();

    /**
     * Id-name-hash of all existing groups.
     *
     * @var array
     */
    var $_groupList;

    /**
     * List of sub groups.
     *
     * @see listAllUsers()
     * @var array
     */
    var $_subGroups = array();

    /**
     * Cache of parent groups.
     *
     * This is an array with group IDs as keys and the integer group id of the
     * direct parent as values.
     *
     * @see getGroupParent
     * @var array
     */
    var $_groupParents = array();

    /**
     * Cache of parent group trees.
     *
     * This is an array with group IDs as keys and id-name-hashes of all
     * parents as values.
     *
     * @see getGroupParentList
     * @var array
     */
    var $_groupParentList = array();

    /**
     * Cache of parents tree.
     *
     * @see getGroupParents()
     * @var array
     */
    var $_parentTree = array();

    /**
     * Hash of groups of certain users.
     *
     * @see getGroupMemberShips()
     * @var array
     */
    var $_userGroups;

    /**
     * Constructor.
     */
    function Group($params)
    {
        $this->_params = $params;
        $this->__wakeup();
    }

    /**
     * Initializes the object.
     */
    function __wakeup()
    {
        global $conf;

        if (empty($conf['datatree']['driver'])) {
            Horde::fatal('You must configure a DataTree backend to use Groups.', __FILE__, __LINE__);
        }

        $driver = $conf['datatree']['driver'];
        $this->_datatree = &DataTree::singleton($driver,
                                                array_merge(Horde::getDriverConfig('datatree', $driver),
                                                            array('group' => 'horde.groups')));

        foreach (array_keys($this->_groupCache) as $name) {
            $this->_groupCache[$name]->setGroupOb($this);
            $this->_groupCache[$name]->setDataTree($this->_datatree);
        }
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
        if (empty($name)) {
            return PEAR::raiseError(_("Group names must be non-empty"));
        }

        if ($parent != GROUP_ROOT) {
            $name = $this->getGroupName($parent) . ':' . DataTree::encodeName($name);
        }

        $group = &new DataTreeObject_Group($name);
        $group->setGroupOb($this);
        return $group;
    }

    /**
     * Returns a DataTreeObject_Group object corresponding to the named group,
     * with the users and other data retrieved appropriately.
     *
     * @param string $name The name of the group to retrieve.
     */
    function &getGroup($name)
    {
        if (!isset($this->_groupCache[$name])) {
            $this->_groupCache[$name] = &$this->_datatree->getObject($name, 'DataTreeObject_Group');
            if (!is_a($this->_groupCache[$name], 'PEAR_Error')) {
                $this->_groupCache[$name]->setGroupOb($this);
                $this->_groupMap[$this->_groupCache[$name]->getId()] = $name;
            }
        }

        return $this->_groupCache[$name];
    }

    /**
     * Returns a DataTreeObject_Group object corresponding to the given unique
     * ID, with the users and other data retrieved appropriately.
     *
     * @param integer $cid  The unique ID of the group to retrieve.
     */
    function &getGroupById($cid)
    {
        if (isset($this->_groupMap[$cid])) {
            $group = $this->_groupCache[$this->_groupMap[$cid]];
        } else {
            $group = $this->_datatree->getObjectById($cid, 'DataTreeObject_Group');
            if (!is_a($group, 'PEAR_Error')) {
                $group->setGroupOb($this);
                $name = $group->getName();
                $this->_groupCache[$name] = &$group;
                $this->_groupMap[$cid] = $name;
            }
        }

        return $group;
    }

    /**
     * Returns a globally unique ID for a group.
     *
     * @param DataTreeObject_Group $group  The group.
     *
     * @return string  A GUID referring to $group.
     */
    function getGUID($group)
    {
        return 'horde:group:' . $this->getGroupId($group);
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
        if (!is_a($group, 'DataTreeObject_Group')) {
            return PEAR::raiseError('Groups must be DataTreeObject_Group objects or extend that class.');
        }
        $result = $this->_datatree->add($group);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $id = $group->getId();
        $name = $group->getName();
        $this->_groupCache[$name] = &$group;
        $this->_groupMap[$id] = $name;
        if (isset($this->_groupList)) {
            $this->_groupList[$id] = $name;
        }

        /* Log the addition of the group in the history log. */
        $history = &Horde_History::singleton();
        $log = $history->log($this->getGUID($group), array('action' => 'add'), true);
        if (is_a($log, 'PEAR_Error')) {
            return $log;
        }

        return $result;
    }

    /**
     * Stores updated data - users, etc. - of a group to the backend system.
     *
     * @param DataTreeObject_Group $group  The group to update.
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

        $this->_groupCache[$group->getName()] = &$group;

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
     * Removes a group from the groups system permanently.
     *
     * @param DataTreeObject_Group $group  The group to remove.
     * @param boolean $force               Force to remove every child.
     */
    function removeGroup($group, $force = false)
    {
        if (!is_a($group, 'DataTreeObject_Group')) {
            return PEAR::raiseError('Groups must be DataTreeObject_Group objects or extend that class.');
        }

        $id = $group->getId();
        unset($this->_groupMap[$id]);
        if (isset($this->_groupList)) {
            unset($this->_groupList[$id]);
        }
        unset($this->_groupCache[$group->getName()]);

        $history = &Horde_History::singleton();
        $history->log($this->getGUID($group), array('action' => 'delete'), true);

        return $this->_datatree->remove($group, $force);
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
        if (is_a($gid, 'DataTreeObject_Group')) {
            $gid = $gid->getId();
        }

        if (isset($this->_groupMap[$gid])) {
            return $this->_groupMap[$gid];
        }
        if (isset($this->_groupList[$gid])) {
            return $this->_groupList[$gid];
        }

        return $this->_datatree->getName($gid);
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
        return $this->_datatree->getShortName($group);
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
        if (is_a($group, 'DataTreeObject_Group')) {
            $group = $group->getName();
        }

        $id = array_search($group, $this->_groupMap);
        if ($id !== false) {
            return $id;
        }
        if (isset($this->_groupList)) {
            $id = array_search($group, $this->_groupList);
            if ($id !== false) {
                return $id;
            }
        }

        return $this->_datatree->getId($group);
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
        if (isset($this->_groupCache[$group]) ||
            (isset($this->_groupList) &&
             array_search($group, $this->_groupList) !== false)) {
            return true;
        }

        return $this->_datatree->exists($group);
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
        if (!isset($this->_parentTree[$gid])) {
            $name = $this->getGroupName($gid);
            $parents = $this->_datatree->getParents($name);
            if (is_a($parents, 'PEAR_Error')) {
                return $parents;
            }
            $this->_parentTree[$gid] = $parents;
        }

        return $this->_parentTree[$gid];
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
        if (!isset($this->_groupParents[$gid])) {
            $parent = $this->_datatree->getParentById($gid);
            if (is_a($parent, 'PEAR_Error')) {
                return $parent;
            }
            $this->_groupParents[$gid] = $parent;
        }

        return $this->_groupParents[$gid];
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
        if (!isset($this->_groupParentList[$gid])) {
            $parents = $this->_datatree->getParentList($gid);
            if (is_a($parents, 'PEAR_Error')) {
                return $parents;
            }
            $this->_groupParentList[$gid] = $parents;
        }

        return $this->_groupParentList[$gid];
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
        if ($refresh || !isset($this->_groupList)) {
            $this->_groupList = $this->_datatree->get(DATATREE_FORMAT_FLAT, GROUP_ROOT, true);
            unset($this->_groupList[GROUP_ROOT]);
        }

        return $this->_groupList;
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
        $groupOb = &$this->getGroupById($gid);
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
     * @param integer $group  The ID of the parent group.
     *
     * @return array  The complete user list.
     */
    function listAllUsers($gid)
    {
        if (!isset($this->_subGroups[$gid])) {
            // Get a list of every group that is a sub-group of $group.
            $groups = $this->_datatree->get(DATATREE_FORMAT_FLAT, $this->getGroupName($gid), true);
            if (is_a($groups, 'PEAR_Error')) {
                return $groups;
            }
            $this->_subGroups[$gid] = array_keys($groups);
        }

        $users = array();
        foreach ($this->_subGroups[$gid] as $groupId) {
            $users = array_merge($users, $this->listUsers($groupId));
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
        if (!isset($this->_userGroups[$user])) {
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

            $this->_userGroups[$user] = $groups;
        }

        return $this->_userGroups[$user];
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
        if (!$this->exists($this->getGroupName($gid))) {
            return false;
        } elseif ($subgroups) {
            $groups = $this->getGroupMemberships($user, true);
            if (is_a($groups, 'PEAR_Error')) {
                Horde::logMessage($groups, __FILE__, __LINE__, PEAR_LOG_ERR);
                return false;
            }

            return !empty($groups[$gid]);
        } else {
            $users = $this->listUsers($gid);
            if (is_a($users, 'PEAR_Error')) {
                Horde::logMessage($users, __FILE__, __LINE__, PEAR_LOG_ERR);
                return false;
            }
            return in_array($user, $users);
        }
    }

    /**
     * Returns the nesting level of the given group. 0 is returned for any
     * object directly below GROUP_ROOT.
     *
     * @param integer $gid  The DataTree ID of the group.
     *
     * @return The DataTree level of the group.
     */
    function getLevel($gid)
    {
        $name = $this->getGroupName($gid);
        return substr_count($name, ':');
    }

    /**
     * Stores the object in the session cache.
     */
    function shutdown()
    {
        $session = new Horde_SessionObjects();
        $session->overwrite('horde_group', $this, false);
    }

    /**
     * Returns the properties that need to be serialized.
     *
     * @return array  List of serializable properties.
     */
    function __sleep()
    {
        $properties = get_object_vars($this);
        unset($properties['_datatree']);
        $properties = array_keys($properties);
        return $properties;
    }

    /**
     * Attempts to return a concrete Group instance based on $driver.
     *
     * @param mixed $driver  The type of concrete Group subclass to return.
     * @param array $params  A hash containing any additional configuration or
     *                       connection parameters a subclass might need.
     *
     * @return Group  The newly created concrete Group instance, or a
     *                PEAR_Error object on an error.
     */
    function &factory($driver = '', $params = null)
    {
        if (is_null($params)) {
            $params = Horde::getDriverConfig('group', $driver);
        }

        $class = Group::_loadDriver($driver);
        if (class_exists($class)) {
            $group = &new $class($params);
        } else {
            $group = PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }

        return $group;
    }

    /**
     * Attempts to return a reference to a concrete Group instance.
     * It will only create a new instance if no Group instance
     * currently exists.
     *
     * This method must be invoked as: $var = &Group::singleton()
     *
     * @return Group  The concrete Group reference, or false on an error.
     */
    function &singleton()
    {
        static $group;

        if (isset($group)) {
            return $group;
        }

        $group_driver = null;
        $group_params = null;
        $auth = &Auth::singleton($GLOBALS['conf']['auth']['driver']);
        if ($auth->hasCapability('groups')) {
            $group_driver = $auth->getDriver();
            $group_params = $auth;
        } elseif (!empty($GLOBALS['conf']['group']['driver']) &&
                  $GLOBALS['conf']['group']['driver'] != 'datatree') {
            $group_driver = $GLOBALS['conf']['group']['driver'];
            $group_params = Horde::getDriverConfig('group', $group_driver);
        }

        Group::_loadDriver($group_driver);

        $group = null;
        if (!empty($GLOBALS['conf']['group']['cache'])) {
            $session = new Horde_SessionObjects();
            $group = $session->query('horde_group');
        }

        if (!$group) {
            $group = Group::factory($group_driver, $group_params);
        }

        if (!empty($GLOBALS['conf']['group']['cache'])) {
            register_shutdown_function(array(&$group, 'shutdown'));
        }

        return $group;
    }

    function _loadDriver($driver)
    {
        if (!$driver) {
            $class = 'Group';
        } else {
            $driver = basename($driver);
            $class = 'Group_' . $driver;
            if (!class_exists($class)) {
                include 'Horde/Group/' . $driver . '.php';
            }
        }

        return $class;
    }

}

/**
 * Extension of the DataTreeObject class for storing Group information
 * in the Categories driver. If you want to store specialized Group
 * information, you should extend this class instead of extending
 * DataTreeObject directly.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 2.1
 * @package Horde_Group
 */
class DataTreeObject_Group extends DataTreeObject {

    /**
     * The Group object which this group is associated with - needed
     * for updating data in the backend to make changes stick, etc.
     *
     * @var Group
     */
    var $_groupOb;

    /**
     * This variable caches the users added or removed from the group
     * for History logging of user-groups relationship.
     *
     * @var array
     */
    var $_auditLog = array();

    /**
     * The DataTreeObject_Group constructor. Just makes sure to call
     * the parent constructor so that the group's name is set
     * properly.
     *
     * @param string $name  The name of the group.
     */
    function DataTreeObject_Group($name)
    {
        parent::DataTreeObject($name);
    }

    /**
     * Returns the properties that need to be serialized.
     *
     * @return array  List of serializable properties.
     */
    function __sleep()
    {
        $properties = get_object_vars($this);
        unset($properties['datatree'], $properties['_groupOb']);
        $properties = array_keys($properties);
        return $properties;
    }

    /**
     * Associates a Group object with this group.
     *
     * @param Group $groupOb  The Group object.
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
        return $this->_groupOb->updateGroup($this);

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
        if ($update && $this->_groupOb->exists($this->getName())) {
            return $this->save();
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
            return $this->save();
        }
    }

    /**
     * Get a list of every user that is a part of this group
     * (and only this group)
     *
     * @return array  The user list
     */
    function listUsers()
    {
        return $this->_groupOb->listUsers($this->getId());
    }

    /**
     * Get a list of every user that is a part of this group and
     * any of it's subgroups
     *
     * @return array  The complete user list
     */
    function listAllUsers()
    {
        return $this->_groupOb->listAllUsers($this->getId());
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
