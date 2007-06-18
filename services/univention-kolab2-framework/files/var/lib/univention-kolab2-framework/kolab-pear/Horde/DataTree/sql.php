<?php
/**
 * The DataTree_sql:: class provides an SQL implementation of the
 * Horde DataTree system.
 *
 * Required values for $params:
 *      'phptype'        The database type (ie. 'pgsql', 'mysql, etc.).
 *      'hostspec'       The hostname of the database server.
 *      'protocol'       The communication protocol ('tcp', 'unix', etc.).
 *      'username'       The username with which to connect to the database.
 *      'password'       The password associated with 'username'.
 *      'database'       The name of the database.
 *      'charset'        The charset used by the database.
 *
 * Optional values:
 *      'table'          The name of the data table in 'database'.
 *                       Defaults to 'horde_datatree'.
 *
 * The table structure for the DataTree system is in
 * horde/scripts/db/datatree.sql.
 *
 * $Horde: framework/DataTree/DataTree/sql.php,v 1.122 2004/05/06 15:48:45 chuck Exp $
 *
 * Copyright 1999-2004 Stephane Huther <shuther@bigfoot.com>
 * Copyright 2001-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If
 * you did not receive this file, see
 * http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Stephane Huther <shuther@bigfoot.com>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.1
 * @package Horde_DataTree
 */
class DataTree_sql extends DataTree {

    /**
     * Handle for the current database connection.
     * @var resource $_db
     */
    var $_db;

    /**
     * Boolean indicating whether or not we're connected to the SQL server.
     * @var boolean $_connected
     */
    var $_connected = false;

    /**
     * The number of copies of the horde_datatree_attributes table
     * that we need to join on in the current query.
     * @var integer $_tableCount
     */
    var $_tableCount = 1;

    /**
     * Constructs a new SQL DataTree object.
     *
     * @param array $params  A hash containing connection parameters.
     */
    function DataTree_sql($params)
    {
        parent::DataTree($params);
        $this->_connect();
    }

    /**
     * Does the current backend have persistent storage?
     *
     * @return boolean  True if there is persistent storage, false if not.
     */
    function isPersistent()
    {
        return true;
    }

