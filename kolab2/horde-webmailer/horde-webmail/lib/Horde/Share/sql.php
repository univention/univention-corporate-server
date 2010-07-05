<?php
/**
 * Horde_Share_sql:: provides the sql backend for the horde share
 * driver.
 *
 * $Horde: framework/Share/Share/sql.php,v 1.1.2.57 2009-08-12 13:52:00 jan Exp $
 *
 * Copyright 2008-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Duck <duck@obala.net>
 * @since   Horde 3.2
 * @package Horde_Share
 */

/** The share has user permissions */
define('HORDE_SHARE_SQL_FLAG_USERS', 1);

/** The share has group permissions */
define('HORDE_SHARE_SQL_FLAG_GROUPS', 2);

/**
 * @package Horde_Share
 */
class Horde_Share_sql extends Horde_Share {

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
     * SQL connection parameters
     */
    var $_params = array();

    /**
     * Main share table for the current scope.
     *
     * @var string
     */
    var $_table;

    /**
     * The Horde_Share_Object subclass to instantiate objects as
     *
     * @var string
     */
    var $_shareObject = 'Horde_Share_Object_sql';

    /**
     * Initializes the object.
     */
    function __wakeup()
    {
        $this->_table = $this->_app . '_shares';
        $this->_connect();

        foreach (array_keys($this->_cache) as $name) {
            $this->_cache[$name]->setShareOb($this);
        }

        parent::__wakeup();
    }

    /**
     * Returns the properties that need to be serialized.
     *
     * @return array  List of serializable properties.
     */
    function __sleep()
    {
        $properties = get_object_vars($this);
        unset($properties['_sortList'],
              $properties['_db'],
              $properties['_write_db']);
        return array_keys($properties);
    }

    /**
     * Get storage table
     */
    function getTable()
    {
        return $this->_table;
    }

    /**
     * Refetence to write db
     */
    function &getWriteDb()
    {
        return $this->_write_db;
    }

    /**
     * Finds out if the share has user set
     */
    function _hasUsers($share)
    {
        return $share['share_flags'] & HORDE_SHARE_SQL_FLAG_USERS;
    }

    /**
     * Finds out if the share has user set
     */
    function _hasGroups($share)
    {
        return $share['share_flags'] & HORDE_SHARE_SQL_FLAG_GROUPS;
    }

    /**
     * Get users permissions
     *
     * @param array $share Share data array
     */
    function _getShareUsers(&$share)
    {
        if ($this->_hasUsers($share)) {
            $stmt = $this->_db->prepare('SELECT user_uid, perm FROM ' . $this->_table . '_users WHERE share_id = ?');
            if (is_a($stmt, 'PEAR_Error')) {
                Horde::logMessage($stmt, __FILE__, __LINE__, PEAR_LOG_ERR);
                return $stmt;
            }
            $result = $stmt->execute(array($share['share_id']));
            if (is_a($result, 'PEAR_Error')) {
                Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                return $result;
            } elseif (!empty($result)) {
                while ($row = $result->fetchRow(MDB2_FETCHMODE_ASSOC)) {
                    $share['perm']['users'][$row['user_uid']] = (int)$row['perm'];
                }
            }
            $stmt->free();
            $result->free();
        }
    }
    /**
     * Get groups permissions
     *
     * @param array $share Share data array
     */
    function _getShareGroups(&$share)
    {
        if ($this->_hasGroups($share)) {
            // Get groups permissions
            $stmt = $this->_db->prepare('SELECT group_uid, perm FROM ' . $this->_table . '_groups WHERE share_id = ?');
            if (is_a($stmt, 'PEAR_Error')) {
                Horde::logMessage($stmt, __FILE__, __LINE__, PEAR_LOG_ERR);
                return $stmt;
            }
            $result = $stmt->execute(array($share['share_id']));
            if (is_a($result, 'PEAR_Error')) {
                Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                return $result;
            } elseif (!empty($result)) {
                while ($row = $result->fetchRow(MDB2_FETCHMODE_ASSOC)) {
                    $share['perm']['groups'][$row['group_uid']] = (int)$row['perm'];
                }
            }
            $stmt->free();
            $result->free();
        }
    }

