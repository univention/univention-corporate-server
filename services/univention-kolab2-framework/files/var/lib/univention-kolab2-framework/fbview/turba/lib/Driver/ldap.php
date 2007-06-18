<?php
/**
 * Turba directory driver implementation for PHP's LDAP extension.
 *
 * $Horde: turba/lib/Driver/ldap.php,v 1.49 2004/04/07 14:43:52 chuck Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jon Parise <jon@csh.rit.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Turba 0.0.1
 * @package Turba
 */
class Turba_Driver_ldap extends Turba_Driver {

    /** Handle for the current LDAP connection. */
    var $_ds = 0;

    /**
     * Constructs a new Turba LDAP driver object.
     *
     * @param $params       Hash containing additional configuration parameters.
     */
    function Turba_Driver_ldap($params)
    {
        if (!extension_loaded('ldap')) {
            Horde::fatal(PEAR::raiseError(_("LDAP support is required but the LDAP module is not available or not loaded.")), __FILE__, __LINE__);
        }

        if (empty($params['server'])) {
            $params['server'] = 'localhost';
        }
        if (empty($params['port'])) {
            $params['port'] = 389;
        }
        if (empty($params['root'])) {
            $params['root'] = '';
        }
        if (empty($params['multiple_entry_separator'])) {
            $params['multiple_entry_separator'] = ', ';
        }
        if (empty($params['charset'])) {
            $params['charset'] = '';
        }

        parent::Turba_Driver($params);
    }

    function init()
    {
        if (!($this->_ds = @ldap_connect($this->_params['server'], $this->_params['port']))) {
            return PEAR::raiseError(_("Connection failure"));
        }

        // Set the LDAP protocol version.
        if (!empty($this->_params['version'])) {
            @ldap_set_option($this->_ds, LDAP_OPT_PROTOCOL_VERSION, $this->_params['version']);
        }

        if (isset($this->_params['bind_dn']) &&
            isset($this->_params['bind_password'])) {
            if (!@ldap_bind($this->_ds, $this->_params['bind_dn'], $this->_params['bind_password'])) {
                return PEAR::raiseError(sprintf(_("Bind failed: (%s) %s"), ldap_errno($this->_ds), ldap_error($this->_ds)));
            }
        } else if (!(@ldap_bind($this->_ds))) {
            return PEAR::raiseError(sprintf(_("Bind failed: (%s) %s"), ldap_errno($this->_ds), ldap_error($this->_ds)));
        }
    }

    /**
     * Searches the LDAP directory with the given criteria and returns
     * a filtered list of results. If no criteria are specified, all
     * records are returned.
     *
     * @param $criteria      Array containing the search criteria.
     * @param $fields        List of fields to return.
     *
     * @return array  Hash containing the search results.
     */
    function search($criteria, $fields)
    {
        /* Build the LDAP filter. */
        $filter = '';
        if (count($criteria)) {
            foreach ($criteria as $key => $vals) {
                if ($key == 'OR') {
                    $filter .= '(|' . $this->_buildSearchQuery($vals) . ')';
                } elseif ($key == 'AND') {
                    $filter .= '(&' . $this->_buildSearchQuery($vals) . ')';
                }
            }
        } else {
            // Filter on objectclass.
            $filter = $this->_buildObjectclassFilter();
        }

        /* Add source-wide filters, which are _always_ AND-ed. */
        if (!empty($this->_params['filter'])) {
            $filter = '(&' . '(' . $this->_params['filter'] . ')' . $filter . ')';
        }

        /* Four11 (at least) doesn't seem to return 'cn' if you don't
         * ask for 'sn' as well. Add 'sn' implicitly. */
        $attr = $fields;
        if (!in_array('sn', $attr)) {
            $attr[] = 'sn';
        }

        /* Add a sizelimit, if specified. Default is 0, which means no
         * limit.  Note: You cannot override a server-side limit with
         * this. */
        $sizelimit = 0;
        if (!empty($this->_params['sizelimit'])) {
            $sizelimit = $this->_params['sizelimit'];
        }

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('LDAP search by %s: root = %s (%s); filter = "%s"; attributes = "%s"; sizelimit = %d',
                                  Auth::getAuth(), $this->_params['root'], $this->_params['server'], $filter, implode(', ', $attr), $sizelimit),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Send the query to the LDAP server and fetch the matching
         * entries. */
        if (!($res = @ldap_search($this->_ds, $this->_params['root'], $filter, $attr, 0, $sizelimit))) {
            return PEAR::raiseError(sprintf(_("Query failed: (%s) %s"), ldap_errno($this->_ds), ldap_error($this->_ds)));
        }

        return $this->getResults($fields, $res);
    }

