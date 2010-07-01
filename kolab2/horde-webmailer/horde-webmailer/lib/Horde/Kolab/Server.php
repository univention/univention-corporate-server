<?php
/**
 * A library for accessing the Kolab user database.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Server.php,v 1.2.2.9 2009-04-25 08:56:34 wrobel Exp $
 *
 * PHP version 4
 *
 * @category Kolab
 * @package  Kolab_Server
 * @author   Gunnar Wrobel <wrobel@pardus.de>
 * @license  http://www.fsf.org/copyleft/lgpl.html LGPL
 * @link     http://pear.horde.org/index.php?package=Kolab_Server
 */

/** We need PEAR */
require_once 'PEAR.php';

/** Provide access to the Kolab specific objects. */
require_once 'Horde/Kolab/Server/Object.php';

/** Define types of return values. */
define('KOLAB_SERVER_RESULT_SINGLE', 1);
define('KOLAB_SERVER_RESULT_STRICT', 2);
define('KOLAB_SERVER_RESULT_MANY',   3);

/**
 * This class provides methods to deal with Kolab objects stored in
 * the Kolab object db.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Server.php,v 1.2.2.9 2009-04-25 08:56:34 wrobel Exp $
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
class Horde_Kolab_Server {

    /**
     * Server parameters.
     *
     * @var array
     */
    var $_params = array();

    /**
     * The UID of the current user.
     *
     * @var string
     */
    var $uid;

    /**
     * Valid Kolab object types
     *
     * @var array
     */
    var $valid_types = array(
        KOLAB_OBJECT_ADDRESS,
        KOLAB_OBJECT_ADMINISTRATOR,
        KOLAB_OBJECT_DISTLIST,
        KOLAB_OBJECT_DOMAINMAINTAINER,
        KOLAB_OBJECT_GROUP,
        KOLAB_OBJECT_MAINTAINER,
        KOLAB_OBJECT_SERVER,
        KOLAB_OBJECT_SHAREDFOLDER,
        KOLAB_OBJECT_USER,
    );

    /**
     * Construct a new Horde_Kolab_Server object.
     *
     * @param array $params Parameter array.
     */
    function Horde_Kolab_Server($params = array())
    {
        $this->_params = $params;
        if (isset($params['uid'])) {
            $this->uid = $params['uid'];
        }
    }

    /**
     * Attempts to return a concrete Horde_Kolab_Server instance based
     * on $driver.
     *
     * @param mixed $driver The type of concrete Horde_Kolab_Server subclass to
     *                      return.
     * @param array $params A hash containing any additional
     *                      configuration or connection parameters a subclass
     *                      might need.
     *
     * @return Horde_Kolab_Server|PEAR_Error The newly created concrete
     *                                       Horde_Kolab_Server instance.
     */
    function &factory($driver, $params = array())
    {
        $driver = basename($driver);
        if (empty($driver) || $driver == 'none') {
            $db = new Horde_Kolab_Server($params);
            return $db;
        }

        if (file_exists(dirname(__FILE__) . '/Server/' . $driver . '.php')) {
            include_once dirname(__FILE__) . '/Server/' . $driver . '.php';
        }

        $class = 'Horde_Kolab_Server_' . $driver;
        if (class_exists($class)) {
            $db = new $class($params);
        } else {
            $db = PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }

        return $db;
    }

    /**
     * Attempts to return a reference to a concrete Horde_Kolab_Server
     * instance based on $driver. It will only create a new instance
     * if no Horde_Kolab_Server instance with the same parameters currently
     * exists.
     *
     * This method must be invoked as:
     * $var = &Horde_Kolab_Server::singleton()
     *
     * @param array $params An array of optional login parameters. May
     *                      contain "uid" (for the login uid), "user"
     *                      (if the uid is not yet known), and "pass"
     *                      (for a password).
     *
     * @return Horde_Kolab_Server|PEAR_Error The concrete Horde_Kolab_Server
     *                                       reference.
     */
    function &singleton($params = null)
    {
        global $conf;

        static $instances = array();

        if (isset($conf['kolab']['server']['driver'])) {
            $driver = $conf['kolab']['server']['driver'];
            if (isset($conf['kolab']['server']['params'])) {
                $server_params = $conf['kolab']['server']['params'];
            } else {
                $server_params = array();
            }
        } else if (isset($conf['kolab']['ldap']['server'])
                   && isset($conf['kolab']['ldap']['basedn'])
                   && isset($conf['kolab']['ldap']['phpdn'])
                   && isset($conf['kolab']['ldap']['phppw'])) {
            $driver = 'ldap';

            $server_params = array('server'  => $conf['kolab']['ldap']['server'],
                                   'base_dn' => $conf['kolab']['ldap']['basedn'],
                                   'uid'     => $conf['kolab']['ldap']['phpdn'],
                                   'pass'    => $conf['kolab']['ldap']['phppw']);
            if (isset($conf['kolab']['ldap']['map'])) {
                $server_params['map'] = $conf['kolab']['ldap']['map'];
            }
        } else {
            $driver        = null;
            $server_params = array();
        }

        if (!empty($params)) {
            if (isset($params['user'])) {
                $tmp_server = &Horde_Kolab_Server::factory($driver, $server_params);

                $uid = $tmp_server->uidForIdOrMail($params['user']);
                if (is_a($uid, 'PEAR_Error')) {
                    return PEAR::raiseError(sprintf(_("Failed identifying the UID of the Kolab user %s. Error was: %s"),
                                                    $params['user'],
                                                    $uid->getMessage()));
                }
                $server_params['uid'] = $uid;
            }
            if (isset($params['pass'])) {
                if (isset($server_params['pass'])) {
                    $server_params['search_pass'] = $server_params['pass'];
                }
                $server_params['pass'] = $params['pass'];
            }
            if (isset($params['uid'])) {
                if (isset($server_params['uid'])) {
                    $server_params['search_uid'] = $server_params['pass'];
                }
                $server_params['uid'] = $params['uid'];
            }
        }

        $sparam         = $server_params;
        $sparam['pass'] = isset($sparam['pass']) ? md5($sparam['pass']) : '';
        $signature      = serialize(array($driver, $sparam));
        if (empty($instances[$signature])) {
            $instances[$signature] = &Horde_Kolab_Server::factory($driver,
                                                                  $server_params);
        }

        return $instances[$signature];
    }

    /**
     * Return the root of the UID values on this server.
     *
     * @return string The base UID on this server (base DN on ldap).
     */
    function getBaseUid()
    {
        return '';
    }

    /**
     * Fetch a Kolab object.
     *
     * @param string $uid  The UID of the object to fetch.
     * @param string $type The type of the object to fetch.
     *
     * @return Kolab_Object|PEAR_Error The corresponding Kolab object.
     */
    function &fetch($uid = null, $type = null)
    {
        if (!isset($uid)) {
            $uid = $this->uid;
        }
        if (empty($type)) {
            $type = $this->_determineType($uid);
            if (is_a($type, 'PEAR_Error')) {
                return $type;
            }
        } else {
            if (!in_array($type, $this->valid_types)) {
                return PEAR::raiseError(sprintf(_("Invalid Kolab object type \"%s\"."),
                                                $type));
            }
        }

        $object = &Horde_Kolab_Server_Object::factory($type, $uid, $this);
        return $object;
    }

    /**
     * Add a Kolab object.
     *
     * @param array $info The object to store.
     *
     * @return Kolab_Object|PEAR_Error The newly created Kolab object.
     */
    function &add($info)
    {
        if (!isset($info['type'])) {
            return PEAR::raiseError('The type of a new object must be specified!');
        }
        if (!in_array($info['type'], $this->valid_types)) {
            return PEAR::raiseError(sprintf(_("Invalid Kolab object type \"%s\"."),
                                            $type));
        }

        $uid = $this->generateUid($info['type'], $info);
        if (is_a($uid, 'PEAR_Error')) {
            return $uid;
        }

        $object = &Horde_Kolab_Server_Object::factory($info['type'], $uid, $this);
        if (is_a($object, 'PEAR_Error')) {
            return $object;
        }

        if ($object->exists()) {
            return PEAR::raiseError('The object does already exist!');
        }

        $result = $object->save($info);
        if (is_a($result, 'PEAR_Error')) {
            return PEAR::raiseError(sprintf('Adding object failed: %s',
                                            $result->getMessage()));
        }
        return $object;
    }

    /**
     * Update or create a Kolab object.
     *
     * @param string $type The type of the object to store.
     * @param array  $info Any additional information about the object to store.
     * @param string $uid  The unique id of the object to store.
     *
     * @return Kolab_Object|PEAR_Error The updated Kolab object.
     */
    function &store($type, $info, $uid = null)
    {
        if (!in_array($type, $this->valid_types)) {
            return PEAR::raiseError(sprintf(_("Invalid Kolab object type \"%s\"."),
                                            $type));
        }
        if (empty($uid)) {
            $uid = $this->generateUid($type, $info);
        }

        $object = &Horde_Kolab_Server_Object::factory($type, $uid, $this);
        $result = $object->save($info);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        return $object;
    }

    /**
     * Get the groups for this object
     *
     * @param string $uid The UID of the object to fetch.
     *
     * @return array|PEAR_Error An array of group ids.
     */
    function getGroups($uid)
    {
        return array();
    }

    /**
     * Read object data.
     *
     * @param string $uid   The object to retrieve.
     * @param string $attrs Restrict to these attributes.
     *
     * @return array|PEAR_Error An array of attributes.
     */
    function read($uid, $attrs = null)
    {
        return $this->_read($uid, $attrs);
    }

    /**
     * Stub for reading object data.
     *
     * @param string $uid   The object to retrieve.
     * @param string $attrs Restrict to these attributes.
     *
     * @return array|PEAR_Error An array of attributes.
     */
    function _read($uid, $attrs = null)
    {
        return PEAR::raiseError(_("Not implemented!"));
    }

    /**
     * Stub for saving object data.
     *
     * @param string $uid  The object to save.
     * @param string $data The data of the object.
     *
     * @return array|PEAR_Error An array of attributes.
     */
    function save($uid, $data)
    {
        return PEAR::raiseError(_("Not implemented!"));
    }

    /**
     * Determine the type of a Kolab object.
     *
     * @param string $uid The UID of the object to examine.
     *
     * @return string The corresponding Kolab object type.
     */
    function _determineType($uid)
    {
        return KOLAB_OBJECT_USER;
    }

    /**
     * Identify the primary mail attribute for the first object found
     * with the given ID or mail.
     *
     * @param string $id Search for objects with this ID/mail.
     *
     * @return mixed|PEAR_Error The mail address or false if there was
     *                          no result.
     */
    function mailForIdOrMail($id)
    {
        /* In the default class we just return the id */
        return $id;
    }

    /**
     * Returns a list of allowed email addresses for the given user.
     *
     * @param string $user The user name.
     *
     * @return array|PEAR_Error An array of allowed mail addresses.
     */
    function addrsForIdOrMail($user)
    {
        /* In the default class we just return the user name */
        return $user;
    }

    /**
     * Return the UID for a given primary mail, uid, or alias.
     *
     * @param string $mail A valid mail address for the user.
     *
     * @return mixed|PEAR_Error The UID or false if there was no result.
     */
    function uidForMailAddress($mail)
    {
        /* In the default class we just return the mail address */
        return $mail;
    }

    /**
     * Identify the UID for the first user found using a specified
     * attribute value.
     *
     * @param string $attr     The name of the attribute used for searching.
     * @param string $value    The desired value of the attribute.
     * @param int    $restrict A KOLAB_SERVER_RESULT_* result restriction.
     *
     * @return mixed|PEAR_Error The UID or false if there was no result.
     */
    function uidForAttr($attr, $value,
                       $restrict = KOLAB_SERVER_RESULT_SINGLE)
    {
        /* In the default class we just return false */
        return false;
    }

    /**
     * Identify the GID for the first group found using a specified
     * attribute value.
     *
     * @param string $attr     The name of the attribute used for searching.
     * @param string $value    The desired value of the attribute.
     * @param int    $restrict A KOLAB_SERVER_RESULT_* result restriction.
     *
     * @return mixed|PEAR_Error The GID or false if there was no result.
     */
    function gidForAttr($attr, $value,
                        $restrict = KOLAB_SERVER_RESULT_SINGLE)
    {
        /* In the default class we just return false */
        return false;
    }

    /**
     * Is the given UID member of the group with the given mail address?
     *
     * @param string $uid  UID of the user.
     * @param string $mail Search the group with this mail address.
     *
     * @return boolean|PEAR_Error True in case the user is in the
     *                            group, false otherwise.
     */
    function memberOfGroupAddress($uid, $mail)
    {
        /* No groups in the default class */
        return false;
    }

    /**
     * Identify the UID for the first object found with the given ID.
     *
     * @param string $id       Search for objects with this ID.
     * @param int    $restrict A KOLAB_SERVER_RESULT_* result restriction.
     *
     * @return mixed|PEAR_Error The UID or false if there was no result.
     */
    function uidForId($id,
                      $restrict = KOLAB_SERVER_RESULT_SINGLE)
    {
        return $this->uidForAttr(KOLAB_ATTR_SID, $id);
    }

    /**
     * Identify the UID for the first user found with the given mail.
     *
     * @param string $mail     Search for users with this mail address.
     * @param int    $restrict A KOLAB_SERVER_RESULT_* result restriction.
     *
     * @return mixed|PEAR_Error The UID or false if there was no result.
     */
    function uidForMail($mail,
                        $restrict = KOLAB_SERVER_RESULT_SINGLE)
    {
        return $this->uidForAttr('mail', $mail);
    }

    /**
     * Identify the GID for the first group found with the given mail.
     *
     * @param string $mail     Search for groups with this mail address.
     * @param int    $restrict A KOLAB_SERVER_RESULT_* result restriction.
     *
     * @return mixed|PEAR_Error The GID or false if there was no result.
     */
    function gidForMail($mail,
                        $restrict = KOLAB_SERVER_RESULT_SINGLE)
    {
        return $this->gidForAttr('mail', $mail);
    }

    /**
     * Identify the UID for the first object found with the given ID or mail.
     *
     * @param string $id Search for objects with this uid/mail.
     *
     * @return mixed|PEAR_Error The UID or false if there was no result.
     */
    function uidForIdOrMail($id)
    {
        $uid = $this->uidForAttr(KOLAB_ATTR_SID, $id);
        if (!$uid) {
            $uid = $this->uidForAttr('mail', $id);
        }
        return $uid;
    }

    /**
     * Identify the UID for the first object found with the given alias.
     *
     * @param string $mail     Search for objects with this mail alias.
     * @param int    $restrict A KOLAB_SERVER_RESULT_* result restriction.
     *
     * @return mixed|PEAR_Error The UID or false if there was no result.
     */
    function uidForAlias($mail,
                      $restrict = KOLAB_SERVER_RESULT_SINGLE)
    {
        return $this->uidForAttr('alias', $mail);
    }

    /**
     * Identify the UID for the first object found with the given mail
     * address or alias.
     *
     * @param string $mail Search for objects with this mail address
     * or alias.
     *
     * @return mixed|PEAR_Error The UID or false if there was no result.
     */
    function uidForMailOrAlias($mail)
    {
        $uid = $this->uidForAttr('alias', $mail);
        if (!$uid) {
            $uid = $this->uidForAttr('mail', $mail);
        }
        return $uid;
    }

    /**
     * Identify the UID for the first object found with the given ID,
     * mail or alias.
     *
     * @param string $id Search for objects with this ID/mail/alias.
     *
     * @return mixed|PEAR_Error The UID or false if there was no result.
     */
    function uidForMailOrIdOrAlias($id)
    {
        $uid = $this->uidForAttr(KOLAB_ATTR_SID, $id);
        if (!$uid) {
            $uid = $this->uidForAttr('mail', $id);
            if (!$uid) {
                $uid = $this->uidForAttr('alias', $id);
            }
        }
        return $uid;
    }

    /**
     * Generate a hash representation for a list of objects.
     *
     * @param string $type   The type of the objects to be listed
     * @param array  $params Additional parameters.
     *
     * @return array|PEAR_Error An array of Kolab objects.
     */
    function listHash($type, $params = null)
    {
        $list = $this->_listObjects($type, $params);
        if (is_a($list, 'PEAR_Error')) {
            return $list;
        }

        if (isset($params['attributes'])) {
            $attributes = $params['attributes'];
        } else {
            $attributes = null;
        }

        $hash = array();
        foreach ($list as $entry) {
            $hash[] = $entry->toHash($attributes);
        }

        return $hash;
    }

    /**
     * List all objects of a specific type
     *
     * @param string $type   The type of the objects to be listed
     * @param array  $params Additional parameters.
     *
     * @return array|PEAR_Error An array of Kolab objects.
     */
    function listObjects($type, $params = null)
    {
        if (!in_array($type, $this->valid_types)) {
            return PEAR::raiseError(sprintf(_("Invalid Kolab object type \"%s\"."),
                                            $type));
        }

        return $this->_listObjects($type, $params);
    }

    /**
     * List all objects of a specific type
     *
     * @param string $type   The type of the objects to be listed
     * @param array  $params Additional parameters.
     *
     * @return array|PEAR_Error An array of Kolab objects.
     */
    function _listObjects($type, $params = null)
    {
        return array();
    }

    /**
     * Generates a unique ID for the given information.
     *
     * @param string $type The type of the object to create.
     * @param array  $info Any additional information about the object to create.
     *
     * @return string|PEAR_Error The UID.
     */
    function generateUid($type, $info)
    {
        if (!class_exists($type)) {
            $result = Horde_Kolab_Server_Object::loadClass($type);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $id = call_user_func(array($type, 'generateId'), $info);
        if (is_a($id, 'PEAR_Error')) {
            return $id;
        }
        return $this->_generateUid($type, $id, $info);
    }

    /**
     * Generates a UID for the given information.
     *
     * @param string $type The type of the object to create.
     * @param string $id   The id of the object.
     * @param array  $info Any additional information about the object to create.
     *
     * @return string|PEAR_Error The UID.
     */
    function _generateUid($type, $id, $info)
    {
        return $id;
    }

}
