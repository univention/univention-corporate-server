<?php

require_once 'Horde/Cache.php';

/**
 * The Perms_sql:: class provides a SQL driver for the Horde
 * permissions system.
 *
 * $Horde: framework/Perms/Perms/sql.php,v 1.1.2.16 2009-10-05 21:17:23 jan Exp $
 *
 * Copyright 2008-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Duck <duck@obala.net>
 * @since   Horde 3.2
 * @package Horde_Perms
 */
class Perms_sql extends Perms {

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
     * Pointer to a Horde_Cache instance
     *
     * @var Horde_Cache
     */
    var $_cache;

    /**
     * Constructor.
     */
    function Perms_sql()
    {
        $this->_cache = Horde_Cache::singleton($GLOBALS['conf']['cache']['driver'],
                                               Horde::getDriverConfig('cache', $GLOBALS['conf']['cache']['driver']));
    }

    /**
     * Returns a new permissions object.
     *
     * @param string $name  The permission's name.
     *
     * @return SQLObject_Permissions  A new permissions object.
     */
    function &newPermission($name)
    {
        $type = 'matrix';
        $params = null;
        if ($pos = strpos($name, ':')) {
            $info = $this->getApplicationPermissions(substr($name, 0, $pos));
            if (!is_a($info, 'PEAR_Error')) {
                if (isset($info['type']) && isset($info['type'][$name])) {
                    $type = $info['type'][$name];
                }
                if (isset($info['params']) && isset($info['params'][$name])) {
                    $params = $info['params'][$name];
                }
            }
        }

        $perm = &new SQLObject_Permission($name, $type, $params);
        return $perm;
    }

    /**
     * Returns a SQLObject_Permission object corresponding to the
     * named permission, with the users and other data retrieved
     * appropriately.
     *
     * @param string $name  The name of the permission to retrieve.
     */
    function &getPermission($name)
    {
        /* Cache of previously retrieved permissions. */
        static $permsCache = array();

        if (isset($permsCache[$name])) {
            return $permsCache[$name];
        }

        $this->_connect();

        $perm = $this->_cache->get('perm_sql' . $name, $GLOBALS['conf']['cache']['default_lifetime']);
        if (empty($perm)) {
            $query = 'SELECT perm_id, perm_data FROM horde_perms WHERE perm_name = ?';
            $result = $this->_db->getRow($query, array($name), DB_FETCHMODE_ASSOC);

            if (is_a($result, 'PEAR_Error')) {
                return $result;
            } elseif (empty($result)) {
                return PEAR::RaiseError('Does not exist');
            }

            $object = &new SQLObject_Permission($name);
            $object->setId($result['perm_id']);
            $object->setData(unserialize($result['perm_data']));

            $this->_cache->set('perm_sql' . $name, serialize($object));

            $permsCache[$name] = $object;
        } else {
            $permsCache[$name] = unserialize($perm);
        }

        $permsCache[$name]->setSQLOb($this->_write_db);

        return $permsCache[$name];
    }

    /**
     * Returns a SQLObject_Permission object corresponding to the given
     * unique ID, with the users and other data retrieved appropriately.
     *
     * @param integer $id  The unique ID of the permission to retrieve.
     */
    function &getPermissionById($id)
    {
        $this->_connect();

        if ($id == PERMS_ROOT || empty($id)) {
            $object = &$this->newPermission(PERMS_ROOT);
        } else {
            $query = 'SELECT perm_name, perm_data FROM horde_perms WHERE perm_id = ?';
            $result = $this->_db->getRow($query, array($id), DB_FETCHMODE_ASSOC);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            } elseif (empty($result)) {
                return PEAR::RaiseError('Does not exsists exits');
            }

            $object = &new SQLObject_Permission($result['perm_name']);
            $object->setId($id);
            $object->setData(unserialize($result['perm_data']));
            $object->setSQLOb($this->_write_db);
        }

