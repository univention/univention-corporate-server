<?php
/**
 * The DataTree_null:: class provides a dummy implementation of the
 * DataTree:: API; no data will last beyond a single page request.
 *
 * $Horde: framework/DataTree/DataTree/null.php,v 1.15.2.8 2009-01-06 15:23:02 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Stephane Huther <shuther1@free.fr>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 3.0
 * @package Horde_DataTree
 */
class DataTree_null extends DataTree {

    /**
     * Cache of attributes for any objects created during this page request.
     *
     * @var array
     */
    var $_attributeCache = array();

    /**
     * Cache of data for any objects created during this page request.
     *
     * @var array
     */
    var $_dataCache = array();

    /**
     * Load (a subset of) the datatree into the $_data array. Part of the
     * DataTree API that must be overridden by subclasses.
     *
     * @param string  $root    Which portion of the tree to load. Defaults to
     *                         all of it.
     * @param boolean $reload  Re-load already loaded values?
     *
     * @return mixed  True on success or a PEAR_Error on failure.
     *
     * @access private
     */
    function _load($root = null, $reload = false)
    {
    }

    /**
     * Load a specific object identified by its unique ID ($id), and
     * its parents, into the $_data array.
     *
     * @param integer $cid  The unique ID of the object to load.
     *
     * @return mixed  True on success or a PEAR_Error on failure.
     *
     * @access private
     */
    function _loadById($cid)
    {
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
        return false;
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
        return null;
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
        return null;
    }

    /**
     * Get a tree sorted by the specified attribute name and/or key.
     *
     * @since Horde 3.1
     *
     * @param string  $root       Which portion of the tree to sort.
     *                            Defaults to all of it.
     * @param boolean $loadTree   Sort the tree starting at $root, or just the
     *                            requested level and direct parents?
     *                            Defaults to single level.
     * @param array $sortby_name  Attribute name to use for sorting.
     * @param array $sortby_key   Attribute key to use for sorting.
     * @param array $direction    Sort direction:
     *                              0 - ascending
     *                              1 - descending
     *
     * @return array TODO
     */
    function getSortedTree($root, $loadTree = false, $sortby_name = null, $sortby_key = null, $direction = 0)
    {
        return array();
    }

    /**
     * Add an object. Part of the DataTree API that must be
     * overridden by subclasses.
     *
     * @param mixed $fullname  The object to add (string or DataTreeObject).
     */
    function add($object)
    {
        if (is_a($object, 'DataTreeObject')) {
            $fullname = $object->getName();
            $order = $object->order;
        } else {
            $fullname = $object;
            $order = null;
        }

        $id = md5(mt_rand());
        if (strpos($fullname, ':') !== false) {
            $parts = explode(':', $fullname);
            $name = array_pop($parts);
            $parent = implode(':', $parts);
            $pid = $this->getId($parent);
            if (is_a($pid, 'PEAR_Error')) {
                $this->add($parent);
            }
        } else {
            $pid = DATATREE_ROOT;
        }

        if (parent::exists($fullname)) {
            return PEAR::raiseError('Already exists');
        }

        $added = parent::_add($fullname, $id, $pid, $order);
        if (is_a($added, 'PEAR_Error')) {
            return $added;
        }
        return $this->updateData($object);
    }

    /**
     * Change order of the children of an object.
     *
     * @param string $parents  The parent id string path.
     * @param mixed $order     A specific new order position or an array
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
        if (is_array($order) && !empty($order)) {
            // Multi update.
            $this->_reorder($pid, $order);
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
    }

    /**
     * Removes an object.
     *
     * @param mixed   $object  The object to remove.
     * @param boolean $force   Force removal of every child object?
     */
    function remove($object, $force = false)
    {
    }

    /**
     * Remove one or more objects by id. This function does *not* do
     * the validation, reordering, etc. that remove() does. If you
     * need to check for children, re-do ordering, etc., then you must
     * remove() objects one-by-one. This is for code that knows it's
     * dealing with single (non-parented) objects and needs to delete
     * a batch of them quickly.
     *
     * @param array $ids  The objects to remove.
     */
    function removeByIds($ids)
    {
    }

