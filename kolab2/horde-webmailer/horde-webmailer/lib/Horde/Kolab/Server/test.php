<?php
/**
 * A driver for simulating a Kolab user database stored in LDAP.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Server/test.php,v 1.2.2.8 2009-04-25 08:56:34 wrobel Exp $
 *
 * PHP version 4
 *
 * @category Kolab
 * @package  Kolab_Server
 * @author   Gunnar Wrobel <wrobel@pardus.de>
 * @license  http://www.fsf.org/copyleft/lgpl.html LGPL
 * @link     http://pear.horde.org/index.php?package=Kolab_Server
 */

/** Require the LDAP based class as our base class */
require_once 'Horde/Kolab/Server/ldap.php';

/**
 * This class provides a class for testing the Kolab Server DB.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Server/test.php,v 1.2.2.8 2009-04-25 08:56:34 wrobel Exp $
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
class Horde_Kolab_Server_test extends Horde_Kolab_Server_ldap {

    /**
     * Array holding the current result set.
     *
     * @var array
     */
    var $_result;

    /**
     * Buffer for error numbers.
     *
     * @var int
     */
    var $_errno = 0;

    /**
     * Buffer for error descriptions.
     *
     * @var int
     */
    var $_error = '';

    /**
     * Attribute used for sorting.
     *
     * @var string
     */
    var $_sort_by;

    /**
     * A result cache for iterating over the result.
     *
     * @var array
     */
    var $_current_result;

    /**
     * An index into the current result for iterating.
     *
     * @var int
     */
    var $_current_index;

    /**
     * Construct a new Horde_Kolab_Server object.
     *
     * @param array $params Parameter array.
     */
    function Horde_Kolab_Server_test($params = array())
    {
        if (isset($params['data'])) {
            $GLOBALS['KOLAB_SERVER_TEST_DATA'] = $params['data'];
        } else {
            if (!isset($GLOBALS['KOLAB_SERVER_TEST_DATA'])) {
                $GLOBALS['KOLAB_SERVER_TEST_DATA'] = array();
            }
        }
        Horde_Kolab_Server::Horde_Kolab_Server($params);
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

        if (!empty($dn)) {
            if (!isset($GLOBALS['KOLAB_SERVER_TEST_DATA'][$dn])) {
                return PEAR::raiseError('User does not exist!');
            }

            $this->_bound = true;

            $data = $this->_read($dn, $attrs = array('userPassword'));
            if (is_a($data, 'PEAR_Error')) {
                $this->_bound = false;
                return $data;
            }
            if (!isset($data['userPassword'])) {
                $this->_bound = false;
                return PEAR::raiseError('User has no password entry!');
            }
            $this->_bound = $data['userPassword'][0] == $pw;
            if (!$this->_bound) {
                return PEAR::raiseError('Incorrect password!');
            }
        } else if (!empty($this->_params['no_anonymous_bind'])) {
            $this->_bound = false;
            return PEAR::raiseError('Anonymous bind is not allowed!');
        } else {
            $this->_bound = true;
        }
        return $this->_bound;
    }

    /**
     * Disconnect from LDAP.
     *
     * @return NULL
     */
    function unbind()
    {
        $this->_bound = false;
    }

    /**
     * Parse LDAP filter.
     * Partially derived from Net_LDAP_Filter.
     *
     * @param string $filter The filter string.
     *
     * @return array|PEAR_Error An array of the parsed filter.
     */
    function _parse($filter)
    {
        $result = array();
        if (preg_match('/^\((.+?)\)$/', $filter, $matches)) {
            if (in_array(substr($matches[1], 0, 1), array('!', '|', '&'))) {
                $result['op']  = substr($matches[1], 0, 1);
                $result['sub'] = $this->_parseSub(substr($matches[1], 1));
                return $result;
            } else {
                if (stristr($matches[1], ')(')) {
                    return PEAR::raiseError("Filter parsing error: invalid filter syntax - multiple leaf components detected!");
                } else {
                    $filter_parts = preg_split('/(?<!\\\\)(=|=~|>|<|>=|<=)/',
                                               $matches[1], 2,
                                               PREG_SPLIT_DELIM_CAPTURE);
                    if (count($filter_parts) != 3) {
                        return PEAR::raiseError("Filter parsing error: invalid filter syntax - unknown matching rule used");
                    } else {
                        $result['att'] = $filter_parts[0];
                        $result['log'] = $filter_parts[1];
                        $result['val'] = $filter_parts[2];
                        return $result;
                    }
                }
            }
        } else {
            return PEAR::raiseError(sprintf("Filter parsing error: %s - filter components must be enclosed in round brackets",
                                            $filter));
        }
    }

    /**
     * Parse a LDAP subfilter.
     *
     * @param string $filter The subfilter string.
     *
     * @return array|PEAR_Error An array of the parsed subfilter.
     */
    function _parseSub($filter)
    {
        $result  = array();
        $level   = 0;
        $collect = '';
        while (preg_match('/^(\(.+?\))(.*)/', $filter, $matches)) {
            if (in_array(substr($matches[1], 0, 2), array('(!', '(|', '(&'))) {
                $level++;
            }
            if ($level) {
                $collect .= $matches[1];
                if (substr($matches[2], 0, 1) == ')') {
                    $collect   .= ')';
                    $matches[2] = substr($matches[2], 1);
                    $level--;
                    if (!$level) {
                        $result[] = $this->_parse($collect);
                    }
                }
            } else {
                $result[] = $this->_parse($matches[1]);
            }
            $filter = $matches[2];
        }
        return $result;
    }

    /**
     * Search for an object.
     *
     * @param string $filter     Filter criteria.
     * @param array  $attributes Restrict the search result to
     *                           these attributes.
     * @param string $base       DN of the search base.
     *
     * @return array|PEAR_Error A LDAP serach result.
     */
    function _search($filter, $attributes = null, $base = null)
    {
        if (!$this->_bound) {
            $result = $this->_bind();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        if (!empty($attributes)) {
            $this->mapKeys($attributes);
        }

        $filter = $this->_parse($filter);
        if (is_a($filter, 'PEAR_Error')) {
            return $filter;
        }
        $result = $this->_doSearch($filter, $attributes);
        if (empty($result)) {
            return null;
        }
        if ($base) {
            $subtree = array();
            foreach ($result as $entry) {
                if (strpos($entry['dn'], $base)) {
                    $subtree[] = $entry;
                }
            }
            $result = $subtree;
        }

        $this->unmapAttributes($result);

        return $result;
    }

    /**
     * Perform the search.
     *
     * @param array $filter     Filter criteria-
     * @param array $attributes Restrict the search result to
     *                          these attributes.
     *
     * @return array|PEAR_Error A LDAP serach result.
     */
    function _doSearch($filter, $attributes = null)
    {
        if (isset($filter['log'])) {
            $result = array();
            foreach ($GLOBALS['KOLAB_SERVER_TEST_DATA'] as $element) {
                if (isset($element['data'][$filter['att']])) {
                    switch ($filter['log']) {
                    case '=':
                        $value = $element['data'][$filter['att']];
                        if ((($filter['val'] == '*'  || $filter['val'] == '\2a')
                             && !empty($value))
                            || $value == $filter['val']
                            || (is_array($value)
                                && in_array($filter['val'], $value))) {
                            if (empty($attributes)) {
                                $result[] = $element;
                            } else {
                                $selection = $element;
                                foreach ($element['data'] as $attr => $value) {
                                    if (!in_array($attr, $attributes)) {
                                        unset($selection['data'][$attr]);
                                    }
                                }
                                $result[] = $selection;
                            }
                        }
                        break;
                    default:
                        return PEAR::raiseError(_("Not implemented!"));
                    }
                }
            }
            return $result;
        } else {
            $subresult   = array();
            $filtercount = count($filter['sub']);
            foreach ($filter['sub'] as $subfilter) {
                $subresult = array_merge($subresult,
                                         $this->_doSearch($subfilter,
                                                          $attributes));
            }
            $result = array();
            $dns    = array();
            foreach ($subresult as $element) {
                $dns[] = $element['dn'];

                $result[$element['dn']] = $element;
            }
            switch ($filter['op']) {
            case '&':
                $count     = array_count_values($dns);
                $selection = array();
                foreach ($count as $dn => $value) {
                    if ($value == $filtercount) {
                        $selection[] = $result[$dn];
                    }
                }
                return $selection;
            case '|':
                return array_values($result);
            case '!':
                $dns = array();
                foreach ($result as $entry) {
                    if (!in_array($entry['dn'], $dns) ) {
                        $dns[] = $entry['dn'];
                    }
                }
                $all_dns = array_keys($GLOBALS['KOLAB_SERVER_TEST_DATA']);
                $diff    = array_diff($all_dns, $dns);

                $result = array();
                foreach ($diff as $dn) {
                    if (empty($attributes)) {
                        $result[] = $GLOBALS['KOLAB_SERVER_TEST_DATA'][$dn];
                    } else {
                        $selection = $GLOBALS['KOLAB_SERVER_TEST_DATA'][$dn];
                        foreach ($GLOBALS['KOLAB_SERVER_TEST_DATA'][$dn]['data']
                                 as $attr => $value) {
                            if (!in_array($attr, $attributes)) {
                                unset($selection['data'][$attr]);
                            }
                        }
                        $result[] = $selection;
                    }
                }
                return $result;
            default:
                return PEAR::raiseError(_("Not implemented!"));
            }
        }
    }

    /**
     * Read object data.
     *
     * @param string $dn    The object to retrieve.
     * @param string $attrs Restrict to these attributes
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

        if (!isset($GLOBALS['KOLAB_SERVER_TEST_DATA'][$dn])) {
            return PEAR::raiseError(sprintf("LDAP Error: No such object: %s: No such object",
                                            $dn));
        }
        if (empty($attrs)) {
            $data = $GLOBALS['KOLAB_SERVER_TEST_DATA'][$dn]['data'];
            $this->unmapAttributes($data);
            return $data;
        } else {
            $this->mapKeys($attrs);

            $result = array();
            $data   = $GLOBALS['KOLAB_SERVER_TEST_DATA'][$dn]['data'];

            foreach ($attrs as $attr) {
                if (isset($data[$attr])) {
                    $result[$attr] = $data[$attr];
                    array_push($result, $attr);
                }
            }

            $this->unmapAttributes($result);

            $result['count'] = 1;
            return $result;
        }
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

        $ldap_data = array();
        foreach ($data as $key => $val) {
            if (!is_array($val)) {
                $val = array($val);
            }
            $ldap_data[$key] = array_merge(array('count' => count($val)), $val);
        }

        $GLOBALS['KOLAB_SERVER_TEST_DATA'][$dn] = array(
            'dn' => $dn,
            'data' => $ldap_data
        );
    }

    /**
     * Count the number of results.
     *
     * @param array $result The LDAP search result.
     *
     * @return int The number of records found.
     */
    function _count($result)
    {
        if (is_array($result)) {
            return count($result);
        } else {
            return false;
        }
    }

    /**
     * Return the dn of an entry.
     *
     * @param array $entry The LDAP entry.
     *
     * @return string  The DN of the entry.
     */
    function _getDn($entry)
    {
        if (is_array($entry) && isset($entry['dn'])) {
            if (isset($entry['count'])) {
                return $entry['dn'][0];
            } else {
                return $entry['dn'];
            }
        }
        return false;
    }

    /**
     * Return the attributes of an entry.
     *
     * @param array $entry The LDAP entry.
     *
     * @return array  The attributes of the entry.
     */
    function _getAttributes($entry)
    {
        if (is_array($entry)) {
            return $entry;
        }
        return false;
    }

    /**
     * Return the current entry of a result.
     *
     * @return mixe  The current entry of the result or false.
     */
    function _fetchEntry()
    {
        if (is_array($this->_current_result)
            && $this->_current_index < count($this->_current_result)) {

            $data = array_keys($this->_current_result[$this->_current_index]['data']);

            $data['count']       = 1;
            $data['dn']          = array($this->_current_result[$this->_current_index]['dn']);
            $data['dn']['count'] = 1;

            foreach ($this->_current_result[$this->_current_index]['data']
                     as $attr => $value) {
                if (!is_array($value)) {
                    $value = array($value);
                }
                $data[$attr]          = $value;
                $data[$attr]['count'] = count($value);
            }
            $this->_current_index++;
            return $data;
        }
        return false;
    }

    /**
     * Return the first entry of a result.
     *
     * @param array $result The LDAP search result.
     *
     * @return mixed The first entry of the result or false.
     */
    function _firstEntry($result)
    {
        $this->_current_result = $result;
        $this->_current_index  = 0;
        return $this->_fetchEntry();
    }

    /**
     * Return the next entry of a result.
     *
     * @param resource $entry The current LDAP entry.
     *
     * @return resource The next entry of the result.
     */
    function _nextEntry($entry)
    {
        return $this->_fetchEntry();
    }

    /**
     * Return the entries of a result.
     *
     * @param array $result The LDAP search result.
     *
     * @return mixed The entries of the result or false.
     */
    function _getEntries($result)
    {
        if (is_array($result)) {
            $data          = array();
            $data['count'] = count($result);
            foreach ($result as $entry) {
                $t       = $entry['data'];
                $t['dn'] = $entry['dn'];
                $data[]  = $t;
            }
            return $data;
        }
        return false;
    }

    /**
     * Sort the entries of a result.
     *
     * @param resource &$result   The LDAP search result.
     * @param string   $attribute The attribute used for sorting.
     *
     * @return boolean  True if sorting succeeded.
     */
    function _sort(&$result, $attribute)
    {
        if (empty($result)) {
            return $result;
        }

        $this->_sort_by = $attribute;
        usort($result, array($this, '_resultSort'));
        return false;
    }

    /**
     * Sort two entries.
     *
     * @param array $a First entry.
     * @param array $b Second entry.
     *
     * @return int  Comparison result.
     */
    function _resultSort($a, $b)
    {
        $x = isset($a['data'][$this->_sort_by][0])?$a['data'][$this->_sort_by][0]:'';
        $y = isset($b['data'][$this->_sort_by][0])?$b['data'][$this->_sort_by][0]:'';
        return strcasecmp($x, $y);
    }


    /**
     * Return the current LDAP error number.
     *
     * @return int  The current LDAP error number.
     */
    function _errno()
    {
        return $this->_errno;
    }

    /**
     * Return the current LDAP error description.
     *
     * @return string  The current LDAP error description.
     */
    function _error()
    {
        return $this->_error;
    }

}
