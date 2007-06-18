<?php
/**
 * The DataTree_null:: class provides a dummy implementation of the
 * DataTree:: API; no data will last beyond a single page request.
 *
 * $Horde: framework/DataTree/DataTree/null.php,v 1.13 2004/04/08 19:35:36 chuck Exp $
 *
 * Copyright 1999, 2000, 2001, 2002 Stephane Huther <shuther@bigfoot.com>
 * Copyright 2001, 2002 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_DataTree
 */
class DataTree_null extends DataTree {

    /**
     * Cache of attributes for any objects created during this page
     * request.
     * @var array $_attributeCache
     */
    var $_attributeCache = array();

    /**
     * Cache of data for any objects created during this page
     * request.
     * @var array $_dataCache
     */
    var $_dataCache = array();

    /**
     * Load (a subset of) the datatree into the $_data
     * array. Part of the DataTree API that must be overridden by
     * subclasses.
     *
     * @param optional string  $root    Which portion of the
     *                                  tree to load. Defaults to all of it.
     * @param optional boolean $reload  Re-load already loaded values?
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
        if (strstr($fullname, ':')) {
            $parts = explode(':', $fullname);
            $name = array_pop($parts);
            $parent = implode(':', $parts);
            $pid = $this->getId($parent);
            if (is_a($pid, 'PEAR_Error')) {
                $this->add($parent);
            }
        } else {
            $pid = '-1';
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
     * Return a set of object ids based on a set of attribute
     * criteria.
     *
     * @param array $criteria  The array of criteria.
     */
    function getByAttributes($criteria)
    {
        if (!count($criteria)) {
            return array();
        }

        return array_keys($this->_attributeCache);
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
     * Change order of the children of an object.
     *
     * @param string $parents The parent id string path.
     * @param mixed  $order   A specific new order position or an
     *                        array containing the new positions
     *                        for the given $parents object.
     * @param int    $cid     If provided indicates insertion of
     *                        a new child to the object, and
     *                        will be used to avoid incrementing
     *                        it when shifting up all other
     *                        children's order. If not provided
     *                        indicates deletion, hence shift all
     *                        other positions down one.
     */
    function reorder($parents, $order = null, $cid = null)
    {
        if (is_array($order) && !empty($order)) {
            // Multi update.
            $this->_reorder($pid, $order);
        }
    }

}