    /**
     * Returns a Horde_Share_Object_sql object corresponding to the given
     * share name, with the details retrieved appropriately.
     *
     * @param string $name  The name of the share to retrieve.
     *
     * @return Horde_Share_Object_sql  The requested share.
     */
    function &_getShare($name)
    {
        $stmt = $this->_db->prepare('SELECT * FROM ' . $this->_table . ' WHERE share_name = ?');
        if (is_a($stmt, 'PEAR_Error')) {
            Horde::logMessage($stmt, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $stmt;
        }
        $results = $stmt->execute(array($name));
        if (is_a($results, 'PEAR_Error')) {
            Horde::logMessage($results, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $results;
        }
        $data = $results->fetchRow(MDB2_FETCHMODE_ASSOC);
        if (is_a($data, 'PEAR_Error')) {
            Horde::logMessage($data, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $data;
        } elseif (empty($data)) {
            return PEAR::RaiseError(sprintf(_("Share \"%s\" does not exist."), $name));
        }
        $stmt->free();
        $results->free();

        // Convert charset
        $data = $this->_fromDriverCharset($data);

        // Populate the perms array
        $this->_loadPermissions($data);

        $share = &new $this->_shareObject($data);
        return $share;
    }

    /**
     * Helper function to load the permissions data into the share data
     *
     * @param array $data  Array of share attributes
     */
    function _loadPermissions(&$data) {
        $this->_getShareUsers($data);
        $this->_getShareGroups($data);
        $this->_getSharePerms($data);
    }

    function _getSharePerms(&$data)
    {
        $data['perm']['type'] = 'matrix';
        $data['perm']['default'] = isset($data['perm_default']) ? (int)$data['perm_default'] : 0;
        $data['perm']['guest'] = isset($data['perm_guest']) ? (int)$data['perm_guest'] : 0;
        $data['perm']['creator'] = isset($data['perm_creator']) ? (int)$data['perm_creator'] : 0;
        unset($data['perm_creator'], $data['perm_guest'], $data['perm_default']);
    }

    /**
     * Returns a Horde_Share_Object_sql object corresponding to the given
     * unique ID, with the details retrieved appropriately.
     *
     * @param integer $cid  The id of the share to retrieve.
     *
     * @return Horde_Share_Object_sql  The requested share.
     */
    function &_getShareById($id)
    {
        $params = array($id);
        $stmt = $this->_db->prepare('SELECT * FROM ' . $this->_table . ' WHERE share_id = ?');
        if (is_a($stmt, 'PEAR_Error')) {
            Horde::logMessage($stmt, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $stmt;
        }
        $results = $stmt->execute($params);
        if (is_a($results, 'PEAR_Error')) {
            Horde::logMessage($results, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $results;
        }
        $data = $results->fetchRow(MDB2_FETCHMODE_ASSOC);
        if (is_a($data, 'PEAR_Error')) {
            Horde::logMessage($data, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $data;
        } elseif (empty($data)) {
            return PEAR::RaiseError(sprintf(_("Share ID %d does not exist."), $id));
        }

        $stmt->free();
        $results->free();

        // Convert charset
        $data = $this->_fromDriverCharset($data);

        // Get permissions
        $this->_loadPermissions($data);

        $share = &new $this->_shareObject($data);
        return $share;
    }

    /**
     * Returns an array of Horde_Share_Object_sql objects corresponding
     * to the given set of unique IDs, with the details retrieved
     * appropriately.
     *
     * @param array $cids  The array of ids to retrieve.
     *
     * @return array  The requested shares.
     */
    function &_getShares($ids)
    {
        $shares = array();
        $query = 'SELECT * FROM ' . $this->_table . ' WHERE share_id IN (' . implode(', ', $ids) . ')';
        $result = $this->_db->query($query);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        } elseif (empty($result)) {
            return array();
        }

        $groups = array();
        $users = array();
        while ($share = $result->fetchRow(MDB2_FETCHMODE_ASSOC)) {
            $shares[(int)$share['share_id']] = $this->_fromDriverCharset($share);
            if ($this->_hasUsers($share)) {
                $users[] = (int)$share['share_id'];
            }
            if ($this->_hasGroups($share)) {
                $groups[] = (int)$share['share_id'];
            }
        }
        $result->free();

        // Get users permissions
        if (!empty($users)) {
            $query = 'SELECT share_id, user_uid, perm FROM ' . $this->_table . '_users '
                    . ' WHERE share_id IN (' . implode(', ', $users) . ')';
            $result = $this->_db->query($query);
            if (is_a($result, 'PEAR_Error')) {
                Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                return $result;
            } elseif (!empty($result)) {
                while ($share = $result->fetchRow(MDB2_FETCHMODE_ASSOC)) {
                    $shares[$share['share_id']]['perm']['users'][$share['user_uid']] = (int)$share['perm'];
                }
                $result->free();
            }
        }

        // Get groups permissions
        if (!empty($groups)) {
            $query = 'SELECT share_id, group_uid, perm FROM ' . $this->_table . '_groups'
                   . ' WHERE share_id IN (' . implode(', ', $groups) . ')';
            $result = $this->_db->query($query);
            if (is_a($result, 'PEAR_Error')) {
                Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                return $result;
            } elseif (!empty($result)) {
                while ($share = $result->fetchRow(MDB2_FETCHMODE_ASSOC)) {
                    $shares[$share['share_id']]['perm']['groups'][$share['group_uid']] = (int)$share['perm'];
                }
                $result->free();
            }
        }

        $sharelist = array();
        foreach ($shares as $id => $data) {
            $this->_getSharePerms($data);
            $sharelist[$data['share_name']] = &new $this->_shareObject($data);
        }

        return $sharelist;
    }

    /**
     * Lists *all* shares for the current app/share, regardless of
     * permissions.
     *
     * This is for admin functionality and scripting tools, and shouldn't be
     * called from user-level code!
     *
     * @return array  All shares for the current app/share.
     */
    function listAllShares()
    {
        return $this->_listAllShares();
    }

    /**
     * Lists *all* shares for the current app/share, regardless of
     * permissions.
     *
     * @return array  All shares for the current app/share.
     */
    function &_listAllShares()
    {
        $shares = array();
        $query = 'SELECT * FROM ' . $this->_table . ' ORDER BY share_name ASC';
        $result = $this->_db->query($query);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        } elseif (empty($result)) {
            return array();
        }

        while ($share = $result->fetchRow(MDB2_FETCHMODE_ASSOC)) {
            $shares[(int)$share['share_id']] = $this->_fromDriverCharset($share);
        }
        $result->free();

        // Get users permissions
        $query = 'SELECT share_id, user_uid, perm FROM ' . $this->_table . '_users';
        $result = $this->_db->query($query);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        } elseif (!empty($result)) {
            while ($share = $result->fetchRow(MDB2_FETCHMODE_ASSOC)) {
                $shares[$share['share_id']]['perm']['users'][$share['user_uid']] = (int)$share['perm'];
            }
            $result->free();
        }

        // Get groups permissions
        $query = 'SELECT share_id, group_uid, perm FROM ' . $this->_table . '_groups';
        $result = $this->_db->query($query);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        } elseif (!empty($result)) {
            while ($share = $result->fetchRow(MDB2_FETCHMODE_ASSOC)) {
                $shares[$share['share_id']]['perm']['groups'][$share['group_uid']] = (int)$share['perm'];
            }
            $result->free();
        }

        $sharelist = array();
        foreach ($shares as $id => $data) {
            $this->_getSharePerms($data);
            $sharelist[$data['share_name']] = &new $this->_shareObject($data);
            $sharelist[$data['share_name']]->setShareOb($this);
        }

        return $sharelist;
    }

    /**
     * Returns an array of all shares that $userid has access to.
     *
     * @param string $userid     The userid of the user to check access for.
     * @param integer $perm      The level of permissions required.
     * @param mixed $attributes  Restrict the shares counted to those
     *                           matching $attributes. An array of
     *                           attribute/values pairs or a share owner
     *                           username.
     *
     * @return array  The shares the user has access to.
     */
    function &listShares($userid, $perm = PERMS_SHOW, $attributes = null,
                         $from = 0, $count = 0, $sort_by = null, $direction = 0)
    {
        $shares = array();
        if (is_null($sort_by)) {
            $sortfield = 's.share_name';
        } elseif ($sort_by == 'owner' || $sort_by == 'id') {
            $sortfield = 's.share_' . $sort_by;
        } else {
            $sortfield = 's.attribute_' . $sort_by;
        }

        $query = 'SELECT DISTINCT s.* '
            . $this->_getShareCriteria($userid, $perm, $attributes)
            . ' ORDER BY ' . $sortfield
            . (($direction == 0) ? ' ASC' : ' DESC');
        if ($from > 0 || $count > 0) {
            $this->_db->setLimit($count, $from);
        }

        // Fix field names for sqlite. MDB2 tries to handle this with
        // MDB2_PORTABILITY_FIX_ASSOC_FIELD_NAMES, but it doesn't stick.
        if ($this->_db->phptype == 'sqlite') {
            $connection = &$this->_db->getConnection();
            @sqlite_query('PRAGMA full_column_names=0', $connection);
            @sqlite_query('PRAGMA short_column_names=1', $connection);
        }

        $result = $this->_db->query($query);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        } elseif (empty($result)) {
            return array();
        }

        $users = array();
        $groups = array();
        while ($share = $result->fetchRow(MDB2_FETCHMODE_ASSOC)) {
            $shares[(int)$share['share_id']] = $this->_fromDriverCharset($share);
            if ($this->_hasUsers($share)) {
                $users[] = (int)$share['share_id'];
            }
            if ($this->_hasGroups($share)) {
                $groups[] = (int)$share['share_id'];
            }
        }
        $result->free();

        // Get users permissions
        if (!empty($users)) {
            $query = 'SELECT share_id, user_uid, perm FROM ' . $this->_table
                 . '_users WHERE share_id IN (' . implode(', ', $users)
                 . ')';
            $result = $this->_db->query($query);
            if (is_a($result, 'PEAR_Error')) {
                Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                return $result;
            } elseif (!empty($result)) {
                while ($share = $result->fetchRow(MDB2_FETCHMODE_ASSOC)) {
                    $shares[$share['share_id']]['perm']['users'][$share['user_uid']] = (int)$share['perm'];
                }
                $result->free();
            }
        }

        // Get groups permissions
        if (!empty($groups)) {
            $query = 'SELECT share_id, group_uid, perm FROM ' . $this->_table
                     . '_groups WHERE share_id IN (' . implode(', ', $groups)
                     . ')';
            $result = $this->_db->query($query);
            if (is_a($result, 'PEAR_Error')) {
                Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                return $result;
            } elseif (!empty($result)) {
                while ($share = $result->fetchRow(MDB2_FETCHMODE_ASSOC)) {
                    $shares[$share['share_id']]['perm']['groups'][$share['group_uid']] = (int)$share['perm'];
                }
                $result->free();
            }
        }

        $sharelist = array();
        foreach ($shares as $id => $data) {
            $this->_getSharePerms($data);
            $sharelist[$data['share_name']] = &new $this->_shareObject($data);
            $sharelist[$data['share_name']]->setShareOb($this);
        }
        unset($shares);

        $result = Horde::callHook('_horde_hook_share_list',
                                  array($userid, $perm, $attributes, $sharelist),
                                  'horde', false);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }

        return $sharelist;
    }

