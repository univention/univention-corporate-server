<?php

require_once 'Horde/DataTree.php';
require_once 'Horde/Cache.php';

/**
 * The Perms_datatree:: class provides a DataTree driver for the Horde
 * permissions system.
 *
 * $Horde: framework/Perms/Perms/datatree.php,v 1.6.2.24 2009-08-14 21:45:52 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.0
 * @package Horde_Perms
 */
class Perms_datatree extends Perms {

    /**
     * Pointer to a DataTree instance to manage the different
     * permissions.
     *
     * @var DataTree
     */
    var $_datatree;

    /**
     * Pointer to a Horde_Cache instance
     *
     * @var Horde_Cache
     */
    var $_cache;

    /**
     * Constructor.
     */
    function Perms_datatree()
    {
        global $conf;

        if (empty($conf['datatree']['driver'])) {
            Horde::fatal('You must configure a DataTree backend to use the Perms DataTree driver.', __FILE__, __LINE__);
        }

        $driver = $conf['datatree']['driver'];
        $this->_datatree = &DataTree::singleton($driver,
                                                array_merge(Horde::getDriverConfig('datatree', $driver),
                                                            array('group' => 'horde.perms')));

        $this->_cache = Horde_Cache::singleton($GLOBALS['conf']['cache']['driver'],
                                               Horde::getDriverConfig('cache', $GLOBALS['conf']['cache']['driver']));
    }

    /**
     * Returns a new permissions object.
     *
     * @param string $name  The permission's name.
     *
     * @return DataTreeObject_Permissions  A new permissions object.
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

        $perm = &new DataTreeObject_Permission($name, $type, $params);
        $perm->setDataTree($this->_datatree);

        return $perm;
    }

    /**
     * Returns a DataTreeObject_Permission object corresponding to the
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

        $perm = $this->_cache->get('perm_' . $name, $GLOBALS['conf']['cache']['default_lifetime']);
        if ($perm === false) {
            $perm = $this->_datatree->getObject($name, 'DataTreeObject_Permission');
            $this->_cache->set('perm_' . $name, serialize($perm), $GLOBALS['conf']['cache']['default_lifetime']);
            $permsCache[$name] = $perm;
        } else {
            $permsCache[$name] = unserialize($perm);
        }

        return $permsCache[$name];
    }

    /**
     * Returns a DataTreeObject_Permission object corresponding to the given
     * unique ID, with the users and other data retrieved appropriately.
     *
     * @param integer $cid  The unique ID of the permission to retrieve.
     */
    function &getPermissionById($cid)
    {
        if ($cid == PERMS_ROOT) {
            $object = &$this->newPermission(PERMS_ROOT);
        } else {
            $object = &$this->_datatree->getObjectById($cid, 'DataTreeObject_Permission');
        }
        return $object;
    }

    /**
     * Adds a permission to the permissions system. The permission must first
     * be created with Perm::newPermission(), and have any initial users
     * added to it, before this function is called.
     *
     * @param DataTreeObject_Permission $perm  The new perm object.
     */
    function addPermission(&$perm)
    {
        if (!is_a($perm, 'DataTreeObject_Permission')) {
            return PEAR::raiseError('Permissions must be DataTreeObject_Permission objects or extend that class.');
        }

        $name = $perm->getName();
        if (empty($name)) {
            return PEAR::raiseError('Permission names must be non-empty');
        }
        $this->_cache->expire('perm_' . $name);
        $this->_cache->expire('perm_exists_' . $name);

        return $this->_datatree->add($perm);
    }

