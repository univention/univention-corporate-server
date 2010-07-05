<?php
/**
 * @package Kolab_Storage
 *
 * $Horde: framework/Kolab_Storage/lib/Horde/Kolab/Storage/Perms.php,v 1.2.2.2 2009-01-06 15:23:18 jan Exp $
 */

/** Basic Horde Permission library. **/
require_once 'Horde/Perms.php';

/**
 * The Horde_Permission_Kolab provides a bridge between Horde
 * Permission handling and the IMAP permission system used on the
 * Kolab server.
 *
 * $Horde: framework/Kolab_Storage/lib/Horde/Kolab/Storage/Perms.php,v 1.2.2.2 2009-01-06 15:23:18 jan Exp $
 *
 * Copyright 2006-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @package Kolab_Storage
 */
class Horde_Permission_Kolab extends Horde_Permission {

    /**
     * The folder name.
     *
     * @var string
     */
    var $_folder;

    /**
     * A cache for the folder acl settings. The cache holds the permissions
     * in horde compatible format, not in the IMAP permission format.
     *
     * @var string
     */
    var $data;

    /**
     * A cache for the raw IMAP folder acl settings.
     *
     * @var string
     */
    var $acl;

    /**
     * Constructor.
     *
     * @param Kolab_Folder   $folder   The Kolab Folder
                                       these permissions belong to.
     * @param array          $perms    A set of initial permissions.
     */
    function Horde_Permission_Kolab(&$folder, $perms = null)
    {
        $this->setFolder($folder);
        if (!isset($perms)) {
            $result = $this->getPerm();
            if (is_a($result, 'PEAR_Error')) {
                Horde::logMessage(sprintf("Failed parsing permission information. Error was: %s",
                                          $result->getMessage()), __FILE__, __LINE__);
            } else {
                $perms = $result;
            }
        }
        $this->data = $perms;

    }

    /**
     * Returns the properties that need to be serialized.
     *
     * @return array  List of serializable properties.
     */
    function __sleep()
    {
        $properties = get_object_vars($this);
        unset($properties['_folder']);
        $properties = array_keys($properties);
        return $properties;
    }

    /**
     * Sets the folder object for this permission object.
     *
     * @param string $folder  Kolab Folder object.
     */
    function setFolder(&$folder)
    {
        $this->_folder = $folder;
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
        // This object only handles permissions. So only return these
        switch ($attribute) {
        case 'perm':
            return $this->data;
        case 'type':
            return 'matrix';
        default:
            // User requested something other than permissions: return null
            return null;
        }
    }

    /**
     * Gets the current permission of the folder and stores the values in the
     * cache.
     *
     * @return array|PEAR_Error  The data array representing the permissions.
     */
    function getPerm()
    {
        $acl = $this->_folder->getACL();
        if (is_a($acl, 'PEAR_Error')) {
            Horde::logMessage($acl, __FILE__, __LINE__);
            return array();
        }
        if (empty($acl)) {
            return array();
        }
        $this->acl = &$acl;

        // Loop through the returned users
        $data = array();
        foreach ($acl as $user => $rights) {
            // Convert the user rights to horde format
            $result = 0;
            for ($i = 0, $j = strlen($rights); $i < $j; $i++) {
                switch ($rights[$i]) {
                case 'l':
                    $result |= PERMS_SHOW;
                    break;
                case 'r':
                    $result |= PERMS_READ;
                    break;
                case 'i':
                    $result |= PERMS_EDIT;
                    break;
                case 'd':
                    $result |= PERMS_DELETE;
                    break;
                }
            }

            // Check for special users
            $name = '';
            switch ($user) {
            case 'anyone':
                $name = 'default';
                break;
            case 'anonymous':
                $name = 'guest';
                break;
            }

            // Did we have a special user?
            if ($name) {
                // Store the converted acl in the cache
                $data[$name] = $result;
                continue;
            }

            // Is it a group?
            if (substr($user, 0, 6) == 'group:') {
                if (!isset($groups)) {
                    require_once 'Horde/Group.php';
                    $groups = &Group::singleton();
                }
                $group_id = $groups->getGroupId(substr($user, 6));
                if (!is_a($group_id, 'PEAR_Error')) {
                    // Store the converted acl in the cache
                    $data['groups'][$group_id] = $result;
                }

                continue;
            }

            // Standard user
            // Store the converted acl in the cache
            $data['users'][$user] = $result;
        }

        return $data;
    }