    /**
     * Returns the number of shares that $userid has access to.
     *
     * @param string $userid     The userid of the user to check access for.
     * @param integer $perm      The level of permissions required.
     * @param mixed $attributes  Restrict the shares counted to those
     *                           matching $attributes. An array of
     *                           attribute/values pairs or a share owner
     *                           username.
     *
     * @return integer  The number of shares
     */
    function _countShares($userid, $perm = PERMS_SHOW, $attributes = null)
    {
        $query = $this->_getShareCriteria($userid, $perm, $attributes);
        $query = 'SELECT COUNT(DISTINCT s.share_id) ' . $query;

        return $this->_db->queryOne($query);
    }

    /**
     * Returns a new share object.
     *
     * @param string $name  The share's name.
     *
     * @return Horde_Share_Object_sql  A new share object.
     */
    function &_newShare($name)
    {
        $share = &new $this->_shareObject(array('share_name' => $name));
        return $share;
    }

    /**
     * Adds a share to the shares system.
     *
     * The share must first be created with
     * Horde_Share_sql::_newShare(), and have any initial details added
     * to it, before this function is called.
     *
     * @param Horde_Share_Object_sql $share  The new share object.
     */
    function _addShare(&$share)
    {
        return $share->save();
    }

    /**
     * Removes a share from the shares system permanently.
     *
     * @param Horde_Share_Object_sql $share  The share to remove.
     */
    function _removeShare(&$share)
    {
        $params = array($share->getId());
        $tables = array($this->_table,
                        $this->_table . '_users',
                        $this->_table . '_groups');
        foreach ($tables as $table) {

            /* Remove the share entry */
            $stmt = $this->_write_db->prepare('DELETE FROM ' . $table . ' WHERE share_id = ?', null, MDB2_PREPARE_MANIP);
            if (is_a($stmt, 'PEAR_Error')) {
                Horde::logMessage($stmt, __FILE__, __LINE__, PEAR_LOG_ERR);
                return $stmt;
            }
            $result = $stmt->execute($params);
            if (is_a($result, 'PEAR_Error')) {
                Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                return $result;
            }
            $stmt->free();
        }

        return true;
    }