    /**
     * Removes a permission from the permissions system permanently.
     *
     * @param DataTreeObject_Permission $perm  The permission to remove.
     * @param boolean $force                   Force to remove every child.
     */
    function removePermission(&$perm, $force = false)
    {
        if (!is_a($perm, 'DataTreeObject_Permission')) {
            return PEAR::raiseError('Permissions must be DataTreeObject_Permission objects or extend that class.');
        }

        $keys = $this->_datatree->get(DATATREE_FORMAT_FLAT, $perm->name, true);
        foreach ($keys as $key) {
            $this->_cache->expire('perm_' . $key);
            $this->_cache->expire('perm_exists_' . $key);
        }

        return $this->_datatree->remove($perm->name, $force);
    }

    /**
     * Returns the unique identifier of this permission.
     *
     * @param DataTreeObject_Permission $permission  The permission object to
     *                                               get the ID of.
     *
     * @return integer  The unique id.
     */
    function getPermissionId($permission)
    {
        return $this->_datatree->getId($permission->getName());
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
        $key = 'perm_exists_' . $permission;
        $exists = $this->_cache->get($key, $GLOBALS['conf']['cache']['default_lifetime']);
        if ($exists === false) {
            $exists = $this->_datatree->exists($permission);
            $this->_cache->set($key, (string)$exists);
        }

        return (bool)$exists;
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
        return $this->_datatree->getParents($child);
    }

    /**
     * Returns a child's direct parent ID.
     *
     * @param mixed $child  Either the object, an array containing the
     *                      path elements, or the object name for which
     *                      to look up the parent's ID.
     *
     * @return mixed  The unique ID of the parent or PEAR_Error on error.
     */
    function getParent($child)
    {
        return $this->_datatree->getParent($child);
    }

    /**
     * Returns all permissions of the system in a tree format.
     *
     * @return array  A hash with all permissions in a tree format.
     */
    function &getTree()
    {
        $tree = $this->_datatree->get(DATATREE_FORMAT_FLAT, PERMS_ROOT, true);
        return $tree;
    }

}

/**
 * Extension of the DataTreeObject class for storing Permission information in
 * the DataTree driver. If you want to store specialized Permission
 * information, you should extend this class instead of extending
 * DataTreeObject directly.
 *
 * @TODO This class duplicates most of the functionality of the
 * Horde_Permission class. However, because for BC/DataTree reasons it
 * must extend DataTreeObject, we can't remove these methods yet.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 2.1
 * @package Horde_Perms
 */
class DataTreeObject_Permission extends DataTreeObject {

    /**
     * The DataTreeObject_Permission constructor. Just makes sure to call the
     * parent constructor so that the perm's name is set properly.
     *
     * @param string $name   The name of the perm.
     * @param string $type   The permission type.
     * @param array $params  A hash with any parameters that the permission
     *                       type needs.
     */
    function DataTreeObject_Permission($name, $type = 'matrix', $params = null)
    {
        parent::DataTreeObject($name);
        $this->data['type'] = $type;
        if (is_array($params)) {
            $this->data['params'] = $params;
        }
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
        $value = parent::get($attribute);
        if (is_null($value) && $attribute == 'type') {
            $value = 'matrix';
        }
        return $value;
    }