    /**
     * Load (a subset of) the datatree into the $_data array.
     *
     * @access private
     *
     * @param optional string  $root    Which portion of the tree to
     *                                  load. Defaults to all of it.
     * @param optional boolean $reload  Re-load already loaded values?
     *
     * @return mixed  True on success or a PEAR_Error on failure.
     */
    function _load($root = '-1', $reload = false)
    {
        /* Do NOT use DataTree::exists() here; that would cause an
           infinite loop. */
        if (!$reload &&
            (in_array($root, $this->_nameMap) ||
             (count($this->_data) > 0 && $root == '-1'))) {
            return true;
        }
        if (!empty($root) && $root != '-1') {
            if (strstr($root, ':')) {
                $parts = explode(':', $root);
                $root = array_pop($parts);
            }
            $root = (string)$root;

            $query = sprintf('SELECT datatree_id, datatree_parents FROM %s' .
                             ' WHERE datatree_name = %s AND group_uid = %s ORDER BY datatree_id',
                             $this->_params['table'],
                             $this->_db->quote($root),
                             $this->_db->quote($this->_params['group']));

            Horde::logMessage('SQL Query by DataTree_sql::_load(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $root = $this->_db->getAssoc($query);
            if (is_a($root, 'PEAR_Error') || count($root) == 0) {
                return $root;
            }

            $where = '';
            $first_time = true;
            foreach ($root as $object_id => $object_parents) {
                $pstring = $object_parents . ':' . $object_id . ':%';
                $pquery = '';
                if (!empty($object_parents)) {
                    $ids = substr($object_parents, 1);
                    $pquery = ' OR datatree_id IN (' . str_replace(':', ', ', $ids) . ')';
                }
                $pquery .= ' OR datatree_parents = ' . $this->_db->quote(substr($pstring, 0, -2));

                if (!$first_time) {
                    $where .= ' OR ';
                }
                $where .= sprintf('datatree_parents LIKE %s OR datatree_id = %s%s',
                                   $this->_db->quote($pstring),
                                   $object_id,
                                   $pquery);

                $first_time = false;
            }

            $query = sprintf('SELECT datatree_id, datatree_name, datatree_parents, datatree_order FROM %s' .
                             ' WHERE (%s)'.
                             ' AND group_uid = %s',
                             $this->_params['table'],
                             $where,
                             $this->_db->quote($this->_params['group']));
        } else {
            $query = sprintf('SELECT datatree_id, datatree_name, datatree_parents, datatree_order FROM %s' .
                             ' WHERE group_uid = %s',
                             $this->_params['table'],
                             $this->_db->quote($this->_params['group']));
        }

        Horde::logMessage('SQL Query by DataTree_sql::_load(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $data = $this->_db->getAll($query);
        if (is_a($data, 'PEAR_Error')) {
            return $data;
        }

        return $this->set(DATATREE_FORMAT_FETCH, $data, $this->_params['charset']);
    }

    /**
     * Load a set of objects identified by their unique IDs, and their
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
            $cids = array($cids);
        }

        /* Bail out now if there's nothing to load. */
        if (!count($cids)) {
            return true;
        }

        /* Don't load any that are already loaded. Also, make sure that
           everything in the $ids array that we are building is an integer. */
        $ids = array();
        foreach ($cids as $cid) {
            /* Do NOT use DataTree::exists() here; that would cause an
               infinite loop. */
            if (!isset($this->_data[$cid])) {
                $ids[] = (int)$cid;
            }
        }

        /* If there are none left to load, return. */
        if (!count($ids)) {
            return true;
        }

        $query = sprintf('SELECT datatree_id, datatree_parents FROM %s' .
                         ' WHERE datatree_id IN (%s) AND group_uid = %s' .
                         ' ORDER BY datatree_id',
                         $this->_params['table'],
                         implode(', ', $ids),
                         $this->_db->quote($this->_params['group']));
        $parents = $this->_db->getAssoc($query);
        if (is_a($parents, 'PEAR_Error')) {
            return $parents;
        }

        $pquery = '';
        $pids = array();
        foreach ($parents as $cid => $parent) {
            /* Add each object id in $cids to the list we'll load. */
            $pids[] = (int)$cid;

            /* Load the parents of each of these. */
            $pquery .= ' OR datatree_parents = ' . $this->_db->quote($parent . ':' . $cid);

            /* If this is a non-top-level object, load siblings too. */
            if (!empty($parent)) {
                /* Strip off the beginning ':', explode and add to the mix. */
                $pids = array_merge($pids, explode(':', substr($parent, 1)));
            }
        }
        $pids = array_unique($pids);

        /* If $pids is empty, we have nothing to load. */
        if (!count($pids)) {
            return true;
        }

        $query = sprintf('SELECT datatree_id, datatree_name, datatree_parents, datatree_order FROM %s' .
                         ' WHERE (datatree_id IN (%s)%s)'.
                         ' AND group_uid = %s ORDER BY datatree_id',
                         $this->_params['table'],
                         implode(', ', $pids),
                         $pquery,
                         $this->_db->quote($this->_params['group']));

        Horde::logMessage('SQL Query by DataTree_sql::_loadById(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $data = $this->_db->getAll($query);
        if (is_a($data, 'PEAR_Error')) {
            return $data;
        }

        return $this->set(DATATREE_FORMAT_FETCH, $data, $this->_params['charset']);
    }

    /**
     * Add an object.
     *
     * @param mixed $object              The object to add (string or
     *                                   DataTreeObject).
     * @param optional bool $id_as_name  True or false to indicate if object
     *                                   ID is to be used as object name.
     *                                   Used in situations where there is no
     *                                   available unique input for object
     *                                   name. Defaults to false.
     */
    function add($object, $id_as_name = false)
    {
        $this->_connect();

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
        $id = $this->_db->nextId($this->_params['table']);
        if (is_a($id, 'PEAR_Error')) {
            Horde::logMessage($id, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $id;
        }

        if (strstr($fullname, ':')) {
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
            $pid = -1;
        }

        if (parent::exists($fullname)) {
            return PEAR::raiseError(_("Already exists"));
        }

        $query = sprintf('INSERT INTO %s (datatree_id, group_uid, datatree_name, datatree_order, datatree_data, user_uid, datatree_serialized, datatree_parents)' .
                         ' VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                         $this->_params['table'],
                         (int)$id,
                         $this->_db->quote($this->_params['group']),
                         $this->_db->quote(String::convertCharset($name, NLS::getCharset(), $this->_params['charset'])),
                         is_null($order) ? 'NULL' : (int)$order,
                         $this->_db->quote($data),
                         $this->_db->quote((string)Auth::getAuth()),
                         (int)$ser,
                         $this->_db->quote($parents));

        Horde::logMessage('SQL Query by DataTree_sql::add(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $result = $this->_db->query($query);
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
     * Change order of the children of an object.
     *
     * @param string $parents  The parent id string path.
     * @param mixed  $order    A specific new order position or an array
     *                         containing the new positions for the given
     *                         $parents object.
     * @param integer $cid     If provided indicates insertion of a new child
     *                         to the object, and will be used to avoid
     *                         incrementing it when shifting up all other
     *                         children's order. If not provided indicates
     *                         deletion, hence shift all other positions down
     *                         one.
     */
    function reorder($parents, $order = null, $cid = null)
    {
        if (!$parents) {
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
                             $this->_db->quote($this->_params['group']),
                             $this->_db->quote($parents),
                             is_null($order) ? 'NULL' : (int)$order) . $pquery;

            Horde::logMessage('SQL Query by DataTree_sql::reorder(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $result = $this->_db->query($query);

        } elseif (is_array($order)) {
            /* Multi update. */
            $query = sprintf('SELECT COUNT(datatree_id) FROM %s WHERE group_uid = %s AND datatree_parents = %s GROUP BY datatree_parents',
                             $this->_params['table'],
                             $this->_db->quote($this->_params['group']),
                             $this->_db->quote($parents));

            Horde::logMessage('SQL Query by DataTree_sql::reorder(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);

            $result = $this->_db->getOne($query);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            } elseif (count($order) != $result) {
                return PEAR::raiseError(_("Cannot reorder, number of entries supplied for reorder does not match number stored."));
            }

            $o_key = 0;
            foreach ($order as $o_cid) {
                $query = sprintf('UPDATE %s SET datatree_order = %s WHERE datatree_id = %s',
                                 $this->_params['table'],
                                 (int)$o_key,
                                 is_null($o_cid) ? 'NULL' : (int)$o_cid);

                Horde::logMessage('SQL Query by DataTree_sql::reorder(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);

                $result = $this->_db->query($query);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }

                $o_key++;
            }

            $pid = $this->getId($parents);

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
        $query = sprintf('UPDATE %s SET datatree_order = %s WHERE datatree_id = %s',
                         $this->_params['table'],
                         is_null($order) ? 'NULL' : (int)$order,
                         (int)$id);

        Horde::logMessage('SQL Query by DataTree_sql::setOrder(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);

        return $this->_db->query($query);
    }

    /**
     * Remove one or more objects.
     *
     * @param array $ids  The objects to remove.
     */
    function removeById($ids)
    {
    }

    /**
     * Remove an object.
     *
     * @param mixed $object            The object to remove.
     * @param optional boolean $force  Force to remove every child?
     */
    function remove($object, $force = false)
    {
        $this->_connect();

        $id = $this->getId($object);
        $order = $this->getOrder($object);

        $query = sprintf('SELECT datatree_id FROM %s ' .
                         ' WHERE group_uid = %s AND datatree_parents LIKE %s' .
                         ' ORDER BY datatree_id',
                         $this->_params['table'],
                         $this->_db->quote($this->_params['group']),
                         $this->_db->quote('%:' . (int)$id . ''));

        Horde::logMessage('SQL Query by DataTree_sql::remove(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $children = $this->_db->getAll($query, DB_FETCHMODE_ASSOC);

        if (count($children)) {
            if ($force) {
                foreach ($children as $child) {
                    $cat = $this->getName($child['datatree_id']);
                    $result = !$this->remove($cat,true);
                }
            } else {
                return PEAR::raiseError(sprintf(_("Cannot remove; children exist (%s)"), count($children)));
            }
        }

        /* Remove attributes for this object. */
        $query = sprintf('DELETE FROM %s WHERE datatree_id = %s',
                         $this->_params['table_attributes'],
                         (int)$id);

        Horde::logMessage('SQL Query by DataTree_sql::remove(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $result = $this->_db->query($query);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $query = sprintf('DELETE FROM %s WHERE datatree_id = %s',
                         $this->_params['table'],
                         (int)$id);

        Horde::logMessage('SQL Query by DataTree_sql::remove(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $result = $this->_db->query($query);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $parents = $this->getParentIdString($object);
        $reorder = $this->reorder($parents, $order);
        if (is_a($reorder, 'PEAR_Error')) {
            return $reorder;
        }
        return is_a(parent::remove($object), 'PEAR_Error') ? $id : true;
    }

    /**
     * Move an object to a new parent.
     *
     * @param mixed  $object     The object to move.
     * @param string $newparent  The new parent object. Defaults to the root.
     */
    function move($object, $newparent = null)
    {
        $this->_connect();

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
        $query = sprintf('SELECT datatree_id, datatree_parents FROM %s' .
                         ' WHERE datatree_parents = %s OR datatree_parents LIKE %s OR datatree_id = %s',
                         $this->_params['table'],
                         $this->_db->quote($old_parent_path . ':' . $id),
                         $this->_db->quote($old_parent_path . ':' . $id . ':%'),
                         (int)$id);

        Horde::logMessage('SQL Query by DataTree_sql::move(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $rowset = $this->_db->query($query);
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
                             $this->_db->quote($ppath),
                             (int)$row['datatree_id']);

            Horde::logMessage('SQL Query by DataTree_sql::move(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $result = $this->_db->query($query);
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
        $this->_connect();

        /* Do the cache renaming first */
        $result = parent::rename($old_object, $new_object_name);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        /* Get the object id and set up the sql query. */
        $id = $this->getId($old_object);
        $query = sprintf('UPDATE %s SET datatree_name = %s' .
                         ' WHERE datatree_id = %s',
                         $this->_params['table'],
                         $this->_db->quote(String::convertCharset($new_object_name, NLS::getCharset(), $this->_params['charset'])),
                         (int)$id);

        Horde::logMessage('SQL Query by DataTree_sql::rename(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $result = $this->_db->query($query);

        return is_a($result, 'PEAR_Error') ? $result : true;
    }

    /**
     * Retrieve data for an object from the datatree_data field.
     *
     * @param integer $cid  The object id to fetch, or an array of object ids.
     */
    function getData($cid)
    {
        require_once 'Horde/Serialize.php';

        $this->_connect();

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
                $data[$id] = Horde_Serialize::unserialize($row[0], $row[1], NLS::getCharset());
                /* Convert old data to the new format. */
                if ($row[1] == SERIALIZE_BASIC) {
                    $data[$id] = String::convertCharset($data[$id], NLS::getCharset(true));
                }

                $data[$id] = (is_null($data[$id]) || !is_array($data[$id])) ? array() : $data[$id];
            }

            return $data;
        } else {
            $query = sprintf('SELECT datatree_data, datatree_serialized FROM %s WHERE datatree_id = %s',
                             $this->_params['table'],
                             (int)$cid);

            Horde::logMessage('SQL Query by DataTree_sql::getData(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $row = $this->_db->getRow($query, DB_FETCHMODE_ASSOC);

            $data = Horde_Serialize::unserialize($row['datatree_data'], $row['datatree_serialized'], NLS::getCharset());
            /* Convert old data to the new format. */
            if ($row['datatree_serialized'] == SERIALIZE_BASIC) {
                $data = String::convertCharset($data, NLS::getCharset(true));
            }
            return (is_null($data) || !is_array($data)) ? array() : $data;
        }
    }

    /**
     * Retrieve data for an object from the horde_datatree_attributes
     * table.
     *
     * @param integer | array $cid  The object id to fetch,
     *                              or an array of object ids.
     *
     * @return array  A hash of attributes, or a multi-level hash
     *                of object ids => their attributes.
     */
    function getAttributes($cid)
    {
        $this->_connect();

        if (is_array($cid)) {
            $query = sprintf('SELECT datatree_id, attribute_name as name, attribute_key as "key", attribute_value as value FROM %s WHERE datatree_id IN (%s)',
                             $this->_params['table_attributes'],
                             implode(', ', $cid));

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
            $query = sprintf('SELECT attribute_name as name, attribute_key as "key", attribute_value as value FROM %s WHERE datatree_id = %s',
                             $this->_params['table_attributes'],
                             (int)$cid);

            Horde::logMessage('SQL Query by DataTree_sql::getAttributes(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $rows = $this->_db->getAll($query, DB_FETCHMODE_ASSOC);
            for ($i = 0; $i < count($rows); $i++) {
                $rows[$i]['value'] = String::convertCharset($rows[$i]['value'], $this->_params['charset'], NLS::getCharset());
            }
            return $rows;
        }
    }

    /**
     * Return a set of object ids based on a set of attribute criteria.
     *
     * @param array $criteria               The array of criteria. Example:
     *                                      $criteria['OR'] = array(
     *                                          array('AND' => array(
     *                                              array('field' => 'name',
     *                                                    'op'    => '=',
     *                                                    'test'  => 'foo'),
     *                                              array('field' => 'key',
     *                                                    'op'    => '=',
     *                                                    'test'  => 'abc'))),
     *                                          array('AND' => array(
     *                                              array('field' => 'name',
     *                                                    'op'    => '=',
     *                                                    'test'  => 'bar'),
     *                                              array('field' => 'key',
     *                                                    'op'    => '=',
     *                                                    'test'  => 'xyz'))));
     *                                      This would fetch all object ids
     *                                      where attribute name is "foo" AND
     *                                      key is "abc", OR "bar" AND "xyz".
     * @param optional string $parent       The parent share to start searching
     *                                      from.
     * @param optional bool $allLevels      Return all levels, or just the
     *                                      direct children of $parent?
     *                                      Defaults to all levels.
     * @param optional bool $restrictNames  Only return attributes with the
     *                                      same attribute_name.
     */
    function getByAttributes($criteria, $parent = '-1', $allLevels = true, $restrictNames = true)
    {
        if (!count($criteria)) {
            return array();
        }

        /* Build the query. */
        $this->_tableCount = 1;
        $query = '';
        foreach ($criteria as $key => $vals) {
            if ($key == 'OR' || $key == 'AND') {
                if (!empty($query)) {
                    $query .= ' ' . $key . ' ';
                }
                $query .= '(' . $this->_buildAttributeQuery($key, $vals) . ')';
            }
        }

        // Add filtering by parent, and for one or all levels.
        $levelQuery = '';
        if ($parent != '-1') {
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
                $levelQuery = sprintf('AND datatree_parents = %s', $this->_db->quote($parents));
            }
        } elseif (!$allLevels) {
            $levelQuery = "AND datatree_parents = ''";
        }

        // Build the FROM/JOIN clauses.
        $joins = array();
        $pairs = array();
        for ($i = 1; $i <= $this->_tableCount; $i++) {
            $joins[] = 'LEFT JOIN ' . $this->_params['table_attributes'] . ' a' . $i . ' ON a' . $i . '.datatree_id = c.datatree_id';
            if ($restrictNames) {
                $pairs[] = 'AND a1.attribute_name = a' . $i . '.attribute_name';
            }
        }
        $joins = implode(' ', $joins);
        $pairs = implode(' ', $pairs);

        $query = sprintf('SELECT a1.datatree_id, c.datatree_name FROM %s c %s' .
                         ' WHERE c.group_uid = %s AND %s %s %s ORDER BY c.datatree_order, c.datatree_name, c.datatree_id',
                         $this->_params['table'],
                         $joins,
                         $this->_db->quote($this->_params['group']),
                         $query,
                         $levelQuery,
                         $pairs);

        Horde::logMessage('SQL Query by DataTree_sql::getByAttributes(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);

        return $this->_db->getAssoc($query);
    }

    /**
     * Build a piece of an attribute query.
     *
     * @param string  $glue      The glue to join the criteria (OR/AND).
     * @param array   $criteria  The array of criteria.
     * @param boolean $join      Should we join on a clean horde_datatree_attributes
     *                           table? Defaults to false.
     *
     * @return string  An SQL fragment.
     */
    function _buildAttributeQuery($glue, $criteria, $join = false)
    {
        require_once 'Horde/SQL.php';

        // Initialize the clause that we're building.
        $clause = '';

        // Get the table alias to use for this set of criteria.
        if ($join) {
            $alias = $this->_getAlias(true);
        } else {
            $alias = $this->_getAlias();
        }

        foreach ($criteria as $key => $vals) {
            if (!empty($vals['OR']) || !empty($vals['AND'])) {
                if (!empty($clause)) {
                    $clause .= ' ' . $glue . ' ';
                }
                $clause .= '(' . $this->_buildAttributeQuery($glue, $vals) . ')';
            } elseif (!empty($vals['JOIN'])) {
                if (!empty($clause)) {
                    $clause .= ' ' . $glue . ' ';
                }
                $clause .= $this->_buildAttributeQuery($glue, $vals['JOIN'], true);
            } else {
                if (isset($vals['field'])) {
                    if (!empty($clause)) {
                        $clause .= ' ' . $glue . ' ';
                    }
                    $clause .= Horde_SQL::buildClause($this->_db, $alias . '.attribute_' . $vals['field'], $vals['op'], $vals['test']);
                } else {
                    foreach ($vals as $test) {
                        if (!empty($clause)) {
                            $clause .= ' ' . $key . ' ';
                        }
                        $clause .= Horde_SQL::buildClause($this->_db, $alias . '.attribute_' . $test['field'], $test['op'], $test['test']);
                    }
                }
            }
        }

        return $clause;
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
     * @param string $object  The object.
     */
    function updateData($object)
    {
        $this->_connect();

        if (!is_a($object, 'DataTreeObject')) {
            /* Nothing to do for non objects. */
            return true;
        }

        /* Get the object id. */
        $id = $this->getId($object->getName());

        /* See if we can break the object out to datatree_attributes table. */
        if (method_exists($object, '_toAttributes')) {
            /* If we can, clear out the datatree_data field to make
             * sure it doesn't get picked up by
             * getData(). Intentionally don't check for errors here in
             * case datatree_data goes away in the future. */
            $query = sprintf('UPDATE %s SET datatree_data = NULL WHERE datatree_id = %s',
                             $this->_params['table'],
                             (int)$id);

            Horde::logMessage('SQL Query by DataTree_sql::updateData(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $this->_db->query($query);

            /* Start a transaction. */
            $this->_db->autoCommit(false);

            /* Delete old attributes. */
            $query = sprintf('DELETE FROM %s WHERE datatree_id = %s',
                             $this->_params['table_attributes'],
                             (int)$id);

            Horde::logMessage('SQL Query by DataTree_sql::updateData(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $result = $this->_db->query($query);
            if (is_a($result, 'PEAR_Error')) {
                $this->_db->rollback();
                $this->_db->autoCommit(true);
                return $result;
            }

            /* Get the new attribute set, and insert each into the
             * DB. If anything fails in here, rollback the
             * transaction, return the relevant error, and bail
             * out. */
            $attributes = $object->_toAttributes();
            foreach ($attributes as $attr) {
                $query = sprintf('INSERT INTO %s (datatree_id, attribute_name, attribute_key, attribute_value) VALUES (%s, %s, %s, %s)',
                                 $this->_params['table_attributes'],
                                 (int)$id,
                                 $this->_db->quote($attr['name']),
                                 $this->_db->quote($attr['key']),
                                 $this->_db->quote(String::convertCharset($attr['value'], NLS::getCharset(), $this->_params['charset'])));

                Horde::logMessage('SQL Query by DataTree_sql::updateData(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
                $result = $this->_db->query($query);
                if (is_a($result, 'PEAR_Error')) {
                    $this->_db->rollback();
                    $this->_db->autoCommit(true);
                    return $result;
                }
            }

            /* Commit the transaction, and turn autocommit back on. */
            $result = $this->_db->commit();
            $this->_db->autoCommit(true);

            return is_a($result, 'PEAR_Error') ? $result : true;
        } else {
            /* Write to the datatree_data field. */
            require_once 'Horde/Serialize.php';
            $ser = SERIALIZE_UTF7_BASIC;
            $data = Horde_Serialize::serialize($object->getData(), $ser, NLS::getCharset());

            $query = sprintf('UPDATE %s SET datatree_data = %s, datatree_serialized = %s' .
                             ' WHERE datatree_id = %s',
                             $this->_params['table'],
                             $this->_db->quote($data),
                             (int)$ser,
                             (int)$id);

            Horde::logMessage('SQL Query by DataTree_sql::updateData(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $result = $this->_db->query($query);

            return is_a($result, 'PEAR_Error') ? $result : true;
        }
    }

    /**
     * Attempts to open a connection to the SQL server.
     *
     * @return boolean  True.
     */
    function _connect()
    {
        if (!$this->_connected) {
            Horde::assertDriverConfig($this->_params, 'storage',
                array('phptype', 'hostspec', 'username', 'database', 'charset'),
                'DataTree SQL');

            if (!isset($this->_params['password'])) {
                $this->_params['password'] = '';
            }

            if (!isset($this->_params['table'])) {
                $this->_params['table'] = 'horde_datatree';
            }

            if (!isset($this->_params['table_attributes'])) {
                $this->_params['table_attributes'] = 'horde_datatree_attributes';
            }

            /* Connect to the SQL server using the supplied
             * parameters. */
            require_once 'DB.php';
            $this->_db = &DB::connect($this->_params,
                                      array('persistent' => !empty($this->_params['persistent'])));
            if (is_a($this->_db, 'PEAR_Error')) {
                Horde::fatal($this->_db, __FILE__, __LINE__);
            }

            /* Enable the "portability" option. */
            $this->_db->setOption('optimize', 'portability');
            $this->_connected = true;
        }

        return true;
    }

}