    /**
     * Checks if a share exists in the system.
     *
     * @param string $share  The share to check.
     *
     * @return boolean  True if the share exists.
     */
    function _exists($share)
    {
        $stmt = $this->_db->prepare('SELECT 1 FROM ' . $this->_table
                . ' WHERE share_name = ?');

        if (is_a($stmt, 'PEAR_Error')) {
            Horde::logMessage($stmt, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $stmt;

        }
        $result = $stmt->execute(array($share));
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }

        $exists = (bool)$result->fetchOne();
        $stmt->free();
        $result->free();

        return $exists;
    }

    /**
     * Returns an array of criteria for querying shares.
     * @access protected
     *
     * @param string  $userid      The userid of the user to check access for.
     * @param integer $perm        The level of permissions required.
     * @param mixed   $attributes  Restrict the shares returned to those who
     *                             have these attribute values.
     *
     * @return string  The criteria string for fetching this user's shares.
     */
    function _getShareCriteria($userid, $perm = PERMS_SHOW, $attributes = null)
    {
        require_once 'Horde/SQL.php';

        $query = ' FROM ' . $this->_table . ' s ';
        $where = '';

        if (!empty($userid)) {
            // (owner == $userid)
            $where .= 's.share_owner = ' . $this->_write_db->quote($userid);

            // (name == perm_creator and val & $perm)
            $where .= ' OR (' . Horde_SQL::buildClause($this->_db, 's.perm_creator', '&', $perm) . ')';

            // (name == perm_creator and val & $perm)
            $where .= ' OR (' . Horde_SQL::buildClause($this->_db, 's.perm_default',  '&', $perm) . ')';

            // (name == perm_users and key == $userid and val & $perm)
            $query .= ' LEFT JOIN ' . $this->_table . '_users AS u ON u.share_id = s.share_id';
            $where .= ' OR ( u.user_uid = ' .  $this->_write_db->quote($userid)
                . ' AND (' . Horde_SQL::buildClause($this->_db, 'u.perm', '&', $perm) . '))';

            // If the user has any group memberships, check for those also.
            require_once 'Horde/Group.php';
            $group = &Group::singleton();
            $groups = $group->getGroupMemberships($userid, true);
            if (!is_a($groups, 'PEAR_Error') && $groups) {
                // (name == perm_groups and key in ($groups) and val & $perm)
                $ids = array_keys($groups);
                $group_ids = array();
                foreach ($ids as $id) {
                    $group_ids[] = $this->_db->quote($id);
                }
                $query .= ' LEFT JOIN ' . $this->_table . '_groups AS g ON g.share_id = s.share_id';
                $where .= ' OR (g.group_uid IN (' . implode(',', $group_ids) . ')'
                    . ' AND (' . Horde_SQL::buildClause($this->_db, 'g.perm', '&', $perm) . '))';
            } elseif (is_a($groups, 'PEAR_Error')) {
                Horde::logMessage($groups, __FILE__, __LINE__, PEAR_LOG_ERR);
            }
        } else {
            $where = '(' . Horde_SQL::buildClause($this->_db, 's.perm_guest', '&', $perm) . ')';
        }

        $attributes = $this->_toDriverKeys($attributes);
        $attributes = $this->_toDriverCharset($attributes);

        if (is_array($attributes)) {
            // Build attribute/key filter.
            $where = ' (' . $where . ') ';
            foreach ($attributes as $key => $value) {
                $where .= ' AND ' . $key . ' = ' . $this->_db->quote($value);
            }
        } elseif (!empty($attributes)) {
            // Restrict to shares owned by the user specified in the
            // $attributes string.
            $where = ' (' . $where . ') AND s.share_owner = ' . $this->_db->quote($attributes);
        }

        return $query . ' WHERE ' . $where;
    }

