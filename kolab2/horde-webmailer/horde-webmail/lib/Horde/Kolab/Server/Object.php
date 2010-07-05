<?php
/**
 * The base class representing Kolab objects stored in the server
 * database.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Server/Object.php,v 1.2.2.9 2009-04-25 08:56:34 wrobel Exp $
 *
 * PHP version 4
 *
 * @category Kolab
 * @package  Kolab_Server
 * @author   Gunnar Wrobel <wrobel@pardus.de>
 * @license  http://www.fsf.org/copyleft/lgpl.html LGPL
 * @link     http://pear.horde.org/index.php?package=Kolab_Server
 */

/** Define the different Kolab object types */
define('KOLAB_OBJECT_ADDRESS',          'Horde_Kolab_Server_Object_address');
define('KOLAB_OBJECT_ADMINISTRATOR',    'Horde_Kolab_Server_Object_administrator');
define('KOLAB_OBJECT_DOMAINMAINTAINER', 'Horde_Kolab_Server_Object_domainmaintainer');
define('KOLAB_OBJECT_GROUP',            'Horde_Kolab_Server_Object_group');
define('KOLAB_OBJECT_DISTLIST',         'Horde_Kolab_Server_Object_distlist');
define('KOLAB_OBJECT_MAINTAINER',       'Horde_Kolab_Server_Object_maintainer');
define('KOLAB_OBJECT_SHAREDFOLDER',     'Horde_Kolab_Server_Object_sharedfolder');
define('KOLAB_OBJECT_USER',             'Horde_Kolab_Server_Object_user');
define('KOLAB_OBJECT_SERVER',           'Horde_Kolab_Server_Object_server');

/** Define the possible Kolab object attributes */
define('KOLAB_ATTR_OC',           'objectClass');
define('KOLAB_ATTR_UID',          'dn');
define('KOLAB_ATTR_ID',           'id');
define('KOLAB_ATTR_SN',           'sn');
define('KOLAB_ATTR_CN',           'cn');
define('KOLAB_ATTR_GIVENNAME',    'givenName');
define('KOLAB_ATTR_FN',           'fn');
define('KOLAB_ATTR_LNFN',         'lnfn');
define('KOLAB_ATTR_FNLN',         'fnln');
define('KOLAB_ATTR_MAIL',         'mail');
define('KOLAB_ATTR_ALIAS',        'alias');
define('KOLAB_ATTR_SID',          'uid');
define('KOLAB_ATTR_ACL',          'acl');
define('KOLAB_ATTR_MEMBER',       'member');
define('KOLAB_ATTR_USERTYPE',     'usertype');
define('KOLAB_ATTR_DOMAIN',       'domain');
define('KOLAB_ATTR_FOLDERTYPE',   'kolabFolderType');
define('KOLAB_ATTR_USERPASSWORD', 'userPassword');
define('KOLAB_ATTR_DELETED',      'kolabDeleteFlag');
define('KOLAB_ATTR_FREEBUSYHOST', 'kolabFreeBusyServer');
define('KOLAB_ATTR_IMAPHOST',     'kolabImapServer');
define('KOLAB_ATTR_HOMESERVER',   'kolabHomeServer');
define('KOLAB_ATTR_KOLABDELEGATE','kolabDelegate');
define('KOLAB_ATTR_IPOLICY',      'kolabInvitationPolicy');
define('KOLAB_ATTR_QUOTA',        'cyrus-userquota');
define('KOLAB_ATTR_FBPAST',       'kolabFreeBusyPast');
define('KOLAB_ATTR_FBFUTURE',     'kolabFreeBusyFuture');
define('KOLAB_ATTR_VISIBILITY',   'visible');

/** Define the possible Kolab object classes */
define('KOLAB_OC_TOP',                'top');
define('KOLAB_OC_INETORGPERSON',      'inetOrgPerson');
define('KOLAB_OC_KOLABINETORGPERSON', 'kolabInetOrgPerson');
define('KOLAB_OC_HORDEPERSON',        'hordePerson');
define('KOLAB_OC_KOLABGROUPOFNAMES',  'kolabGroupOfNames');
define('KOLAB_OC_KOLABSHAREDFOLDER',  'kolabSharedFolder');

/** Define the possible Kolab user types */
define('KOLAB_UT_STANDARD',           0);
define('KOLAB_UT_INTERNAL',           1);
define('KOLAB_UT_GROUP',              2);
define('KOLAB_UT_RESOURCE',           3);