    /**
     * Saves the current permission values from the cache to the IMAP folder.
     *
     * @return boolean|PEAR_Error True on success, false if there is
     *                            nothing to save.
     */
    function save()
    {
        if (!isset($this->data)) {
            return false;
        }

        // FIXME: If somebody else accessed the folder before us, we will overwrite
        //        the change here.
        $current = $this->getPerm();

        foreach ($this->data as $user => $user_perms) {
            if (is_array($user_perms)) {
                foreach ($user_perms as $userentry => $perms) {
                    if ($user == 'groups') {
                        if (!isset($groups)) {
                            require_once 'Horde/Group.php';
                            $groups = &Group::singleton();
                        }
                        // Convert group id back to name
                        $group_name = $groups->getGroupName($userentry);
                        if (is_a($group_name, 'PEAR_Error')) {
                            return $group_name;
                        }
                        $name = 'group:' . $group_name;
                    } else if ($user == 'users') {
                        $name = $userentry;
                    } else {
                        continue;
                    }
                    $result = $this->savePermission($name, $perms);
                    if (is_a($result, 'PEAR_Error')) {
                        return $result;
                    }
                    unset($current[$user][$userentry]);
                }
            } else {
                if ($user == 'default') {
                    $name = 'anyone';
                } else if ($user == 'guest') {
                    $name = 'anonymous';
                } else {
                    continue;
                }
                $result = $this->savePermission($name, $user_perms);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }
                unset($current[$user]);
            }
        }

        // Delete ACLs that have been removed
        foreach ($current as $user => $user_perms) {
            if (is_array($user_perms)) {
                foreach ($user_perms as $userentry => $perms) {
                    if ($user == 'groups') {
                        if (!isset($groups)) {
                            require_once 'Horde/Group.php';
                            $groups = &Group::singleton();
                        }
                        // Convert group id back to name
                        $group_name = $groups->getGroupName($userentry);
                        if (is_a($group_name, 'PEAR_Error')) {
                            return $group_name;
                        }
                        $name = 'group:' . $group_name;
                    } else {
                        $name = $userentry;
                    }

                    $result = $this->_folder->deleteACL($name);
                    if (is_a($result, 'PEAR_Error')) {
                        return $result;
                    }
                }
            } else {
                if ($user == 'default') {
                    $name = 'anyone';
                } else if ($user == 'guest') {
                    $name = 'anonymous';
                } else {
                    continue;
                }
                $result = $this->_folder->deleteACL($name);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }
            }
        }

        // Load the permission from the folder again
        $this->data = $this->getPerm();

        return true;
    }

    /**
     * Saves the specified permission values for the given user on the
     * IMAP folder.
     *
     * @return boolean|PEAR_Error  True on success.
     */
    function savePermission($user, $perms)
    {
        // Convert the horde permission style to IMAP permissions
        $result = $user == $this->_folder->getOwner() ? 'a' : '';
        if ($perms & PERMS_SHOW) {
            $result .= 'l';
        }
        if ($perms & PERMS_READ) {
            $result .= 'r';
        }
        if ($perms & PERMS_EDIT) {
            $result .= 'iswc';
        }
        if ($perms & PERMS_DELETE) {
            $result .= 'd';
        }

        $result = $this->_folder->setACL($user, $result);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return true;
    }

    /**
     * Finds out what rights the given user has to this object.
     *
     * @param string $user The user to check for. Defaults to the current
     * user.
     * @param string $creator The user who created the object.
     *
     * @return mixed A bitmask of permissions, a permission value, or
     *               an array of permission values the user has,
     *               depending on the permission type and whether the
     *               permission value is ambiguous. False if there is
     *               no such permsission.
     */
    function getPermissions($user = null, $creator = null)
    {
        if ($user === null) {
            $user = Auth::getAuth();
        }
        // If $creator was specified, check creator permissions.
        if ($creator !== null) {
            // If the user is the creator see if there are creator
            // permissions.
            if (strlen($user) && $user === $creator &&
                ($perms = $this->getCreatorPermissions()) !== null) {
                return $perms;
            }
        }

        // Check user-level permissions.
        $userperms = $this->getUserPermissions();
        if (isset($userperms[$user])) {
            return $userperms[$user];
        }

        // If no user permissions are found, try group permissions.
        $groupperms = $this->getGroupPermissions();
        if (!empty($groupperms)) {
            require_once 'Horde/Group.php';
            $groups = &Group::singleton();

            $composite_perm = null;
            foreach ($this->data['groups'] as $group => $perm) {
                $result = $groups->userIsInGroup($user, $group);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }

                if ($result) {
                    if ($composite_perm === null) {
                        $composite_perm = 0;
                    }
                    $composite_perm |= $perm;
                }
            }

            if ($composite_perm !== null) {
                return $composite_perm;
            }
        }

        // If there are default permissions, return them.
        if (($perms = $this->getDefaultPermissions()) !== null) {
            return $perms;
        }

        // Otherwise, deny all permissions to the object.
        return false;
    }

    /**
     * Finds out if the user has the specified rights to the given object.
     *
     * @param string $user    The user to check for.
     * @param integer $perm   The permission level that needs to be checked
     *                        for.
     * @param string $creator The creator of the shared object.
     *
     * @return boolean True if the user has the specified permissions.
     */
    function hasPermission($user, $perm, $creator = null)
    {
        return ($this->getPermissions($user, $creator) & $perm);
    }
}
