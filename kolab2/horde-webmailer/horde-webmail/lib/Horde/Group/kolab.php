<?php

require_once 'Horde/Group/ldap.php';
require_once 'Horde/LDAP.php';

/**
 * The Group_kolab class provides a Kolab backend for the Horde groups
 * system.
 *
 * FIXME: A better solution would be to let this class rely on
 *        Horde/Kolab/LDAP.php.
 *
 * $Horde: framework/Group/Group/kolab.php,v 1.4.2.2 2009-01-06 15:23:08 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @since   Horde 3.2
 * @package Horde_Group
 */
class Group_kolab extends Group_ldap {

    /**
     * A marker for fatal errors
     */
    var $_error;

    /**
     * Constructor.
     */
    function Group_kolab($params)
    {
        if (!function_exists('ldap_connect')) {
            $this->_error = PEAR::raiseError(_("The Kolab group driver requires LDAP support."));
        }

        $this->_params = array();
        $this->_params['hostspec'] = $GLOBALS['conf']['kolab']['ldap']['server'];
        $this->_params['basedn'] = $GLOBALS['conf']['kolab']['ldap']['basedn'];
        $this->_params['binddn'] = $GLOBALS['conf']['kolab']['ldap']['phpdn'];
        $this->_params['password'] = $GLOBALS['conf']['kolab']['ldap']['phppw'];
        $this->_params['version'] = 3;
        $this->_params['gid'] = 'cn';
        $this->_params['memberuid'] = 'member';
        $this->_params['attrisdn'] = true;
        $this->_params['filter_type'] = 'objectclass';
        $this->_params['objectclass'] = 'kolabGroupOfNames';
        $this->_params['newgroup_objectclass'] = 'kolabGroupOfNames';

        $this->_filter = 'objectclass=' . $this->_params['objectclass'];

        $this->__wakeup();
    }

    /**
     * Initializes the object.
     */
    function __wakeup()
    {
        foreach (array_keys($this->_groupCache) as $name) {
            $this->_groupCache[$name]->setGroupOb($this);
        }
    }

    /**
     * Returns the properties that need to be serialized.
     *
     * @return array  List of serializable properties.
     */
    function __sleep()
    {
        $properties = get_object_vars($this);
        unset($properties['_datatree'], $properties['_ds']);
        $properties = array_keys($properties);
        return $properties;
    }


    /**
     * Returns a new group object.
     *
     * @param string $name    The group's name.
     * @param string $parent  The group's parent's name.
     *
     * @return Kolab_Group  A new group object.
     */
    function &newGroup($name)
    {
        return PEAR::raiseError(_("Unsupported"));
    }

    /**
     * Adds a group to the groups system. The group must first be created with
     * Group::newGroup(), and have any initial users added to it, before this
     * function is called.
     *
     * @param Kolab_Group $group  The new group object.
     */
    function addGroup($group)
    {
        return PEAR::raiseError(_("Unsupported"));
    }

    /**
     * Stores updated data - users, etc. - of a group to the backend system.
     *
     * @param Kolab_Group $group  The group to update.
     */
    function updateGroup($group)
    {
        return PEAR::raiseError(_("Unsupported"));
    }

    /**
     * Removes a group from the groups system permanently.
     *
     * @param Kolab_Group $group  The group to remove.
     * @param boolean $force               Force to remove every child.
     */
    function removeGroup($group, $force = false)
    {
        return PEAR::raiseError(_("Unsupported"));
    }

    /**
     * Return a Kolab_Group object corresponding to the given dn, with the
     * users and other data retrieved appropriately.
     *
     * @param string $dn  The dn of the group to retrieve.
     *
     * @return Kolab_Group  The requested group.
     */
    function &getGroupById($dn)
    {
        static $cache = array();

        if (!isset($cache[$dn])) {

            if (is_a($this->_error, 'PEAR_Error')) {
                return $this->_error;
            }

            /* Connect to the LDAP server. */
            $success = $this->_connect();
            if (is_a($success, 'PEAR_Error')) {
                return PEAR::raiseError($success->getMessage());
            }

            $search = @ldap_search($this->_ds, $dn, $this->_filter);
            if (!$search) {
                return PEAR::raiseError(_("Could not reach the LDAP server"));
            }

            $result = @ldap_get_entries($this->_ds, $search);
            @ldap_close($this->_ds);
            if (!is_array($result) || (count($result) <= 1)) {
                return PEAR::raiseError(_("Empty result"));
            }

            $attributes = array();
            for ($i = 0; $i < $result[0]['count']; $i++) {
                if ($result[0][$result[0][$i]]['count'] > 1) {
                    $attributes[$result[0][$i]] = array();
                    for ($j = 0; $j < $result[0][$result[0][$i]]['count']; $j++) {
                        $attributes[$result[0][$i]][] = $result[0][$result[0][$i]][$j];
                    }
                } else {
                    $attributes[$result[0][$i]] = $result[0][$result[0][$i]][0];
                }
            }
            $attributes['dn'] = $result[0]['dn'];

            $group = new Kolab_Group($this->getGroupName($dn));
            $group->_fromAttributes($attributes);
            $group->setGroupOb($this);
            $cache[$dn] = $group;
        }

        return $cache[$dn];
    }


