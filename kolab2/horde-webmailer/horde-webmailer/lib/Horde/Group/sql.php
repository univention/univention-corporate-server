<?php
/**
 * The Group:: class provides the Horde groups system.
 *
 * $Horde: framework/Group/Group/sql.php,v 1.1.2.12 2009-02-25 05:35:42 chuck Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Duck <duck@obala.net>
 * @since   Horde 3.2
 * @package Horde_Group
 */
class Group_sql extends Group {

    /**
     * Boolean indicating whether or not we're connected to the SQL server.
     *
     * @var boolean
     */
    var $_connected = false;

    /**
     * Handle for the current database connection.
     *
     * @var DB
     */
    var $_db;

    /**
     * Handle for the current database connection, used for writing. Defaults
     * to the same handle as $db if a separate write database is not required.
     *
     * @var DB
     */
    var $_write_db;

    /**
     * Constructor.
     */
    function Group_sql($params)
    {
        $this->_params = $params;
    }

    /**
     * Initializes the object.
     */
    function __wakeup()
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

    /**
     * Stores the object in the session cache.
     */
    function shutdown()
    {
    }

    /**
     * Replace all occurences of ':' in an object name with '.'.
     *
     * @param string $name  The name of the object.
     *
     * @return string  The encoded name.
     */
    function encodeName($name)
    {
        return str_replace(':', '.', $name);
    }

    /**
     * Returns a new group object.
     *
     * @param string $name    The group's name.
     * @param string $parent  The group's parent's name.
     *
     * @return SQLObject_Group  A new group object.
     */
    function &newGroup($name, $parent = GROUP_ROOT)
    {
        if (empty($name)) {
            return PEAR::raiseError(_("Group names must be non-empty"));
        }

        if ($parent != GROUP_ROOT) {
            $name = $this->getGroupName($parent) . ':' . $this->encodeName($name);
        }

        $group = &new SQLObject_Group($name);
        $group->setGroupOb($this);
        return $group;
    }

    /**
     * Returns a SQLObject_Group object corresponding to the named group,
     * with the users and other data retrieved appropriately.
     *
     * @param string $name The name of the group to retrieve.
     */
    function &getGroup($name)
    {
        if (!isset($this->_groupCache[$name])) {
            $this->_connect();
            $sql = 'SELECT group_uid, group_email FROM horde_groups WHERE group_name = ?';
            $group = $this->_db->getRow($sql, array($name), DB_FETCHMODE_ASSOC);

            if (is_a($group, 'PEAR_Error')) {
                return $group;
            } elseif (empty($group)) {
                return PEAR::raiseError($name . ' does not exist');
            }

            $sql = 'SELECT user_uid FROM horde_groups_members '
                . ' WHERE group_uid = ? ORDER BY user_uid ASC';
            $users = $this->_db->getCol($sql, 0, array($group['group_uid']));
            if (is_a($users, 'PEAR_Error')) {
                return $users;
            }

            $object = &new SQLObject_Group($name);
            $object->id = $group['group_uid'];
            $object->data['email'] = $group['group_email'];

            if (!empty($users)) {
                $object->data['users'] = array_flip($users);
            }

            $this->_groupCache[$name] = $object;
            $this->_groupCache[$name]->setGroupOb($this);
            $this->_groupMap[$this->_groupCache[$name]->getId()] = $name;
        }

        return $this->_groupCache[$name];
    }

