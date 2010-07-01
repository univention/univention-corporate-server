<?php
/**
 * The DataTree_sql:: class provides an SQL implementation of the Horde
 * DataTree system.
 *
 * Required parameters:<pre>
 *   'phptype'      The database type (ie. 'pgsql', 'mysql', etc.).
 *   'charset'      The charset used by the database.</pre>
 *
 * Optional parameters:<pre>
 *   'table'        The name of the data table in 'database'.
 *                  DEFAULT: 'horde_datatree'</pre>
 *
 * Required by some database implementations:<pre>
 *   'database'     The name of the database.
 *   'username'     The username with which to connect to the database.
 *   'password'     The password associated with 'username'.
 *   'hostspec'     The hostname of the database server.
 *   'protocol'     The communication protocol ('tcp', 'unix', etc.).
 *   'options'      Additional options to pass to the database.
 *   'port'         The port on which to connect to the database.
 *   'tty'          The TTY on which to connect to the database.</pre>
 *
 * Optional values when using separate reading and writing servers, for example
 * in replication settings:<pre>
 *   'splitread'   Boolean, whether to implement the separation or not.
 *   'read'        Array containing the parameters which are different for
 *                 the read database connection, currently supported
 *                 only 'hostspec' and 'port' parameters.</pre>
 *
 * The table structure for the DataTree system is in
 * scripts/sql/horde_datatree.sql.
 *
 * $Horde: framework/DataTree/DataTree/sql.php,v 1.156.2.44 2009-02-25 05:35:42 chuck Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If
 * you did not receive this file, see
 * http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Stephane Huther <shuther1@free.fr>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 2.1
 * @package Horde_DataTree
 */
class DataTree_sql extends DataTree {

    /**
     * Handle for the current database connection, used for reading.
     *
     * @var DB
     */
    var $_db;

    /**
     * Handle for the current database connection, used for writing. Defaults
     * to the same handle as $_db if a separate write database is not required.
     *
     * @var DB
     */
    var $_write_db;

    /**
     * The number of copies of the horde_datatree_attributes table
     * that we need to join on in the current query.
     *
     * @var integer
     */
    var $_tableCount = 1;

