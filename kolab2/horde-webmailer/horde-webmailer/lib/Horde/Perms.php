<?php

/** Existence of object is known - object is shown to user. */
define('PERMS_SHOW', 2);

/** Contents of the object can be read. */
define('PERMS_READ', 4);

/** Contents of the object can be edited. */
define('PERMS_EDIT', 8);

/** The object can be deleted. */
define('PERMS_DELETE', 16);

/**
 * A bitmask of all possible permission values. Useful for
 * removeXxxPermission(), unsetPerm(), etc.
 */
define('PERMS_ALL', PERMS_SHOW | PERMS_READ | PERMS_EDIT | PERMS_DELETE);

/**
 * The root permission
 */
define('PERMS_ROOT', -1);

/**
 * The Perms:: class provides the Horde permissions system.
 *
 * $Horde: framework/Perms/Perms.php,v 1.80.10.22 2009-01-06 15:23:29 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 2.1
 * @package Horde_Perms
 */
class Perms {

    /**
     * Caches information about application permissions.
     *
     * @var array
     */
    var $_applicationPermissions;

    /**
     * Returns the available permissions for a given level.
     *
     * @param string $name  The permission's name.
     *
     * @return array  An array of available permissions and their titles or
     *                false if not sub permissions exist for this level.
     */
    function getAvailable($name)
    {
        if ($name == PERMS_ROOT) {
            $name = '';
        }

        if (empty($name)) {
            /* No name passed, so top level permissions are requested. These
             * can only be applications. */
            $apps = $GLOBALS['registry']->listApps(array('notoolbar', 'active', 'hidden'), true);
            foreach (array_keys($apps) as $app) {
                $apps[$app] = $GLOBALS['registry']->get('name', $app) . ' (' . $app . ')';
            }
            asort($apps);
            return $apps;
        } else {
            /* Name has been passed, explode the name to get all the levels in
             * permission being requisted, with the app as the first level. */
            $levels = array();
            $levels = explode(':', $name);

            /* First level is always app. */
            $app = $levels[0];

            /* Return empty if no app defined API method for providing
             * permission information. */
            if (!$GLOBALS['registry']->hasMethod('perms', $app)) {
                return false;
            }

            /* Call the app's permission function to return the permissions
             * specific to this app. */
            $perms = $this->getApplicationPermissions($app);
            if (is_a($perms, 'PEAR_Error')) {
                return $perms;
            }

            require_once 'Horde/Array.php';
            /* Get the part of the app's permissions based on the permission
             * name requested. */
            $children = Horde_Array::getElement($perms['tree'], $levels);
            if ($children === false ||
                !is_array($children) ||
                !count($children)) {
                /* No array of children available for this permission name. */
                return false;
            }

            $perms_list = array();
            foreach ($children as $perm_key => $perm_val) {
                $perms_list[$perm_key] = $perms['title'][$name . ':' . $perm_key];
            }
            return $perms_list;
        }
    }

    /**
     * Returns the short name of an object, the last portion of the full name.
     *
     * @static
     *
     * @param string $name  The name of the object.
     *
     * @return string  The object's short name.
     */
    function getShortName($name)
    {
        /* If there are several components to the name, explode and
         * get the last one, otherwise just return the name. */
        if (strpos($name, ':') !== false) {
            $tmp = explode(':', $name);
            return array_pop($tmp);
        } else {
            return $name;
        }
    }

    /**
     * Given a permission name, returns the title for that permission by
     * looking it up in the applications's permission api.
     *
     * @param string $name  The permissions's name.
     *
     * @return string  The title for the permission.
     */
    function getTitle($name)
    {
        if ($name === PERMS_ROOT) {
            return _("All Permissions");
        }

        $levels = explode(':', $name);
        if (count($levels) == 1) {
            return $GLOBALS['registry']->get('name', $name) . ' (' . $name . ')';
        }
        $perm = array_pop($levels);

        /* First level is always app. */
        $app = $levels[0];

        /* Return empty if no app defined API method for providing permission
         * information. */
        if (!$GLOBALS['registry']->hasMethod('perms', $app)) {
            return Perms::getShortName($name);
        }

        $app_perms = $this->getApplicationPermissions($app);

        return isset($app_perms['title'][$name])
            ? $app_perms['title'][$name] . ' (' . Perms::getShortName($name) . ')'
            : Perms::getShortName($name);
    }

    /**
     * Returns information about permissions implemented by an application.
     *
     * @since Horde 3.1
     *
     * @param string $app  An application name.
     *
     * @return array  Hash with permissions information.
     */
    function getApplicationPermissions($app)
    {
        if (!isset($this->_applicationPermissions[$app])) {
            $perms = $GLOBALS['registry']->callByPackage($app, 'perms');
            $this->_applicationPermissions[$app] = is_a($perms, 'PEAR_Error') ? array() : $perms;
        }

        return $this->_applicationPermissions[$app];
    }

