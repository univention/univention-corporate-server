<?php

require_once 'Horde/DataTree.php';

/** Existence of object is known - object is shown to user. */
define('PERMS_SHOW', 2);

/** Contents of the object can be read. */
define('PERMS_READ', 4);

/** Contents of the object can be edited. */
define('PERMS_EDIT', 8);

/** The object can be deleted. */
define('PERMS_DELETE', 16);

/**
 * The Perms:: class provides the Horde permissions system.
 *
 * $Horde: framework/Perms/Perms.php,v 1.72 2004/04/07 14:43:11 chuck Exp $
 *
 * Copyright 2001-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.1
 * @package Horde_Perms
 */
class Perms {

    /**
     * Pointer to a DataTree instance to manage the different
     * permissions.
     *
     * @var object DataTree $_datatree
     */
    var $_datatree;

    /**
     * Constructor.
     */
    function Perms()
    {
        global $conf;

        if (!isset($conf['datatree']['driver'])) {
            Horde::fatal(_("You must configure a DataTree backend to use Horde."), __FILE__, __LINE__);
        }

        $driver = $conf['datatree']['driver'];
        $this->_datatree = &DataTree::singleton($driver,
                                                array_merge(Horde::getDriverConfig('datatree', $driver),
                                                            array('group' => 'horde.perms')));
    }

    /**
     * Attempts to return a reference to a concrete Perms instance.
     * It will only create a new instance if no Perms instance
     * currently exists.
     *
     * This method must be invoked as: $var = &Perms::singleton()
     *
     * @return object Perms  The concrete Perm reference, or false on an
     *                       error.
     */
    function &singleton()
    {
        static $perm;

        if (!isset($perm)) {
            $perm = &new Perms();
        }

        return $perm;
    }

    /**
     * Return the available permissions for a given level.
     *
     * @param string $name  The perm's name.
     *
     * @return array  An array of available permissions and their titles.
     */
    function getAvailable($name)
    {
        global $registry;

        if (empty($name)) {
            /* No name passed, so top level permissions are requested. These
             * can only be applications. */
            $apps = $registry->listApps(array('notoolbar', 'active', 'hidden'), true);
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
            if (!$registry->hasMethod('perms', $app)) {
                return '';
            }

            /* Call the app's permission function to return the permissions
             * specific to this app. */
            $perms = $registry->callByPackage($app, 'perms');

            require_once 'Horde/Array.php';
            /* Get the part of the app's permissions based on the permission
             * name requested. */
            $childs = Horde_Array::getElement($perms['tree'], $levels);
            if ($childs === false || !is_array($childs)) {
                /* No array of childs available for this permission name. */
                return $childs;
            }

            $perms_list = array();
            foreach ($childs as $perm_key => $perm_val) {
                $perms_list[$perm_key] = $perms['title'][$name . ':' . $perm_key];
            }
            return $perms_list;
        }
    }

    /**
     * Given a permission name, return the title for that permission by
     * looking it up in the app's permission api.
     *
     * @param string $name  The perm's name.
     *
     * @return string  The title for the permission.
     */
    function getTitle($name)
    {
        global $registry;

        $levels = explode(':', $name);
        if (count($levels) == 1) {
            return $name;
        }
        $perm = array_pop($levels);

        /* First level is always app. */
        $app = $levels[0];

        /* Return empty if no app defined API method for providing
         * permission information. */
        if (!$registry->hasMethod('perms', $app)) {
            return DataTree::getShortName($name);
        }

        /* Call the app's permission function to return the
         * permissions specific to this app. */
        $perms = $registry->callByPackage($app, 'perms');

        return isset($perms['title'][$name]) ? $perms['title'][$name] : $name;
    }

    /**
     * Return a new permissions object.
     *
     * @param string $name  The perm's name.
     *
     * @return object DataTreeObject_Permissions  A new permissions object.
     */
    function &newPermission($name)
    {
        if (empty($name)) {
            return PEAR::raiseError('Permission names must be non-empty');
        }
        $perm = &new DataTreeObject_Permission($name);
        $perm->setPermsOb($this);
        return $perm;
    }

