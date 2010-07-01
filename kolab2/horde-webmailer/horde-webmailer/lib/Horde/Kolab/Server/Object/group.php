<?php
/**
 * Representation of a Kolab user group.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Server/Object/group.php,v 1.2.2.5 2009-04-25 08:56:33 wrobel Exp $
 *
 * PHP version 4
 *
 * @category Kolab
 * @package  Kolab_Server
 * @author   Gunnar Wrobel <wrobel@pardus.de>
 * @license  http://www.fsf.org/copyleft/lgpl.html LGPL
 * @link     http://pear.horde.org/index.php?package=Kolab_Server
 */

/**
 * This class provides methods to deal with groups for Kolab.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Server/Object/group.php,v 1.2.2.5 2009-04-25 08:56:33 wrobel Exp $
 *
 * Copyright 2008-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @category Kolab
 * @package  Kolab_Server
 * @author   Gunnar Wrobel <wrobel@pardus.de>
 * @license  http://www.fsf.org/copyleft/lgpl.html LGPL
 * @link     http://pear.horde.org/index.php?package=Kolab_Server
 */
class Horde_Kolab_Server_Object_group extends Horde_Kolab_Server_Object {

    /**
     * The attributes supported by this class
     *
     * @var array
     */
    var $_supported_attributes = array(
        KOLAB_ATTR_CN,
        KOLAB_ATTR_MAIL,
        KOLAB_ATTR_MEMBER,
        KOLAB_ATTR_DELETED,
    );

    /**
     * Attributes derived from the LDAP values.
     *
     * @var array
     */
    var $_derived_attributes = array(
        KOLAB_ATTR_ID,
        KOLAB_ATTR_VISIBILITY,
    );

    /**
     * The attributes required when creating an object of this class.
     *
     * @var array
     */
    var $_required_attributes = array(
        KOLAB_ATTR_CN,
    );

    /**
     * The ldap classes for this type of object.
     *
     * @var array
     */
    var $_object_classes = array(
        KOLAB_OC_TOP,
        KOLAB_OC_KOLABGROUPOFNAMES,
    );

    /**
     * Sort by this attributes (must be a LDAP attribute).
     *
     * @var string
     */
    var $sort_by = KOLAB_ATTR_MAIL;

    /**
     * Derive an attribute value.
     *
     * @param string $attr The attribute to derive.
     *
     * @return mixed The value of the attribute.
     */
    function _derive($attr)
    {
        switch ($attr) {
        case KOLAB_ATTR_VISIBILITY:
            return strpos($this->_uid, 'cn=internal') === false;
        default:
            return parent::_derive($attr);
        }
    }

    /**
     * Return the filter string to retrieve this object type.
     *
     * @return string The filter to retrieve this object type from the server
     *                database.
     */
    public static function getFilter()
    {
        $criteria = array('AND' => array(array('field' => KOLAB_ATTR_OC,
                                               'op'    => '=',
                                               'test'  => KOLAB_OC_KOLABGROUPOFNAMES),
                          ),
        );
        return $criteria;
    }

    /**
     * Convert the object attributes to a hash.
     *
     * @param string $attrs The attributes to return.
     *
     * @return array|PEAR_Error The hash representing this object.
     */
    function toHash($attrs = null)
    {
        if (!isset($attrs)) {
            $attrs = array(
                KOLAB_ATTR_ID,
                KOLAB_ATTR_MAIL,
                KOLAB_ATTR_VISIBILITY,
            );
        }
        return parent::toHash($attrs);
    }

    /**
     * Generates an ID for the given information.
     *
     * @param array $info The data of the object.
     *
     * @static
     *
     * @return string|PEAR_Error The ID.
     */
    function generateId($info)
    {
        if (isset($info['mail'])) {
            return trim($info['mail'], " \t\n\r\0\x0B,");
        } else {
            return trim($info['cn'], " \t\n\r\0\x0B,");
        }
    }

    /**
     * Saves object information.
     *
     * @param array $info The information about the object.
     *
     * @return boolean|PEAR_Error True on success.
     */
    function save($info)
    {
        if (!isset($info['cn'])) {
            if (!isset($info['mail'])) {
                return PEAR::raiseError('Either the mail address or the common name has to be specified for a group object!');
            } else {
                $info['cn'] = $info['mail'];
            }
        }
        return parent::save($info);
    }

    /**
     * Retrieve the member list for this group.
     *
     * @return array|PEAR_Error The list of members in this group.
     */
    function getMembers()
    {
        return $this->_get(KOLAB_ATTR_MEMBER, false);
    }

    /**
     * Add a member to this group.
     *
     * @param string $member The UID of the member to add.
     *
     * @return array|PEAR_Error True if successful.
     */
    function addMember($member)
    {
        $members = $this->getMembers();
        if (is_a($members, 'PEAR_Error')) {
            return $members;
        }
        if (!in_array($member, $members)) {
            $this->_cache[KOLAB_ATTR_MEMBER][] = $member;
        } else {
            return PEAR::raiseError(_("The UID %s is already a member of the group %s!"),
                                    $member, $this->_uid);
        }
        return $this->save($this->_cache);
    }

    /**
     * Delete a member from this group.
     *
     * @param string $member The UID of the member to delete.
     *
     * @return array|PEAR_Error True if successful.
     */
    function deleteMember($member)
    {
        $members = $this->getMembers();
        if (is_a($members, 'PEAR_Error')) {
            return $members;
        }
        if (in_array($member, $members)) {
            $this->_cache[KOLAB_ATTR_MEMBER] = array_diff($this->_cache[KOLAB_ATTR_MEMBER],
                                                          array($member));
        } else {
            return PEAR::raiseError(_("The UID %s is no member of the group %s!"),
                                    $member, $this->_uid);

        }
        return $this->save($this->_cache);
    }

    /**
     * Is the specified UID member of this group?
     *
     * @param string $member The UID of the member to check.
     *
     * @return boolean|PEAR_Error True if the UID is a member of the group,
     *                            false otherwise.
     */
    function isMember($member)
    {
        $members = $this->getMembers();
        if (is_a($members, 'PEAR_Error') || !is_array($members)) {
            return $members;
        }
        if (!in_array($member, $members)) {
            return false;
        } else {
            return true;
        }
    }

}