/**
 * This class provides methods to deal with Kolab objects stored in
 * the Kolab db.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Server/Object.php,v 1.2.2.9 2009-04-25 08:56:34 wrobel Exp $
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
class Horde_Kolab_Server_Object {

    /**
     * Link into the Kolab server.
     *
     * @var Kolab_Server
     */
    var $_db;

    /**
     * UID of this object on the Kolab server.
     *
     * @var string
     */
    var $_uid;

    /**
     * The cached LDAP result
     *
     * FIXME: Include _ldap here
     *
     * @var mixed
     */
    var $_cache = false;

    /** FIXME: Add an attribute cache for the get() function */

    /**
     * The LDAP filter to retrieve this object type.
     *
     * @var string
     */
    var $filter = '';

    /**
     * The group the UID must be member of so that this object really
     * matches this class type. This may not include the root UID.
     *
     * @var string
     */
    var $required_group;

    /**
     * The LDAP attributes supported by this class.
     *
     * @var array
     */
    var $_supported_attributes = array();

    /**
     * Attributes derived from the LDAP values.
     *
     * @var array
     */
    var $_derived_attributes = array(
        KOLAB_ATTR_ID,
    );

    /**
     * The attributes required when creating an object of this class.
     *
     * @var array
     */
    var $_required_attributes = array();

    /**
     * The ldap classes for this type of object.
     *
     * @var array
     */
    var $_object_classes = array();

    /**
     * Sort by this attributes (must be a LDAP attribute).
     *
     * @var string
     */
    var $sort_by = KOLAB_ATTR_SN;

    /**
     * Initialize the Kolab Object. Provide either the UID or a
     * LDAP search result.
     *
     * @param Horde_Kolab_Server &$db  The link into the Kolab db.
     * @param string             $uid  UID of the object.
     * @param array              $data A possible array of data for the object
     */
    function Horde_Kolab_Server_Object(&$db, $uid = null, $data = null)
    {
        $this->_db = &$db;
        if (empty($uid)) {
            if (empty($data) || !isset($data[KOLAB_ATTR_UID])) {
                $this->_cache = PEAR::raiseError(_('Specify either the UID or a search result!'));
                return;
            }
            if (is_array($data[KOLAB_ATTR_UID])) {
                $this->_uid = $data[KOLAB_ATTR_UID][0];
            } else {
                $this->_uid = $data[KOLAB_ATTR_UID];
            }
            $this->_cache = $data;
        } else {
            $this->_uid = $uid;
        }
    }

    /**
     * Attempts to return a concrete Horde_Kolab_Server_Object instance based on
     * $type.
     *
     * @param mixed  $type     The type of the Horde_Kolab_Server_Object subclass
     *                         to return.
     * @param string $uid      UID of the object
     * @param array  &$storage A link to the Kolab_Server class handling read/write.
     * @param array  $data     A possible array of data for the object
     *
     * @return Horde_Kolab_Server_Object|PEAR_Error The newly created concrete
     *                                 Horde_Kolab_Server_Object instance.
     */
    function &factory($type, $uid, &$storage, $data = null)
    {
        $result = Horde_Kolab_Server_Object::loadClass($type);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (class_exists($type)) {
            $object = &new $type($storage, $uid, $data);
        } else {
            $object = PEAR::raiseError('Class definition of ' . $type . ' not found.');
        }

        return $object;
    }

    /**
     * Attempts to load the concrete Horde_Kolab_Server_Object class based on
     * $type.
     *
     * @param mixed $type The type of the Horde_Kolab_Server_Object subclass.
     *
     * @static
     *
     * @return true|PEAR_Error True if successfull.
     */
    function loadClass($type)
    {
        if (in_array($type, array(KOLAB_OBJECT_ADDRESS, KOLAB_OBJECT_ADMINISTRATOR,
                                  KOLAB_OBJECT_DISTLIST, KOLAB_OBJECT_DOMAINMAINTAINER,
                                  KOLAB_OBJECT_GROUP, KOLAB_OBJECT_MAINTAINER,
                                  KOLAB_OBJECT_SHAREDFOLDER, KOLAB_OBJECT_USER,
                                  KOLAB_OBJECT_SERVER))) {
            $name = substr($type, 26);
        } else {
            return PEAR::raiseError(sprintf('Object type "%s" not supported.',
                                            $type));
        }

        $name = basename($name);

        if (file_exists(dirname(__FILE__) . '/Object/' . $name . '.php')) {
            include_once dirname(__FILE__) . '/Object/' . $name . '.php';
        }
    }

    /**
     * Does the object exist?
     *
     * @return NULL
     */
    function exists()
    {
        $this->_read();
        if (!$this->_cache || is_a($this->_cache, 'PEAR_Error')) {
            return false;
        }
        return true;
    }

    /**
     * Read the object into the cache
     *
     * @return NULL
     */
    function _read()
    {
        $this->_cache = $this->_db->read($this->_uid,
                                         $this->_supported_attributes);
    }

    /**
     * Get the specified attribute of this object
     *
     * @param string $attr The attribute to read
     *
     * @return string the value of this attribute
     */
    function get($attr)
    {
        if ($attr != KOLAB_ATTR_UID) {
            if (!in_array($attr, $this->_supported_attributes)
                && !in_array($attr, $this->_derived_attributes)) {
                return PEAR::raiseError(sprintf(_("Attribute \"%s\" not supported!"),
                                                $attr));
            }
            if (!$this->_cache) {
                $this->_read();
            }
            if (is_a($this->_cache, 'PEAR_Error')) {
                return $this->_cache;
            }
        }

        if (in_array($attr, $this->_derived_attributes)) {
            return $this->_derive($attr);
        }

        switch ($attr) {
        case KOLAB_ATTR_UID:
            return $this->_getUID();
        case KOLAB_ATTR_FN:
            return $this->_getFn();
        case KOLAB_ATTR_SN:
        case KOLAB_ATTR_CN:
        case KOLAB_ATTR_GIVENNAME:
        case KOLAB_ATTR_MAIL:
        case KOLAB_ATTR_SID:
        case KOLAB_ATTR_USERPASSWORD:
        case KOLAB_ATTR_DELETED:
        case KOLAB_ATTR_IMAPHOST:
        case KOLAB_ATTR_FREEBUSYHOST:
        case KOLAB_ATTR_HOMESERVER:
        case KOLAB_ATTR_FBPAST:
        case KOLAB_ATTR_FBFUTURE:
        case KOLAB_ATTR_FOLDERTYPE:
            return $this->_get($attr, true);
        default:
            return $this->_get($attr, false);
        }
    }

    /**
     * Get the specified attribute of this object
     *
     * @param string  $attr   The attribute to read
     * @param boolean $single Should a single value be returned
     *                        or are multiple values allowed?
     *
     * @return string the value of this attribute
     */
    function _get($attr, $single = true)
    {
        if (isset($this->_cache[$attr])) {
            if ($single && is_array($this->_cache[$attr])) {
                return $this->_cache[$attr][0];
            } else {
                return $this->_cache[$attr];
            }
        }
        return false;
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
        case KOLAB_ATTR_ID:
            $result = split(',', $this->_uid);
            if (substr($result[0], 0, 3) == 'cn=') {
                return substr($result[0], 3);
            } else {
                return $result[0];
            }
        case KOLAB_ATTR_LNFN:
            $gn = $this->_get(KOLAB_ATTR_GIVENNAME, true);
            $sn = $this->_get(KOLAB_ATTR_SN, true);
            return sprintf('%s, %s', $sn, $gn);
        case KOLAB_ATTR_FNLN:
            $gn = $this->_get(KOLAB_ATTR_GIVENNAME, true);
            $sn = $this->_get(KOLAB_ATTR_SN, true);
            return sprintf('%s %s', $gn, $sn);
        default:
            return false;
        }
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
            $attrs = array();
        }
        $result = array();
        foreach ($attrs as $key) {
            $value = $this->get($key);
            if (is_a($value, 'PEAR_Error')) {
                return $value;
            }
            $result[$key] = $value;
        }

        return $result;
    }

    /**
     * Get the UID of this object
     *
     * @return string the UID of this object
     */
    function _getUid()
    {
        return $this->_uid;
    }

    /**
     * Get the "first name" attribute of this object
     *
     * FIXME: This should get refactored to be combined with the Id value.
     *
     * @return string the "first name" of this object
     */
    function _getFn()
    {
        $sn = $this->_get(KOLAB_ATTR_SN, true);
        $cn = $this->_get(KOLAB_ATTR_CN, true);
        return trim(substr($cn, 0, strlen($cn) - strlen($sn)));
    }

    /**
     * Get the groups for this object
     *
     * @return mixed An array of group ids or a PEAR Error in case of
     *               an error.
     */
    function getGroups()
    {
        return array();
    }

    /**
     * Returns the server url of the given type for this user.
     *
     * This method can be used to encapsulate multidomain support.
     *
     * @param string $server_type The type of server URL that should be returned.
     *
     * @return string|PEAR_Error The server url or empty.
     */
    function getServer($server_type)
    {
        return PEAR::raiseError('Not implemented!');
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
        $id_mapfields = array('givenName', 'sn');
        $id_format    = '%s %s';

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
        foreach ($this->_required_attributes as $attribute) {
            if (!isset($info[$attribute])) {
                return PEAR::raiseError(sprintf('The value for "%s" is missing!',
                                                $attribute));
            }
        }

        $info['objectClass'] = $this->_object_classes;

        $result = $this->_db->save($this->_uid, $info);
        if ($result === false || is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $this->_cache = $info;

        return $result;
    }
};
