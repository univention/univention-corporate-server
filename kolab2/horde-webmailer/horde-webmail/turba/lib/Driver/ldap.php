<?php
/**
 * Turba directory driver implementation for PHP's LDAP extension.
 *
 * $Horde: turba/lib/Driver/ldap.php,v 1.54.4.24 2009-10-07 16:16:38 mrubinsk Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jon Parise <jon@csh.rit.edu>
 * @package Turba
 */
class Turba_Driver_ldap extends Turba_Driver {

    /**
     * Handle for the current LDAP connection.
     *
     * @var resource
     */
    var $_ds = 0;

    /**
     * Cache _getSyntax calls to avoid lots of repeated server calls.
     *
     * @var array
     */
    var $_syntaxCache = array();

    /**
     * Constructs a new Turba LDAP driver object.
     *
     * @access private
     *
     * @param $params  Hash containing additional configuration parameters.
     */
    function Turba_Driver_ldap($params)
    {
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
        if (empty($params['scope'])) {
            $params['scope'] = 'sub';
        }
        if (empty($params['deref'])) {
            $params['deref'] = LDAP_DEREF_NEVER;
        }

        parent::Turba_Driver($params);
    }

    function _init()
    {
        if (!Util::extensionExists('ldap')) {
            return PEAR::raiseError(_("LDAP support is required but the LDAP module is not available or not loaded."));
        }

        if (!($this->_ds = @ldap_connect($this->_params['server'], $this->_params['port']))) {
            return PEAR::raiseError(_("Connection failure"));
        }

        /* Set the LDAP protocol version. */
        if (!empty($this->_params['version'])) {
            @ldap_set_option($this->_ds, LDAP_OPT_PROTOCOL_VERSION, $this->_params['version']);
        }

        /* Set the LDAP deref option for dereferencing aliases. */
        if (!empty($this->_params['deref'])) {
            @ldap_set_option($this->_ds, LDAP_OPT_DEREF, $this->_params['deref']);
        }

        /* Set the LDAP referrals. */
        if (!empty($this->_params['referrals'])) {
            @ldap_set_option($this->_ds, LDAP_OPT_REFERRALS, $this->_params['referrals']);
        }

        /* Start TLS if we're using it. */
        if (!empty($this->_params['tls'])) {
            if (!@ldap_start_tls($this->_ds)) {
                return PEAR::raiseError(sprintf(_("STARTTLS failed: (%s) %s"), ldap_errno($this->_ds), ldap_error($this->_ds)));
            }
        }

        /* Bind to the server. */
        if (isset($this->_params['bind_dn']) &&
            isset($this->_params['bind_password'])) {
            if (!@ldap_bind($this->_ds, $this->_params['bind_dn'], $this->_params['bind_password'])) {
                return PEAR::raiseError(sprintf(_("Bind failed: (%s) %s"), ldap_errno($this->_ds), ldap_error($this->_ds)));
            }
        } elseif (!(@ldap_bind($this->_ds))) {
            return PEAR::raiseError(sprintf(_("Bind failed: (%s) %s"), ldap_errno($this->_ds), ldap_error($this->_ds)));
        }

        return true;
    }