    /**
     * Return a DataTreeObject_Permission object corresponding to the
     * named perm, with the users and other data retrieved
     * appropriately.
     *
     * @param string $name The name of the perm to retrieve.
     */
    function &getPermission($name)
    {
        /* Cache of previously retrieved permissions. */
        static $permsCache = array();

        if (isset($permsCache[$name])) {
            return $permsCache[$name];
        }

        $permsCache[$name] = $this->_datatree->getObject($name, 'DataTreeObject_Permission');
        if (!is_a($permsCache[$name], 'PEAR_Error')) {
            $permsCache[$name]->setPermsOb($this);
        }
        return $permsCache[$name];
    }

    /**
     * Return a DataTreeObject_Permission object corresponding to the
     * given unique ID, with the users and other data retrieved
     * appropriately.
     *
     * @param string $cid  The unique ID of the permission to retrieve.
     */
    function &getPermissionById($cid)
    {
        $perm = $this->_datatree->getObjectById($cid, 'DataTreeObject_Permission');
        if (!is_a($perm, 'PEAR_Error')) {
            $perm->setPermsOb($this);
        }
        return $perm;
    }

    /**
     * Add a perm to the perms system. The perm must first be created
     * with Perm::newPermission(), and have any initial users added to
     * it, before this function is called.
     *
     * @param object DataTreeObject_Permission $perm The new perm object.
     */
    function addPermission($perm)
    {
        if (!is_a($perm, 'DataTreeObject_Permission')) {
            return PEAR::raiseError('Permissions must be DataTreeObject_Permission objects or extend that class.');
        }

        return $this->_datatree->add($perm);
    }

    /**
     * Store updated data - users, etc. - of a perm to the backend
     * system.
     *
     * @param object DataTreeObject_Permission $perm   The perm to update.
     */
    function updatePermission($perm)
    {
        if (!is_a($perm, 'DataTreeObject_Permission')) {
            return PEAR::raiseError('Permissions must be DataTreeObject_Permission objects or extend that class.');
        }
        return $this->_datatree->updateData($perm);
    }

    /**
     * Remove a perm from the perms system permanently.
     *
     * @param object DataTreeObject_Permission $perm   The permission to remove.
     *
     * @param optional boolean force [default = false] Force to remove
     *                         every child
     */
    function removePermission($perm, $force = false)
    {
        if (!is_a($perm, 'DataTreeObject_Permission')) {
            return PEAR::raiseError('Permissions must be DataTreeObject_Permission objects or extend that class.');
        }

        return $this->_datatree->remove($perm->getName(), $force);
    }