    /**
     * Resets the current database name so that MDB2 is always selecting the
     * database before sending a query.
     */
    function _selectDB(&$db, $scope, $message, $is_manip = null)
    {
        if ($scope == 'query') {
            $db->connected_database_name = '';
        }
    }

    /**
     * Attempts to open a connection to the sql server.
     *
     * @return boolean  True on success; exits (Horde::fatal()) on error.
     */
    function _connect()
    {
        $this->_params = $GLOBALS['conf']['sql'];
        if (!isset($this->_params['database'])) {
            $this->_params['database'] = '';
        }
        if (!isset($this->_params['username'])) {
            $_params['username'] = '';
        }
        if (!isset($this->_params['hostspec'])) {
            $this->_params['hostspec'] = '';
        }

        /* Connect to the sql server using the supplied parameters. */
        require_once 'MDB2.php';
        $params = $this->_params;
        unset($params['charset']);
        $this->_write_db = &MDB2::factory($params);
        if (is_a($this->_write_db, 'PEAR_Error')) {
            Horde::fatal($this->_write_db, __FILE__, __LINE__);
        }

        /* Attach debug handler. */
        $this->_write_db->setOption('debug', true);
        $this->_write_db->setOption('seqcol_name', 'id');
        $this->_write_db->setOption('debug_handler', array($this, '_selectDB'));

        /* Set DB portability options. */
        switch ($this->_write_db->phptype) {
        case 'mssql':
            $this->_write_db->setOption('field_case', CASE_LOWER);
            $this->_write_db->setOption('portability', MDB2_PORTABILITY_FIX_CASE | MDB2_PORTABILITY_ERRORS | MDB2_PORTABILITY_RTRIM | MDB2_PORTABILITY_FIX_ASSOC_FIELD_NAMES);
            break;

        case 'pgsql':
            /* The debug handler breaks PostgreSQL. In most cases it shouldn't
             * be necessary, but this may mean we simply can't support use of
             * multiple Postgres databases right now. See
             * http://bugs.horde.org/ticket/7825 */
            $this->_write_db->setOption('debug', false);
            // Fall through

        default:
            $this->_write_db->setOption('field_case', CASE_LOWER);
            $this->_write_db->setOption('portability', MDB2_PORTABILITY_FIX_CASE | MDB2_PORTABILITY_ERRORS | MDB2_PORTABILITY_FIX_ASSOC_FIELD_NAMES);
        }

        /* Check if we need to set up the read DB connection seperately. */
        if (!empty($this->_params['splitread'])) {
            $params = array_merge($params, $this->_params['read']);
            unset($params['charset']);
            $this->_db = &MDB2::singleton($params);
            if (is_a($this->_db, 'PEAR_Error')) {
                Horde::fatal($this->_db, __FILE__, __LINE__);
            }
            $this->_db->setOption('seqcol_name', 'id');

            /* Set DB portability options. */
            switch ($this->_db->phptype) {
            case 'mssql':
                $this->_db->setOption('field_case', CASE_LOWER);
                $this->_db->setOption('portability', MDB2_PORTABILITY_FIX_CASE | MDB2_PORTABILITY_ERRORS | MDB2_PORTABILITY_RTRIM | MDB2_PORTABILITY_FIX_ASSOC_FIELD_NAMES);
                break;

            case 'pgsql':
                /* The debug handler breaks PostgreSQL. In most cases it shouldn't
                 * be necessary, but this may mean we simply can't support use of
                 * multiple Postgres databases right now. See
                 * http://bugs.horde.org/ticket/7825 */
                $this->_write_db->setOption('debug', false);
                // Fall through

            default:
                $this->_db->setOption('field_case', CASE_LOWER);
                $this->_db->setOption('portability', MDB2_PORTABILITY_FIX_CASE | MDB2_PORTABILITY_ERRORS | MDB2_PORTABILITY_FIX_ASSOC_FIELD_NAMES);
            }
        } else {
            /* Default to the same DB handle as the writer for reading too */
            $this->_db = &$this->_write_db;
        }

        return true;
    }