    /**
     * Updates the permissions based on data passed in the array.
     *
     * @param array $perms  An array containing the permissions which are to be
     *                      updated.
     */
    function updatePermissions($perms)
    {
        $type = $this->get('type');

        if ($type == 'matrix') {
            /* Array of permission types to iterate through. */
            $perm_types = Perms::getPermsArray();
        }

        foreach ($perms as $perm_class => $perm_values) {
            switch ($perm_class) {
            case 'default':
            case 'guest':
            case 'creator':
                if ($type == 'matrix') {
                    foreach ($perm_types as $val => $label) {
                        if (!empty($perm_values[$val])) {
                            $this->setPerm($perm_class, $val, false);
                        } else {
                            $this->unsetPerm($perm_class, $val, false);
                        }
                    }
                } elseif (!empty($perm_values)) {
                    $this->setPerm($perm_class, $perm_values, false);
                } else {
                    $this->unsetPerm($perm_class, null, false);
                }
                break;

            case 'u':
            case 'g':
                $permId = array('class' => $perm_class == 'u' ? 'users' : 'groups');
                /* Figure out what names that are stored in this permission
                 * class have not been submitted for an update, ie. have been
                 * removed entirely. */
                $current_names = isset($this->data[$permId['class']])
                    ? array_keys($this->data[$permId['class']])
                    : array();
                $updated_names = array_keys($perm_values);
                $removed_names = array_diff($current_names, $updated_names);

                /* Remove any names that have been completely unset. */
                foreach ($removed_names as $name) {
                    unset($this->data[$permId['class']][$name]);
                }

                /* If nothing to actually update finish with this case. */
                if (is_null($perm_values)) {
                    continue;
                }

                /* Loop through the names and update permissions for each. */
                foreach ($perm_values as $name => $name_values) {
                    $permId['name'] = $name;

                    if ($type == 'matrix') {
                        foreach ($perm_types as $val => $label) {
                            if (!empty($name_values[$val])) {
                                $this->setPerm($permId, $val, false);
                            } else {
                                $this->unsetPerm($permId, $val, false);
                            }
                        }
                    } elseif (!empty($name_values)) {
                        $this->setPerm($permId, $name_values, false);
                    } else {
                        $this->unsetPerm($permId, null, false);
                    }
                }

                break;
            }
        }
    }

    /**
     * FIXME: needs docs
     */
    function setPerm($permId, $permission, $update = true)
    {
        if (is_array($permId)) {
            if (empty($permId['name'])) {
                return;
            }
            if ($this->get('type') == 'matrix' &&
                isset($this->data[$permId['class']][$permId['name']])) {
                $this->data[$permId['class']][$permId['name']] |= $permission;
            } else {
                $this->data[$permId['class']][$permId['name']] = $permission;
            }
        } else {
            if ($this->get('type') == 'matrix' &&
                isset($this->data[$permId])) {
                $this->data[$permId] |= $permission;
            } else {
                $this->data[$permId] = $permission;
            }
        }

        if ($update) {
            $this->save();
        }
    }

    /**
     * FIXME: needs docs
     */
    function unsetPerm($permId, $permission, $update = true)
    {
        if (is_array($permId)) {
            if (empty($permId['name'])) {
                return;
            }
            if ($this->get('type') == 'matrix') {
                if (isset($this->data[$permId['class']][$permId['name']])) {
                    $this->data[$permId['class']][$permId['name']] &= ~$permission;
                    if (empty($this->data[$permId['class']][$permId['name']])) {
                        unset($this->data[$permId['class']][$permId['name']]);
                    }
                    if ($update) {
                        $this->save();
                    }
                }
            } else {
                unset($this->data[$permId['class']][$permId['name']]);
                if ($update) {
                    $this->save();
                }
            }
        } else {
            if ($this->get('type') == 'matrix') {
                if (isset($this->data[$permId])) {
                    $this->data[$permId] &= ~$permission;
                    if ($update) {
                        $this->save();
                    }
                }
            } else {
                unset($this->data[$permId]);
                if ($update) {
                    $this->save();
                }
            }
        }
    }

    /**
     * Grants a user additional permissions to this object.
     *
     * @param string $user          The user to grant additional permissions
     *                              to.
     * @param constant $permission  The permission (PERMS_DELETE, etc.) to add.
     * @param boolean $update       Whether to automatically update the
     *                              backend.
     */
    function addUserPermission($user, $permission, $update = true)
    {
        if (empty($user)) {
            return;
        }
        if ($this->get('type') == 'matrix' &&
            isset($this->data['users'][$user])) {
            $this->data['users'][$user] |= $permission;
        } else {
            $this->data['users'][$user] = $permission;
        }

        if ($update) {
            $this->save();
        }
    }

