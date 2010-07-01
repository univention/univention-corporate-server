<?php
/**
 * A standard Kolab user.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Server/Object/user.php,v 1.2.2.12 2009-04-25 12:34:52 wrobel Exp $
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
 * This class provides methods to deal with Kolab users stored in
 * the Kolab db.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Server/Object/user.php,v 1.2.2.12 2009-04-25 12:34:52 wrobel Exp $
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
class Horde_Kolab_Server_Object_user extends Horde_Kolab_Server_Object {

    /**
     * The attributes supported by this class
     *
     * @var array
     */
    var $_supported_attributes = array(
        KOLAB_ATTR_SN,
        KOLAB_ATTR_CN,
        KOLAB_ATTR_GIVENNAME,
        KOLAB_ATTR_FN,
        KOLAB_ATTR_SID,
        KOLAB_ATTR_USERPASSWORD,
        KOLAB_ATTR_MAIL,
        KOLAB_ATTR_DELETED,
        KOLAB_ATTR_IMAPHOST,
        KOLAB_ATTR_FREEBUSYHOST,
        KOLAB_ATTR_HOMESERVER,
        KOLAB_ATTR_KOLABDELEGATE,
        KOLAB_ATTR_IPOLICY,
        KOLAB_ATTR_FBFUTURE,
    );

    /**
     * Attributes derived from the LDAP values.
     *
     * @var array
     */
    var $_derived_attributes = array(
        KOLAB_ATTR_ID,
        KOLAB_ATTR_USERTYPE,
        KOLAB_ATTR_LNFN,
        KOLAB_ATTR_FNLN,
    );

    /**
     * The attributes required when creating an object of this class.
     *
     * @var array
     */
    var $_required_attributes = array(
        KOLAB_ATTR_SN,
        KOLAB_ATTR_GIVENNAME,
        KOLAB_ATTR_USERPASSWORD,
        KOLAB_ATTR_MAIL,
        KOLAB_ATTR_HOMESERVER,
    );

    /**
     * The ldap classes for this type of object.
     *
     * @var array
     */
    var $_object_classes = array(
        KOLAB_OC_TOP,
        KOLAB_OC_INETORGPERSON,
        KOLAB_OC_KOLABINETORGPERSON,
        KOLAB_OC_HORDEPERSON,
    );

    /**
     * Initialize the Kolab Object. Provide either the UID or a
     * LDAP search result.
     *
     * @param Horde_Kolab_Server &$db  The link into the Kolab db.
     * @param string             $dn   UID of the object.
     * @param array              $data A possible array of data for the object
     */
    function Horde_Kolab_Server_Object_user(&$db, $dn = null, $data = null)
    {
        global $conf;

        /** Allows to customize the supported user attributes. */
        if (isset($conf['kolab']['server']['user_supported_attrs'])) {
            $this->_supported_attributes = $conf['kolab']['server']['user_supported_attrs'];
        }

        /** Allows to customize the required user attributes. */
        if (isset($conf['kolab']['server']['user_required_attrs'])) {
            $this->_required_attributes = $conf['kolab']['server']['user_required_attrs'];
        }

        /** Allows to customize the user object classes. */
        if (isset($conf['kolab']['server']['user_objectclasses'])) {
            $this->_object_classes = $conf['kolab']['server']['user_object_classes'];
        }

        Horde_Kolab_Server_Object::Horde_Kolab_Server_Object($db, $dn, $data);
    }

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
        case KOLAB_ATTR_USERTYPE:
            if (strpos($this->_uid, 'cn=internal')) {
                return KOLAB_UT_INTERNAL;
            } else if (strpos($this->_uid, 'cn=group')) {
                return KOLAB_UT_GROUP;
            } else if (strpos($this->_uid, 'cn=resource')) {
                return KOLAB_UT_RESOURCE;
            } else {
                return KOLAB_UT_STANDARD;
            }
        default:
            return parent::_derive($attr);
        }
    }

    /**
     * The LDAP filter to retrieve this object type
     *
     * @return string
     */
    function getFilter()
    {
        $criteria = array('AND' => array(
                              array('field' => KOLAB_ATTR_SN,
                                    'op'    => '=',
                                    'test'  => '*'),
                              array('field' => KOLAB_ATTR_MAIL,
                                    'op'    => '=',
                                    'test'  => '*'),
                              array('field' => KOLAB_ATTR_SID,
                                    'op'    => '=',
                                    'test'  => '*'),
                              array('field' => KOLAB_ATTR_OC,
                                    'op'    => '=',
                                    'test'  => KOLAB_OC_KOLABINETORGPERSON),
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
                KOLAB_ATTR_SID,
                KOLAB_ATTR_FN,
                KOLAB_ATTR_MAIL,
                KOLAB_ATTR_USERTYPE,
            );
        }
        return parent::toHash($attrs);
    }

    /**
     * Get the groups for this object
     *
     * @return mixed|PEAR_Error An array of group ids, false if no groups were
     *                          found.
     */
    function getGroups()
    {
        return $this->_db->getGroups($this->_uid);
    }

    /**
     * Get the group mail addresses for this object
     *
     * @return mixed|PEAR_Error An array of group addresses, false if no groups were
     *                          found.
     */
    function getGroupAddresses()
    {
        return $this->_db->getGroupAddresses($this->_uid);
    }

    /**
     * Returns the server url of the given type for this user.
     *
     * This method is used to encapsulate multidomain support.
     *
     * @param string $server_type The type of server URL that should be returned.
     *
     * @return string The server url or empty on error.
     */
    function getServer($server_type)
    {
        global $conf;

        switch ($server_type) {
        case 'freebusy':
            $server = $this->get(KOLAB_ATTR_FREEBUSYHOST);
            if (!is_a($server, 'PEAR_Error') && !empty($server)) {
                return $server;
            }
            $server = $this->getServer('homeserver');
            if (is_a($server, 'PEAR_Error')) {
                return $server;
            }
            if (empty($server)) {
                $server = $_SERVER['SERVER_NAME'];
            }
            if (isset($conf['kolab']['freebusy']['server'])) {
                return $conf['kolab']['freebusy']['server'];
            }
            if (isset($conf['kolab']['server']['freebusy_url_format'])) {
                return sprintf($conf['kolab']['server']['freebusy_url_format'],
                               $server);
            } else {
                return 'https://' . $server . '/freebusy';
            }
        case 'imap':
            $server = $this->get(KOLAB_ATTR_IMAPHOST);
            if (!is_a($server, 'PEAR_Error') && !empty($server)) {
                return $server;
            }
        case 'homeserver':
        default:
            $server = $this->get(KOLAB_ATTR_HOMESERVER);
            if (empty($server)) {
                $server = $_SERVER['SERVER_NAME'];
            }
            return $server;
        }
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
        global $conf;

        /** The fields that should get mapped into the user ID. */
        if (isset($conf['kolab']['server']['user_id_mapfields'])) {
            $id_mapfields = $conf['kolab']['server']['user_id_mapfields'];
        } else {
            $id_mapfields = array('givenName', 'sn');
        }

        /** The user ID format. */
        if (isset($conf['kolab']['server']['user_id_format'])) {
            $id_format = $conf['kolab']['server']['user_id_format'];
        } else {
            $id_format = '%s %s';
        }

        $fieldarray = array();
        foreach ($id_mapfields as $mapfield) {
            if (isset($info[$mapfield])) {
                $fieldarray[] = $info[$mapfield];
            } else {
                $fieldarray[] = '';
            }
        }
        return trim(vsprintf($id_format, $fieldarray), " \t\n\r\0\x0B,");
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
            if (!isset($info['sn']) || !isset($info['givenName'])) {
                return PEAR::raiseError('Either the last name or the given name is missing!');
            } else {
                $info['cn'] = $this->generateId($info);
            }
        }

        if (isset($conf['kolab']['server']['user_mapping'])) {
            $mapped = array();
            $map    = $conf['kolab']['server']['user_mapping'];
            foreach ($map as $key => $val) {
                $mapped[$val] = $info[$key];
            }
            $info = $mapped;
        }

        if (isset($conf['kolab']['server']['user_mapping'])) {
            $mapped = array();
            $map    = $conf['kolab']['server']['user_mapping'];
            foreach ($map as $key => $val) {
                $mapped[$val] = $info[$key];
            }
            $info = $mapped;
        }

        return parent::save($info);
    }
};