    /**
     * Utility function to convert from the SQL server's charset.
     */
    function _fromDriverCharset($data)
    {
        foreach ($data as $key => $value) {
            if (substr($key, 0, 9) == 'attribute') {
                $data[$key] = String::convertCharset(
                    $data[$key], $this->_params['charset']);
            }
        }

        return $data;
    }

    /**
     * Utility function to convert TO the SQL server's charset.
     */
    function _toDriverCharset($data)
    {
        if (!is_array($data)) {
            return $data;
        }

        foreach ($data as $key => $value) {
            if (substr($key, 0, 9) == 'attribute') {
                $data[$key] = String::convertCharset(
                    $data[$key], NLS::getCharset(), $this->_params['charset']);
            }
        }

        return $data;
    }

    /**
     * Convert an array keyed on client keys to an array keyed on the driver
     * keys.
     *
     * @param array  $data  The client code keyed array.
     *
     * @return array  The driver keyed array.
     */
    function _toDriverKeys($data)
    {
        if (!is_array($data)) {
            return $data;
        }

        $driver_keys = array();
        foreach ($data as $key => $value) {
            if ($key == 'owner') {
                $driver_keys['share_owner'] = $value;
            } else {
                $driver_keys['attribute_' . $key] = $value;
            }
        }

        return $driver_keys;
    }

}