    /**
     * Retrieve the ID of the given group.
     *
     * NOTE: If given a group name, this function can be unreliable if more
     * than one group exists with the same name.
     *
     * @param mixed $group   LDAP_Group object, or a group name (string)
     *
     * @return string  The group's ID.
     */
    function getGroupId($group)
    {
        static $cache = array();

        if (is_a($group, 'Kolab_Group')) {
            return $group->getDn();
        }

        if (!isset($cache[$group])) {

            if (is_a($this->_error, 'PEAR_Error')) {
                return $this->_error;
            }

            $this->_connect();
            $search = @ldap_search($this->_ds, $this->_params['basedn'],
                                   $this->_params['gid'] . '=' . $group,
                                   array($this->_params['gid']));
            if (!$search) {
                return PEAR::raiseError(_("Could not reach the LDAP server"));
            }

            $result = @ldap_get_entries($this->_ds, $search);
            @ldap_close($this->_ds);
            if (!is_array($result) || (count($result) <= 1)) {
                return PEAR::raiseError(_("Empty result"));
            }
            $cache[$group] = $result[0]['dn'];
        }

        return $cache[$group];
    }

    /**
     * Get a list of the parents of a child group.
     *
     * @param string $dn  The fully qualified group dn
     *
     * @return array  Nested array of parents
     */
    function getGroupParents($dn)
    {
        return array();
    }

    /**
     * Get the parent of the given group.
     *
     * @param string $dn  The dn of the child group.
     *
     * @return string  The dn of the parent group.
     */
    function getGroupParent($dn)
    {
        return null;
    }

    /**
     * Get a list of parents all the way up to the root object for the given
     * group.
     *
     * @param string $dn  The dn of the group.
     *
     * @return array  A flat list of all of the parents of the given group,
     *                hashed in $dn => $name format.
     */
    function getGroupParentList($dn)
    {
        return array();
    }

    /**
     * Tries to find a DN for a given kolab mail address.
     *
     * @param string $mail  The mail address to search for.
     *
     * @return string  The corresponding dn or false.
     */
    function dnForMail($mail)
    {
        $filter = '(&(objectclass=kolabInetOrgPerson)(mail=' . Horde_LDAP::quote($mail) . '))';
        $search = @ldap_search($this->_ds, $this->_params['basedn'], $filter);
        if (!$search) {
            return PEAR::raiseError(_("Could not reach the LDAP server"));
        }
        $dn = @ldap_first_entry($this->_ds, $search);
        if ($dn) {
            return ldap_get_dn($this->_ds, $dn);
        }
        return PEAR::raiseError(sprintf(_("Error searching for user with the email address \"%s\"!"),
                                        $mail));
    }