    /**
     * Returns a SQLObject_Group object corresponding to the given unique
     * ID, with the users and other data retrieved appropriately.
     *
     * @param integer $cid  The unique ID of the group to retrieve.
     */
    function &getGroupById($cid)
    {
        if (isset($this->_groupMap[$cid])) {
            return $this->_groupCache[$this->_groupMap[$cid]];
        }

        $this->_connect();
        $sql = 'SELECT group_name, group_email FROM horde_groups WHERE group_uid = ?';
        $row = $this->_db->getRow($sql, array($cid), DB_FETCHMODE_ASSOC);

        if (is_a($row, 'PEAR_Error')) {
            return $row;
        } elseif (empty($row)) {
            return PEAR::raiseError($cid . ' does not exist');
        }

        $sql = 'SELECT user_uid FROM horde_groups_members '
            . ' WHERE group_uid = ? ORDER BY user_uid ASC';
        $users = $this->_db->getCol($sql, 0, array($cid));
        if (is_a($users, 'PEAR_Error')) {
            return $users;
        }

        $group = &new SQLObject_Group($row['group_name']);
        $group->id = $cid;
        $group->data['email'] = $row['group_email'];

        if (!empty($users)) {
            $group->data['users'] = array_flip($users);
        }

        $group->setGroupOb($this);
        $name = $group->getName();
        $this->_groupCache[$name] = &$group;
        $this->_groupMap[$cid] = $name;

        return $group;
    }