    /**
     * Expands the parent->toDriverKeys Function to build composed fields needed for the dn
     * based on the contents of $this->map.
     *
     * @param array $hash  Hash using Turba keys.
     *
     * @return array  Translated version of $hash.
     */
    function toDriverKeys($hash)
    {
        // First check for combined fields in the dn-fields and add them.
        if (is_array($this->_params['dn'])) {
            foreach ($this->_params['dn'] as $param) {
                foreach ($this->map as $turbaname => $ldapname) {
                    if ((is_array($this->map[$turbaname])) &&
                        (isset($this->map[$turbaname]['attribute'])) &&
                        ($this->map[$turbaname]['attribute'] == $param)) {
                        $fieldarray = array();
                        foreach ($this->map[$turbaname]['fields'] as $mapfield) {
                            if (isset($hash[$mapfield])) {
                                $fieldarray[] = $hash[$mapfield];
                            } else {
                                $fieldarray[] = '';
                            }
                        }
                        $hash[$turbaname] = trim(vsprintf($this->map[$turbaname]['format'], $fieldarray), " \t\n\r\0\x0B,");
                    }
                }
            }
        }

        // Now convert the turba-fieldnames to ldap-fieldnames
        return parent::toDriverKeys($hash);
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
    function _search($criteria, $fields)
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
            /* Filter on objectclass. */
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
        Horde::logMessage(sprintf('LDAP query by Turba_Driver_ldap::_search(): user = %s, root = %s (%s); filter = "%s"; attributes = "%s"; deref = "%s"  ; sizelimit = %d',
                                  Auth::getAuth(), $this->_params['root'], $this->_params['server'], $filter, implode(', ', $attr), $this->_params['deref'], $sizelimit),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Send the query to the LDAP server and fetch the matching
         * entries. */
        if ($this->_params['scope'] == 'one') {
            $func = 'ldap_list';
        } else {
            $func = 'ldap_search';
        }

        if (!($res = @$func($this->_ds, $this->_params['root'], $filter, $attr, 0, $sizelimit))) {
            return PEAR::raiseError(sprintf(_("Query failed: (%s) %s"), ldap_errno($this->_ds), ldap_error($this->_ds)));
        }

        return $this->_getResults($fields, $res);
    }

    /**
     * Reads the LDAP directory for a given element and returns
     * the results.
     *
     * @param string $key    The primary key field to use.
     * @param mixed $ids     The ids of the contacts to load.
     * @param string $owner  Only return contacts owned by this user.
     * @param array $fields  List of fields to return.
     *
     * @return array  Hash containing the search results.
     */
    function _read($key, $ids, $owner, $fields)
    {
        /* Only DN. */
        if ($key != 'dn') {
            return array();
        }

        $filter = $this->_buildObjectclassFilter();

        /* Four11 (at least) doesn't seem to return 'cn' if you don't
         * ask for 'sn' as well. Add 'sn' implicitly. */
        $attr = $fields;
        if (!in_array('sn', $attr)) {
            $attr[] = 'sn';
        }

        /* Handle a request for multiple records. */
        if (is_array($ids)) {
            $results = array();
            foreach ($ids as $d) {
                $res = @ldap_read($this->_ds, String::convertCharset($d, NLS::getCharset(), $this->_params['charset']), $filter, $attr);
                if ($res) {
                    if (!is_a($result = $this->_getResults($fields, $res), 'PEAR_Error')) {
                        $results = array_merge($results, $result);
                    } else {
                        return $result;
                    }
                } else {
                    return PEAR::raiseError(sprintf(_("Read failed: (%s) %s"), ldap_errno($this->_ds), ldap_error($this->_ds)));
                }
            }
            return $results;
        }

        $res = @ldap_read($this->_ds, String::convertCharset($ids, NLS::getCharset(), $this->_params['charset']), $filter, $attr);
        if (!$res) {
            return PEAR::raiseError(sprintf(_("Read failed: (%s) %s"), ldap_errno($this->_ds), ldap_error($this->_ds)));
        }

        return $this->_getResults($fields, $res);
    }

    /**
     * Adds the specified entry to the LDAP directory.
     *
     * @param array $attributes  The initial attributes for the new object.
     */
    function _add($attributes)
    {
        if (empty($attributes['dn'])) {
            return PEAR::raiseError('Tried to add an object with no dn: [' . serialize($attributes) . '].');
        } elseif (empty($this->_params['objectclass'])) {
            return PEAR::raiseError('Tried to add an object with no objectclass: [' . serialize($attributes) . '].');
        }

        /* Take the DN out of the attributes array. */
        $dn = $attributes['dn'];
        unset($attributes['dn']);

        /* Put the objectClass into the attributes array. */
        if (!is_array($this->_params['objectclass'])) {
            $attributes['objectclass'] = $this->_params['objectclass'];
        } else {
            $i = 0;
            foreach ($this->_params['objectclass'] as $objectclass) {
                $attributes['objectclass'][$i] = $objectclass;
                $i++;
            }
        }

        /* Don't add empty attributes. */
        $attributes = array_filter($attributes, array($this, '_emptyAttributeFilter'));

        /* If a required attribute doesn't exist, add a dummy
         * value. */
        if (!empty($this->_params['checkrequired'])) {
            $required = $this->_checkRequiredAttributes($this->_params['objectclass']);
            if (is_a($required, 'PEAR_Error')) {
                return $required;
            }

            foreach ($required as $k => $v) {
                if (!isset($attributes[$v])) {
                    $attributes[$v] = $this->_params['checkrequired_string'];
                }
            }
        }

        $this->_encodeAttributes($attributes);

        if (!@ldap_add($this->_ds, String::convertCharset($dn, NLS::getCharset(), $this->_params['charset']), $attributes)) {
            return PEAR::raiseError('Failed to add an object: [' . ldap_errno($this->_ds) . '] "' . ldap_error($this->_ds) . '" DN: ' . $dn . ' (attributes: [' . serialize($attributes) . ']).' . "Charset:" . NLS::getCharset());
        } else {
            return true;
        }
    }

    /**
     * @see turba/lib/Turba_Driver#_canAdd()
     */
    function _canAdd()
    {
        return true;
    }

    /**
     * Deletes the specified entry from the LDAP directory.
     */
    function _delete($object_key, $object_id)
    {
        if ($object_key != 'dn') {
            return PEAR::raiseError(_("Invalid key specified."));
        }

        if (!@ldap_delete($this->_ds, String::convertCharset($object_id, NLS::getCharset(), $this->_params['charset']))) {
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
    function _save($object_key, $object_id, $attributes)
    {
        /* Get the old entry so that we can access the old
         * values. These are needed so that we can delete any
         * attributes that have been removed by using ldap_mod_del. */
        $filter = $this->_buildObjectclassFilter();
        $oldres = @ldap_read($this->_ds, String::convertCharset($object_id, NLS::getCharset(), $this->_params['charset']), $filter, array_merge(array_keys($attributes), array('objectclass')));
        $info = ldap_get_attributes($this->_ds, ldap_first_entry($this->_ds, $oldres));

        if ($this->_params['version'] == 3 &&
            String::lower(str_replace(array(',', '"'), array('\\2C', ''), $this->_makeKey($attributes))) !=
            String::lower(str_replace(',', '\\2C', $object_id))) {
            /* Need to rename the object. */
            $newrdn = $this->_makeRDN($attributes);
            if ($newrdn == '') {
                return PEAR::raiseError(_("Missing DN in LDAP source configuration."));
            }

            if (ldap_rename($this->_ds, String::convertCharset($object_id, NLS::getCharset(), $this->_params['charset']),
                            String::convertCharset($newrdn, NLS::getCharset(), $this->_params['charset']), $this->_params['root'], true)) {
                $object_id = $newrdn . ',' . $this->_params['root'];
            } else {
                return PEAR::raiseError(sprintf(_("Failed to change name: (%s) %s; Old DN = %s, New DN = %s, Root = %s"),
                                                ldap_errno($this->_ds), ldap_error($this->_ds), $object_id, $newrdn, $this->_params['root']));
            }
        }

        /* Work only with lowercase keys. */
        $info = array_change_key_case($info, CASE_LOWER);
        $attributes = array_change_key_case($attributes, CASE_LOWER);

        foreach ($info as $key => $value) {
            $var = $info[$key];
            $oldval = null;

            /* Check to see if the old value and the new value are
             * different and that the new value is empty. If so then
             * we use ldap_mod_del to delete the attribute. */
            if (isset($attributes[$key]) &&
                ($var[0] != $attributes[$key]) &&
                $attributes[$key] == '') {

                $oldval[$key] = $var[0];
                if (!@ldap_mod_del($this->_ds, String::convertCharset($object_id, NLS::getCharset(), $this->_params['charset']), $oldval)) {
                    return PEAR::raiseError(sprintf(_("Modify failed: (%s) %s"), ldap_errno($this->_ds), ldap_error($this->_ds)));
                }
                unset($attributes[$key]);
            }
        }

        unset($attributes[String::lower($object_key)]);
        $this->_encodeAttributes($attributes);
        $attributes = array_filter($attributes, array($this, '_emptyAttributeFilter'));

        /* Modify objectclass if old one is outdated. */
        $attributes['objectclass'] = array_unique(array_map('strtolower', array_merge($info['objectclass'], $this->_params['objectclass'])));
        unset($attributes['objectclass']['count']);
        $attributes['objectclass'] = array_values($attributes['objectclass']);

        if (!@ldap_modify($this->_ds, String::convertCharset($object_id, NLS::getCharset(), $this->_params['charset']), $attributes)) {
            return PEAR::raiseError(sprintf(_("Modify failed: (%s) %s"), ldap_errno($this->_ds), ldap_error($this->_ds)));
        } else {
            return $object_id;
        }
    }

    /**
     * Build a RDN based on a set of attributes and what attributes
     * make a RDN for the current source.
     *
     * @param array $attributes The attributes (in driver keys) of the
     *                          object being added.
     *
     * @return string  The RDN for the new object.
     */
    function _makeRDN($attributes)
    {
        if (!is_array($this->_params['dn'])) {
            return '';
        }

        $pairs = array();
        foreach ($this->_params['dn'] as $param) {
            if (isset($attributes[$param])) {
                $pairs[] = array($param, $attributes[$param]);
            }
        }
        return $this->_quoteDN($pairs);
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
    function _makeKey($attributes)
    {
        return $this->_makeRDN($attributes) . ',' . $this->_params['root'];
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
                    $clause .= Horde_LDAP::buildClause($vals['field'], $vals['op'], $rhs, array('begin' => !empty($vals['begin'])));
                } else {
                    foreach ($vals as $test) {
                        if (!empty($test['OR'])) {
                            $clause .= '(|' . $this->_buildSearchQuery($test) . ')';
                        } elseif (!empty($test['AND'])) {
                            $clause .= '(&' . $this->_buildSearchQuery($test) . ')';
                        } else {
                            $rhs = String::convertCharset($test['test'], NLS::getCharset(), $this->_params['charset']);
                            $clause .= Horde_LDAP::buildClause($test['field'], $test['op'], $rhs, array('begin' => !empty($vals['begin'])));
                        }
                    }
                }
            }
        }

        return $clause;
    }

    /**
     * Get some results from a result identifier and clean them up.
     *
     * @param array    $fields  List of fields to return.
     * @param resource $res     Result identifier.
     *
     * @return array  Hash containing the results.
     */
    function _getResults($fields, $res)
    {
        $entries = @ldap_get_entries($this->_ds, $res);
        if ($entries === false) {
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
                    $result[$field] = String::convertCharset($entry[$field_l], $this->_params['charset']);
                } else {
                    $result[$field] = '';
                    if (!empty($entry[$field_l])) {
                        for ($j = 0; $j < $entry[$field_l]['count']; $j++) {
                            if (!empty($result[$field])) {
                                $result[$field] .= $this->_params['multiple_entry_separator'];
                            }
                            $result[$field] .= String::convertCharset($entry[$field_l][$j], $this->_params['charset']);
                        }

                        /* If schema checking is enabled check the
                         * backend syntax. */
                        if (!empty($this->_params['checksyntax'])) {
                            $postal = $this->_isPostalAddress($field_l);
                        } else {
                            /* Otherwise rely on the attribute mapping
                             * in attributes.php. */
                            $attr = array_search($field_l, $this->map);
                            $postal = (!empty($attr) && !empty($GLOBALS['attributes'][$attr]) &&
                                       $GLOBALS['attributes'][$attr]['type'] == 'address');
                        }
                        if ($postal) {
                            $result[$field] = str_replace('$', "\r\n", $result[$field]);
                        }
                    }
                }
            }

            $results[] = $result;
        }