/**
 * Extension of the Horde_Share_Object class for storing share information in
 * the sql driver.
 *
 * @author  Duck <duck@obala.net>
 * @since   Horde 3.2
 * @package Horde_Share
 */
class Horde_Share_Object_sql extends Horde_Share_Object {

    /**
     * The actual storage object that holds the data.
     *
     * @var mixed
     */
    var $data = array();

    /**
     * Constructor.
     *
     * @param array $data Share data array.
     */
    function Horde_Share_Object_sql($data)
    {
        if (!isset($data['perm']) || !is_array($data['perm'])) {
            $this->data['perm'] = array(
                'users' => array(),
                'type' => 'matrix',
                'default' => isset($data['perm_default'])
                    ? (int)$data['perm_default'] : 0,
                'guest' => isset($data['perm_guest'])
                    ? (int)$data['perm_guest'] : 0,
                'creator' => isset($data['perm_creator'])
                    ? (int)$data['perm_creator'] : 0,
                'groups' => array());

            unset($data['perm_creator'], $data['perm_guest'],
                  $data['perm_default']);
        }
        $this->data = array_merge($data, $this->data);
    }

    /**
     * Sets an attribute value in this object.
     *
     * @param string $attribute  The attribute to set.
     * @param mixed $value       The value for $attribute.
     *
     * @return mixed  True if setting the attribute did succeed, a PEAR_Error
     *                otherwise.
     */
    function _set($attribute, $value)
    {
        if ($attribute == 'owner') {
            return $this->data['share_owner'] = $value;
        } else {
            return $this->data['attribute_' . $attribute] = $value;
        }
    }

    /**
     * Returns one of the attributes of the object, or null if it isn't
     * defined.
     *
     * @param string $attribute  The attribute to retrieve.
     *
     * @return mixed  The value of the attribute, or an empty string.
     */
    function _get($attribute)
    {
        if ($attribute == 'owner') {
            return $this->data['share_owner'];
        } elseif (isset($this->data['attribute_' . $attribute])) {
            return $this->data['attribute_' . $attribute];
        }
    }

    /**
     * Returns the ID of this share.
     *
     * @return string  The share's ID.
     */
    function _getId()
    {
        return isset($this->data['share_id']) ? $this->data['share_id'] : null;
    }

    /**
     * Returns the name of this share.
     *
     * @return string  The share's name.
     */
    function _getName()
    {
        return $this->data['share_name'];
    }