    /**
     * Adds a group to the groups system. The group must first be created with
     * Group::newGroup(), and have any initial users added to it, before this
     * function is called.
     *
     * @param SQLObject_Group $group  The new group object.
     */
    function addGroup(&$group)
    {
        if (!is_a($group, 'SQLObject_Group')) {
            return PEAR::raiseError('Groups must be SQLObject_Group objects or extend that class.');
        }

        $this->_connect();
        $group->setGroupOb($this);
        $name = $group->getName();

        $email = isset($group->data['email']) ? $group->data['email'] : '';
        $group_id = $this->_write_db->nextId('horde_groups');
        if (is_a($group_id, 'PEAR_Error')) {
            return $group_id;
        }

        $group->id = $group_id;
        $query = 'INSERT INTO horde_groups (group_uid, group_name, group_parents, group_email) VALUES (?, ?, ?, ?)';
        $result = $this->_write_db->query($query, array($group->id, $name, '', $email));
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (!empty($group->data['users'])) {
            $query = 'INSERT INTO horde_groups_members (group_uid, user_uid)'
                .' VALUES (' . (int)$group->id . ', ?)';
            $sth = $this->_write_db->prepare($query);
            $result = $this->_write_db->executeMultiple($sth, $group->data['users']);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $this->_groupCache[$name] = &$group;
        $this->_groupMap[$group_id] = $name;
        if (isset($this->_groupList)) {
            $this->_groupList[$group_id] = $name;
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
     * @param SQLObject_Group $group  The group to update.
     */
    function updateGroup($group)
    {
        if (!is_a($group, 'SQLObject_Group')) {
            return PEAR::raiseError('Groups must be SQLObject_Group objects or extend that class.');
        }

        $this->_connect();

        $query = 'UPDATE horde_groups SET group_email = ? WHERE group_uid = ?';
        $result = $this->_write_db->query($query, array($this->data['email'], $this->id));
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $query = 'DELETE FROM horde_groups_members WHERE group_uid = ?';
        $result = $this->_write_db->query($query, array($this->id));
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $query = 'INSERT INTO horde_groups_members (group_uid, user_uid)'
            .' VALUES (' . (int)$this->id . ', ?)';
        $sth = $this->_write_db->prepare($query);
        $result = $this->_groupOb->_write_db->executeMultiple($sth, $this->data['users']);
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
     * @param SQLObject_Group $group  The group to remove.
     * @param boolean $force               Force to remove every child.
     */
    function removeGroup($group, $force = false)
    {
        if (!is_a($group, 'SQLObject_Group')) {
            return PEAR::raiseError('Groups must be SQLObject_Group objects or extend that class.');
        }

        $this->_connect();
        $id = $group->getId();
        $name = $group->getName();
        unset($this->_groupMap[$id]);
        if (isset($this->_groupList)) {
            unset($this->_groupList[$id]);
        }
        unset($this->_groupCache[$name]);

        $history = &Horde_History::singleton();
        $history->log($this->getGUID($group), array('action' => 'delete'), true);

        $query = 'DELETE FROM horde_groups_members WHERE group_uid = ?';
        $result = $this->_write_db->query($query, array($id));
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $query = 'DELETE FROM horde_groups WHERE group_uid = ?';
        $result = $this->_write_db->query($query, array($id));
        if (!$force || is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $query = 'DELETE FROM horde_groups WHERE group_name LIKE ?';
        return $this->_write_db->query($query, array($name . ':%'));
    }

    /**
     * Retrieves the name of a group.
     *
     * @param integer|SQLObject_Group $gid  The id of the group or the
     *                                           group object to retrieve the
     *                                           name for.
     *
     * @return string  The group's name.
     */
    function getGroupName($gid)
    {
        if (is_a($gid, 'SQLObject_Group')) {
            $gid = $gid->getId();
        }

        if (isset($this->_groupMap[$gid])) {
            return $this->_groupMap[$gid];
        }
        if (isset($this->_groupList[$gid])) {
            return $this->_groupList[$gid];
        }

        $this->_connect();
        $query = 'SELECT group_name FROM horde_groups WHERE group_uid = ?';
        return $this->_db->getOne($query, $gid);
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
        /* If there are several components to the name, explode and get the
         * last one, otherwise just return the name. */
        if (strpos($group, ':') !== false) {
            $name = explode(':', $group);
            return array_pop($name);
        }

        return $group;
    }

    /**
     * Retrieves the ID of a group.
     *
     * @param string|SQLObject_Group $group  The group name or object to
     *                                            retrieve the ID for.
     *
     * @return integer  The group's ID.
     */
    function getGroupId($group)
    {
        if (is_a($group, 'SQLObject_Group')) {
            return $group->getId();
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

        $this->_connect();
        $query = 'SELECT group_uid FROM horde_groups WHERE group_name = ?';
        return $this->_db->getOne($query, $group);
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

        $this->_connect();
        $query = 'SELECT COUNT(*) FROM horde_groups WHERE group_name = ?';
        return (bool)$this->_db->getOne($query, $group);
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
            $this->_connect();
            $parents = $this->_getGroupParents($name);
            if (is_a($parents, 'PEAR_Error')) {
                return $parents;
            }

            $this->_parentTree[$gid] = $parents;
        }

        return $this->_parentTree[$gid];
    }

    /**
     * Returns a list of parent permissions.
     *
     * @param string $child  The name of the child to retrieve parents for.
     *
     * @return array  A hash with all parents in a tree format.
     */
    function _getGroupParents($child)
    {
        if (($pos = strrpos($child, ':')) !== false) {
            $child = substr($child, 0, $pos);
        }

        return $this->_getParents($child);
    }

    /**
     */
    function _getParents($parents)
    {
        $mother = array();
        if (!empty($parents)) {
            $pname = $parents;
            $parents = substr($parents, 0, strrpos($parents, ':'));
            $mother[$pname] = $this->_getParents($parents);
        } else {
            return array(GROUP_ROOT => true);
        }

        return $mother;
    }

    /**
     * Returns the single parent ID of the given group.
     *
     * @param integer $gid  The ID of the child group.
     *
     * @return integer  The parent of the given group.
     */
    function getGroupParent($gid)
    {
        if (!isset($this->_groupParents[$gid])) {
            $this->_connect();

            $name = $this->getGroupName($gid);
            if (is_a($name, 'PEAR_Error')) {
                return $name;
            }

            if (($pos = strrpos($name, ':')) !== false) {
                $this->_groupParents[$gid] = $this->getGroupId(substr($name, 0, $pos));
            } else {
                $this->_groupParents[$gid] = GROUP_ROOT;
            }
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
            $name = $this->getGroupName($gid);
            $pos = strpos($name, ':');
            if ($pos == false) {
                $this->_groupParentList[$gid] = array();
                return $this->_groupParentList[$gid];
            }

            $parents = array();
            while ($pos) {
                $name = substr($name, 0, $pos);
                $parents[] = $name;
                $pos = strpos($name, ':');
            }

            $query = 'SELECT group_uid, group_name FROM horde_groups '
                . ' WHERE group_name IN (' . str_repeat('?, ', count($parents) - 1) . '?) ';
            $parents = $this->_db->getAssoc($query, false, $parents);
            if (is_a($parents, 'PEAR_Error')) {
                return $parents;
            }

            $this->_groupParentList[$gid] = $parents;
        }

        return $this->_groupParentList[$gid];
    }

    /**
     * Returns a flat list of the parents of a child group
     *
     * @param integer $gid  The id of the group.
     *
     * @return array  A flat list of all of the parents of $group, hashed in
     *                $id => $name format.
     */
    function _getGroupParentNameList($name)
    {
        $parents = array();

        while ($pos) {
            $name = substr($name, 0, $pos);
            $parents[] = $name;
            $pos = strpos($name, ':');
        }

        return $parents;
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
            $this->_connect();
            $sql = 'SELECT group_uid, group_name FROM horde_groups ORDER BY group_uid';
            $this->_groupList = $this->_db->getAssoc($sql);
        }

        return $this->_groupList;
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
            $name = $this->getGroupName($gid);
            $query = 'SELECT group_uid FROM horde_groups WHERE group_name LIKE ?';
            $parents = $this->_db->getCol($query, 0, array($name .  ':%'));
            $this->_subGroups[$gid] = $parents;
            $this->_subGroups[$gid][] = $gid;
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
        if (isset($_SESSION['horde']['groups']['m'][$user][$parentGroups])) {
            return $_SESSION['horde']['groups']['m'][$user][$parentGroups];
        }

        $this->_connect();

        $sql = 'SELECT g.group_uid AS group_uid, g.group_name AS group_name FROM horde_groups g, horde_groups_members m '
            . ' WHERE m.user_uid = ? AND g.group_uid = m.group_uid ORDER BY g.group_name';
        $result = $this->_db->query($sql, $user);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $groups = array();
        while ($row = $result->fetchRow(DB_FETCHMODE_ASSOC)) {
            $groups[(int)$row['group_uid']] = $this->getGroupShortName($row['group_name']);
        }

        if ($parentGroups) {
            foreach ($groups as $id => $g) {
                $parents = $this->getGroupParentList($id);
                if (is_a($parents, 'PEAR_Error')) {
                    return $parents;
                }
                $groups += $parents;
            }
        }

        $_SESSION['horde']['groups']['m'][$user][$parentGroups] = $groups;
        return $groups;
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
        if (isset($_SESSION['horde']['groups']['i'][$user][$subgroups][$gid])) {
            return $_SESSION['horde']['groups']['i'][$user][$subgroups][$gid];
        }

        if ($subgroups) {
            $groups = $this->getGroupMemberships($user, true);
            if (is_a($groups, 'PEAR_Error')) {
                Horde::logMessage($groups, __FILE__, __LINE__, PEAR_LOG_ERR);
                return false;
            }

            $result = !empty($groups[$gid]);
        } else {
            $this->_connect();
            $query = 'SELECT COUNT(*) FROM horde_groups_members WHERE group_uid = ? AND user_uid = ?';
            $result = $this->_db->getOne($query, array($gid, $user));

        }

        $_SESSION['horde']['groups']['i'][$user][$subgroups][$gid] = (bool)$result;
        return (bool)$result;
    }

    /**
     * Attempts to open a persistent connection to the sql server.
     *
     * @return boolean  True on success; exits (Horde::fatal()) on error.
     */
    function _connect()
    {
        if ($this->_connected) {
            return true;
        }
        if (!isset($this->_params['database'])) {
            $this->_params['database'] = '';
        }
        if (!isset($this->_params['username'])) {
            $this->_params['username'] = '';
        }
        if (!isset($this->_params['hostspec'])) {
            $this->_params['hostspec'] = '';
        }

        /* Connect to the sql server using the supplied parameters. */
        require_once 'DB.php';
        $this->_write_db = DB::connect($this->_params,
                                       array('persistent' => !empty($this->_params['persistent']),
                                             'ssl' => !empty($this->_params['ssl'])));
        if (is_a($this->_write_db, 'PEAR_Error')) {
            Horde::fatal($this->_write_db, __FILE__, __LINE__);
        }

        /* Set DB portability options. */
        switch ($this->_write_db->phptype) {
        case 'mssql':
            $this->_write_db->setOption('portability', DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS | DB_PORTABILITY_RTRIM);
            break;
        default:
            $this->_write_db->setOption('portability', DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS);
        }

        /* Check if we need to set up the read DB connection seperately. */
        if (!empty($this->_params['splitread'])) {
            $params = array_merge($this->_params, $this->_params['read']);
            $this->_db = DB::connect($params,
                                     array('persistent' => !empty($params['persistent']),
                                           'ssl' => !empty($params['ssl'])));
            if (is_a($this->_db, 'PEAR_Error')) {
                Horde::fatal($this->_db, __FILE__, __LINE__);
            }

            /* Set DB portability options. */
            switch ($this->_db->phptype) {
            case 'mssql':
                $this->_db->setOption('portability', DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS | DB_PORTABILITY_RTRIM);
                break;
            default:
                $this->_db->setOption('portability', DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS);
            }
        } else {
            /* Default to the same DB handle for the writer too. */
            $this->_db = $this->_write_db;
        }

        $this->_connected = true;
        return true;
    }

}

/**
 * Extension of the SQLObject class for storing Group information
 * in the Categories driver. If you want to store specialized Group
 * information, you should extend this class instead of extending
 * SQLObject directly.
 *
 * @author  Duck <duck@obala.net>
 * @since   Horde 3.2
 * @package Horde_Group
 */
class SQLObject_Group extends DataTreeObject_Group {

    /**
     * The unique name of this object.
     * These names have the same requirements as other object names - they must
     * be unique, etc.
     *
     * @var string
     */
    var $name;

    /**
     * The unique name of this object.
     * These names have the same requirements as other object names - they must
     * be unique, etc.
     *
     * @var integer
     */
    var $id;

    /**
     * Key-value hash that will be serialized.
     *
     * @see getData()
     * @var array
     */
    var $data = array();

    /**
     * The SQLObject_Group constructor. Just makes sure to call
     * the parent constructor so that the group's name is set
     * properly.
     *
     * @param string $name  The name of the group.
     */
    function SQLObject_Group($name)
    {
        $this->name = $name;
    }

    /**
     * Gets the ID of this object.
     *
     * @return string  The object's ID.
     */
    function getId()
    {
        return $this->id;
    }

    /**
     * Gets the name of this object.
     *
     * @return string The object name.
     */
    function getName()
    {
        return $this->name;
    }

    /**
     * Gets one of the attributes of the object, or null if it isn't defined.
     *
     * @param string $attribute  The attribute to get.
     *
     * @return mixed  The value of the attribute, or null.
     */
    function get($attribute)
    {
        return isset($this->data[$attribute])
            ? $this->data[$attribute]
            : null;
    }

    /**
     * Sets one of the attributes of the object.
     *
     * @param string $attribute  The attribute to set.
     * @param mixed $value       The value for $attribute.
     */
    function set($attribute, $value)
    {
        $this->data[$attribute] = $value;
    }

    /**
     * Save group
     */
    function save()
    {
        if (isset($this->data['email'])) {
            $query = 'UPDATE horde_groups SET group_email = ? WHERE group_uid = ?';
            $result = $this->_groupOb->_write_db->query($query, array($this->data['email'], $this->id));
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $query = 'DELETE FROM horde_groups_members WHERE group_uid = ?';
        $result = $this->_groupOb->_write_db->query($query, array($this->id));
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (!empty($this->data['users'])) {
            $query = 'INSERT INTO horde_groups_members (group_uid, user_uid)'
                .' VALUES (' . $this->_groupOb->_write_db->quote($this->id) . ', ?)';
            $sth = $this->_groupOb->_write_db->prepare($query);
            $result = $this->_groupOb->_write_db->executeMultiple($sth, array_keys($this->data['users']));
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
    }

}