    /**
     * Grants guests additional permissions to this object.
     *
     * @param constant $permission  The permission (PERMS_DELETE, etc.) to add.
     * @param boolean $update       Whether to automatically update the
     *                              backend.
     */
    function addGuestPermission($permission, $update = true)
    {
        if ($this->get('type') == 'matrix' &&
            isset($this->data['guest'])) {
            $this->data['guest'] |= $permission;
        } else {
            $this->data['guest'] = $permission;
        }

        if ($update) {
            $this->save();
        }
    }

    /**
     * Grants creators additional permissions to this object.
     *
     * @param constant $permission  The permission (PERMS_DELETE, etc.) to add.
     * @param boolean $update       Whether to automatically update the
     *                              backend.
     */
    function addCreatorPermission($permission, $update = true)
    {
        if ($this->get('type') == 'matrix' &&
            isset($this->data['creator'])) {
            $this->data['creator'] |= $permission;
        } else {
            $this->data['creator'] = $permission;
        }

        if ($update) {
            $this->save();
        }
    }

    /**
     * Grants additional default permissions to this object.
     *
     * @param constant $permission  The permission (PERMS_DELETE, etc.) to add.
     * @param boolean $update       Whether to automatically update the
     *                              backend.
     */
    function addDefaultPermission($permission, $update = true)
    {
        if ($this->get('type') == 'matrix' &&
            isset($this->data['default'])) {
            $this->data['default'] |= $permission;
        } else {
            $this->data['default'] = $permission;
        }

        if ($update) {
            $this->save();
        }
    }

    /**
     * Grants a group additional permissions to this object.
     *
     * @param integer $groupId      The id of the group to grant additional
     *                              permissions to.
     * @param constant $permission  The permission (PERMS_DELETE, etc.) to add.
     * @param boolean $update       Whether to automatically update the
     *                              backend.
     */
    function addGroupPermission($groupId, $permission, $update = true)
    {
        if (empty($groupId)) {
            return;
        }

        if ($this->get('type') == 'matrix' &&
            isset($this->data['groups'][$groupId])) {
            $this->data['groups'][$groupId] |= $permission;
        } else {
            $this->data['groups'][$groupId] = $permission;
        }

        if ($update) {
            $this->save();
        }
    }

    /**
     * Removes a permission that a user currently has on this object.
     *
     * @param string $user          The user to remove the permission from.
     * @param constant $permission  The permission (PERMS_DELETE, etc.) to
     *                              remove.
     * @param boolean $update       Whether to automatically update the
     *                              backend.
     */
    function removeUserPermission($user, $permission, $update = true)
    {
        if (empty($user) || !isset($this->data['users'][$user])) {
            return;
        }

        if ($this->get('type') == 'matrix') {
            $this->data['users'][$user] &= ~$permission;
            if (empty($this->data['users'][$user])) {
                unset($this->data['users'][$user]);
            }
        } else {
            unset($this->data['users'][$user]);
        }

        if ($update) {
            $this->save();
        }
    }

    /**
     * Removes a permission that guests currently have on this object.
     *
     * @param constant $permission  The permission (PERMS_DELETE, etc.) to
     *                              remove.
     * @param boolean $update       Whether to automatically update the
     *                              backend.
     */
    function removeGuestPermission($permission, $update = true)
    {
        if (!isset($this->data['guest'])) {
            return;
        }

        if ($this->get('type') == 'matrix') {
            $this->data['guest'] &= ~$permission;
            if ($update) {
                $this->save();
            }
        } else {
            unset($this->data['guest']);
            if ($update) {
                $this->save();
            }
        }
    }

    /**
     * Removes a permission that creators currently have on this object.
     *
     * @param constant $permission  The permission (PERMS_DELETE, etc.) to
     *                              remove.
     * @param boolean $update       Whether to automatically update the
     *                              backend.
     */
    function removeCreatorPermission($permission, $update = true)
    {
        if (!isset($this->data['creator'])) {
            return;
        }

        if ($this->get('type') == 'matrix') {
            $this->data['creator'] &= ~$permission;
            if ($update) {
                $this->save();
            }
        } else {
            unset($this->data['creator']);
            if ($update) {
                $this->save();
            }
        }
    }