    /**
     * Returns a new permissions object.
     *
     * @param string $name  The permission's name.
     *
     * @return Permissions  A new permissions object.
     */
    function &newPermission($name)
    {
        return PEAR::raiseError(_("The administrator needs to configure a permanent Permissions backend if you want to use Permissions."));
    }

    /**
     * Returns a Permission object corresponding to the named permission,
     * with the users and other data retrieved appropriately.
     *
     * @param string $name  The name of the permission to retrieve.
     */
    function &getPermission($name)
    {
        return PEAR::raiseError(_("The administrator needs to configure a permanent Permissions backend if you want to use Permissions."));
    }

    /**
     * Returns a Permission object corresponding to the given unique ID, with
     * the users and other data retrieved appropriately.
     *
     * @param integer $cid  The unique ID of the permission to retrieve.
     */
    function &getPermissionById($cid)
    {
        return PEAR::raiseError(_("The administrator needs to configure a permanent Permissions backend if you want to use Permissions."));
    }

    /**
     * Adds a permission to the permissions system. The permission must first
     * be created with Perm::newPermission(), and have any initial users
     * added to it, before this function is called.
     *
     * @param Permission $perm  The new perm object.
     */
    function addPermission(&$perm)
    {
        return PEAR::raiseError(_("The administrator needs to configure a permanent Permissions backend if you want to use Permissions."));
    }

    /**
     * Removes a permission from the permissions system permanently.
     *
     * @param Permission $perm  The permission to remove.
     * @param boolean $force    Force to remove every child.
     */
    function removePermission(&$perm, $force = false)
    {
        return PEAR::raiseError(_("The administrator needs to configure a permanent Permissions backend if you want to use Permissions."));
    }

    /**
     * Finds out what rights the given user has to this object.
     *
     * @param mixed $permission  The full permission name of the object to
     *                           check the permissions of, or the Permission
     *                           object.
     * @param string $user       The user to check for. Defaults to the current
     *                           user.
     * @param string $creator    The user who created the event.
     *
     * @return mixed  A bitmask of permissions the user has, false if there
     *                are none.
     */
    function getPermissions($permission, $user = null, $creator = null)
    {
        if (is_string($permission)) {
            $permission = &$this->getPermission($permission);
            if (is_a($permission, 'PEAR_Error')) {
                Horde::logMessage($permission, __FILE__, __LINE__, PEAR_LOG_DEBUG);
                return false;
            }
        }

        if (is_null($user)) {
            $user = Auth::getAuth();
        }

        // If this is a guest user, only check guest permissions.
        if (empty($user)) {
            return $permission->getGuestPermissions();
        }

        // If $creator was specified, check creator permissions.
        if (!is_null($creator)) {
            // If the user is the creator of the event see if there
            // are creator permissions.
            if (strlen($user) && $user === $creator &&
                ($perms = $permission->getCreatorPermissions()) !== null) {
                return $perms;
            }
        }

        // Check user-level permissions.
        $userperms = $permission->getUserPermissions();
        if (isset($userperms[$user])) {
            return $userperms[$user];
        }

        // If no user permissions are found, try group permissions.
        if (isset($permission->data['groups']) &&
            is_array($permission->data['groups']) &&
            count($permission->data['groups'])) {
            require_once 'Horde/Group.php';
            $groups = &Group::singleton();

            $composite_perm = null;
            $type = $permission->get('type');
            foreach ($permission->data['groups'] as $group => $perm) {
                if ($groups->userIsInGroup($user, $group)) {
                    if (is_null($composite_perm)) {
                        $composite_perm = $type == 'matrix' ? 0 : array();
                    }
                    if ($type == 'matrix') {
                        $composite_perm |= $perm;
                    } else {
                        $composite_perm[] = $perm;
                    }
                }
            }

            if ($composite_perm !== null) {
                return $composite_perm;
            }
        }

        // If there are default permissions, return them.
        if (($perms = $permission->getDefaultPermissions()) !== null) {
            return $perms;
        }

        // Otherwise, deny all permissions to the object.
        return false;
    }

    /**
     * Returns the unique identifier of this permission.
     *
     * @param Permission $permission  The permission object to get the ID of.
     *
     * @return integer  The unique id.
     */
    function getPermissionId($permission)
    {
        return PEAR::raiseError(_("The administrator needs to configure a permanent Permissions backend if you want to use Permissions."));
    }