    /**
     * Build a piece of a search query.
     *
     * @param array  $criteria  The array of criteria.
     *
     * @return string  An LDAP query fragment.
     */
    function _buildSearchQuery($criteria)
    {
        require_once 'Horde/LDAP.php';

        $clause = '';
        foreach ($criteria as $key => $vals) {
            if (!empty($vals['OR'])) {
                $clause .= '(|' . $this->_buildSearchQuery($vals) . ')';
            } elseif (!empty($vals['AND'])) {
                $clause .= '(&' . $this->_buildSearchQuery($vals) . ')';
            } else {
                if (isset($vals['field'])) {
                    $rhs = String::convertCharset($vals['test'], NLS::getCharset(), $this->_params['charset']);
                    $clause .= Horde_LDAP::buildClause($vals['field'], $vals['op'], $rhs);
                } else {
                    foreach ($vals as $test) {
                        if (!empty($test['OR'])) {
                            $clause .= '(|' . $this->_buildSearchQuery($test) . ')';
                        } elseif (!empty($test['AND'])) {
                            $clause .= '(&' . $this->_buildSearchQuery($test) . ')';
                        } else {
                            $rhs = String::convertCharset($test['test'], NLS::getCharset(), $this->_params['charset']);
                            $clause .= Horde_LDAP::buildClause($test['field'], $test['op'], $rhs);
                        }
                    }
                }
            }
        }

        return $clause;
    }

    /**
     * Reads the LDAP directory for a given element and returns
     * the result's fields.
     *
     * @param string $criteria  Search criteria (must be 'dn').
     * @param mixed  $dn        The dn of the object to read.
     * @param array  $fields    List of fields to return.
     *
     * @return array  Hash containing the search results.
     */
    function read($criteria, $dn, $fields)
    {
        // Only DN
        if ($criteria != 'dn') {
            return array();
        }

        $filter = $this->_buildObjectclassFilter();

        /* Four11 (at least) doesn't seem to return 'cn' if you don't
         * ask for 'sn' as well. Add 'sn' implicitly. */
        $attr = $fields;
        if (!in_array('sn', $attr)) {
            $attr[] = 'sn';
        }

        // Handle a request for multiple records.
        if (is_array($dn)) {
            $results = array();
            foreach ($dn as $d) {
                $res = @ldap_read($this->_ds, $d, $filter, $attr);
                if ($res) {
                    if (!is_a($result = $this->getResults($fields, $res), 'PEAR_Error')) {
                        $results += $result;
                    } else {
                        return $result;
                    }
                } else {
                    return PEAR::raiseError(sprintf(_("Read failed: (%s) %s"), ldap_errno($this->_ds), ldap_error($this->_ds)));
                }
            }
            return $results;
        }

        $res = @ldap_read($this->_ds, $dn, $filter, $attr);
        if (!$res) {
            return PEAR::raiseError(sprintf(_("Read failed: (%s) %s"), ldap_errno($this->_ds), ldap_error($this->_ds)));
        }

        return $this->getResults($fields, $res);
    }