    /**
     * Find out what rights the given user has to this object.
     *
     * @param mixed  $permission  The full permission name of the object
     *                            to check the permissions of, or the
     *                            DataTreeObject_Permission object.
     * @param string $user        (optional) The user to check for.
     *                            Defaults to Auth::getAuth().
     * @param string $creator     (optional) The user who created the event.
     *
     * @return integer  Any permissions the user has, false if there
     *                  are none.
     */
    function getPermissions($permission, $user = null, $creator = null)
    {
        if (!is_a($permission, 'DataTreeObject_Permission')) {
            $permission = &$this->getPermission($permission);
            if (is_a($permission, 'PEAR_Error')) {
                Horde::logMessage($permission, __FILE__, __LINE__);
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

        // Check user-level permissions first.
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
            foreach ($permission->data['groups'] as $group => $perm) {
                if ($groups->userIsInGroup($user, $groups->getGroupName($group))) {
                    if (is_null($composite_perm)) {
                        $composite_perm = 0;
                    }
                    $composite_perm |= $perm;
                }
            }

            if (!is_null($composite_perm)) {
                return $composite_perm;
            }
        }

        // If there is no creator, then assume the current user will
        // be the creator (likely it's an add).
        if (empty($creator)) {
            $creator = Auth::getAuth();
        }

        // If the user is the creator of the event see if there are
        // creator permissions.
        if (!empty($user) && $user == $creator && 
            ($perms = $permission->getCreatorPermissions()) !== null) {
            return $perms;
        }

        // If there are default permissions, return them.
        if (($perms = $permission->getDefaultPermissions()) !== null) {
            return $perms;
        }

        // Otherwise, deny all permissions to the object.
        return false;
    }

    /**
     * Get the unique identifier of this permission.
     *
     * @param object DataTreeObject_Permission $permission  The permission object to get the ID of.
     *
     * @return integer  The unique id.
     */
    function getPermissionId($permission)
    {
        return $this->_datatree->getId($permission->getName());
    }

    /**
     * Find out if the user has the specified rights to the given object.
     *
     * @param string $permission The permission to check.
     * @param string $user The user to check for.
     * @param int    $perm The permission level that needs to be checked for.
     * @param string $creator (optional) The creator of the event
     *
     * @return boolean True if the user has the specified permissions, and
     *                 false otherwise.
     */
    function hasPermission($permission, $user, $perm, $creator = null)
    {
        return ($this->getPermissions($permission, $user, $creator) & $perm);
    }

    /**
     * Check if a permission exists in the system.
     *
     * @param string $permission  The permission to check.
     *
     * @return boolean  True if the permission exists, false otherwise.
     */
    function exists($permission)
    {
        return $this->_datatree->exists($permission);
    }

    /**
     * Get a list of parent permissions.
     *
     * @param string $child The name of the child to retrieve parents for.
     *
     * @return array [child] [parent] with a tree format
     */
    function getParents($child)
    {
        return $this->_datatree->getParents($child);
    }


    /**
     * Returns an array of the available permissions.
     *
     * @return array  The available permissions as an array.
     */
    function getPermsArray()
    {
        return array(PERMS_SHOW => _("Show"),
                     PERMS_READ => _("Read"),
                     PERMS_EDIT => _("Edit"),
                     PERMS_DELETE => _("Delete"));
    }

    /**
     * Given an integer value of permissions returns an array representation
     * of the integer.
     *
     * @param int $int  The integer representation of permissions.
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

}

/**
 * Extension of the DataTreeObject class for storing Permission
 * information in the DataTree driver. If you want to store
 * specialized Permission information, you should extend this class
 * instead of extending DataTreeObject directly.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.1
 * @package Horde_Perms
 */
class DataTreeObject_Permission extends DataTreeObject {

    /**
     * The Perms object which this permission came from - needed for
     * updating data in the backend to make changes stick, etc.
     *
     * @var object Perms $permsOb
     */
    var $_permsOb;

    /**
     * The DataTreeObject_Permission constructor. Just makes sure to
     * call the parent constructor so that the perm's name is set
     * properly.
     *
     * @param string $name The name of the perm.
     */
    function DataTreeObject_Permission($name)
    {
        parent::DataTreeObject($name);
    }

    /**
     * Associates a Perms object with this perm.
     *
     * @param object Perm $permsOb The Perm object.
     */
    function setPermsOb(&$permsOb)
    {
        $this->_permsOb = &$permsOb;
    }

    /**
     * Get the unique identifier of this permission.
     *
     * @return integer  The unique id.
     */
    function getId()
    {
        return $this->_permsOb->getPermissionId($this);
    }

    /**
     * Update the permissions based on data passed in the array.
     *
     * @param array $perms  An array containing the permissions which are to be
     *                      updated.
     */
    function updatePermissions($perms)
    {
        /* Array of permission types to iterate through. */
        $perm_types = Perms::getPermsArray();

        foreach ($perms as $perm_class => $perm_values) {
            switch ($perm_class) {
            case 'default':
            case 'guest':
            case 'creator':
                foreach ($perm_types as $val => $label) {
                    if (!empty($perm_values[$val])) {
                        $this->setPerm($perm_class, $val, false);
                    } else {
                        $this->unsetPerm($perm_class, $val, false);
                    }
                }
                break;

            case 'u':
            case 'g':
                $permId = array('class' => $perm_class == 'u' ? 'users' : 'groups');
                /* Figure out what names that are stored in this permission
                 * class have not been submitted for an update, ie. have been
                 * removed entirely. */
                $current_names = isset($this->data[$permId['class']]) ? array_keys($this->data[$permId['class']]) : array();
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

                    foreach ($perm_types as $val => $label) {
                        if (!empty($name_values[$val])) {
                            $this->setPerm($permId, $val, false);
                        } else {
                            $this->unsetPerm($permId, $val, false);
                        }
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
            if (isset($this->data[$permId['class']][$permId['name']])) {
                $this->data[$permId['class']][$permId['name']] |= $permission;
            } else {
                $this->data[$permId['class']][$permId['name']] = $permission;
            }
        } else {
            if (isset($this->data[$permId])) {
                $this->data[$permId] |= $permission;
            } else {
                $this->data[$permId] = $permission;
            }
        }

        if ($update) {
            $this->_permsOb->updatePermission($this);
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
            if (isset($this->data[$permId['class']][$permId['name']])) {
                $this->data[$permId['class']][$permId['name']] &= ~$permission;
                if (empty($this->data[$permId['class']][$permId['name']])) {
                    unset($this->data[$permId['class']][$permId['name']]);
                }
                if ($update) {
                    $this->_permsOb->updatePermission($this);
                }
            }
        } else {
            if (isset($this->data[$permId])) {
                $this->data[$permId] &= ~$permission;
                if ($update) {
                    $this->_permsOb->updatePermission($this);
                }
            }
        }
    }

    /**
     * Give a user additional permissions to this object.
     *
     * @param string   $user        The user to grant additional permissions to.
     * @param constant $permission  The permission (PERMS_DELE, etc.) to add.
     * @param boolean  $update      (optional) Whether to automatically update the
     *                              backend. Defaults to true.
     */
    function addUserPermission($user, $permission, $update = true)
    {
        if (empty($user)) {
            return;
        }
        if (isset($this->data['users'][$user])) {
            $this->data['users'][$user] |= $permission;
        } else {
            $this->data['users'][$user] = $permission;
        }
        if ($update) {
            $this->_permsOb->updatePermission($this);
        }
    }

    /**
     * Grant guests additional permissions to this object.
     *
     * @param constant $permission  The permission (PERMS_DELE, etc.) to add.
     * @param boolean  $update     (optional) Whether to automatically update the
     *                             backend. Defaults to true.
     */
    function addGuestPermission($permission, $update = true)
    {
        if (isset($this->data['guest'])) {
            $this->data['guest'] |= $permission;
        } else {
            $this->data['guest'] = $permission;
        }
        if ($update) {
            $this->_permsOb->updatePermission($this);
        }
    }

    /**
     * Grant creators additional permissions to this object.
     *
     * @param constant $permission  The permission (PERMS_DELE, etc.) to add.
     * @param boolean  $update      (optional) Whether to automatically update the
     *                              backend. Defaults to true.
     */
    function addCreatorPermission($permission, $update = true)
    {
        if (isset($this->data['creator'])) {
            $this->data['creator'] |= $permission;
        } else {
            $this->data['creator'] = $permission;
        }
        if ($update) {
            $this->_permsOb->updatePermission($this);
        }
    }

    /**
     * Grant additional default permissions to this object.
     *
     * @param integer $permission  The permission (PERMS_DELE, etc.) to add.
     * @param boolean $update      (optional) Whether to automatically update the
     *                             backend. Defaults to true.
     */
    function addDefaultPermission($permission, $update = true)
    {
        if (isset($this->data['default'])) {
            $this->data['default'] |= $permission;
        } else {
            $this->data['default'] = $permission;
        }
        if ($update) {
            $this->_permsOb->updatePermission($this);
        }
    }

    /**
     * Give a group additional permissions to this object.
     *
     * @param integer  $groupId    The id of the group to grant additional permissions to.
     * @param constant $permission  The permission (PERMS_DELE, etc.) to add.
     * @param boolean  $update     (optional) Whether to automatically update the
     *                             backend. Defaults to true.
     */
    function addGroupPermission($groupId, $permission, $update = true)
    {
        if (empty($groupId)) {
            return;
        }

        if (isset($this->data['groups'][$groupId])) {
            $this->data['groups'][$groupId] |= $permission;
        } else {
            $this->data['groups'][$groupId] = $permission;
        }
        if ($update) {
            $this->_permsOb->updatePermission($this);
        }
    }

    /**
     * Remove a permission that a user currently has on this object.
     *
     * @param string   $user         The user to remove the permission from.
     * @param constant $permission   The permission (PERMS_DELE, etc.) to
     *                               remove.
     * @param optional bool $update  Whether to automatically update the
     *                               backend. Defaults to true.
     */
    function removeUserPermission($user, $permission, $update = true)
    {
        if (empty($user)) {
            return;
        }
        if (isset($this->data['users'][$user])) {
            $this->data['users'][$user] &= ~$permission;
            if (empty($this->data['users'][$user])) {
                unset($this->data['users'][$user]);
            }
            if ($update) {
                $this->_permsOb->updatePermission($this);
            }
        }
    }

    /**
     * Remove a permission that guests currently have on this object.
     *
     * @param constant $permission  The permission (PERMS_DELE, etc.) to remove.
     * @param boolean  $update      (optional) Whether to automatically update the
     *                              backend. Defaults to true.
     */
    function removeGuestPermission($permission, $update = true)
    {
        if (isset($this->data['guest'])) {
            $this->data['guest'] &= ~$permission;
            if ($update) {
                $this->_permsOb->updatePermission($this);
            }
        }
    }

    /**
     * Remove a permission that creators currently have on this object.
     *
     * @param constant $permission  The permission (PERMS_DELE, etc.) to remove.
     * @param boolean  $update      (optional) Whether to automatically update the
     *                              backend. Defaults to true.
     */
    function removeCreatorPermission($permission, $update = true)
    {
        if (isset($this->data['creator'])) {
            $this->data['creator'] &= ~$permission;
            if ($update) {
                $this->_permsOb->updatePermission($this);
            }
        }
    }

    /**
     * Remove a default permission on this object.
     *
     * @param constant $permission  The permission (PERMS_DELE, etc.) to remove.
     * @param boolean  $update      (optional) Whether to automatically update the
     *                              backend. Defaults to true.
     */
    function removeDefaultPermission($permission, $update = true)
    {
        if (isset($this->data['default'])) {
            $this->data['default'] &= ~$permission;
            if ($update) {
                $this->_permsOb->updatePermission($this);
            }
        }
    }

    /**
     * Remove a permission that a group currently has on this object.
     *
     * @param integer  $groupId     The id of the group to remove the permission from.
     * @param constant $permission  The permission (PERMS_DELE, etc.) to remove.
     * @param boolean  $update      (optional) Whether to automatically update the
     *                              backend. Defaults to true.
     */
    function removeGroupPermission($groupId, $permission, $update = true)
    {
        if (empty($groupId)) {
            return;
        }

        if (isset($this->data['groups'][$groupId])) {
            $this->data['groups'][$groupId] &= ~$permission;
            if (empty($this->data['groups'][$groupId])) {
                unset($this->data['groups'][$groupId]);
            }
            if ($update) {
                $this->_permsOb->updatePermission($this);
            }
        }
    }

    /**
     * Save any changes to this object to the backend permanently.
     */
    function save()
    {
        $this->_permsOb->updatePermission($this);
    }

    /**
     * Get an array of all user permissions on this object.
     *
     * @param optional integer $perm  List only users with this permission
     *                                level. Defaults to all users.
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
     * Get the guest permissions on this object.
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
     * Get the creator permissions on this object.
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
     * Get the default permissions on this object.
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
     * Get an array of all group permissions on this object.
     *
     * @param optional integer $perm  List only users with this permission
     *                                level. Defaults to all users.
     *
     * @return array  All group permissions for this object, indexed by group.
     */
    function getGroupPermissions($perm = null)
    {
        if (!isset($this->data['groups']) || !is_array($this->data['groups'])) {
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