        return $object;
    }

    /**
     * Adds a permission to the permissions system. The permission must first
     * be created with Perm::newPermission(), and have any initial users
     * added to it, before this function is called.
     *
     * @param SQLObject_Permission $perm  The new perm object.
     */
    function addPermission(&$perm)
    {
        if (!is_a($perm, 'SQLObject_Permission')) {
            return PEAR::raiseError('Permissions must be SQLObject_Permission objects or extend that class.');
        }

        $name = $perm->getName();
        if (empty($name)) {
            return PEAR::raiseError('Permission names must be non-empty');
        }

        $this->_cache->expire('perm_sql' . $name);
        $this->_cache->expire('perm_sql_exists_' . $name);

        $this->_connect();
        $id = $this->_write_db->nextId('horde_perms');

        // remove root from the name
        if (substr($name, 0, 3) == (PERMS_ROOT . ':')) {
            $name = substr($name, 3);
        }

        // build parents
        $parents = '';
        if (($pos = strrpos($name, ':')) !== false) {
            $parent_name = substr($name, 0, $pos);
            $query = 'SELECT perm_id, perm_parents FROM horde_perms WHERE perm_name = ?';
            $result = $this->_db->getRow($query, array($parent_name), DB_FETCHMODE_ASSOC);
            if (!empty($result)) {
                $parents = $result['perm_parents'] . ':' . $result['perm_id'];
            }
        }

        $query = 'INSERT INTO horde_perms (perm_id, perm_name, perm_parents) VALUES (?, ?, ?)';
        $perm->setId($id);

        $result = $this->_write_db->query($query, array($id, $name, $parents));
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $perm->setSQLOb($this->_write_db);
        $perm->save();

        return $id;
    }

    /**
     * Removes a permission from the permissions system permanently.
     *
     * @param SQLObject_Permission $perm  The permission to remove.
     * @param boolean $force                   Force to remove every child.
     */
    function removePermission(&$perm, $force = false)
    {
        if (!is_a($perm, 'SQLObject_Permission')) {
            return PEAR::raiseError('Permissions must be SQLObject_Permission objects or extend that class.');
        }

        $name = $perm->getName();
        $this->_cache->expire('perm_sql' . $name);
        $this->_cache->expire('perm_sql_exists_' . $name);

        $this->_connect();
        $query = 'DELETE FROM horde_perms WHERE perm_name = ?';
        $result = $this->_write_db->query($query, array($name));
        if (!$force || is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $query = 'DELETE FROM horde_perms WHERE perm_name LIKE ?';
        return $this->_write_db->query($query, array($name . ':%'));
    }

    /**
     * Returns the unique identifier of this permission.
     *
     * @param SQLObject_Permission $permission  The permission object to
     *                                               get the ID of.
     *
     * @return integer  The unique id.
     */
    function getPermissionId($permission)
    {
        if ($permission->getName() == PERMS_ROOT) {
            return PERMS_ROOT;
        }

        $this->_connect();
        $query = 'SELECT perm_id FROM horde_perms WHERE perm_name = ?';
        return $this->_db->getOne($query, array($permission->getName()));
    }

    /**
     * Checks if a permission exists in the system.
     *
     * @param string $permission  The permission to check.
     *
     * @return boolean  True if the permission exists.
     */
    function exists($permission)
    {
        $key = 'perm_sql_exists_' . $permission;
        $exists = $this->_cache->get($key, $GLOBALS['conf']['cache']['default_lifetime']);
        if ($exists === false) {
            $this->_connect();
            $query = 'SELECT COUNT(*) FROM horde_perms WHERE perm_name = ?';
            $exists = $this->_db->getOne($query, array($permission));
            if (is_a($exists, 'PEAR_Error')) {
                return $exists;
            }

            $this->_cache->set($key, (string)$exists);
        }

        return (bool)$exists;
    }

    /**
     * Returns a child's direct parent ID.
     *
     * @param mixed $child  The object name for which
     *                      to look up the parent's ID.
     *
     * @return mixed  The unique ID of the parent or PEAR_Error on error.
     */
    function getParent($child)
    {
        $this->_connect();
        $query = 'SELECT perm_parents FROM horde_perms WHERE perm_name = ?';
        $parents = $this->_db->getOne($query, array($child));

        if (is_a($parents, 'PEAR_Error')) {
            return $parents;
        }

        if (empty($parents)) {
            return PERMS_ROOT;
        }

        $parents = explode(':', $parents);
        return array_pop($parents);
    }

    /**
     * Returns a list of parent permissions.
     *
     * @param string $child  The name of the child to retrieve parents for.
     *
     * @return array  A hash with all parents in a tree format.
     */
    function getParents($child)
    {
        $this->_connect();
        $query = 'SELECT perm_parents FROM horde_perms WHERE perm_name = ?';
        $result = $this->_db->getOne($query, array($child));
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        } elseif (empty($result)) {
            return PEAR::RaiseError('Does not exsists exits');
        }

        $parents = $this->_getParents($result);

        return $parents;
    }

    function _getParents($parents)
    {
        $mother = array();
        if (!empty($parents)) {
            $pname = $parents;
            $parents = substr($parents, 0, strrpos($parents, ':'));
            $mother[$pname] = $this->_getParents($parents);
        } else {
            return array(PERMS_ROOT => true);
        }

        return $mother;
    }

    /**
     * Returns all permissions of the system in a tree format.
     *
     * @return array  A hash with all permissions in a tree format.
     */
    function &getTree()
    {
        $this->_connect();
        $query = 'SELECT perm_id, perm_name FROM horde_perms ORDER BY perm_name ASC';
        $tree = $this->_db->getAssoc($query);
        if (is_a($tree, 'PEAR_Error')) {
            return $tree;
        }

        $tree[PERMS_ROOT] = PERMS_ROOT;
        return $tree;
    }

    /**
     * Attempts to open a connection to the sql server.
     *
     * @return boolean  True on success; exits (Horde::fatal()) on error.
     */
    function _connect()
    {
        if ($this->_connected) {
            return true;
        }

        require_once 'DB.php';

        $_params = $GLOBALS['conf']['sql'];
        if (!isset($_params['database'])) {
            $_params['database'] = '';
        }
        if (!isset($_params['username'])) {
            $_params['username'] = '';
        }
        if (!isset($_params['hostspec'])) {
            $_params['hostspec'] = '';
        }

        /* Connect to the sql server using the supplied parameters. */
        require_once 'DB.php';
        $this->_write_db = DB::connect($_params,
                                       array('persistent' => !empty($_params['persistent']),
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
        if (!empty($_params['splitread'])) {
            $params = array_merge($_params, $_params['read']);
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
 * Extension of the Horde_Permission class for storing permission
 * information in the SQL driver.
 *
 * @author  Duck <duck@obala.net>
 * @since   Horde 3.2
 * @package Horde_Perms
 */
class SQLObject_Permission extends Horde_Permission {

    /**
     * The string permission id.
     *
     * @var string
     */
    var $_id;

    /**
     * Database handle for saving changes.
     *
     * @var DB
     */
    var $_write_db;

    /**
     * The Horde_Permission constructor.
     *
     * @param string $name   The name of the perm.
     * @param string $type   The permission type.
     * @param array $params  A hash with any parameters that the permission
     *                       type needs.
     */
    function SQLObject_Permission($name, $type = 'matrix', $params = null)
    {
        $this->setName($name);
        parent::Horde_Permission($name, $type, $params);
    }

    /**
     * Associates a DB object with this share.
     *
     * @param DB $write_db  The DB object.
     */
    function setSQLOb(&$write_db)
    {
        $this->_write_db = &$write_db;
    }

    /**
     * Get permission ID
     */
    function getId()
    {
        return $this->_id;
    }

    /**
     * Set permission id
     *
     * @param string $id  Permission ID
     */
    function setId($id)
    {
        $this->_id = $id;
    }

    /**
     * Saves any changes to this object to the backend permanently. New objects
     * are added instead.
     *
     * @return boolean|PEAR_Error  PEAR_Error on failure.
     */
    function save()
    {
        $name = $this->getName();
        if (empty($name)) {
            return PEAR::raiseError('Permission names must be non-empty');
        }

        $query = 'UPDATE horde_perms SET perm_data = ? WHERE perm_id = ?';
        $params = array(serialize($this->data), $this->getId());
        $result = $this->_write_db->query($query, $params);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $cache = Horde_Cache::singleton($GLOBALS['conf']['cache']['driver'], Horde::getDriverConfig('cache', $GLOBALS['conf']['cache']['driver']));
        $cache->expire('perm_sql_' . $name);
        $cache->expire('perm_sql_exists_' . $name);

        return true;
    }

}