    /**
     * Get some results from a result identifier and clean them up.
     *
     * @param array    $fields  List of fields to return.
     * @param resource $res     Result identifier.
     *
     * @return array  Hash containing the results.
     */
    function getResults($fields, $res)
    {
        if (!($entries = @ldap_get_entries($this->_ds, $res))) {
            return PEAR::raiseError(sprintf(_("Read failed: (%s) %s"), ldap_errno($this->_ds), ldap_error($this->_ds)));
        }

        /* Return only the requested fields (from $fields, above). */
        $results = array();
        for ($i = 0; $i < $entries['count']; $i++) {
            $entry = $entries[$i];
            $result = array();

            foreach ($fields as $field) {
                $field_l = String::lower($field);
                if ($field == 'dn') {
                    $result[$field] = $entry[$field_l];
                } else {
                    $result[$field] = '';
                    if (!empty($entry[$field_l])) {
                        for ($j = 0; $j < $entry[$field_l]['count']; $j++) {
                            if (!empty($result[$field])) {
                                $result[$field] .= $this->_params['multiple_entry_separator'];
                            }
                            $result[$field] .= String::convertCharset($entry[$field_l][$j], $this->_params['charset']);
                        }
                    }
                }
            }

            $results[] = $result;
        }

        return $results;
    }

    /**
     * Adds the specified entry to the LDAP directory.
     *
     * @param array $attributes  The initial attributes for the new object.
     */
    function addObject($attributes)
    {
        if (empty($attributes['dn'])) {
            return PEAR::raiseError('Tried to add an object with no dn: [' . serialize($attributes) . '].');
        } elseif (empty($this->_params['objectclass'])) {
            return PEAR::raiseError('Tried to add an object with no objectclass: [' . serialize($attributes) . '].');
        }

        // Take the DN out of the attributes array
        $dn = $attributes['dn'];
        unset($attributes['dn']);

        // Put the Objectclass into the attributes array
        if (!is_array($this->_params['objectclass'])) {
            $attributes['objectclass'] = $this->_params['objectclass'];
        } else {
            $i = 0;
            foreach ($this->_params['objectclass'] as $objectclass) {
                $attributes['objectclass'][$i] = $objectclass;
                $i++;
            }
        }

        // Don't add empty attributes.
        $attributes = array_filter($attributes, array($this, '_emptyAttributeFilter'));

        // Encode entries.
        foreach ($attributes as $key => $val) {
            if (!is_array($val)) {
                $attributes[$key] = String::convertCharset($val, NLS::getCharset(), $this->_params['charset']);
            }
        }

        if (!@ldap_add($this->_ds, $dn, $attributes)) {
            return PEAR::raiseError('Failed to add an object: [' . ldap_errno($this->_ds) . '] "' . ldap_error($this->_ds) . '" (attributes: [' . serialize($attributes) . ']).' . "Charset:" . NLS::getCharset());
        } else {
            return true;
        }
    }

    /**
     * Deletes the specified entry from the LDAP directory.
     */
    function removeObject($object_key, $object_id)
    {
        if ($object_key != 'dn') {
            return PEAR::raiseError(_("Invalid key specified."));
        }

        if (!@ldap_delete($this->_ds, $object_id)) {
            return PEAR::raiseError(sprintf(_("Delete failed: (%s) %s"), ldap_errno($this->_ds), ldap_error($this->_ds)));
        } else {
            return true;
        }
    }