    /**
     * Get a list of every group that the given user is a member of.
     *
     * @param string  $user          The user to get groups for.
     * @param boolean $parentGroups  Also return the parents of any groups?
     *
     * @return array  An array of all groups the user is in.
     */
    function getGroupMemberships($user, $parentGroups = false)
    {
        static $cache = array();

        if (empty($cache[$user])) {

            if (is_a($this->_error, 'PEAR_Error')) {
                return $this->_error;
            }

            /* Connect to the LDAP server. */
            $success = $this->_connect();
            if (is_a($success, 'PEAR_Error')) {
                return PEAR::raiseError($success->getMessage());
            }

            $dn = $this->dnForMail($user);
            if (is_a($dn, 'PEAR_Error')) {
                return $dn;
            }

            // Set up search filter
            $filter = '(' . $this->_params['memberuid'] . '=' . $dn . ')';

            // Perform search
            $search = @ldap_search($this->_ds, $this->_params['basedn'], $filter);
            if (!$search) {
                return PEAR::raiseError(_("Could not reach the LDAP server"));
            }

            $result = @ldap_get_entries($this->_ds, $search);
            @ldap_close($this->_ds);
            if (!is_array($result) || (count($result) <= 1)) {
                return array();
            }

            $groups = array();
            $current_charset = NLS::getCharset();
            for ($i = 0; $i < $result['count']; $i++) {
                $utf8_dn = String::convertCharset($result[$i]['dn'], 'UTF-8', $current_charset);
                $groups[$utf8_dn] = $this->getGroupName($utf8_dn);
            }

            $cache[$user] = $groups;
        }

        return $cache[$user];
    }

}

/**
 *
 *
 * @author  Ben Chavet <ben@horde.org>
 * @since   Horde 3.1
 * @package Horde_Group
 */
class Kolab_Group extends LDAP_Group {

    /**
     * Constructor.
     *
     * @param string $name    The name of this group.
     * @param string $parent  The dn of the parent of this group.
     */
    function Kolab_Group($name, $parent = null)
    {
        $this->setName($name);
    }

    /**
     * Fetch the ID of this group
     *
     * @return string The group's ID
     */
    function getId()
    {
        return $this->getDn();
    }

    /**
     * Save any changes to this object to the backend permanently.
     */
    function save()
    {
        return PEAR::raiseError(_("Unsupported"));
    }

    /**
     * Adds a user to this group, and makes sure that the backend is
     * updated as well.
     *
     * @param string $username The user to add.
     */
    function addUser($username, $update = true)
    {
        return PEAR::raiseError(_("Unsupported"));
    }


    /**
     * Removes a user from this group, and makes sure that the backend
     * is updated as well.
     *
     * @param string $username The user to remove.
     */
    function removeUser($username, $update = true)
    {
        return PEAR::raiseError(_("Unsupported"));
    }

    /**
     * Get all the users recently added or removed from the group.
     */
    function getAuditLog()
    {
        return array();
    }

    /**
     * Clears the audit log. To be called after group update.
     */
    function clearAuditLog()
    {
    }

    /**
     * Sets the name of this object.
     *
     * @param string $name  The name to set this object's name to.
     */
    function getDn()
    {
        return $this->name . ',' . $GLOBALS['conf']['kolab']['ldap']['basedn'];
    }

    /**
     * Take in a list of attributes from the backend and map it to our
     * internal data array.
     *
     * @param array $attributes  The list of attributes from the backend.
     */
    function _fromAttributes($attributes = array())
    {
        $this->data['users'] = array();
        foreach ($attributes as $key => $value) {
            if (String::lower($key) == 'member') {
                if (is_array($value)) {
                    foreach ($value as $user) {
                        $pattern = '/^cn=([^,]+).*$/';
                        $results = array();
                        preg_match($pattern, $user, $results);
                        if (isset($results[1])) {
                            $user = $results[1];
                        }
                        $this->data['users'][$user] = '1';
                    }
                } else {
                    $pattern = '/^cn=([^,]+).*$/';
                    $results = array();
                    preg_match($pattern, $value, $results);
                    if (isset($results[1])) {
                        $value = $results[1];
                    }
                    $this->data['users'][$value] = '1';
                }
            } elseif ($key == 'mail') {
                $this->data['email'] = $value;
            } else {
                $this->data[$key] = $value;
            }
        }
    }

    /**
     * Map this object's attributes from the data array into a format that
     * can be stored in an LDAP entry.
     *
     * @return array  The entry array.
     */
    function _toAttributes()
    {
        $attributes = array();
        foreach ($this->data as $key => $value) {
            if ($key == 'users') {
                foreach ($value as $user => $membership) {
                    $user = 'cn=' . $user . ',' . $GLOBALS['conf']['kolab']['ldap']['basedn'];
                    $attributes['member'][] = $user;
                }
            } elseif ($key == 'email') {
                if (!empty($value)) {
                    $attributes['mail'] = $value;
                }
            } elseif ($key != 'dn' && $key != 'member') {
                $attributes[$key] = !empty($value) ? $value : ' ';
            }
        }

        return $attributes;
    }

}