        return $results;
    }

    /**
     * Remove empty attributes from attributes array.
     *
     * @param mixed $val    Value from attributes array.
     *
     * @return boolean         Boolean used by array_filter.
     */
    function _emptyAttributeFilter($var)
    {
        if (!is_array($var)) {
            return $var != '';
        } else {
            if (!count($var)) {
                return false;
            }
            foreach ($var as $v) {
                if ($v == '') {
                    return false;
                }
            }
            return true;
        }
    }

    /**
     * Format and encode attributes including postal addresses,
     * character set encoding, etc.
     */
    function _encodeAttributes(&$attributes)
    {
        foreach ($attributes as $key => $val) {
            /* If schema checking is enabled check the backend syntax. */
            if (!empty($this->_params['checksyntax'])) {
                $postal = $this->_isPostalAddress($key);
            } else {
                /* Otherwise rely on the attribute mapping in
                 * attributes.php. */
                $attr = array_search($key, $this->map);
                $postal = (!empty($attr) && !empty($val) && !empty($GLOBALS['attributes'][$attr]) &&
                           $GLOBALS['attributes'][$attr]['type'] == 'address');
            }
            if ($postal) {
                /* Correctly store postal addresses. */
                $val = str_replace(array("\r\n", "\r", "\n"), '$', $val);
            }

            if (!is_array($val)) {
                $attributes[$key] = String::convertCharset($val, NLS::getCharset(), $this->_params['charset']);
            }
        }
    }

    /**
     * Build an LDAP filter based on the objectclass parameter.
     *
     * @return string  An LDAP filter.
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

    /**
     * Returns a list of required attributes.
     *
     * @access private
     *
     * @param array $objectclasses  List of objectclasses that should be
     *                              checked for required attributes.
     *
     * @return array  List of attribute names of the specified objectclasses
     *                that have been configured as being required.
     */
    function _checkRequiredAttributes($objectclasses)
    {
       $schema = &$this->_getSchema();
       if (is_a($schema, 'PEAR_Error')) {
           return $schema;
       }

       $retval = array();

       foreach ($objectclasses as $oc) {
           if (String::lower($oc) == 'top') {
               continue;
           }

           $required = $schema->must($oc);

           if (is_array($required)) {
               foreach ($required as $v) {
                   if ($this->_isString($v)) {
                       $retval[] = String::lower($v);
                   }
               }
           }
       }

       return $retval;
    }

    /**
     * Checks if an attribute refers to a string.
     *
     * @access private
     *
     * @param string $attribute  An attribute name.
     *
     * @return boolean  True if the specified attribute refers to a string.
     */
    function _isString($attribute)
    {
        $syntax = $this->_getSyntax($attribute);

        /* Syntaxes we want to allow, i.e. no integers.
         * Syntaxes have the form:
         * 1.3.6.1.4.1.1466.115.121.1.$n{$y}
         * ... where $n is the integer used below and $y is a sizelimit. */
        $okSyntax = array(44 => 1, /* Printable string. */
                          41 => 1, /* Postal address. */
                          39 => 1, /* Other mailbox. */
                          34 => 1, /* Name and optional UID. */
                          26 => 1, /* IA5 string. */
                          15 => 1, /* Directory string. */
                          );

        if (preg_match('/^(.*)\.(\d+)\{\d+\}$/', $syntax, $matches) &&
            $matches[1] == "1.3.6.1.4.1.1466.115.121.1" &&
            isset($okSyntax[$matches[2]])) {
            return true;
        }
        return false;
    }

    /**
     * Checks if an attribute refers to a Postal Address.
     *
     * @access private
     *
     * @param string $attribute  An attribute name.
     *
     * @return boolean  True if the specified attribute refers to a Postal Address.
     */
    function _isPostalAddress($attribute)
    {
        /* LDAP postal address syntax is
         * 1.3.6.1.4.1.1466.115.121.1.41 */
        return $this->_getSyntax($attribute) == '1.3.6.1.4.1.1466.115.121.1.41';
    }

    /**
     * Returns the syntax of an attribute, if necessary recursively.
     *
     * @access private
     *
     * @param string $att  Attribute name.
     *
     * @return string  Attribute syntax.
     */
    function _getSyntax($att)
    {
        $schema = &$this->_getSchema();
        if (is_a($schema, 'PEAR_Error')) {
            return $schema;
        }

        if (!isset($this->_syntaxCache[$att])) {
            $attv = $schema->get('attribute', $att);
            if (isset($attv['syntax'])) {
                $this->_syntaxCache[$att] = $attv['syntax'];
            } else {
                $this->_syntaxCache[$att] = $this->_getSyntax($attv['sup'][0]);
            }
        }

        return $this->_syntaxCache[$att];
    }

    /**
     * Returns an LDAP_Schema object that containts the LDAP schema.
     *
     * @access private
     *
     * @return Net_LDAP_Schema  Returns a reference to the ldap schema object.
     */
    function &_getSchema()
    {
        require_once 'Net/LDAP.php';

        static $_schema;

        /* Check if the cached schema is valid, */
        if (is_object($_schema) && is_a($_schema, 'Net_LDAP_Schema')) {
            return $_schema;
        }

        $config = array('host' => $this->_params['server'],
                        'port' => $this->_params['port']);
        if (!class_exists('Net_LDAP')) {
            return PEAR::raiseError(_('You must have the Net_LDAP PEAR library installed to use the schema check function.'));
        }
        $ldap = new Net_LDAP($config);
        $ldap->_link = $this->_ds;

        $_schema = $ldap->schema();

        return $_schema;
    }

    /**
     * Take an array of DN elements and properly quote it according to
     * RFC 1485.
     *
     * @see Horde_LDAP::quoteDN()
     *
     * @param array $parts  An array of tuples containing the attribute
     *                      name and that attribute's value which make
     *                      up the DN. Example:
     *
     *    $parts = array(0 => array('cn', 'John Smith'),
     *                   1 => array('dc', 'example'),
     *                   2 => array('dc', 'com'));
     *
     * @return string  The properly quoted string DN.
     */
    function _quoteDN($parts)
    {
        $dn = '';
        $count = count($parts);
        for ($i = 0; $i < $count; $i++) {
            if ($i > 0) {
                $dn .= ',';
            }
            $dn .= $parts[$i][0] . '=';

            /* See if we need to quote the value. */
            if (preg_match('/^\s|\s$|\s\s|[,+="\r\n<>#;]/', $parts[$i][1])) {
                $dn .= '"' . str_replace('"', '\\"', $parts[$i][1]) . '"';
            } else {
                $dn .= $parts[$i][1];
            }
        }

        return $dn;
    }

}