    /**
     * Modifies the specified entry in the LDAP directory.
     *
     * @return string  The object id, possibly updated.
     */
    function setObject($object_key, $object_id, $attributes)
    {
        // Get the old entry so that we can access the old
        // values. These are needed so that we can delete any
        // attributes that have been removed by using ldap_mod_del.
        $filter = $this->_buildObjectclassFilter();
        $oldres = @ldap_read($this->_ds, $object_id, $filter, array_keys($attributes));
        $info = ldap_get_attributes($this->_ds, ldap_first_entry($this->_ds, $oldres));

        // Check if we need to rename the object.
        if ($this->_params['version'] == 3 && $this->makeKey($attributes) != $object_id) {
            if (isset($this->_params['dn']) && is_array($this->_params['dn']) && count($this->_params['dn'])) {
                $newrdn = '';
                foreach ($this->_params['dn'] as $param) {
                    if (isset($attributes[$param])) {
                        $newrdn .= $param . '=' . $attributes[$param] . ',';
                    }
                }
                $newrdn = substr($newrdn, 0, -1);
            } else {
                return PEAR::raiseError(_("Missing DN in LDAP source configuration."));
            }

            if (ldap_rename($this->_ds, $object_id, $newrdn, $this->_params['root'], true)) {
                $object_id = $newrdn . ',' . $this->_params['root'];
            } else {
                return PEAR::raiseError( sprintf(_("Failed to change name: (%s) %s, %s"), ldap_errno($this->_ds), ldap_error($this->_ds), "$object_id,$newrdn,{$this->_params['root']}"));
            }
        }

        // The attributes in the attributes array are all lower case
        // while they are mixedCase in the search result. So convert
        // the keys to lower.
        $info = array_change_key_case($info, CASE_LOWER);

        foreach ($info as $key => $value) {
            $var = $info[$key];
            $oldval = null;

            // Check to see if the old value and the new value are
            // different and that the new value is empty. If so then
            // we use ldap_mod_del to delete the attribute.
            if (isset($attributes[$key]) &&
                ($var[0] != $attributes[$key]) &&
                $attributes[$key] == '') {

                $oldval[$key] = $var[0];
                if (!@ldap_mod_del($this->_ds, $object_id, $oldval)) {
                    return PEAR::raiseError(sprintf(_("Modify failed: (%s) %s"), ldap_errno($this->_ds), ldap_error($this->_ds)));
                }
                unset($attributes[$key]);
            }
        }

        // Encode entries.
        foreach ($attributes as $key => $val) {
            if (!is_array($val)) {
                $attributes[$key] = String::convertCharset($val, NLS::getCharset(), $this->_params['charset']);
            }
        }

        unset($attributes[$object_key]);
        $attributes = array_filter($attributes, array($this, '_emptyAttributeFilter'));

        if (!@ldap_modify($this->_ds, $object_id, $attributes)) {
            return PEAR::raiseError(sprintf(_("Modify failed: (%s) %s"), ldap_errno($this->_ds), ldap_error($this->_ds)));
        } else {
            return $object_id;
        }
    }

    /**
     * Build a DN based on a set of attributes and what attributes
     * make a DN for the current source.
     *
     * @param array $attributes The attributes (in driver keys) of the
     *                          object being added.
     *
     * @return string  The DN for the new object.
     */
    function makeKey($attributes)
    {
        $dn = '';
        if (is_array($this->_params['dn'])) {
            foreach ($this->_params['dn'] as $param) {
                if (isset($attributes[$param])) {
                    $dn .= $param . '=' . $attributes[$param] . ',';
                }
            }
        }

        $dn .= $this->_params['root'];
        return $dn;
    }

    /**
     * Remove empty attributes from attributes array
     *
     * @param mixed $val    Value from attributes array.
     * @return bool         Boolean used by array_filter.
     */
    function _emptyAttributeFilter($var)
    {
        if (!is_array($var)) {
            return ($var != '');
        } else {
            foreach ($var as $v) {
                if ($v == '') {
                    return false;
                }
            }
            return true;
        }
    }

    /**
     * Build an LDAP filter based on the objectclass parameter.
     *
     * @return string An LDAP filter.
     */
    function _buildObjectclassFilter()
    {
        $filter = '';
        if (!empty($this->_params['objectclass'])) {
            if (!is_array($this->_params['objectclass'])) {
                $filter = '(objectclass=' . $this->_params['objectclass'] . ')';
            } else {
                $filter = '(|';
                foreach ($this->_params['objectclass'] as $objectclass) {
                    $filter .= '(objectclass=' . $objectclass . ')';
                }
                $filter .= ')';
            }
        }
        return $filter;
    }

}