    /**
     * Remove one or more objects by name. This function does *not* do
     * the validation, reordering, etc. that remove() does. If you
     * need to check for children, re-do ordering, etc., then you must
     * remove() objects one-by-one. This is for code that knows it's
     * dealing with single (non-parented) objects and needs to delete
     * a batch of them quickly.
     *
     * @param array $names  The objects to remove.
     */
    function removeByNames($names)
    {
    }

    /**
     * Move an object to a new parent.
     *
     * @param mixed  $object     The object to move.
     * @param string $newparent  The new parent object. Defaults to the root.
     */
    function move($object, $newparent = null)
    {
    }

    /**
     * Change an object's name.
     *
     * @param mixed  $old_object       The old object.
     * @param string $new_object_name  The new object name.
     */
    function rename($old_object, $new_object_name)
    {
    }

    /**
     * Retrieve data for an object from the datatree_data field.
     *
     * @param integer $cid  The object id to fetch, or an array of object ids.
     */
    function getData($cid)
    {
        return isset($this->_dataCache[$cid]) ?
            $this->_dataCache[$cid] :
            array();
    }

    /**
     * Retrieve data for an object.
     *
     * @param integer $cid  The object id to fetch.
     */
    function getAttributes($cid)
    {
        if (is_array($cid)) {
            $data = array();
            foreach ($cid as $id) {
                if (isset($this->_attributeCache[$id])) {
                    $data[$id] = $this->_attributeCache[$id];
                }
            }

            return $data;
        } else {
            return isset($this->_attributeCache[$cid]) ?
                $this->_attributeCache[$cid] :
                array();
        }
    }

    /**
     * Returns the number of objects matching a set of attribute
     * criteria.
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
    function countByAttributes($criteria, $parent = DATATREE_ROOT, $allLevels = true, $restrict = 'name')
    {
        if (!count($criteria)) {
            return 0;
        }

        return count($this->_attributeCache);
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
    function getByAttributes($criteria, $parent = DATATREE_ROOT, $allLevels = true, $restrict = 'name', $from = 0, $count = 0,
                             $sortby_name = null, $sortby_key = null, $direction = 0)
    {
        if (!count($criteria)) {
            return PEAR::raiseError('no criteria');
        }

        $cids = array();
        foreach (array_keys($this->_attributeCache) as $cid) {
            $cids[$cid] = null;
        }
        return $cids;
    }

    /**
     * Sorts IDs by attribute values. IDs without attributes will be
     * added to the end of the sorted list.
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
    function sortByAttributes($unordered_ids, $sortby_name = null, $sortby_key = null, $direction = 0)
    {
        return $unordered_ids;
    }

    /**
     * Returns a list of all of the available values of the given
     * attribute name/key combination. Either attribute_name or
     * attribute_key MUST be supplied, and both MAY be supplied.
     *
     * @param string $attribute_name  The name of the attribute.
     * @param string $attribute_key   The key value of the attribute.
     * @param string $parent          The parent node to start searching from.
     * @param boolean $allLevels      Return all levels, or just the direct
     *                                children of $parent?
     *
     * @return array  An array of all of the available values.
     */
    function getAttributeValues($attribute_name = null, $attribute_key = null, $parent = DATATREE_ROOT, $allLevels = true)
    {
        return array();
    }

    /**
     * Update the data in an object. Does not change the object's
     * parent or name, just serialized data.
     *
     * @param string $object  The object.
     */
    function updateData($object)
    {
        if (!is_a($object, 'DataTreeObject')) {
            return true;
        }

        $cid = $this->getId($object->getName());
        if (is_a($cid, 'PEAR_Error')) {
            return $cid;
        }

        // We handle data differently if we can map it to
        // attributes.
        if (method_exists($object, '_toAttributes')) {
            $this->_attributeCache[$cid] = $object->_toAttributes();
        } else {
            $this->_dataCache[$cid] = $object->getData();
        }

        return true;
    }

    /**
     * Init the object.
     *
     * @return boolean  True.
     */
    function _init()
    {
       return true;
    }

}
