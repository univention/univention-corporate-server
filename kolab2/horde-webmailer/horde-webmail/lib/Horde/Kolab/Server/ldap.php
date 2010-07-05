<?php
/**
 * The driver for accessing the Kolab user database stored in LDAP.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Server/ldap.php,v 1.2.2.11 2009-04-25 08:56:34 wrobel Exp $
 *
 * PHP version 4
 *
 * @category Kolab
 * @package  Kolab_Server
 * @author   Gunnar Wrobel <wrobel@pardus.de>
 * @license  http://www.fsf.org/copyleft/lgpl.html LGPL
 * @link     http://pear.horde.org/index.php?package=Kolab_Server
 */

/** We need the Horde LDAP tools for this class **/
require_once 'Horde/LDAP.php';

/**
 * This class provides methods to deal with Kolab objects stored in
 * the standard Kolab LDAP db.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Server/ldap.php,v 1.2.2.11 2009-04-25 08:56:34 wrobel Exp $
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
class Horde_Kolab_Server_ldap extends Horde_Kolab_Server {

    /**
     * LDAP connection handle.
     *
     * @var resource
     */
    var $_connection;

    /**
     * Flag that indicates bound state for the LDAP connection.
     *
     * @var boolean
     */
    var $_bound;

    /**
     * The base dn .
     *
     * @var boolean
     */
    var $_base_dn;

    /**
     * Connects to the LDAP server.
     *
     * @param string $server  LDAP server URL.
     * @param string $base_dn LDAP server base DN.
     *
     * @return boolean|PEAR_Error True if the connection succeeded.
     */
    function _connect($server = null, $base_dn = null)
    {
        if (!function_exists('ldap_connect')) {
            return PEAR::raiseError(_("Cannot connect to the Kolab LDAP server. PHP does not support LDAP!"));
        }

        if (!$server) {
            if (isset($this->_params['server'])) {
                $server = $this->_params['server'];
            } else {
                return PEAR::raiseError(_("Horde_Kolab_Server_ldap needs a server parameter!"));
            }
        }
        if (!$base_dn) {
            if (isset($this->_params['base_dn'])) {
                $this->_base_dn = $this->_params['base_dn'];
            } else {
                return PEAR::raiseError(_("Horde_Kolab_Server_ldap needs a base_dn parameter!"));
            }
        } else {
            $this->_base_dn = $base_dn;
        }

        $this->_connection = @ldap_connect($server);
        if (!$this->_connection) {
            return PEAR::raiseError(sprintf(_("Error connecting to LDAP server %s!"),
                                            $server));
        }

        /* We need version 3 for Kolab */
        if (!ldap_set_option($this->_connection, LDAP_OPT_PROTOCOL_VERSION, 3)) {
            return PEAR::raiseError(sprintf(_("Error setting LDAP protocol on server %s to v3: %s"),
                                            $server,
                                            ldap_error($this->_connection)));
        }

        return true;
    }

    /**
     * Binds the LDAP connection with a specific user and pass.
     *
     * @param string $dn DN to bind with
     * @param string $pw Password associated to this DN.
     *
     * @return boolean|PEAR_Error  Whether or not the binding succeeded.
     */
    function _bind($dn = false, $pw = '')
    {
        if (!$this->_connection) {
            $result = $this->_connect();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        if (!$dn) {
            if (isset($this->_params['uid'])) {
                $dn = $this->_params['uid'];
            } else {
                $dn = '';
            }
        }
        if (!$pw) {
            if (isset($this->_params['pass'])) {
                $pw = $this->_params['pass'];
            }
        }

        $this->_bound = @ldap_bind($this->_connection, $dn, $pw);

        if (!$this->_bound) {
            return PEAR::raiseError(sprintf(_("Unable to bind to the LDAP server as %s!"),
                                            $dn));
        }
        return true;
    }

    /**
     * Disconnect from LDAP.
     *
     * @return NULL
     */
    function unbind()
    {
        $result = @ldap_unbind($this->_connection);
        if (!$result) {
            return PEAR::raiseError("Failed to unbind from the LDAP server!");
        }

        $this->_bound = false;
    }

    /**
     * Search for an object.
     *
     * @param string $filter     Filter criteria.
     * @param array  $attributes Restrict the search result to
     *                           these attributes.
     * @param string $base       The base location for searching.
     *
     * @return array|PEAR_Error A LDAP search result.
     */
    function _search($filter, $attributes = null, $base = null)
    {
        if (!$this->_bound) {
            $result = $this->_bind();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        if (empty($base)) {
            $base = $this->_base_dn;
        }

        if (isset($attributes)) {
            $result = @ldap_search($this->_connection, $base, $filter, $attributes);
        } else {
            $result = @ldap_search($this->_connection, $base, $filter);
        }
        if (!$result && $this->_errno()) {
            return PEAR::raiseError(sprintf(_("LDAP Error: Failed to search using filter %s. Error was: %s"),
                                            $filter, $this->_error()));
        }
        return $result;
    }

    /**
     * Read object data.
     *
     * @param string $dn    The object to retrieve.
     * @param string $attrs Restrict to these attributes.
     *
     * @return array|PEAR_Error An array of attributes.
     */
    function _read($dn, $attrs = null)
    {
        if (!$this->_bound) {
            $result = $this->_bind();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        if (isset($attrs)) {
            $this->mapKeys($attrs);
            $result = @ldap_read($this->_connection, $dn, '(objectclass=*)', $attrs);
        } else {
            $result = @ldap_read($this->_connection, $dn, '(objectclass=*)');
        }
        if (!$result && $this->_errno()) {
            return PEAR::raiseError(sprintf(_("LDAP Error: No such object: %s: %s"),
                                            $dn, $this->_error()));
        }
        $entry = $this->_firstEntry($result);
        if (!$entry) {
            @ldap_free_result($result);
            return PEAR::raiseError(sprintf(_("LDAP Error: Empty result for: %s."),
                                            $dn));
        }
        $object = $this->_getAttributes($entry);
        if (!$object  && $this->_errno()) {
            return PEAR::raiseError(sprintf(_("LDAP Error: No such dn: %s: %s"),
                                            $dn, $this->_error()));
        }
        @ldap_free_result($result);

        $this->unmapAttributes($object);

        return $object;
    }

    /**
     * Add a new object
     *
     * @param string $dn   The DN of the object to be added.
     * @param array  $data The attributes of the object to be added.
     *
     * @return boolean  True if adding succeeded.
     */
    function _add($dn, $data)
    {
        if (!$this->_bound) {
            $result = $this->_bind();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $this->mapAttributes($data);

        return @ldap_add($this->_connection, $dn, $data);
    }

    /**
     * Count the number of results.
     *
     * @param string $result The LDAP search result.
     *
     * @return int The number of records found.
     */
    function _count($result)
    {
        return @ldap_count_entries($this->_connection, $result);
    }

    /**
     * Return the dn of an entry.
     *
     * @param resource $entry The LDAP entry.
     *
     * @return string  The DN of the entry.
     */
    function _getDn($entry)
    {
        return @ldap_get_dn($this->_connection, $entry);
    }

    /**
     * Return the attributes of an entry.
     *
     * @param resource $entry The LDAP entry.
     *
     * @return array  The attributes of the entry.
     */
    function _getAttributes($entry)
    {
        return @ldap_get_attributes($this->_connection, $entry);
    }

    /**
     * Return the first entry of a result.
     *
     * @param resource $result The LDAP search result.
     *
     * @return resource  The first entry of the result.
     */
    function _firstEntry($result)
    {
        return @ldap_first_entry($this->_connection, $result);
    }

    /**
     * Return the next entry of a result.
     *
     * @param resource $entry The current LDAP entry.
     *
     * @return resource  The next entry of the result.
     */
    function _nextEntry($entry)
    {
        return @ldap_next_entry($this->_connection, $entry);
    }

    /**
     * Return the entries of a result.
     *
     * @param resource $result The LDAP search result.
     * @param int      $from   Only return results after this position.
     * @param int      $to     Only return results until this position.
     *
     * @return array  The entries of the result.
     */
    function _getEntries($result, $from = -1, $to = -1)
    {
        if ($from >= 0 || $to >= 0) {
            $result = array();

            $i = 0;
            for ($entry = $this->_firstEntry($result);
                 $entry != false;
                 $entry = $this->_nextEntry($entry)) {
                if (!$entry  && $this->_errno()) {
                    return false;
                }
                if ($i > $from && ($i <= $to || $to == -1)) {
                    $attributes = $this->_getAttributes($entry);
                    if (!$attributes  && $this->_errno()) {
                        return false;
                    }
                    $result[] = $attributes;
                }
                $i++;
            }
            return $result;
        }
        return @ldap_get_entries($this->_connection, $result);
    }

    /**
     * Sort the entries of a result.
     *
     * @param resource $result    The LDAP search result.
     * @param string   $attribute The attribute used for sorting.
     *
     * @return boolean  True if sorting succeeded.
     */
    function _sort($result, $attribute)
    {
        return @ldap_sort($this->_connection, $result, $attribute);
    }

    /**
     * Return the current LDAP error number.
     *
     * @return int  The current LDAP error number.
     */
    function _errno()
    {
        return @ldap_errno($this->_connection);
    }

    /**
     * Return the current LDAP error description.
     *
     * @return string  The current LDAP error description.
     */
    function _error()
    {
        return @ldap_error($this->_connection);
    }

    /*
     * ------------------------------------------------------------------
     * The functions defined below do not call ldap_* functions directly.
     * ------------------------------------------------------------------
     */

    /**
     * Return the root of the UID values on this server.
     *
     * @return string The base UID on this server (base DN on ldap).
     */
    function getBaseUid()
    {
        return $this->_base_dn;
    }

    /**
     * Return the DNs of a result.
     *
     * @param resource $result The LDAP search result.
     * @param int      $from   Only return results after this position.
     * @param int      $to     Only return results until this position.
     *
     * @return array  The DNs of the result.
     */
    function _getDns($result, $from = -1, $to = -1)
    {
        $dns   = array();
        $entry = $this->_firstEntry($result);

        $i = 0;
        for ($entry = $this->_firstEntry($result);
             $entry != false;
             $entry = $this->_nextEntry($entry)) {
            if ($i > $from && ($i <= $to || $to == -1)) {
                $dn = $this->_getDn($entry);
                if (!$dn  && $this->_errno()) {
                    return false;
                }
                $dns[] = $dn;
            }
            $i++;
        }
        if ($this->_errno()) {
            return false;
        }
        return $dns;
    }

    /**
     * Identify the DN of the first result entry.
     *
     * @param array $result   The LDAP search result.
     * @param int   $restrict A KOLAB_SERVER_RESULT_* result restriction.
     *
     * @return string|PEAR_Error The DN.
     */
    function _dnFromResult($result, $restrict = KOLAB_SERVER_RESULT_SINGLE)
    {
        switch ($restrict) {
        case KOLAB_SERVER_RESULT_STRICT:
            $count = $this->_count($result);
            if (!$count) {
                return false;
            } else if ($count > 1) {
                return PEAR::raiseError(sprintf(_("Found %s results when expecting only one!"),
                                                $count));
            }
        case KOLAB_SERVER_RESULT_SINGLE:
            $entry = $this->_firstEntry($result);
            if (!$entry  && $this->_errno()) {
                return PEAR::raiseError(sprintf(_("Search failed. Error was: %s"),
                                                $this->_error()));
            }
            if (!$entry) {
                return false;
            }
            $dn = $this->_getDn($entry);
            if (!$dn  && $this->_errno()) {
                return PEAR::raiseError(sprintf(_("Retrieving DN failed. Error was: %s"),
                                                $this->_error()));
            }
            return $dn;
        case KOLAB_SERVER_RESULT_MANY:
            $entries = $this->_getDns($result);
            if (!$entries  && $this->_errno()) {
                return PEAR::raiseError(sprintf(_("Search failed. Error was: %s"),
                                                $this->_error()));
            }
            if (!$entries) {
                return false;
            }
            return $entries;
        }
        return false;
    }

    /**
     * Get the attributes of the first result entry.
     *
     * @param array $result   The LDAP search result.
     * @param array $attrs    The attributes to retrieve.
     * @param int   $restrict A KOLAB_SERVER_RESULT_* result restriction.
     *
     * @return mixed|PEAR_Error The attributes or false if there were
     *                          no results.
     */
    function _attrsFromResult($result, $attrs,
                              $restrict = KOLAB_SERVER_RESULT_SINGLE)
    {
        $entries = array();

        switch ($restrict) {
        case KOLAB_SERVER_RESULT_STRICT:
            $count = $this->_count($result);
            if (!$count) {
                return false;
            } else if ($count > 1) {
                return PEAR::raiseError(sprintf(_("Found %s results when expecting only one!"),
                                                $count));
            }
        case KOLAB_SERVER_RESULT_SINGLE:
            $first = $this->_firstEntry($result);
            if (!$first  && $this->_errno()) {
                return PEAR::raiseError(sprintf(_("Search failed. Error was: %s"),
                                                $this->_error()));
            }
            if (!$first) {
                return false;
            }
            $entry = $this->_getAttributes($first);
            if (!$entry  && $this->_errno()) {
                return PEAR::raiseError(sprintf(_("Retrieving attributes failed. Error was: %s"),
                                                $this->_error()));
            }

            $result = array();
            foreach ($attrs as $attr) {
                if (isset($entry[$attr]) && $entry[$attr]['count'] > 0) {
                    unset($entry[$attr]['count']);
                    $result[$attr] = $entry[$attr];
                }
            }
            return $result;
        case KOLAB_SERVER_RESULT_MANY:
            $entries = $this->_getEntries($result);
            if (!$entries  && $this->_errno()) {
                return PEAR::raiseError(sprintf(_("Search failed. Error was: %s"),
                                                $this->_error()));
            }
            if (!$entries) {
                return false;
            }
            unset($entries['count']);
            $result = array();

            $i = 0;
            foreach ($entries as $entry) {
                $result[$i] = array();
                foreach ($attrs as $attr) {
                    if (isset($entry[$attr])) {
                        if ($entry[$attr]['count'] > 0) {
                            unset($entry[$attr]['count']);
                            $result[$i][$attr] = $entry[$attr];
                        }
                    }
                }
                $i++;
            }
            return $result;
        }
        return false;
    }

    /**
     * Determine the type of a Kolab object.
     *
     * @param string $dn The DN of the object to examine.
     *
     * @return int The corresponding Kolab object type.
     */
    function _determineType($dn)
    {
        $oc = $this->_getObjectClasses($dn);
        if (is_a($oc, 'PEAR_Error')) {
            return $oc;
        }

        // Not a user type?
        if (!in_array('kolabinetorgperson', $oc)) {
            // Is it a group?
            if (in_array('kolabgroupofnames', $oc)) {
                return KOLAB_OBJECT_GROUP;
            }
            // Is it a shared Folder?
            if (in_array('kolabsharedfolder', $oc)) {
                return KOLAB_OBJECT_SHAREDFOLDER;
            }
            return PEAR::raiseError(sprintf(_("Unkown Kolab object type for DN %s."),
                                            $dn));
        }

        $groups = $this->getGroups($dn);
        if (is_a($groups, 'PEAR_Error')) {
            return $groups;
        }
        if (!empty($groups)) {
            if (in_array('cn=admin,cn=internal,' . $this->_base_dn, $groups)) {
                return KOLAB_OBJECT_ADMINISTRATOR;
            }
            if (in_array('cn=maintainer,cn=internal,' . $this->_base_dn,
                         $groups)) {
                return KOLAB_OBJECT_MAINTAINER;
            }
            if (in_array('cn=domain-maintainer,cn=internal,' . $this->_base_dn,
                         $groups)) {
                return KOLAB_OBJECT_DOMAINMAINTAINER;
            }
        }

        if (strpos($dn, 'cn=external') !== false) {
            return KOLAB_OBJECT_ADDRESS;
        }

        return KOLAB_OBJECT_USER;
    }

    /**
     * Get the LDAP object classes for the given DN.
     *
     * @param string $dn DN of the object.
     *
     * @return array|PEAR_Error An array of object classes.
     */
    function _getObjectClasses($dn)
    {
        $object = $this->_read($dn, array('objectClass'));
        if (is_a($object, 'PEAR_Error')) {
            return $object;
        }
        if (!isset($object['objectClass'])) {
            return PEAR::raiseError('The result has no object classes!');
        }
        unset($object['count']);
        unset($object['objectClass']['count']);
        $result = array_map('strtolower', $object['objectClass']);
        return $result;
    }

    /**
     * Identify the DN for the first object found using a filter.
     *
     * @param string $filter   The LDAP filter to use.
     * @param int    $restrict A KOLAB_SERVER_RESULT_* result restriction.
     *
     * @return mixed|PEAR_Error The DN or false if there was no result.
     */
    function _dnForFilter($filter,
                          $restrict = KOLAB_SERVER_RESULT_SINGLE)
    {
        $result = $this->_search($filter, array());
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        if (!$this->_count($result)) {
            return false;
        }
        return $this->_dnFromResult($result, $restrict);
    }

    /**
     * Identify attributes for the first object found using a filter.
     *
     * @param string $filter   The LDAP filter to use.
     * @param array  $attrs    The attributes to retrieve.
     * @param int    $restrict A KOLAB_SERVER_RESULT_* result restriction.
     *
     * @return mixed|PEAR_Error The DN or false if there was no result.
     */
    function _attrsForFilter($filter, $attrs,
                             $restrict = KOLAB_SERVER_RESULT_SINGLE)
    {
        $result = $this->_search($filter, $attrs);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        return $this->_attrsFromResult($result, $attrs, $restrict);
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
        $criteria = array('AND' =>
                         array(
                             array('field' => KOLAB_ATTR_OC,
                                   'op'    => '=',
                                   'test'  => KOLAB_OC_KOLABINETORGPERSON),
                             array('OR' =>
                                   array(
                                       array('field' => KOLAB_ATTR_SID,
                                             'op'    => '=',
                                             'test'  => $id),
                                       array('field' => KOLAB_ATTR_MAIL,
                                             'op'    => '=',
                                             'test'  => $id),
                                   ),
                             ),
                         ),
        );
        $filter   = $this->searchQuery($criteria);

        $result = $this->_attrsForFilter($filter, array('mail'),
                                         KOLAB_SERVER_RESULT_STRICT);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        return $result['mail'][0];
    }

    /**
     * Identify the UID for the first object found with the given ID
     * or mail.
     *
     * @param string $id Search for objects with this ID/mail.
     *
     * @return mixed|PEAR_Error The UID or false if there was no result.
     */
    function uidForIdOrMail($id)
    {
        $criteria = array('AND' =>
                         array(
                             array('field' => KOLAB_ATTR_OC,
                                   'op'    => '=',
                                   'test'  => KOLAB_OC_KOLABINETORGPERSON),
                             array('OR' =>
                                   array(
                                       array('field' => KOLAB_ATTR_SID,
                                             'op'    => '=',
                                             'test'  => $id),
                                       array('field' => KOLAB_ATTR_MAIL,
                                             'op'    => '=',
                                             'test'  => $id),
                                   ),
                             ),
                         ),
        );
        $filter   = $this->searchQuery($criteria);
        return $this->_dnForFilter($filter, KOLAB_SERVER_RESULT_STRICT);
    }

    /**
     * Returns a list of allowed email addresses for the given user.
     *
     * @param string $id The users primary mail address or ID.
     *
     * @return array|PEAR_Error An array of allowed mail addresses
     */
    function addrsForIdOrMail($id)
    {
        $criteria = array('AND' =>
                         array(
                             array('field' => KOLAB_ATTR_OC,
                                   'op'    => '=',
                                   'test'  => KOLAB_OC_KOLABINETORGPERSON),
                             array('OR' =>
                                   array(
                                       array('field' => KOLAB_ATTR_SID,
                                             'op'    => '=',
                                             'test'  => $id),
                                       array('field' => KOLAB_ATTR_MAIL,
                                             'op'    => '=',
                                             'test'  => $id),
                                   ),
                             ),
                         ),
        );
        $filter   = $this->searchQuery($criteria);

        $result = $this->_attrsForFilter($filter, array('mail', 'alias'),
                                         KOLAB_SERVER_RESULT_STRICT);
        if (empty($result)) {
            return array();
        }
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        if (isset($result['alias'])) {
            $addrs = array_merge((array) $result['mail'], (array) $result['alias']);
        } else {
            $addrs = $result['mail'];
        }
        $mail  = $result['mail'][0];

        $filter = '(&(objectClass=kolabInetOrgPerson)(kolabDelegate='
            . Horde_LDAP::quote($mail) . '))';
        $result = $this->_attrsForFilter($filter, array('mail', 'alias'),
                                         KOLAB_SERVER_RESULT_MANY);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (!empty($result)) {
            foreach ($result as $adr) {
                if (isset($adr['mail'])) {
                    $addrs = array_merge((array) $addrs, (array) $adr['mail']);
                }
                if (isset($adr['alias'])) {
                    $addrs = array_merge((array) $addrs, (array) $adr['alias']);
                }
            }
        }

        $addrs = array_map('strtolower', $addrs);

        return $addrs;
    }

    /**
     * Return the UID for a given primary mail, ID, or alias.
     *
     * @param string $mail A valid mail address for the user.
     *
     * @return mixed|PEAR_Error The UID or false if there was no result.
     */
    function uidForMailAddress($mail)
    {
        $criteria = array('AND' =>
                         array(
                             array('field' => KOLAB_ATTR_OC,
                                   'op'    => '=',
                                   'test'  => KOLAB_OC_KOLABINETORGPERSON),
                             array('OR' =>
                                   array(
                                       array('field' => KOLAB_ATTR_ALIAS,
                                             'op'    => '=',
                                             'test'  => $mail),
                                       array('field' => KOLAB_ATTR_MAIL,
                                             'op'    => '=',
                                             'test'  => $mail),
                                       array('field' => KOLAB_ATTR_SID,
                                             'op'    => '=',
                                             'test'  => $mail),
                                   ),
                             ),
                         ),
        );
        $filter   = $this->searchQuery($criteria);
        return $this->_dnForFilter($filter);
    }

    /**
     * Identify the UID for the first object found using a specified
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
        $criteria = array('AND' =>
                         array(
                             array('field' => KOLAB_ATTR_OC,
                                   'op'    => '=',
                                   'test'  => KOLAB_OC_KOLABINETORGPERSON),
			     array('field' => $attr,
				   'op'    => '=',
				   'test'  => $value),
                             ),
        );
        $filter   = $this->searchQuery($criteria);
        return $this->_dnForFilter($filter, $restrict);
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
        $criteria = array('AND' =>
                         array(
                             array('field' => KOLAB_ATTR_OC,
                                   'op'    => '=',
                                   'test'  => KOLAB_OC_KOLABGROUPOFNAMES),
			     array('field' => $attr,
				   'op'    => '=',
				   'test'  => $value),
                             ),
        );
        $filter   = $this->searchQuery($criteria);
        return $this->_dnForFilter($filter, $restrict);
    }

    /**
     * Is the given UID member of the group with the given mail address?
     *
     * @param string $uid  UID of the user.
     * @param string $mail Search the group with this mail address.
     *
     * @return boolen|PEAR_Error True in case the user is in the
     *                           group, false otherwise.
     */
    function memberOfGroupAddress($uid, $mail)
    {
        $filter = '(&(objectClass=kolabGroupOfNames)(mail='
            . Horde_LDAP::quote($mail) . ')(member='
            . Horde_LDAP::quote($uid) . '))';
        $result = $this->_dnForFilter($filter, KOLAB_SERVER_RESULT_STRICT);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        if (empty($result)) {
            return false;
        }
        return true;
    }

    /**
     * Get the groups for this object.
     *
     * @param string $uid The UID of the object to fetch.
     *
     * @return array|PEAR_Error An array of group ids.
     */
    function getGroups($uid)
    {
        $filter = '(&(objectClass=kolabGroupOfNames)(member='
            . Horde_LDAP::quote($uid) . '))';
        $result = $this->_dnForFilter($filter, KOLAB_SERVER_RESULT_MANY);
        if (empty($result)) {
            return array();
        }
        return $result;
    }

    /**
     * Get the mail addresses for the group of this object.
     *
     * @param string $uid The UID of the object to fetch.
     *
     * @return array|PEAR_Error An array of group ids.
     *
     * @since 0.5.0
     */
    function getGroupAddresses($uid)
    {
        $filter = '(&(objectClass=kolabGroupOfNames)(member='
            . Horde_LDAP::quote($uid) . '))';
        $result = $this->_attrsForFilter($filter, array(KOLAB_ATTR_MAIL),
                                         KOLAB_SERVER_RESULT_MANY);
        if (empty($result)) {
            return array();
        }
        $mails = array();
        foreach ($result as $element) {
            if (isset($element[KOLAB_ATTR_MAIL])) {
                if (is_array($element[KOLAB_ATTR_MAIL])) {
                    $mails = array_merge($mails, $element[KOLAB_ATTR_MAIL]);
                } else {
                    $mails[] = $element[KOLAB_ATTR_MAIL];
                }
            }
        }
        return $mails;
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
        if (empty($params['base_dn'])) {
            $base = $this->_base_dn;
        } else {
            $base = $params['base_dn'];
        }

        $result = Horde_Kolab_Server_Object::loadClass($type);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        $vars   = get_class_vars($type);
        $methods = get_class_methods($type);
        if (!in_array('getFilter', $methods)) {
            $filter = $vars['filter'];
        } else {
            $criteria = call_user_func(array($type, 'getFilter'));
            $filter   = $this->searchQuery($criteria);
        }
        $sort   = $vars['sort_by'];

        if (isset($params['sort'])) {
            $sort = $params['sort'];
        }

        $result = $this->_search($filter, null, $base);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        if (empty($result)) {
            return array();
        }

        if ($sort) {
            $this->_sort($result, $sort);
        }

        if (isset($params['from'])) {
            $from = $params['from'];
        } else {
            $from = -1;
        }

        if (isset($params['to'])) {
            $sort = $params['to'];
        } else {
            $to = -1;
        }

        $entries = $this->_getDns($result, $from, $to);
        if (!$entries  && $this->_errno()) {
            return PEAR::raiseError(sprintf(_("Search failed. Error was: %s"),
                                            $this->_error()));
        }
        if (!$entries) {
            return false;
        }

        if (!empty($vars['required_group'])) {
            $required_group = $this->fetch($vars['required_group'],
                                           KOLAB_OBJECT_GROUP);
        }

        $objects = array();
        foreach ($entries as $dn) {
            if (!empty($vars['required_group']) && $required_group->isMember($dn)) {
                continue;
            }
            $result = $this->fetch($dn, $type);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
            $objects[] = $result;
        }
        return $objects;
    }

    /**
     * Generates a UID for the given information.
     *
     * @param string $type The type of the object to create.
     * @param string $id   The id of the object.
     * @param array  $info Any additional information about the object to create.
     *
     * @return string|PEAR_Error The DN.
     */
    function _generateUid($type, $id, $info)
    {
        switch ($type) {
        case KOLAB_OBJECT_USER:
            if (!isset($info['user_type']) || $info['user_type'] == 0) {
                return sprintf('cn=%s,%s', $id, $this->_base_dn);
            } else if ($info['user_type'] == KOLAB_UT_INTERNAL) {
                return sprintf('cn=%s,cn=internal,%s', $id, $this->_base_dn);
            } else if ($info['user_type'] == KOLAB_UT_GROUP) {
                return sprintf('cn=%s,cn=groups,%s', $id, $this->_base_dn);
            } else if ($info['user_type'] == KOLAB_UT_RESOURCE) {
                return sprintf('cn=%s,cn=resources,%s', $id, $this->_base_dn);
            } else {
                return sprintf('cn=%s,%s', $id, $this->_base_dn);
            }
        case KOLAB_OBJECT_ADDRESS:
            return sprintf('cn=%s,cn=external,%s', $id, $this->_base_dn);
        case KOLAB_OBJECT_SHAREDFOLDER:
        case KOLAB_OBJECT_ADMINISTRATOR:
        case KOLAB_OBJECT_MAINTAINER:
        case KOLAB_OBJECT_DOMAINMAINTAINER:
            return sprintf('cn=%s,%s', $id, $this->_base_dn);
        case KOLAB_OBJECT_GROUP:
        case KOLAB_OBJECT_DISTLIST:
            if (!isset($info['visible']) || !empty($info['visible'])) {
                return sprintf('cn=%s,%s', $id, $this->_base_dn);
            } else {
                return sprintf('cn=%s,cn=internal,%s', $id, $this->_base_dn);
            }
        default:
            return PEAR::raiseError(_("Not implemented!"));
        }
    }

    /**
     * Save an object.
     *
     * @param string $dn   The DN of the object.
     * @param array  $data The data for the object.
     *
     * @return boolean|PEAR_Error True if successfull.
     */
    function save($dn, $data)
    {
        $result = $this->_add($dn, $data);
        if (!$result  && $this->_errno()) {
            return PEAR::raiseError(sprintf(_("Failed saving object. Error was: %s"),
                                            $this->_error()));
        }
    }

    /**
     * Build a search query.
     *
     * Taken from the Turba LDAP driver.
     *
     * @param array $criteria The array of criteria.
     *
     * @return string  An LDAP query filter.
     */
    public function searchQuery($criteria)
    {
        require_once 'Net/LDAP2.php';

        /* Accept everything. */
        $filter = '(' . strtolower(KOLAB_ATTR_OC) . '=*)';

        /* Build the LDAP filter. */
        if (count($criteria)) {
            $f = $this->buildSearchQuery($criteria);
            if (is_a($f, 'Net_LDAP2_Filter')) {
                $filter = $f->asString();
            }
        }
        return $filter;
    }

    /**
     * Build a piece of a search query.
     *
     * Taken from the Turba LDAP driver.
     *
     * @param array $criteria The array of criteria.
     *
     * @return string  An LDAP query fragment.
     */
    protected function &buildSearchQuery($criteria)
    {
        if (isset($criteria['field'])) {
            require_once 'Horde/String.php';
            require_once 'Horde/NLS.php';
            $rhs     = $criteria['test'];
            /* Keep this in for reference as we did not really test servers with different encoding yet */
            //$rhs     = String::convertCharset($criteria['test'], NLS::getCharset(), $this->params['charset']);
            switch ($criteria['op']) {
            case '=':
                $op = 'equals';
                break;
            }
            return Net_LDAP2_Filter::create($this->mapField($criteria['field']),
                                            $op, $rhs);
        }
        foreach ($criteria as $key => $vals) {
            if (!empty($vals['OR'])
                || !empty($vals['AND'])
                || !empty($vals['NOT'])) {
                $parts = $this->buildSearchQuery($vals);
                if (count($parts) > 1) {
                    if (!empty($vals['OR'])) {
                        $operator = '|';
                    } else if (!empty($vals['NOT'])) {
                        $operator = '!';
                    } else {
                        $operator = '&';
                    }
                    return Net_LDAP2_Filter::combine($operator, $parts);
                } else {
                    return $parts[0];
                }
            } else {
                $parts = array();
                foreach ($vals as $test) {
                    $parts[] = &$this->buildSearchQuery($test);
                }
                switch ($key) {
                case 'OR':
                    $operator = '|';
                    break;
                case 'AND':
                    $operator = '&';
                    break;
                case 'NOT':
                    $operator = '!';
                    break;
                }
                if (count($parts) > 1) {
                    return Net_LDAP2_Filter::combine($operator, $parts);
                } else if ($operator == '!') {
                    return Net_LDAP2_Filter::combine($operator, $parts[0]);
                } else {
                    return $parts[0];
                }
            }
        }
    }

    /**
     * Map attributes defined within this library their their real world
     * counterparts.
     *
     * @param array $data The data that has been read and needs to be mapped.
     *
     * @return NULL
     */
    protected function unmapAttributes(&$data)
    {
        if (!empty($this->_params['map'])) {
            foreach ($this->_params['map'] as $attribute => $map) {
                if (isset($data[$map])) {
                    $data[$attribute] = $data[$map];
                    unset($data[$map]);
                }
            }
        }
    }

    /**
     * Map attributes defined within this library into their real world
     * counterparts.
     *
     * @param array $data The data to be written.
     *
     * @return NULL
     */
    protected function mapAttributes(&$data)
    {
        if (!empty($this->_params['map'])) {
            foreach ($this->_params['map'] as $attribute => $map) {
                if (isset($data[$attribute])) {
                    $data[$map] = $data[$attribute];
                    unset($data[$attribute]);
                }
            }
        }
    }

    /**
     * Map attribute keys defined within this library into their real world
     * counterparts.
     *
     * @param array $keys The attribute keys.
     *
     * @return NULL
     */
    protected function mapKeys(&$keys)
    {
        if (!empty($this->_params['map'])) {
            foreach ($this->_params['map'] as $attribute => $map) {
                $key = array_search($attribute, $keys);
                if ($key !== false) {
                    $keys[$key] = $map;
                }
            }
        }
    }

    /**
     * Map a single attribute key defined within this library into its real
     * world counterpart.
     *
     * @param array $field The attribute name.
     *
     * @return The real name of this attribute on the server we connect to.
     */
    protected function mapField($field)
    {
        if (!empty($this->_params['map'])
            && isset($this->_params['map'][$field])) {
            return $this->_params['map'][$field];
        }
        return $field;
    }

}