    /**
     * Returns a list of all groups (root nodes) of the data tree.
     *
     * @return array  The the group IDs
     */
    function getGroups()
    {
        $query = 'SELECT DISTINCT group_uid FROM ' .  $this->_params['table'];

        Horde::logMessage('SQL Query by DataTree_sql::getGroups(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);

        return $this->_db->getCol($query);
    }

    /**
     * Loads (a subset of) the datatree into the $_data array.
     *
     * @access private
     *
     * @param string  $root         Which portion of the tree to load.
     *                              Defaults to all of it.
     * @param boolean $loadTree     Load a tree starting at $root, or just the
     *                              requested level and direct parents?
     *                              Defaults to single level.
     * @param boolean $reload       Re-load already loaded values?
     * @param string  $sortby_name  Attribute name to use for sorting.
     * @param string  $sortby_key   Attribute key to use for sorting.
     * @param integer $direction    Sort direction:
     *                              0 - ascending
     *                              1 - descending
     *
     * @return mixed  True on success or a PEAR_Error on failure.
     */
    function _load($root = DATATREE_ROOT, $loadTree = false, $reload = false,
                   $sortby_name = null, $sortby_key = null, $direction = 0)
    {
        /* Do NOT use DataTree::exists() here; that would cause an infinite
         * loop. */
        if (!$reload &&
            (in_array($root, $this->_nameMap) ||
             (count($this->_data) && $root == DATATREE_ROOT)) ||
            (!is_null($this->_sortHash) &&
             isset($this->_data[$root]['sorter'][$this->_sortHash]))) {
            return true;
        }

        $query = $this->_buildLoadQuery($root,
                                        $loadTree,
                                        DATATREE_BUILD_SELECT,
                                        $sortby_name,
                                        $sortby_key,
                                        $direction);
        if (empty($query)) {
            return true;
        }

        Horde::logMessage('SQL Query by DataTree_sql::_load(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $data = $this->_db->getAll($query);
        if (is_a($data, 'PEAR_Error')) {
            return $data;
        }
        return $this->set($data, $this->_params['charset']);
    }

    /**
     * Counts (a subset of) the datatree which would be loaded into the $_data
     * array if _load() is called with the same value of $root.
     *
     * @access private
     *
     * @param string $root  Which portion of the tree to load. Defaults to all
     *                      of it.
     *
     * @return integer  Number of objects
     */
    function _count($root = DATATREE_ROOT)
    {
        $query = $this->_buildLoadQuery($root, true, DATATREE_BUILD_COUNT);
        if (empty($query)) {
            return 0;
        }
        Horde::logMessage('SQL Query by DataTree_sql::_count(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
        return (int)$this->_db->getOne($query);
    }

    /**
     * Loads (a subset of) the datatree into the $_data array.
     *
     * @access private
     *
     * @param string  $root         Which portion of the tree to load.
     *                              Defaults to all of it.
     * @param boolean $loadTree     Load a tree starting at $root, or just the
     *                              requested level and direct parents?
     *                              Defaults to single level.
     * @param integer $operation    Type of query to build
     * @param string  $sortby_name  Attribute name to use for sorting.
     * @param string  $sortby_key   Attribute key to use for sorting.
     * @param integer $direction    Sort direction:
     *                              0 - ascending
     *                              1 - descending
     *
     * @return mixed  True on success or a PEAR_Error on failure.
     */
    function _buildLoadQuery($root = DATATREE_ROOT, $loadTree = false,
                             $operation = DATATREE_BUILD_SELECT,
                             $sortby_name = null, $sortby_key = null,
                             $direction = 0)
    {
        $sorted = false;
        $where = sprintf('c.group_uid = %s ', $this->_db->quote($this->_params['group']));

        if (!empty($root) && $root != DATATREE_ROOT) {
            $parent_where = $this->_buildParentIds($root, $loadTree, 'c.');
            if (empty($parent_where)) {
                return '';
            } elseif (!is_a($parent_where, 'PEAR_Error')) {
                $where = sprintf('%s AND (%s)', $where, $parent_where);
            }
        }
        if (!is_null($sortby_name)) {
            $where = sprintf('%s AND a.attribute_name = %s ', $where, $this->_db->quote($sortby_name));
            $sorted = true;
        }
        if (!is_null($sortby_key)) {
            $where = sprintf('%s AND a.attribute_key = %s ', $where, $this->_db->quote($sortby_key));
            $sorted = true;
        }

        switch ($operation) {
        case DATATREE_BUILD_COUNT:
            $what = 'COUNT(*)';
            break;

        default:
            $what = 'c.datatree_id, c.datatree_name, c.datatree_parents, c.datatree_order';
            break;
        }

        if ($sorted) {
            $query = sprintf('SELECT %s FROM %s c LEFT JOIN %s a ON (c.datatree_id = a.datatree_id OR c.datatree_name=%s) '.
                             'WHERE %s GROUP BY c.datatree_id, c.datatree_name, c.datatree_parents, c.datatree_order ORDER BY a.attribute_value %s',
                             $what,
                             $this->_params['table'],
                             $this->_params['table_attributes'],
                             $this->_db->quote($root),
                             $where,
                             ($direction == 1) ? 'DESC' : 'ASC');
        } else {
            $query = sprintf('SELECT %s FROM %s c WHERE %s',
                             $what,
                             $this->_params['table'],
                             $where);
        }

        return $query;
    }

    /**
     * Builds parent ID string for selecting trees.
     *
     * @access private
     *
     * @param string  $root      Which portion of the tree to load.
     * @param boolean $loadTree  Load a tree starting at $root, or just the
     *                           requested level and direct parents?
     *                           Defaults to single level.
     * @param string  $join_name Table join name
     *
     * @return string  Id list.
     */
    function _buildParentIds($root, $loadTree = false, $join_name = '')
    {
        if (strpos($root, ':') !== false) {
            $parts = explode(':', $root);
            $root = array_pop($parts);
        }
        $root = (string)$root;

        $query = 'SELECT datatree_id, datatree_parents' .
            ' FROM ' . $this->_params['table'] .
            ' WHERE datatree_name = ? AND group_uid = ?' .
            ' ORDER BY datatree_id';
        $values = array($root,
                        $this->_params['group']);

        Horde::logMessage('SQL Query by DataTree_sql::_buildParentIds(): ' . $query . ', ' . var_export($values, true), __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $root = $this->_db->getAssoc($query, false, $values);
        if (is_a($root, 'PEAR_Error') || !count($root)) {
            return '';
        }

        $where = '';
        $first_time = true;
        foreach ($root as $object_id => $object_parents) {
            $pstring = $object_parents . ':' . $object_id . '%';
            $pquery = '';
            if (!empty($object_parents)) {
                $ids = substr($object_parents, 1);
                $pquery = ' OR ' . $join_name . 'datatree_id IN (' . str_replace(':', ', ', $ids) . ')';
            }
            if ($loadTree) {
                $pquery .= ' OR ' . $join_name . 'datatree_parents = ' . $this->_db->quote(substr($pstring, 0, -1));
            }

            if (!$first_time) {
                $where .= ' OR ';
            }
            $where .= sprintf($join_name . 'datatree_parents LIKE %s OR ' . $join_name . 'datatree_id = %s%s',
                              $this->_db->quote($pstring),
                              $object_id,
                              $pquery);

            $first_time = false;
        }

        return $where;
    }

    /**
     * Loads a set of objects identified by their unique IDs, and their
     * parents, into the $_data array.
     *
     * @access private
     *
     * @param mixed $cids  The unique ID of the object to load, or an array of
     *                     object ids.
     *
     * @return mixed  True on success or a PEAR_Error on failure.
     */
    function _loadById($cids)
    {
        /* Make sure we have an array. */
        if (!is_array($cids)) {
            $cids = array((int)$cids);
        } else {
            array_walk($cids, 'intval');
        }

        /* Bail out now if there's nothing to load. */
        if (!count($cids)) {
            return true;
        }

        /* Don't load any that are already loaded. Also, make sure that
         * everything in the $ids array that we are building is an integer. */
        $ids = array();
        foreach ($cids as $cid) {
            /* Do NOT use DataTree::exists() here; that would cause an
             * infinite loop. */
            if (!isset($this->_data[$cid])) {
                $ids[] = (int)$cid;
            }
        }

        /* If there are none left to load, return. */
        if (!count($ids)) {
            return true;
        }

        $in = array_search(DATATREE_ROOT, $ids) === false ? sprintf('datatree_id IN (%s) AND ', implode(', ', $ids)) : '';
        $query = sprintf('SELECT datatree_id, datatree_parents FROM %s' .
                         ' WHERE %sgroup_uid = %s' .
                         ' ORDER BY datatree_id',
                         $this->_params['table'],
                         $in,
                         $this->_db->quote($this->_params['group']));
        Horde::logMessage('SQL Query by DataTree_sql::_loadById(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $parents = $this->_db->getAssoc($query);
        if (is_a($parents, 'PEAR_Error')) {
            return $parents;
        }
        if (empty($parents)) {
            return PEAR::raiseError(_("Object not found."), null, null, null, 'DataTree ids ' . implode(', ', $ids) . ' not found.');
        }

        $ids = array();
        foreach ($parents as $cid => $parent) {
            $ids[(int)$cid] = (int)$cid;

            $pids = explode(':', substr($parent, 1));
            foreach ($pids as $pid) {
                $pid = (int)$pid;
                if (!isset($this->_data[$pid])) {
                    $ids[$pid] = $pid;
                }
            }
        }

        /* If $ids is empty, we have nothing to load. */
        if (!count($ids)) {
            return true;
        }

        $query = 'SELECT datatree_id, datatree_name, datatree_parents, datatree_order' .
                 ' FROM ' . $this->_params['table'] .
                 ' WHERE datatree_id IN (?' . str_repeat(', ?', count($ids) - 1) . ')' .
                 ' AND group_uid = ? ORDER BY datatree_id';
        $values = array_merge($ids, array($this->_params['group']));

        Horde::logMessage('SQL Query by DataTree_sql::_loadById(): ' . $query . ', ' . var_export($values, true), __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $data = $this->_db->getAll($query, $values);
        if (is_a($data, 'PEAR_Error')) {
            return $data;
        }

        return $this->set($data, $this->_params['charset']);
    }

    /**
     * Check for existance of an object in a backend-specific manner.
     *
     * @param string $object_name Object name to check for.
     *
     * @return boolean True if the object exists, false otherwise.
     */
    function _exists($object_name)
    {
        $query = 'SELECT datatree_id FROM ' . $this->_params['table'] .
            ' WHERE group_uid = ? AND datatree_name = ? AND datatree_parents = ?';

        $object_names = explode(':', $object_name);
        $object_parents = '';
        foreach ($object_names as $name) {
            $values = array($this->_params['group'], $name, $object_parents);
            Horde::logMessage('SQL Query by DataTree_sql::_exists(): ' . $query . ', ' . var_export($values, true), __FILE__, __LINE__, PEAR_LOG_DEBUG);

            $result = $this->_db->getOne($query, $values);
            if (is_a($result, 'PEAR_Error') || !$result) {
                return false;
            }

            $object_parents .= ':' . $result;
        }

        return true;
    }

    /**
     * Look up a datatree id by name.
     *
     * @param string $name
     *
     * @return integer DataTree id
     */
    function _getId($name)
    {
        $query = 'SELECT datatree_id FROM ' . $this->_params['table']
            . ' WHERE group_uid = ? AND datatree_name = ?'
            . ' AND datatree_parents = ?';

        $ids = array();
        $parts = explode(':', $name);
        foreach ($parts as $part) {
            $result = $this->_db->getOne($query, array($this->_params['group'], $part, count($ids) ? ':' . implode(':', $ids) : ''));
            if (is_a($result, 'PEAR_Error') || !$result) {
                return null;
            } else {
                $ids[] = $result;
            }
        }

        return (int)array_pop($ids);
    }

    /**
     * Look up a datatree name by id.
     *
     * @param integer $id
     *
     * @return string DataTree name
     */
    function _getName($id)
    {
        $query = 'SELECT datatree_name FROM ' . $this->_params['table'] .
            ' WHERE group_uid = ? AND datatree_id = ?';
        $values = array($this->_params['group'], (int)$id);
        Horde::logMessage('SQL Query by DataTree_sql::_getName(): ' . $query . ', ' . var_export($values, true), __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $name = $this->_db->getOne($query, $values);
        if (is_a($name, 'PEAR_Error')) {
            return null;
        } else {
            $name = String::convertCharset($name, $this->_params['charset'],
                                           NLS::getCharset());
            // Get the parent names, if any.
            $parent = $this->getParentById($id);
            if ($parent && !is_a($parent, 'PEAR_Error') &&
                $parent != DATATREE_ROOT) {
                return $this->getName($parent) . ':' . $name;
            } else {
                return $name;
            }
        }
    }

    /**
     * Returns a tree sorted by the specified attribute name and/or key.
     *
     * @since Horde 3.1
     *
     * @param string $root         Which portion of the tree to sort.
     *                             Defaults to all of it.
     * @param boolean $loadTree    Sort the tree starting at $root, or just the
     *                             requested level and direct parents?
     *                             Defaults to single level.
     * @param string $sortby_name  Attribute name to use for sorting.
     * @param string $sortby_key   Attribute key to use for sorting.
     * @param integer $direction   Sort direction:
     *                             0 - ascending
     *                             1 - descending
     *
     * @return array TODO
     */
    function getSortedTree($root, $loadTree = false, $sortby_name = null,
                           $sortby_key = null, $direction = 0)
    {
        $query = $this->_buildLoadQuery($root,
                                        $loadTree,
                                        DATATREE_BUILD_SELECT,
                                        $sortby_name,
                                        $sortby_key,
                                        $direction);

        if (empty($query)) {
            return array();
        }
        return $this->_db->getAll($query);
    }

    /**
     * Adds an object.
     *
     * @param mixed $object        The object to add (string or
     *                             DataTreeObject).
     * @param boolean $id_as_name  Whether the object ID is to be used as
     *                             object name.  Used in situations where
     *                             there is no available unique input for
     *                             object name.
     */
    function add($object, $id_as_name = false)
    {
        $attributes = false;
        if (is_a($object, 'DataTreeObject')) {
            $fullname = $object->getName();
            $order = $object->order;

            /* We handle data differently if we can map it to the
             * horde_datatree_attributes table. */
            if (method_exists($object, '_toAttributes')) {
                $data = '';
                $ser = null;

                /* Set a flag for later so that we know to insert the
                 * attribute rows. */
                $attributes = true;
            } else {
                require_once 'Horde/Serialize.php';
                $ser = SERIALIZE_UTF7_BASIC;
                $data = Horde_Serialize::serialize($object->getData(), $ser, NLS::getCharset());
            }
        } else {
            $fullname = $object;
            $order = null;
            $data = '';
            $ser = null;
        }

        /* Get the next unique ID. */
        $id = $this->_write_db->nextId($this->_params['table']);
        if (is_a($id, 'PEAR_Error')) {
            Horde::logMessage($id, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $id;
        }

        if (strpos($fullname, ':') !== false) {
            $parts = explode(':', $fullname);
            $parents = '';
            $pstring = '';
            if ($id_as_name) {
                /* Requested use of ID as name, so discard current name. */
                array_pop($parts);
                /* Set name to ID. */
                $name = $id;
                /* Modify fullname to reflect new name. */
                $fullname = implode(':', $parts) . ':' . $id;
                if (is_a($object, 'DataTreeObject')) {
                    $object->setName($fullname);
                } else {
                    $object = $fullname;
                }
            } else {
                $name = array_pop($parts);
            }
            foreach ($parts as $par) {
                $pstring .= (empty($pstring) ? '' : ':') . $par;
                $pid = $this->getId($pstring);
                if (is_a($pid, 'PEAR_Error')) {
                    /* Auto-create parents. */
                    $pid = $this->add($pstring);
                    if (is_a($pid, 'PEAR_Error')) {
                        return $pid;
                    }
                }
                $parents .= ':' . $pid;
            }
        } else {
            if ($id_as_name) {
                /* Requested use of ID as name, set fullname and name to ID. */
                $fullname = $id;
                $name = $id;
                if (is_a($object, 'DataTreeObject')) {
                    $object->setName($fullname);
                } else {
                    $object = $fullname;
                }
            } else {
                $name = $fullname;
            }
            $parents = '';
            $pid = DATATREE_ROOT;
        }

        if (parent::exists($fullname)) {
            return PEAR::raiseError(sprintf(_("\"%s\" already exists"), $fullname));
        }

        $query = 'INSERT INTO ' . $this->_params['table'] .
                 ' (datatree_id, group_uid, datatree_name, datatree_order,' .
                 ' datatree_data, user_uid, datatree_serialized,' .
                 ' datatree_parents)' .
                 ' VALUES (?, ?, ?, ?, ?, ?, ?, ?)';
        $values = array((int)$id,
                        $this->_params['group'],
                        String::convertCharset($name, NLS::getCharset(), $this->_params['charset']),
                        is_null($order) ? NULL : (int)$order,
                        $data,
                        (string)Auth::getAuth(),
                        (int)$ser,
                        $parents);

        Horde::logMessage('SQL Query by DataTree_sql::add(): ' . $query . ', ' . var_export($values, true), __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $result = $this->_write_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }

        $reorder = $this->reorder($parents, $order, $id);
        if (is_a($reorder, 'PEAR_Error')) {
            Horde::logMessage($reorder, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $reorder;
        }

        $result = parent::_add($fullname, $id, $pid, $order);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        /* If we succesfully inserted the object and it supports
         * being mapped to the attributes table, do that now: */
        if (!empty($attributes)) {
            $result = $this->updateData($object);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        return $id;
    }

    /**
     * Changes the order of the children of an object.
     *
     * @param string $parent  The full id path of the parent object.
     * @param mixed $order    If an array it specifies the new positions for
     *                        all child objects.
     *                        If an integer and $cid is specified, the position
     *                        where the child specified by $cid is inserted. If
     *                        $cid is not specified, the position gets deleted,
     *                        causing the following positions to shift up.
     * @param integer $cid    See $order.
     */
    function reorder($parent, $order = null, $cid = null)
    {
        if (!$parent || is_a($parent, 'PEAR_Error')) {
            // Abort immediately if the parent string is empty; we
            // cannot safely reorder all top-level elements.
            return;
        }

        $pquery = '';
        if (!is_array($order) && !is_null($order)) {
            /* Single update (add/del). */
            if (is_null($cid)) {
                /* No object id given so shuffle down. */
                $direction = '-';
            } else {
                /* We have an object id so shuffle up. */
                $direction = '+';

                /* Leaving the newly inserted object alone. */
                $pquery = sprintf(' AND datatree_id != %s', (int)$cid);
            }
            $query = sprintf('UPDATE %s SET datatree_order = datatree_order %s 1 WHERE group_uid = %s AND datatree_parents = %s AND datatree_order >= %s',
                             $this->_params['table'],
                             $direction,
                             $this->_write_db->quote($this->_params['group']),
                             $this->_write_db->quote($parent),
                             is_null($order) ? 'NULL' : (int)$order) . $pquery;

            Horde::logMessage('SQL Query by DataTree_sql::reorder(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $result = $this->_write_db->query($query);
        } elseif (is_array($order)) {
            /* Multi update. */
            $query = 'SELECT COUNT(datatree_id)' .
                     ' FROM ' . $this->_params['table'] .
                     ' WHERE group_uid = ? AND datatree_parents = ?' .
                     ' GROUP BY datatree_parents';
            $values = array($this->_params['group'],
                            $parent);

            Horde::logMessage('SQL Query by DataTree_sql::reorder(): ' . $query . ', ' . var_export($values, true), __FILE__, __LINE__, PEAR_LOG_DEBUG);

            $result = $this->_db->getOne($query, $values);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            } elseif (count($order) != $result) {
                return PEAR::raiseError(_("Cannot reorder, number of entries supplied for reorder does not match number stored."));
            }

            $o_key = 0;
            foreach ($order as $o_cid) {
                $query = 'UPDATE ' . $this->_params['table'] .
                         ' SET datatree_order = ? WHERE datatree_id = ?';
                $values = array($o_key, is_null($o_cid) ? NULL : (int)$o_cid);

                Horde::logMessage('SQL Query by DataTree_sql::reorder(): ' . $query . ', ' . var_export($values, true), __FILE__, __LINE__, PEAR_LOG_DEBUG);
                $result = $this->_write_db->query($query, $values);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }

                $o_key++;
            }

            $pid = $this->getId($parent);

            /* Re-order our cache. */
            return $this->_reorder($pid, $order);
        }
    }

    /**
     * Explicitly set the order for a datatree object.
     *
     * @param integer $id     The datatree object id to change.
     * @param integer $order  The new order.
     */
    function setOrder($id, $order)
    {
        $query = 'UPDATE ' . $this->_params['table'] .
                 ' SET datatree_order = ? WHERE datatree_id = ?';
        $values = array(is_null($order) ? NULL : (int)$order,
                        (int)$id);

        Horde::logMessage('SQL Query by DataTree_sql::setOrder(): ' . $query . ', ' . var_export($values, true), __FILE__, __LINE__, PEAR_LOG_DEBUG);
        return $this->_write_db->query($query, $values);
    }

    /**
     * Removes an object.
     *
     * @param mixed   $object  The object to remove.
     * @param boolean $force   Force removal of every child object?
     */
    function remove($object, $force = false)
    {
        $id = $this->getId($object);
        if (is_a($id, 'PEAR_Error')) {
            return $id;
        }
        $order = $this->getOrder($object);

        $query = 'SELECT datatree_id FROM ' . $this->_params['table'] .
                 ' WHERE group_uid = ? AND datatree_parents LIKE ?' .
                 ' ORDER BY datatree_id';
        $values = array($this->_params['group'],
                        '%:' . (int)$id . '');

        Horde::logMessage('SQL Query by DataTree_sql::remove(): ' . $query . ', ' . var_export($values, true), __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $children = $this->_db->getAll($query, $values, DB_FETCHMODE_ASSOC);

        if (count($children)) {
            if ($force) {
                foreach ($children as $child) {
                    $cat = $this->getName($child['datatree_id']);
                    $result = $this->remove($cat, true);
                    if (is_a($result, 'PEAR_Error')) {
                        return $result;
                    }
                }
            } else {
                return PEAR::raiseError(sprintf(_("Cannot remove, %d children exist."), count($children)));
            }
        }

        /* Remove attributes for this object. */
        $query = 'DELETE FROM ' . $this->_params['table_attributes'] .
                 ' WHERE datatree_id = ?';
        $values = array((int)$id);

        Horde::logMessage('SQL Query by DataTree_sql::remove(): ' . $query . ', ' . var_export($values, true), __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $result = $this->_write_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $query = 'DELETE FROM ' . $this->_params['table'] .
                 ' WHERE datatree_id = ?';
        $values = array((int)$id);

        Horde::logMessage('SQL Query by DataTree_sql::remove(): ' . $query . ', ' . var_export($values, true), __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $result = $this->_write_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $parents = $this->getParentIdString($object);
        if (is_a($parents, 'PEAR_Error')) {
            return $parents;
        }

        $reorder = $this->reorder($parents, $order);
        if (is_a($reorder, 'PEAR_Error')) {
            return $reorder;
        }

        return is_a(parent::remove($object), 'PEAR_Error') ? $id : true;
    }

    /**
     * Removes one or more objects by id.
     *
     * This function does *not* do the validation, reordering, etc. that
     * remove() does. If you need to check for children, re-do ordering, etc.,
     * then you must remove() objects one-by-one. This is for code that knows
     * it's dealing with single (non-parented) objects and needs to delete a
     * batch of them quickly.
     *
     * @param array $ids  The objects to remove.
     */
    function removeByIds($ids)
    {
        /* Sanitize input. */
        if (!is_array($ids)) {
            $ids = array((int)$ids);
        } else {
            array_walk($ids, 'intval');
        }

        /* Removing zero objects always succeeds. */
        if (!$ids) {
            return true;
        }

        /* Remove attributes for $ids. */
        $query = 'DELETE FROM ' . $this->_params['table_attributes'] .
                 ' WHERE datatree_id IN (?' . str_repeat(', ?', count($ids) - 1) . ')';
        $values = $ids;

        Horde::logMessage('SQL Query by DataTree_sql::removeByIds(): ' . $query . ', ' . var_export($values, true), __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $result = $this->_write_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $query = 'DELETE FROM ' . $this->_params['table'] .
                 ' WHERE datatree_id IN (?' . str_repeat(', ?', count($ids) - 1) . ')';
        $values = $ids;

        Horde::logMessage('SQL Query by DataTree_sql::removeByIds(): ' . $query . ', ' . var_export($values, true), __FILE__, __LINE__, PEAR_LOG_DEBUG);
        return $this->_write_db->query($query, $values);
    }

    /**
     * Removes one or more objects by name.
     *
     * This function does *not* do the validation, reordering, etc. that
     * remove() does. If you need to check for children, re-do ordering, etc.,
     * then you must remove() objects one-by-one. This is for code that knows
     * it's dealing with single (non-parented) objects and needs to delete a
     * batch of them quickly.
     *
     * @param array $names  The objects to remove.
     */
    function removeByNames($names)
    {
        if (!is_array($names)) {
            $names = array($names);
        }

        /* Removing zero objects always succeeds. */
        if (!$names) {
            return true;
        }

        $query = 'SELECT datatree_id FROM ' . $this->_params['table'] .
                 ' WHERE datatree_name IN (?' . str_repeat(', ?', count($names) - 1) . ')';
        $values = $names;

        Horde::logMessage('SQL Query by DataTree_sql::removeByNames(): ' . $query . ', ' . var_export($values, true), __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $ids = $this->_db->getCol($query, 0, $values);
        if (is_a($ids, 'PEAR_Error')) {
            return $ids;
        }

        return $this->removeByIds($ids);
    }

    /**
     * Move an object to a new parent.
     *
     * @param mixed  $object     The object to move.
     * @param string $newparent  The new parent object. Defaults to the root.
     */
    function move($object, $newparent = null)
    {
        $old_parent_path = $this->getParentIdString($object);
        $result = parent::move($object, $newparent);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        $id = $this->getId($object);
        $new_parent_path = $this->getParentIdString($object);

        /* Fetch the object being moved and all of its children, since
         * we also need to update their parent paths to avoid creating
         * orphans. */
        $query = 'SELECT datatree_id, datatree_parents' .
                 ' FROM ' . $this->_params['table'] .
                 ' WHERE datatree_parents = ? OR datatree_parents LIKE ?' .
                 ' OR datatree_id = ?';
        $values = array($old_parent_path . ':' . $id,
                        $old_parent_path . ':' . $id . ':%',
                        (int)$id);

        Horde::logMessage('SQL Query by DataTree_sql::move(): ' . $query . ', ' . var_export($values, true), __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $rowset = $this->_db->query($query, $values);
        if (is_a($rowset, 'PEAR_Error')) {
            return $rowset;
        }

        /* Update each object, replacing the old parent path with the
         * new one. */
        while ($row = $rowset->fetchRow(DB_FETCHMODE_ASSOC)) {
            if (is_a($row, 'PEAR_Error')) {
                return $row;
            }

            $oquery = '';
            if ($row['datatree_id'] == $id) {
                $oquery = ', datatree_order = 0 ';
            }

            /* Do str_replace() only if this is not a first level
             * object. */
            if (!empty($row['datatree_parents'])) {
                $ppath = str_replace($old_parent_path, $new_parent_path, $row['datatree_parents']);
            } else {
                $ppath = $new_parent_path;
            }
            $query = sprintf('UPDATE %s SET datatree_parents = %s' . $oquery . ' WHERE datatree_id = %s',
                             $this->_params['table'],
                             $this->_write_db->quote($ppath),
                             (int)$row['datatree_id']);

            Horde::logMessage('SQL Query by DataTree_sql::move(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $result = $this->_write_db->query($query);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $order = $this->getOrder($object);

        /* Shuffle down the old order positions. */
        $reorder = $this->reorder($old_parent_path, $order);

        /* Shuffle up the new order positions. */
        $reorder = $this->reorder($new_parent_path, 0, $id);

        return true;
    }

    /**
     * Change an object's name.
     *
     * @param mixed  $old_object       The old object.
     * @param string $new_object_name  The new object name.
     */
    function rename($old_object, $new_object_name)
    {
        /* Do the cache renaming first */
        $result = parent::rename($old_object, $new_object_name);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        /* Get the object id and set up the sql query. */
        $id = $this->getId($old_object);
        $query = 'UPDATE ' . $this->_params['table'] .
                 ' SET datatree_name = ? WHERE datatree_id = ?';
        $values = array(String::convertCharset($new_object_name, NLS::getCharset(), $this->_params['charset']),
                        (int)$id);

        Horde::logMessage('SQL Query by DataTree_sql::rename(): ' . $query . ', ' . var_export($values, true), __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $result = $this->_write_db->query($query, $values);

        return is_a($result, 'PEAR_Error') ? $result : true;
    }

    /**
     * Retrieves data for an object from the datatree_data field.
     *
     * @param integer $cid  The object id to fetch, or an array of object ids.
     */
    function getData($cid)
    {
        require_once 'Horde/Serialize.php';

        if (is_array($cid)) {
            if (!count($cid)) {
                return array();
            }

            $query = sprintf('SELECT datatree_id, datatree_data, datatree_serialized FROM %s WHERE datatree_id IN (%s)',
                             $this->_params['table'],
                             implode(', ', $cid));

            Horde::logMessage('SQL Query by DataTree_sql::getData(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $result = $this->_db->getAssoc($query);
            if (is_a($result, 'PEAR_Error')) {
                Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                return $result;
            }

            $data = array();
            foreach ($result as $id => $row) {
                $data[$id] = Horde_Serialize::unserialize($row[0], $row[1],
                                                          NLS::getCharset());
                /* Convert old data to the new format. */
                if ($row[1] == SERIALIZE_BASIC) {
                    $data[$id] = String::convertCharset($data[$id],
                                                        NLS::getCharset(true));
                }

                $data[$id] = (is_null($data[$id]) || !is_array($data[$id]))
                    ? array()
                    : $data[$id];
            }

            return $data;
        } else {
            $query = 'SELECT datatree_data, datatree_serialized' .
                     ' FROM ' . $this->_params['table'] .
                     ' WHERE datatree_id = ?';
            $values = array((int)$cid);

            Horde::logMessage('SQL Query by DataTree_sql::getData(): ' . $query . ', ' . var_export($values, true), __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $row = $this->_db->getRow($query, $values, DB_FETCHMODE_ASSOC);

            $data = Horde_Serialize::unserialize($row['datatree_data'],
                                                 $row['datatree_serialized'],
                                                 NLS::getCharset());
            /* Convert old data to the new format. */
            if ($row['datatree_serialized'] == SERIALIZE_BASIC) {
                $data = String::convertCharset($data, NLS::getCharset(true));
            }
            return (is_null($data) || !is_array($data)) ? array() : $data;
        }
    }

    /**
     * Retrieves data for an object from the horde_datatree_attributes table.
     *
     * @param integer|array $cid  The object id to fetch, or an array of
     *                            object ids.
     * @param array $keys         The attributes keys to fetch.
     *
     * @return array  A hash of attributes, or a multi-level hash of object
     *                ids => their attributes.
     */
    function getAttributes($cid, $keys = false)
    {
        if (empty($cid)) {
            return array();
        }

        if ($keys) {
            $filter = sprintf(' AND attribute_key IN (\'%s\')',
                              implode("', '", $keys));
        } else {
            $filter = '';
        }

        if (is_array($cid)) {
            $query = sprintf('SELECT datatree_id, attribute_name AS name, attribute_key AS "key", attribute_value AS value FROM %s WHERE datatree_id IN (%s)%s',
                             $this->_params['table_attributes'],
                             implode(', ', $cid),
                             $filter);

            Horde::logMessage('SQL Query by DataTree_sql::getAttributes(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $rows = $this->_db->getAll($query, DB_FETCHMODE_ASSOC);
            if (is_a($rows, 'PEAR_Error')) {
                return $rows;
            }

            $data = array();
            foreach ($rows as $row) {
                if (empty($data[$row['datatree_id']])) {
                    $data[$row['datatree_id']] = array();
                }
                $data[$row['datatree_id']][] = array('name' => $row['name'],
                                                     'key' => $row['key'],
                                                     'value' => String::convertCharset($row['value'], $this->_params['charset'], NLS::getCharset()));
            }
            return $data;
        } else {
            $query = sprintf('SELECT attribute_name AS name, attribute_key AS "key", attribute_value AS value FROM %s WHERE datatree_id = %s%s',
                             $this->_params['table_attributes'],
                             (int)$cid,
                             $filter);

            Horde::logMessage('SQL Query by DataTree_sql::getAttributes(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $rows = $this->_db->getAll($query, DB_FETCHMODE_ASSOC);
            for ($i = 0; $i < count($rows); $i++) {
                $rows[$i]['value'] = String::convertCharset($rows[$i]['value'],
                                                            $this->_params['charset'],
                                                            NLS::getCharset());
            }
            return $rows;
        }
    }

    /**
     * Returns the number of objects matching a set of attribute criteria.
     *
     * @see buildAttributeQuery()
     *
     * @param array   $criteria   The array of criteria.
     * @param string  $parent     The parent node to start searching from.
     * @param boolean $allLevels  Return all levels, or just the direct
     *                            children of $parent? Defaults to all levels.
     * @param string  $restrict   Only return attributes with the same
     *                            attribute_name or attribute_id.
     */
    function countByAttributes($criteria, $parent = DATATREE_ROOT,
                               $allLevels = true, $restrict = 'name')
    {
        if (!count($criteria)) {
            return 0;
        }

        $aq = $this->buildAttributeQuery($criteria,
                                         $parent,
                                         $allLevels,
                                         $restrict,
                                         DATATREE_BUILD_COUNT);
        if (is_a($aq, 'PEAR_Error')) {
            return $aq;
        }
        list($query, $values) = $aq;

        Horde::logMessage('SQL Query by DataTree_sql::countByAttributes(): ' . $query . ', ' . var_export($values, true), __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $result = $this->_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }
        $row = $result->fetchRow();
        if (is_a($row, 'PEAR_Error')) {
            Horde::logMessage($row, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $row;
        }

        return $row[0];
    }

    /**
     * Returns a set of object ids based on a set of attribute criteria.
     *
     * @see buildAttributeQuery()
     *
     * @param array   $criteria     The array of criteria.
     * @param string  $parent       The parent node to start searching from.
     * @param boolean $allLevels    Return all levels, or just the direct
     *                              children of $parent? Defaults to all levels.
     * @param string  $restrict     Only return attributes with the same
     *                              attribute_name or attribute_id.
     * @param integer $from         The object to start to fetching
     * @param integer $count        The number of objects to fetch
     * @param string  $sortby_name  Attribute name to use for sorting.
     * @param string  $sortby_key   Attribute key to use for sorting.
     * @param integer $direction    Sort direction:
     *                                0 - ascending
     *                                1 - descending
     */
    function getByAttributes($criteria, $parent = DATATREE_ROOT,
                             $allLevels = true, $restrict = 'name', $from = 0,
                             $count = 0, $sortby_name = null,
                             $sortby_key = null, $direction = 0)
    {
        if (!count($criteria)) {
            return PEAR::raiseError('no criteria');
        }

        // If there are top-level OR criteria, process one at a time
        // and return any results as soon as they're found...but only if
        // there is no LIMIT requested.
        if ($count == 0 && $from == 0) {
            foreach ($criteria as $key => $vals) {
                if ($key == 'OR') {
                    $rows = array();
                    $num_or_statements = count($criteria[$key]);
                    for ($i = 0; $i < $num_or_statements; $i++) {
                        $criteria_or = $criteria['OR'][$i];
                        list($query, $values) = $this->buildAttributeQuery(
                                                    $criteria_or,
                                                    $parent,
                                                    $allLevels,
                                                    $restrict,
                                                    DATATREE_BUILD_SELECT,
                                                    $sortby_name,
                                                    $sortby_key,
                                                    $direction);
                        if ($count) {
                            $query = $this->_db->modifyLimitQuery($query, $from, $count);
                        }

                        Horde::logMessage('SQL Query by DataTree_sql::getByAttributes(): ' . $query . ', ' . var_export($values, true), __FILE__, __LINE__, PEAR_LOG_DEBUG);

                        $result = $this->_db->query($query, $values);
                        if (is_a($result, 'PEAR_Error')) {
                            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                            return $result;
                        }
                        while ($row = $result->fetchRow()) {
                            $rows[$row[0]] = String::convertCharset($row[1], $this->_params['charset']);
                        }
                    }

                    return $rows;
                }
            }
        }
        // Process AND or other complex queries.
        $aq = $this->buildAttributeQuery($criteria,
                                         $parent,
                                         $allLevels,
                                         $restrict,
                                         DATATREE_BUILD_SELECT,
                                         $sortby_name,
                                         $sortby_key,
                                         $direction);
        if (is_a($aq, 'PEAR_Error')) {
            return $aq;
        }

        list($query, $values) = $aq;

        if ($count) {
            $query = $this->_db->modifyLimitQuery($query, $from, $count);
        }

        Horde::logMessage('SQL Query by DataTree_sql::getByAttributes(): ' . $query . ', ' . var_export($values, true), __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $result = $this->_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }

        $rows = array();
        while ($row = $result->fetchRow()) {
            $rows[$row[0]] = String::convertCharset($row[1], $this->_params['charset']);
        }

        return $rows;
    }

    /**
     * Sorts IDs by attribute values. IDs without attributes will be added to
     * the end of the sorted list.
     *
     * @param array $unordered_ids  Array of ids to sort.
     * @param array $sortby_name    Attribute name to use for sorting.
     * @param array $sortby_key     Attribute key to use for sorting.
     * @param array $direction      Sort direction:
     *                                0 - ascending
     *                                1 - descending
     *
     * @return array  Sorted ids.
     */
    function sortByAttributes($unordered_ids, $sortby_name = null,
                              $sortby_key = null, $direction = 0)
    {
        /* Select ids ordered by attribute value. */
        $where = '';
        if (!is_null($sortby_name)) {
            $where = sprintf(' AND attribute_name = %s ',
                             $this->_db->quote($sortby_name));
        }
        if (!is_null($sortby_key)) {
            $where = sprintf('%s AND attribute_key = %s ',
                             $where,
                             $this->_db->quote($sortby_key));
        }

        $query = sprintf('SELECT datatree_id FROM %s WHERE datatree_id IN (%s) %s ORDER BY attribute_value %s',
                         $this->_params['table_attributes'],
                         implode(',', $unordered_ids),
                         $where,
                         ($direction == 1) ? 'DESC' : 'ASC');

        Horde::logMessage('SQL Query by DataTree_sql::sortByAttributes(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $ordered_ids = $this->_db->getCol($query);

        /* Make sure that some ids didn't get lost because has no such
         * attribute name/key. Append them to the end. */
        if (count($ordered_ids) != count($unordered_ids)) {
            $ordered_ids = array_unique(array_merge($ordered_ids, $unordered_ids));
        }

        return $ordered_ids;
    }

    /**
     * Returns the number of all of the available values matching the
     * given criteria. Either attribute_name or attribute_key MUST be
     * supplied, and both MAY be supplied.
     *
     * @since Horde 3.2
     *
     * @see buildAttributeQuery()
     *
     * @param array   $criteria     The array of criteria.
     * @param string  $parent       The parent node to start searching from.
     * @param boolean $allLevels    Return all levels, or just the direct
     *                              children of $parent? Defaults to all levels.
     * @param string  $restrict     Only return attributes with the same
     *                              attribute_name or attribute_id.
     * @param string  $attribute_name  The name of the attribute.
     * @param string  $attribute_key   The key value of the attribute.
     */
    function countValuesByAttributes($criteria, $parent = DATATREE_ROOT,
                                     $allLevels = true, $restrict = 'name',
                                     $key = null, $name = null)
    {
        if (!count($criteria)) {
            return PEAR::raiseError('no criteria');
        }

        $aq = $this->buildAttributeQuery($criteria,
                                         $parent,
                                         $allLevels,
                                         $restrict,
                                         DATATREE_BUILD_VALUES_COUNT);

        $aq[0] .= ' AND a.datatree_id = c.datatree_id';

        if ($key !== null) {
            $aq[0] .=  ' AND a.attribute_key = ?';
            $aq[1][] = $key;
        }

        if ($name !== null) {
            $aq[0] .=  ' AND a.attribute_name = ?';
            $aq[1][] = $name;
        }

        return $this->_db->getOne($aq[0], $aq[1]);
    }

    /**
     * Returns a list of all of the available values of the given criteria
     * Either attribute_name or attribute_key MUST be
     * supplied, and both MAY be supplied.
     *
     * @since Horde 3.2
     *
     * @see buildAttributeQuery()
     *
     * @param array   $criteria     The array of criteria.
     * @param string  $parent       The parent node to start searching from.
     * @param boolean $allLevels    Return all levels, or just the direct
     *                              children of $parent? Defaults to all levels.
     * @param string  $restrict     Only return attributes with the same
     *                              attribute_name or attribute_id.
     * @param integer $from         The object to start to fetching
     * @param integer $count        The number of objects to fetch
     * @param string  $sortby_name  Attribute name to use for sorting.
     * @param string  $sortby_key   Attribute key to use for sorting.
     * @param integer $direction    Sort direction:
     *                                0 - ascending
     *                                1 - descending
     * @param string  $attribute_name  The name of the attribute.
     * @param string  $attribute_key   The key value of the attribute.
     */
    function getValuesByAttributes($criteria, $parent = DATATREE_ROOT,
                                   $allLevels = true, $restrict = 'name', $from = 0,
                                   $count = 0, $sortby_name = null,
                                   $sortby_key = null, $direction = 0,
                                   $key = null, $name = null)
    {
        if (!count($criteria)) {
            return PEAR::raiseError('no criteria');
        }

        $aq = $this->buildAttributeQuery($criteria,
                                         $parent,
                                         $allLevels,
                                         $restrict,
                                         DATATREE_BUILD_VALUES,
                                         $sortby_name,
                                         $sortby_key,
                                         $direction);

        $aq[0] .=  ' AND a.datatree_id = c.datatree_id';

        if ($key !== null) {
            $aq[0] .=  ' AND a.attribute_key = ?';
            $aq[1][] = $key;
        }

        if ($name !== null) {
            $aq[0] .=  ' AND a.attribute_name = ?';
            $aq[1][] = $name;
        }

        if ($count) {
            $aq[0] = $this->_db->modifyLimitQuery($aq[0], $from, $count);
        }

        return $this->_db->getCol($aq[0], 0, $aq[1]);
    }

    /**
     * Returns a list of all of the available values of the given attribute
     * name/key combination. Either attribute_name or attribute_key MUST be
     * supplied, and both MAY be supplied.
     *
     * @param string  $attribute_name  The name of the attribute.
     * @param string  $attribute_key   The key value of the attribute.
     * @param string  $parent          The parent node to start searching from.
     * @param boolean $allLevels       Return all levels, or just the direct
     *                                 children of $parent? Defaults to all
     *                                 levels.
     *
     * @return array  An array of all of the available values.
     */
    function getAttributeValues($attribute_name = null, $attribute_key = null,
                                $parent = DATATREE_ROOT, $allLevels = true)
    {
        // Build the name/key filter.
        $where = '';
        if (!is_null($attribute_name)) {
            $where .= 'a.attribute_name = ' . $this->_db->quote($attribute_name);
        }
        if (!is_null($attribute_key)) {
            if ($where) {
                $where .= ' AND ';
            }
            $where .= 'a.attribute_key = ' . $this->_db->quote($attribute_key);
        }

        // Return if we have no criteria.
        if (!$where) {
            return PEAR::raiseError('no criteria');
        }

        // Add filtering by parent, and for one or all levels.
        $levelQuery = '';
        if ($parent != DATATREE_ROOT) {
            $parts = explode(':', $parent);
            $parents = '';
            $pstring = '';
            foreach ($parts as $part) {
                $pstring .= (empty($pstring) ? '' : ':') . $part;
                $pid = $this->getId($pstring);
                if (is_a($pid, 'PEAR_Error')) {
                    return $pid;
                }
                $parents .= ':' . $pid;
            }

            if ($allLevels) {
                $levelQuery = sprintf('AND (datatree_parents = %s OR datatree_parents LIKE %s)',
                                      $this->_db->quote($parents),
                                      $this->_db->quote($parents . ':%'));
            } else {
                $levelQuery = sprintf('AND datatree_parents = %s',
                                      $this->_db->quote($parents));
            }
        } elseif (!$allLevels) {
            $levelQuery = "AND datatree_parents = ''";
        }

        // Build the FROM/JOIN clauses.
        $joins = 'LEFT JOIN ' . $this->_params['table'] .
            ' c ON a.datatree_id = c.datatree_id';

        $query = sprintf('SELECT DISTINCT a.attribute_value FROM %s a %s WHERE c.group_uid = %s AND %s %s',
                         $this->_params['table_attributes'],
                         $joins,
                         $this->_db->quote($this->_params['group']),
                         $where,
                         $levelQuery);

        Horde::logMessage('SQL Query by DataTree_sql::getAttributeValues(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $rows = $this->_db->getCol($query);
        if (is_a($rows, 'PEAR_Error')) {
            Horde::logMessage($rows, __FILE__, __LINE__, PEAR_LOG_ERR);
        }

        return $rows;
    }

    /**
     * Builds an attribute query. Here is an example $criteria array:
     *
     * <code>
     * $criteria['OR'] = array(
     *     array('AND' => array(
     *         array('field' => 'name',
     *               'op'    => '=',
     *               'test'  => 'foo'),
     *         array('field' => 'key',
     *               'op'    => '=',
     *               'test'  => 'abc'))),
     *         array('AND' => array(
     *             array('field' => 'name',
     *                   'op'    => '=',
     *                   'test'  => 'bar'),
     *             array('field' => 'key',
     *                   'op'    => '=',
     *                   'test'  => 'xyz'))));
     * </code>
     *
     * This would fetch all object ids where attribute name is "foo" AND key
     * is "abc", OR "bar" AND "xyz".
     *
     * @param array   $criteria     The array of criteria.
     * @param string  $parent       The parent node to start searching from.
     * @param boolean $allLevels    Return all levels, or just the direct
     *                              children of $parent? Defaults to all levels.
     * @param string  $restrict     Only return attributes with the same
     *                              attribute_name or attribute_id.
     * @param integer $operation    Type of query to build
     * @param string  $sortby_name  Attribute name to use for sorting.
     * @param string  $sortby_key   Attribute key to use for sorting.
     * @param integer $direction    Sort direction:
     *                                0 - ascending
     *                                1 - descending
     *
     * @return array  An SQL query and a list of values suitable for binding
     *                as an array.
     */
    function buildAttributeQuery($criteria, $parent = DATATREE_ROOT,
                                 $allLevels = true, $restrict = 'name',
                                 $operation = DATATREE_BUILD_SELECT,
                                 $sortby_name = null, $sortby_key = null,
                                 $direction = 0)
    {
        if (!count($criteria)) {
            return array('', array());
        }

        /* Build the query. */
        $this->_tableCount = 1;
        $query = '';
        $values = array();
        foreach ($criteria as $key => $vals) {
            if ($key == 'OR' || $key == 'AND') {
                if (!empty($query)) {
                    $query .= ' ' . $key . ' ';
                }
                $binds = $this->_buildAttributeQuery($key, $vals);
                $query .= '(' . $binds[0] . ')';
                $values += $binds[1];
            }
        }

        // Add filtering by parent, and for one or all levels.
        $levelQuery = '';
        $levelValues = array();
        if ($parent != DATATREE_ROOT) {
            $parts = explode(':', $parent);
            $parents = '';
            $pstring = '';
            foreach ($parts as $part) {
                $pstring .= (empty($pstring) ? '' : ':') . $part;
                $pid = $this->getId($pstring);
                if (is_a($pid, 'PEAR_Error')) {
                    return $pid;
                }
                $parents .= ':' . $pid;
            }

            if ($allLevels) {
                $levelQuery = 'AND (datatree_parents = ? OR datatree_parents LIKE ?)';
                $levelValues = array($parents, $parents . ':%');
            } else {
                $levelQuery = 'AND datatree_parents = ?';
                $levelValues = array($parents);
            }
        } elseif (!$allLevels) {
            $levelQuery = "AND datatree_parents = ''";
        }

        // Build the FROM/JOIN clauses.
        $joins = array();
        $pairs = array();
        for ($i = 1; $i <= $this->_tableCount; $i++) {
            $joins[] = 'LEFT JOIN ' . $this->_params['table_attributes'] .
                ' a' . $i . ' ON a' . $i . '.datatree_id = c.datatree_id';

            if ($i != 1) {
                if ($restrict == 'name') {
                    $pairs[] = 'AND a1.attribute_name = a' . $i . '.attribute_name';
                } elseif ($restrict == 'id') {
                    $pairs[] = 'AND a1.datatree_id = a' . $i . '.datatree_id';
                }
            }
        }

        // Override sorting.
        $sort = array();
        if (!is_null($sortby_name) || !is_null($sortby_key)) {
            $order_table = 'a' . $i;
            $joins[] = 'LEFT JOIN ' . $this->_params['table_attributes'] .
                ' ' . $order_table . ' ON ' . $order_table .
                '.datatree_id = c.datatree_id';

            if (!is_null($sortby_name)) {
                $pairs[] = sprintf('AND %s.attribute_name = ? ', $order_table);
                $sort[] = $sortby_name;
            }
            if (!is_null($sortby_key)) {
                $pairs[] = sprintf('AND %s.attribute_key = ? ', $order_table);
                $sort[] = $sortby_key;
            }

            $order = sprintf('%s.attribute_value %s',
                             $order_table,
                             ($direction == 1) ? 'DESC' : 'ASC');
            $group_by = 'c.datatree_id, c.datatree_name, c.datatree_order, ' .
                $order_table . '.attribute_value';
        } else {
            $order = 'c.datatree_order, c.datatree_name, c.datatree_id';
            $group_by = 'c.datatree_id, c.datatree_name, c.datatree_order';
        }

        $joins = implode(' ', $joins);
        $pairs = implode(' ', $pairs);

        switch ($operation) {

        case DATATREE_BUILD_VALUES_COUNT:
            $what = 'COUNT(DISTINCT(a.attribute_value))';
            $from = ' ' . $this->_params['table_attributes'] . ' a, ' . $this->_params['table'];
            $tail = '';
            break;

        case DATATREE_BUILD_VALUES:
            $what = 'DISTINCT(a.attribute_value)';
            $from = ' ' . $this->_params['table_attributes'] . ' a, ' . $this->_params['table'];
            $tail = '';
            break;

        case DATATREE_BUILD_COUNT:
            $what = 'COUNT(DISTINCT c.datatree_id)';
            $from = $this->_params['table'];
            $tail = '';
            break;

        default:
            $what = 'c.datatree_id, c.datatree_name';
            $from = $this->_params['table'];
            $tail = sprintf('GROUP BY %s ORDER BY %s', $group_by, $order);
            break;
        }

        return array(sprintf('SELECT %s FROM %s c %s WHERE c.group_uid = ? AND %s %s %s %s',
                             $what,
                             $from,
                             $joins,
                             $query,
                             $levelQuery,
                             $pairs,
                             $tail),
                     array_merge(array($this->_params['group']),
                                 $values,
                                 $levelValues,
                                 $sort));
    }

    /**
     * Builds a piece of an attribute query.
     *
     * @param string $glue     The glue to join the criteria (OR/AND).
     * @param array $criteria  The array of criteria.
     * @param boolean $join    Should we join on a clean
     *                         horde_datatree_attributes table? Defaults to
     *                         false.
     *
     * @return array  An SQL fragment and a list of values suitable for binding
     *                as an array.
     */
    function _buildAttributeQuery($glue, $criteria, $join = false)
    {
        require_once 'Horde/SQL.php';

        // Initialize the clause that we're building.
        $clause = '';
        $values = array();

        // Get the table alias to use for this set of criteria.
        $alias = $this->_getAlias($join);

        foreach ($criteria as $key => $vals) {
            if (!empty($clause)) {
                $clause .= ' ' . $glue . ' ';
            }
            if (!empty($vals['OR']) || !empty($vals['AND'])) {
                $binds = $this->_buildAttributeQuery($glue, $vals);
                $clause .= '(' . $binds[0] . ')';
                $values = array_merge($values, $binds[1]);
            } elseif (!empty($vals['JOIN'])) {
                $binds = $this->_buildAttributeQuery($glue, $vals['JOIN'], true);
                $clause .= $binds[0];
                $values = array_merge($values, $binds[1]);
            } else {
                if (isset($vals['field'])) {
                    // All of the attribute_* fields are text, so make
                    // sure we send strings to the database.
                    if (is_array($vals['test'])) {
                        for ($i = 0, $iC = count($vals['test']); $i < $iC; ++$i) {
                            $vals['test'][$i] = (string)$vals['test'][$i];
                        }
                    } else {
                        $vals['test'] = (string)$vals['test'];
                    }

                    $binds = Horde_SQL::buildClause($this->_db, $alias . '.attribute_' . $vals['field'], $vals['op'], $vals['test'], true);
                    $clause .= $binds[0];
                    $values = array_merge($values, $binds[1]);
                } else {
                    $binds = $this->_buildAttributeQuery($key, $vals);
                    $clause .= $binds[0];
                    $values = array_merge($values, $binds[1]);
                }
            }
        }

        return array($clause, $values);
    }

    /**
     * Get an alias to horde_datatree_attributes, incrementing it if
     * necessary.
     *
     * @param boolean $increment  Increment the alias count? Defaults to no.
     */
    function _getAlias($increment = false)
    {
        static $seen = array();

        if ($increment && !empty($seen[$this->_tableCount])) {
            $this->_tableCount++;
        }

        $seen[$this->_tableCount] = true;
        return 'a' . $this->_tableCount;
    }

    /**
     * Update the data in an object. Does not change the object's
     * parent or name, just serialized data or attributes.
     *
     * @param DataTree $object  A DataTree object.
     */
    function updateData($object)
    {
        if (!is_a($object, 'DataTreeObject')) {
            /* Nothing to do for non objects. */
            return true;
        }

        /* Get the object id. */
        $id = $this->getId($object->getName());
        if (is_a($id, 'PEAR_Error')) {
            return $id;
        }

        /* See if we can break the object out to datatree_attributes table. */
        if (method_exists($object, '_toAttributes')) {
            /* If we can, clear out the datatree_data field to make sure it
             * doesn't get picked up by getData(). Intentionally don't check
             * for errors here in case datatree_data goes away in the
             * future. */
            $query = 'UPDATE ' . $this->_params['table'] .
                     ' SET datatree_data = ? WHERE datatree_id = ?';
            $values = array(NULL, (int)$id);

            Horde::logMessage('SQL Query by DataTree_sql::updateData(): ' . $query . ', ' . var_export($values, true), __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $this->_write_db->query($query, $values);

            /* Start a transaction. */
            $this->_write_db->autoCommit(false);

            /* Delete old attributes. */
            $query = 'DELETE FROM ' . $this->_params['table_attributes'] .
                     ' WHERE datatree_id = ?';
            $values = array((int)$id);

            Horde::logMessage('SQL Query by DataTree_sql::updateData(): ' . $query . ', ' . var_export($values, true), __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $result = $this->_write_db->query($query, $values);
            if (is_a($result, 'PEAR_Error')) {
                $this->_write_db->rollback();
                $this->_write_db->autoCommit(true);
                return $result;
            }

            /* Get the new attribute set, and insert each into the DB. If
             * anything fails in here, rollback the transaction, return the
             * relevant error, and bail out. */
            $attributes = $object->_toAttributes();
            $query = 'INSERT INTO ' . $this->_params['table_attributes'] .
                     ' (datatree_id, attribute_name, attribute_key, attribute_value)' .
                     ' VALUES (?, ?, ?, ?)';
            $statement = $this->_write_db->prepare($query);
            foreach ($attributes as $attr) {
                $values = array((int)$id,
                                $attr['name'],
                                $attr['key'],
                                String::convertCharset($attr['value'], NLS::getCharset(), $this->_params['charset']));

                Horde::logMessage('SQL Query by DataTree_sql::updateData(): ' . $query . ', ' . var_export($values, true), __FILE__, __LINE__, PEAR_LOG_DEBUG);

                $result = $this->_write_db->execute($statement, $values);
                if (is_a($result, 'PEAR_Error')) {
                    $this->_write_db->rollback();
                    $this->_write_db->autoCommit(true);
                    return $result;
                }
            }

            /* Commit the transaction, and turn autocommit back on. */
            $result = $this->_write_db->commit();
            $this->_write_db->autoCommit(true);

            return is_a($result, 'PEAR_Error') ? $result : true;
        } else {
            /* Write to the datatree_data field. */
            require_once 'Horde/Serialize.php';
            $ser = SERIALIZE_UTF7_BASIC;
            $data = Horde_Serialize::serialize($object->getData(), $ser, NLS::getCharset());

            $query = 'UPDATE ' . $this->_params['table'] .
                     ' SET datatree_data = ?, datatree_serialized = ?' .
                     ' WHERE datatree_id = ?';
            $values = array($data,
                            (int)$ser,
                            (int)$id);

            Horde::logMessage('SQL Query by DataTree_sql::updateData(): ' . $query . ', ' . var_export($values, true), __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $result = $this->_write_db->query($query, $values);

            return is_a($result, 'PEAR_Error') ? $result : true;
        }
    }

    /**
     * Attempts to open a connection to the SQL server.
     *
     * @return boolean  True.
     */
    function _init()
    {
        Horde::assertDriverConfig($this->_params, 'sql',
            array('phptype', 'charset'),
            'DataTree SQL');

        $default = array(
            'database' => '',
            'username' => '',
            'password' => '',
            'hostspec' => '',
            'table' => 'horde_datatree',
            'table_attributes' => 'horde_datatree_attributes',
        );
        $this->_params = array_merge($default, $this->_params);

        /* Connect to the SQL server using the supplied parameters. */
        require_once 'DB.php';
        $this->_write_db = DB::connect($this->_params,
                                       array('persistent' => !empty($this->_params['persistent']),
                                             'ssl' => !empty($this->_params['ssl'])));
        if (is_a($this->_write_db, 'PEAR_Error')) {
            return $this->_write_db;
        }

        // Set DB portability options.
        $portability = DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS;
        if ($this->_write_db->phptype == 'mssql') {
            $portability |= DB_PORTABILITY_RTRIM;
        }
        $this->_write_db->setOption('portability', $portability);

        /* Check if we need to set up the read DB connection
         * seperately. */
        if (!empty($this->_params['splitread'])) {
            $params = array_merge($this->_params, $this->_params['read']);
            $this->_db = DB::connect($params,
                                     array('persistent' => !empty($params['persistent']),
                                           'ssl' => !empty($params['ssl'])));
            if (is_a($this->_db, 'PEAR_Error')) {
                return $this->_db;
            }

            // Set DB portability options
            $portability = DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS;
            if ($this->_db->phptype == 'mssql') {
                $portability |= DB_PORTABILITY_RTRIM;
            }
            $this->_db->setOption('portability', $portability);
        } else {
            /* Default to the same DB handle for reads. */
            $this->_db = $this->_write_db;
        }

        return true;
    }

}