    /**
     * Saves the current attribute values.
     */
    function _save()
    {
        $db = &$this->_shareOb->getWriteDb();
        $table = $this->_shareOb->getTable();

        $fields = array();
        $params = array();

        foreach ($this->_shareOb->_toDriverCharset($this->data) as $key => $value) {
            if ($key != 'share_id' && $key != 'perm' && $key != 'share_flags') {
                $fields[] = $key;
                $params[] = $value;
            }
        }

        $fields[] = 'perm_creator';
        $params[] = isset($this->data['perm']['creator']) ? (int)$this->data['perm']['creator'] : 0;

        $fields[] = 'perm_default';
        $params[] = isset($this->data['perm']['default']) ? (int)$this->data['perm']['default'] : 0;

        $fields[] = 'perm_guest';
        $params[] = isset($this->data['perm']['guest']) ? (int)$this->data['perm']['guest'] : 0;

        $fields[] = 'share_flags';
        $flags = 0;
        if (!empty($this->data['perm']['users'])) {
            $flags |= HORDE_SHARE_SQL_FLAG_USERS;
        }
        if (!empty($this->data['perm']['groups'])) {
            $flags |= HORDE_SHARE_SQL_FLAG_GROUPS;
        }
        $params[] = $flags;

        if (empty($this->data['share_id'])) {
            $share_id = $db->nextId($table);
            if (is_a($share_id, 'PEAR_Error')) {
                Horde::logMessage($share_id, __FILE__, __LINE__, PEAR_LOG_ERR);
                return $share_id;
            }

            $this->data['share_id'] = $share_id;
            $fields[] = 'share_id';
            $params[] = $this->data['share_id'];

            $query = 'INSERT INTO ' . $table . ' (' . implode(', ', $fields) . ') VALUES (?' . str_repeat(', ?', count($fields) - 1) . ')';
        } else {
            $query = 'UPDATE ' . $table . ' SET ' . implode(' = ?, ', $fields) . ' = ? WHERE share_id = ?';
            $params[] = $this->data['share_id'];
        }
        $stmt = $db->prepare($query, null, MDB2_PREPARE_MANIP);
        if (is_a($stmt, 'PEAR_Error')) {
            Horde::logMessage($stmt, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $stmt;
        }
        $result = $stmt->execute($params);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }
        $stmt->free();

        // Update the share's user permissions
        $stmt = $db->prepare('DELETE FROM ' . $table . '_users WHERE share_id = ?', null, MDB2_PREPARE_MANIP);
        if (is_a($stmt, 'PEAR_Error')) {
            Horde::logMessage($stmt, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $stmt;
        }
        $result = $stmt->execute(array($this->data['share_id']));
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }
        $stmt->free();

        if (!empty($this->data['perm']['users'])) {
            $data = array();
            foreach ($this->data['perm']['users'] as $user => $perm) {
                $stmt = $db->prepare('INSERT INTO ' . $table . '_users (share_id, user_uid, perm) VALUES (?, ?, ?)', null, MDB2_PREPARE_MANIP);
                if (is_a($stmt, 'PEAR_Error')) {
                    Horde::logMessage($stmt, __FILE__, __LINE__, PEAR_LOG_ERR);
                    return $stmt;
                }
                $result = $stmt->execute(array($this->data['share_id'], $user, $perm));
                if (is_a($result, 'PEAR_Error')) {
                    Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                    return $result;
                }
                $stmt->free();
            }
        }

        // Update the share's group permissions
        $stmt = $db->prepare('DELETE FROM ' . $table . '_groups WHERE share_id = ?', null, MDB2_PREPARE_MANIP);
        if (is_a($stmt, 'PEAR_Error')) {
            Horde::logMessage($stmt, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $stmt;
        }
        $result = $stmt->execute(array($this->data['share_id']));
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }
        $stmt->free();

        if (!empty($this->data['perm']['groups'])) {
            $data = array();
            foreach ($this->data['perm']['groups'] as $group => $perm) {
                $stmt = $db->prepare('INSERT INTO ' . $table . '_groups (share_id, group_uid, perm) VALUES (?, ?, ?)', null, MDB2_PREPARE_MANIP);
                if (is_a($stmt, 'PEAR_Error')) {
                    Horde::logMessage($stmt, __FILE__, __LINE__, PEAR_LOG_ERR);
                    return $stmt;
                }
                $result = $stmt->execute(array($this->data['share_id'], $group, $perm));
                if (is_a($result, 'PEAR_Error')) {
                    Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                    return $result;
                }
                $stmt->free();
            }
        }

        return true;
    }

    /**
     * Checks to see if a user has a given permission.
     *
     * @param string $userid       The userid of the user.
     * @param integer $permission  A PERMS_* constant to test for.
     * @param string $creator      The creator of the event.
     *
     * @return boolean  Whether or not $userid has $permission.
     */
    function hasPermission($userid, $permission, $creator = null)
    {
        if ($userid == $this->data['share_owner']) {
            return true;
        }

        return $GLOBALS['perms']->hasPermission($this->getPermission(),
                                                $userid, $permission, $creator);
    }

    /**
     * Sets the permission of this share.
     *
     * @param Horde_Permission $perm  Permission object.
     * @param boolean $update         Should the share be saved
     *                                after this operation?
     *
     * @return boolean  True if no error occured, PEAR_Error otherwise
     */
    function setPermission(&$perm, $update = true)
    {
        $this->data['perm'] = $perm->getData();
        if ($update) {
            return $this->save();
        }
        return true;
    }

    /**
     * Returns the permission of this share.
     *
     * @return Horde_Permission  Permission object that represents the
     *                               permissions on this share.
     */
    function &getPermission()
    {
        $perm = new Horde_Permission($this->getName());
        $perm->data = isset($this->data['perm'])
            ? $this->data['perm']
            : array();

        return $perm;
    }

}