    /**
     * Removes a default permission on this object.
     *
     * @param constant $permission  The permission (PERMS_DELETE, etc.) to
     *                              remove.
     * @param boolean $update       Whether to automatically update the
     *                              backend.
     */
    function removeDefaultPermission($permission, $update = true)
    {
        if (!isset($this->data['default'])) {
            return;
        }

        if ($this->get('type') == 'matrix') {
            $this->data['default'] &= ~$permission;
            if ($update) {
                $this->save();
            }
        } else {
            unset($this->data['default']);
            if ($update) {
                $this->save();
            }
        }
    }

    /**
     * Removes a permission that a group currently has on this object.
     *
     * @param integer $groupId      The id of the group to remove the
     *                              permission from.
     * @param constant $permission  The permission (PERMS_DELETE, etc.) to
     *                              remove.
     * @param boolean $update       Whether to automatically update the
     *                              backend.
     */
    function removeGroupPermission($groupId, $permission, $update = true)
    {
        if (empty($groupId) || !isset($this->data['groups'][$groupId])) {
            return;
        }

        if ($this->get('type') == 'matrix') {
            $this->data['groups'][$groupId] &= ~$permission;
            if (empty($this->data['groups'][$groupId])) {
                unset($this->data['groups'][$groupId]);
            }
            if ($update) {
                $this->save();
            }
        } else {
            unset($this->data['groups'][$groupId]);
            if ($update) {
                $this->save();
            }
        }
    }

    /**
     * Returns an array of all user permissions on this object.
     *
     * @param integer $perm  List only users with this permission level.
     *                       Defaults to all users.
     *
     * @return array  All user permissions for this object, indexed by user.
     */
    function getUserPermissions($perm = null)
    {
        if (!isset($this->data['users']) || !is_array($this->data['users'])) {
            return array();
        } elseif (!$perm) {
            return $this->data['users'];
        } else {
            $users = array();
            foreach ($this->data['users'] as $user => $uperm) {
                if ($uperm & $perm) {
                    $users[$user] = $uperm;
                }
            }
            return $users;
        }
    }

    /**
     * Returns the guest permissions on this object.
     *
     * @return integer  The guest permissions on this object.
     */
    function getGuestPermissions()
    {
        return !empty($this->data['guest']) ?
            $this->data['guest'] :
            null;
    }

    /**
     * Returns the creator permissions on this object.
     *
     * @return integer  The creator permissions on this object.
     */
    function getCreatorPermissions()
    {
        return !empty($this->data['creator']) ?
            $this->data['creator'] :
            null;
    }

    /**
     * Returns the default permissions on this object.
     *
     * @return integer  The default permissions on this object.
     */
    function getDefaultPermissions()
    {
        return !empty($this->data['default']) ?
            $this->data['default'] :
            null;
    }

    /**
     * Returns an array of all group permissions on this object.
     *
     * @param integer $perm  List only users with this permission level.
     *                       Defaults to all users.
     *
     * @return array  All group permissions for this object, indexed by group.
     */
    function getGroupPermissions($perm = null)
    {
        if (!isset($this->data['groups']) ||
            !is_array($this->data['groups'])) {
            return array();
        } elseif (!$perm) {
            return $this->data['groups'];
        } else {
            $groups = array();
            foreach ($this->data['groups'] as $group => $gperm) {
                if ($gperm & $perm) {
                    $groups[$group] = $gperm;
                }
            }
            return $groups;
        }
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
        parent::save();

        $cache = Horde_Cache::singleton($GLOBALS['conf']['cache']['driver'], Horde::getDriverConfig('cache', $GLOBALS['conf']['cache']['driver']));
        $cache->expire('perm_' . $name);
        $cache->expire('perm_exists_' . $name);
    }

}