    /**
     * Finds out if the user has the specified rights to the given object.
     *
     * @param string $permission  The permission to check.
     * @param string $user        The user to check for.
     * @param integer $perm       The permission level that needs to be checked
     *                            for.
     * @param string $creator     The creator of the event
     *
     * @return boolean  True if the user has the specified permissions.
     */
    function hasPermission($permission, $user, $perm, $creator = null)
    {
        return ($this->getPermissions($permission, $user, $creator) & $perm);
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
        return false;
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
        return PEAR::raiseError(_("The administrator needs to configure a permanent Permissions backend if you want to use Permissions."));
    }

    /**
     * Returns all permissions of the system in a tree format.
     *
     * @return array  A hash with all permissions in a tree format.
     */
    function getTree()
    {
        return array();
    }

    /**
     * Returns an hash of the available permissions.
     *
     * @return array  The available permissions as a hash.
     */
    function getPermsArray()
    {
        return array(PERMS_SHOW => _("Show"),
                     PERMS_READ => _("Read"),
                     PERMS_EDIT => _("Edit"),
                     PERMS_DELETE => _("Delete"));
    }

    /**
     * Given an integer value of permissions returns an array
     * representation of the integer.
     *
     * @param integer $int  The integer representation of permissions.
     */
    function integerToArray($int)
    {
        static $array = array();
        if (isset($array[$int])) {
            return $array[$int];
        }

        $array[$int] = array();

        /* Get the available perms array. */
        $perms = Perms::getPermsArray();

        /* Loop through each perm and check if its value is included in the
         * integer representation. */
        foreach ($perms as $val => $label) {
            if ($int & $val) {
                $array[$int][$val] = true;
            }
        }

        return $array[$int];
    }

    /**
     * Attempts to return a concrete Perms instance based on $driver.
     *
     * @param string $driver  The type of the concrete Perms subclass
     *                        to return.  The class name is based on the
     *                        perms driver ($driver).  The code is
     *                        dynamically included.
     * @param array $params   A hash containing any additional configuration or
     *                        connection parameters a subclass might need.
     *
     * @return Perms|boolean  The newly created concrete Perms instance, or
     *                        false on an error.
     */
    function &factory($driver = null, $params = null)
    {
        if (is_null($params)) {
            $params = Horde::getDriverConfig('perms', $driver);
        }

        if (is_null($driver)) {
            $perms = &new Perms($params);
        } else {
            $class = 'Perms_' . $driver;
            if (!class_exists($class)) {
                include 'Horde/Perms/' . $driver . '.php';
            }
            if (class_exists($class)) {
                $perms = &new $class($params);
            } else {
                $perms = false;
            }
        }

        return $perms;
    }

    /**
     * Attempts to return a reference to a concrete Perms instance.
     * It will only create a new instance if no Perms instance
     * currently exists.
     *
     * This method must be invoked as: $var = &Perms::singleton()
     *
     * @return Perms|boolean  The concrete Perm reference, or false on error.
     */
    function &singleton()
    {
        static $perm;
        if (isset($perm)) {
            return $perm;
        }

        $perm_driver = null;
        $perm_params = null;
        if (!empty($GLOBALS['conf']['perms']['driver'])) {
            $perm_driver = $GLOBALS['conf']['perms']['driver'];
            $perm_params = Horde::getDriverConfig('perms', $perm_driver);
        } else {
            $perm_driver = !empty($GLOBALS['conf']['datatree']['driver']) ? 'datatree' : null;
        }

        $perm = Perms::factory($perm_driver, $perm_params);
        return $perm;
    }

}

/**
 * Horde_Permission
 *
 * Instance of a single permissioning object.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 2.1
 * @package Horde_Perms
 */
class Horde_Permission {

    /**
     * The Horde_Permission constructor.
     *
     * @param string $name   The name of the perm.
     * @param string $type   The permission type.
     * @param array $params  A hash with any parameters that the permission
     *                       type needs.
     */
    function Horde_Permission($name, $type = 'matrix', $params = null)
    {
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
        if (isset($this->data[$attribute])) {
            return $this->data[$attribute];
        }

        if ($attribute == 'type') {
            return 'matrix';
        }

        return null;
    }

    /**
     * Get permission name
     */
    function getName()
    {
        return $this->name;
    }

    /**
     * Set permission name
     *
     * @param string $name  Permission name
     */
    function setName($name)
    {
        $this->name = $name;
    }

    /**
     * Get permission details
     */
    function getData()
    {
        return $this->data;
    }

    /**
     * Set permission id
     *
     * @param string $id  Permission ID
     */
    function setData($data)
    {
        $this->data = $data;
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

}
