<?php

// Available import/export formats.
/** @constant DATATREE_FORMAT_TREE List every object in an array,
    similar to PEAR/html/menu.php */
define('DATATREE_FORMAT_TREE', 1);

/** @constant DATATREE_FORMAT_FETCH List every object in an array
    child-parent. Comes from driver pear/sql */
define('DATATREE_FORMAT_FETCH', 2);

/** @constant DATATREE_FORMAT_FLAT Get a full list - an array of keys */
define('DATATREE_FORMAT_FLAT', 3);

/**
 * The DataTree:: class provides a common abstracted interface into
 * the various backends for the Horde DataTree system.
 *
 * A piece of data is just a title that is saved in the page for the
 * null driver or can be saved in a database to be accessed from
 * everywhere. Every stored object must have a different name (inside
 * each groupid).
 *
 * Required values for $params:
 * groupid: define each group of objects we want to build.
 *
 * $Horde: framework/DataTree/DataTree.php,v 1.115 2004/05/12 18:44:29 chuck Exp $
 *
 * Copyright 1999-2004 Stephane Huther <shuther@bigfoot.com>
 * Copyright 2001-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Stephane Huther <shuther@bigfoot.com>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.1
 * @package Horde_DataTree
 */
class DataTree {

    /**
     * Array of all data: indexed by id. The format is:
     * array(id => 'name' => name, 'parent' => parent).
     * @var array $_data
     */
    var $_data = array();

    /**
     * A hash that can be used to map a full object name
     * (parent:child:object) to that object's unique ID.
     * @var array $_nameMap
     */
    var $_nameMap = array();

    /**
     * Hash containing connection parameters.
     * @var array $_params
     */
    var $_params = array();

    /**
     * Constructor
     *
     * @param array $params  A hash containing any additional configuration or
     *                       connection parameters a subclass might need.
     *                       We always need 'groupid', a string that defines the prefix
     *                       for each set of hierarchical data.
     */
    function DataTree($params = null)
    {
        $this->_params = $params;
    }

    /**
     * Does the current backend have persistent storage?
     *
     * @return boolean  True if there is persistent storage, false if not.
     */
    function isPersistent()
    {
        return false;
    }

    /**
     * Remove an object.
     *
     * @param string $object  The object to remove.
     */
    function remove($object)
    {
        if (is_a($object, 'DataTreeObject')) {
            $object = $object->getName();
        }

        if (!$this->exists($object)) {
            return PEAR::raiseError($object . ' does not exist');
        }

        $id = $this->getId($object);
        $pid = $this->getParent($object);
        $order = $this->_data[$id]['order'];
        unset($this->_data[$id]);
        unset($this->_nameMap[$id]);

        // Shift down the order positions.
        $this->_reorder($pid, $order);

        return $id;
    }

    /**
     * Move an object to a new parent.
     *
     * @param mixed  $object     The object to move.
     * @param string $newparent  The new parent object. Defaults to the root.
     */
    function move($object, $newparent = null)
    {
        $cid = $this->getId($object);
        if (is_a($cid, 'PEAR_Error')) {
            return PEAR::raiseError(sprintf('Object to move does not exist: %s', $cid->getMessage()));
        }

        if (!is_null($newparent)) {
            $pid = $this->getId($newparent);
            if (is_a($pid, 'PEAR_Error')) {
                return PEAR::raiseError(sprintf('New parent does not exist: %s', $pid->getMessage()));
            }
        } else {
            $pid = '-1';
        }

        $this->_data[$cid]['parent'] = $pid;

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
        /* Check whether the object exists at all */
        if (!$this->exists($old_object)) {
            return PEAR::raiseError($old_object . ' does not exist');
        }

        /* Check for duplicates - get parent and create new object
         * name */
        $parent = $this->getName($this->getParent($old_object));
        if ($this->exists($parent . ':' . $new_object_name)) {
            return PEAR::raiseError('Duplicate name ' . $new_object_name);
        }

        /* Replace the old name with the new one in the cache */
        $old_object_id = $this->getId($old_object);
        $this->_data[$old_object_id]['name'] = $new_object_name;

        return true;
    }

    /**
     * Change order of children of an object.
     *
     * @param string $pid     The parent object id string path.
     * @param mixed  $order   Specific new order position or an array containing
     *                        the new positions for the given parent.
     * @param int    $cid     If provided indicates insertion of a new child to
     *                        the parent to avoid incrementing it when
     *                        shifting up all other children's order. If not
     *                        provided indicates deletion, so shift all other
     *                        positions down one.
     */
    function _reorder($pid, $order = null, $cid = null)
    {
        if (!is_array($order) && !is_null($order)) {
            // Single update (add/del).
            if (is_null($cid)) {
                // No id given so shuffle down.
                foreach ($this->_data as $c_key => $c_val) {
                    if ($this->_data[$c_key]['parent'] == $pid
                        && $this->_data[$c_key]['order'] > $order) {
                        $this->_data[$c_key]['order']--;
                    }
                }
            } else {
                // We have an id so shuffle up.
                foreach ($this->_data as $c_key => $c_val) {
                    if ($c_key != $cid  && $this->_data[$c_key]['parent'] == $pid
                        && $this->_data[$c_key]['order'] >= $order) {
                        $this->_data[$c_key]['order']++;
                    }
                }
            }
        } elseif (is_array($order) && !empty($order)) {
            // Multi update.
            foreach ($order as $order_position => $cid) {
                $this->_data[$cid]['order'] = $order_position;
            }
        }
    }

    /**
     * Dynamically determine the Object Class
     *
     * @param array $attributes The set of attributes that contain the class information
     *                                            Defaults to DataTreeObject
     */
    function _defineObjectClass($attributes)
    {
        global $registry;

        $class = 'DataTreeObject';
        if (!is_array($attributes)) {
            return $class;
        }
        foreach ($attributes as $attr) {
            if ($attr['name'] == 'DataTree' && $attr['key'] == 'objectType') {
                $objectType = $attr['value'];
                $result = explode('/', $objectType);
                $class = $registry->callByPackage($result[0], 'defineClass', array('type' => $result[1]));
                break;
            }
        }
        return $class;
    }

    /**
     * Return a DataTreeObject (or subclass) object of the data in the
     * object defined by $object.
     *
     * @param string $object        The object to fetch:
     *                                'parent:sub-parent:name'.
     * @param optional string $class  Subclass of DataTreeObject to use.
     *                                Defaults to DataTreeObject.
     *                                Null forces the driver to look into the attributes
     *                                table to determine the subclass to use. If none is found it uses
     *                                DataTreeObject.
     */
    function &getObject($object, $class = 'DataTreeObject')
    {
        if (empty($object)) {
            return PEAR::raiseError('No object requested.');
        }

        $this->_load($object);
        if (!$this->exists($object)) {
            return PEAR::raiseError($object . ' not found.');
        }

        $use_attributes = is_null($class) || is_callable(array($class, '_fromAttributes'));
        if ($use_attributes) {
            $attributes = $this->getAttributes($this->getId($object));
            if (is_a($attributes, 'PEAR_Error')) {
                return $attributes;
            }

            if (is_null($class)) {
                $class = $this->_defineObjectClass($attributes);
            }
        }

        if (!class_exists($class)) {
            return PEAR::raiseError($class . ' not found.');
        }

        $dataOb = &new $class($object);
        /* If the class has a _fromAttributes method, load data from
         * the attributes backend. */
        if ($use_attributes) {
            $dataOb->_fromAttributes($attributes);
        } else {
            /* Otherwise load it from the old data storage field. */
            $dataOb->data = $this->getData($this->getId($object));
        }

        $dataOb->order = $this->getOrder($object);
        return $dataOb;
    }

    /**
     * Return a DataTreeObject (or subclass) object of the data in the
     * object with the ID $id.
     *
     * @param integer $id             An object id.
     * @param optional string $class  Subclass of DataTreeObject to use.
     *                                Defaults to DataTreeObject.
     *                                Null forces the driver to look into the attributes
     *                                table to determine the subclass to use. If none is found it uses
     *                                DataTreeObject.
     */
    function &getObjectById($id, $class = 'DataTreeObject')
    {
        if (empty($id)) {
            return PEAR::raiseError('No id requested.');
        }

        $result = $this->_loadById($id);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $use_attributes = is_null($class) || is_callable(array($class, '_fromAttributes'));
        if ($use_attributes) {
            $attributes = $this->getAttributes($id);
            if (is_a($attributes, 'PEAR_Error')) {
                return $attributes;
            }

            if (is_null($class)) {
                $class = $this->_defineObjectClass($attributes);
            }
        }

        if (!class_exists($class)) {
            return PEAR::raiseError($class . ' not found.');
        }

        $name = $this->getName($id);
        $dataOb = &new $class($name);

        /* If the class has a _fromAttributes method, load data from
         * the attributes backend. */
        if ($use_attributes) {
            $dataOb->_fromAttributes($attributes);
        } else {
            /* Otherwise load it from the old data storage field. */
            $dataOb->data = $this->getData($id);
        }

        $dataOb->order = $this->getOrder($name);
        return $dataOb;
    }

    /**
     * Return an array of DataTreeObject (or subclass) objects
     * corresponding to the objects in $ids, with the object
     * names as the keys of the array.
     *
     * @param array $ids              An array of object ids.
     * @param optional string $class  Subclass of DataTreeObject to use.
     *                                Defaults to DataTreeObject.
     *                                Null forces the driver to look into the attributes
     *                                table to determine the subclass to use. If none is found it uses
     *                                DataTreeObject.
     */
    function &getObjects($ids, $class = 'DataTreeObject')
    {
        $result = $this->_loadById($ids);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $defineClass = is_null($class);
        $attributes = is_null($class) || is_callable(array($class, '_fromAttributes'));

        if ($attributes) {
            $data = $this->getAttributes($ids);
        } else {
            $data = $this->getData($ids);
        }

        $objects = array();
        foreach ($ids as $id) {
            $name = $this->getName($id);
            if (!empty($name) && !empty($data[$id])) {
                if ($defineClass) {
                    $class = $this->_defineObjectClass($data[$id]);
                }

                if (!class_exists($class)) {
                    return PEAR::raiseError($class . ' not found.');
                }

                $objects[$name] = &new $class($name);
                if ($attributes) {
                    $objects[$name]->_fromAttributes($data[$id]);
                } else {
                    $objects[$name]->data = $data[$id];
                }
                $objects[$name]->order = $this->getOrder($name);
            }
        }

        return $objects;
    }

    /**
     * Export a list of objects.
     *
     * @param constant $format            Format of the export
     * @param optional string $startleaf  The name of the leaf from which we
     *                                    start the export tree.
     * @param optional bool $reload       Re-load the requested chunk? Defaults
     *                                    to false (only what is currently
     *                                    loaded).
     * @param optional string $rootname   The label to use for the root element
     *                                    (defaults to '-1').
     * @param optional int $maxdepth      The maximum number of levels to return
     *                                    (defaults to '-1', which is no limit).
     *
     * @return mixed  The tree representation of the objects, or a PEAR_Error
     *                on failure.
     */
    function get($format, $startleaf = '-1', $reload = false,
                 $rootname = '-1', $maxdepth = -1)
    {
        $this->_load($startleaf, $reload);
        $out = array();

        switch ($format) {
        case DATATREE_FORMAT_TREE:
            $startid = $this->getId($startleaf, $maxdepth);
            if (is_a($startid, 'PEAR_Error')) {
                return $startid;
            }
            $this->_extractAllLevelTree($out, $startid, $maxdepth);
            break;

        case DATATREE_FORMAT_FLAT:
            $startid = $this->getId($startleaf);
            if (is_a($startid, 'PEAR_Error')) {
                return $startid;
            }
            $this->_extractAllLevelList($out, $startid, $maxdepth);
            if (!empty($out['-1'])) {
                $out['-1'] = $rootname;
            }
            break;

        default:
            return PEAR::raiseError('Not supported');
        }

        return $out;
    }

    /**
     * Export a list of objects just like get() above, but uses an
     * object id to fetch the list of objects.
     *
     * @param constant $format             Format of the export.
     * @param optional string  $startleaf  The id of the leaf from which
     *                                     we start the export tree.
     * @param optional boolean $reload     Reload the requested chunk? Defaults
     *                                     to false (only what is currently
     *                                     loaded).
     * @param optional string  $rootname   The label to use for the root element
     *                                     (defaults to '-1').
     * @param optional integer $maxdepth   The maximum number of levels to return
     *                                     (defaults to '-1', which is no limit).
     *
     * @return mixed  The tree representation of the objects, or a PEAR_Error
     *                on failure.
     */
    function getById($format, $startleaf = '-1', $reload = false,
                     $rootname = '-1', $maxdepth = -1)
    {
        $this->_load($this->getName($startleaf), $reload);
        $out = array();

        switch ($format) {
        case DATATREE_FORMAT_TREE:
            $this->_extractAllLevelTree($out, $startleaf, $maxdepth);
            break;

        case DATATREE_FORMAT_FLAT:
            $this->_extractAllLevelList($out, $startleaf, $maxdepth);
            if (!empty($out['-1'])) {
                $out['-1'] = $rootname;
            }
            break;

        default:
            return PEAR::raiseError('Not supported');
        }

        return $out;
    }

    /**
     * Import a list of objects. Used by drivers to populate the
     * internal $_data array.
     *
     * @access private
     *
     * @param integer $format   Format of the import (DATATREE_FORMAT_*).
     * @param array   $data     The data to import.
     * @param string  $charset  The charset to convert the object name from.
     */
    function set($format, $data, $charset = null)
    {
        switch ($format) {
        case DATATREE_FORMAT_FETCH:
            $cats = array();
            $cids = array();
            foreach ($data as $cat) {
                if (!is_null($charset)) {
                    $cat[1] = String::convertCharset($cat[1], $charset);
                }
                $cids[$cat[0]] = $cat[1];
                $cparents[$cat[0]] = $cat[2];
                $corders[$cat[0]] = $cat[3];
            }
            foreach ($cids as $id => $name) {
                $this->_data[$id]['name'] = $name;
                $this->_data[$id]['order'] = $corders[$id];
                if (!empty($cparents[$id])) {
                    $parents = explode(':', substr($cparents[$id], 1));
                    $par = $parents[count($parents) - 1];
                    $this->_data[$id]['parent'] = $par;
                    $this->_nameMap[$id] = '';
                    foreach ($parents as $parID) {
                        if (!empty($this->_nameMap[$id])) {
                            $this->_nameMap[$id] .= ':';
                        }
                        $this->_nameMap[$id] .= $cids[$parID];
                    }
                    $this->_nameMap[$id] .= ':' . $name;
                } else {
                    $this->_data[$id]['parent'] = '-1';
                    $this->_nameMap[$id] = $name;
                }
            }
            break;

        default:
            return PEAR::raiseError('Not supported');
        }

        return true;
    }

    /**
     * Extract one level of data for a parent leaf, sorted first by
     * their order and then by name. This function is a way to get a
     * collection of $leaf's children.
     *
     * @param optional string $leaf  Name of the parent from which to start.
     *
     * @return array
     */
    function _extractOneLevel($leaf = '-1')
    {
        $out = array();
        foreach ($this->_data as $id => $vals) {
            if ($vals['parent'] == $leaf) {
                $out[$id] = $vals;
            }
        }

        uasort($out, array($this, '_cmp'));
        return $out;
    }

    /**
     * Extract all levels of data, starting from a given parent
     * leaf in the datatree.
     *
     * @param array $out                  This is an iterating function, so $out
     *                                    is passed by reference to contain the
     *                                    result.
     * @param optional string  $parent    The name of the parent from which to
     *                                    begin.
     * @param optional integer $maxdepth  Max of levels of depth to check.
     *
     * @note If nothing is returned that means there is no child, but
     * don't forget to add the parent if any subsequent operations are
     * required!
     */
    function _extractAllLevelTree(&$out, $parent = '-1', $maxdepth = -1)
    {
        if ($maxdepth == 0) {
            return false;
        }

        $out[$parent] = true;

        $k = $this->_extractOneLevel($parent);
        foreach ($k as $object => $v) {
            if (!is_array($out[$parent])) {
                $out[$parent] = array();
            }
            $out[$parent][$object] = true;
            $this->_extractAllLevelTree($out[$parent], $object, $maxdepth - 1);
        }
    }

    /**
     * Extract all levels of data, starting from any parent in
     * the tree.
     *
     * Returned array format: array(parent => array(child => true))
     *
     * @param array $out                  This is an iterating function, so $out
     *                                    is passed by reference to contain the
     *                                    result.
     * @param optional string  $parent    The name of the parent from which to
     *                                    begin.
     * @param optional integer $maxdepth  Max number of levels of depth to check.
     */
    function _extractAllLevelList(&$out, $parent = '-1', $maxdepth = -1)
    {
        if ($maxdepth == 0) {
            return false;
        }

        // This is redundant most of the time, so make sure we need to
        // do it.
        if (empty($out[$parent])) {
            $out[$parent] = $this->getName($parent);
        }

        $k = array_keys($this->_extractOneLevel($parent));
        foreach ($k as $object) {
            $out[$object] = $this->getName($object);
            $this->_extractAllLevelList($out, $object, $maxdepth - 1);
        }
    }

    /**
     * Get a $child's direct parent ID.
     *
     * @param string $child  Get the parent of this object.
     *
     * @return integer  The unique ID of the parent.
     */
    function getParent($child)
    {
        if (is_a($child, 'DataTreeObject')) {
            $child = $child->getName();
        }
        $id = $this->getId($child);
        if (is_a($id, 'PEAR_Error')) {
            return $id;
        }

        return $this->_data[$id]['parent'];
    }

    /**
     * Get a $child's direct parent ID.
     *
     * @param integer $childId  Get the parent of this object.
     *
     * @return integer  The unique ID of the parent.
     */
    function getParentById($childId)
    {
        $this->_loadById($childId);
        return isset($this->_data[$childId]) ?
            $this->_data[$childId]['parent'] :
            PEAR::raiseError($childId . ' not found');
    }

    /**
     * Get a list of parents all the way up to the root object for
     * $child.
     *
     * @param mixed   $child   The name of the child
     * @param boolean $getids  If true, return parent IDs; otherwise, return
     *                         names.
     *
     * @return array  [child] [parent] in a tree format.
     */
    function getParents($child, $getids = false)
    {
        $pid = $this->getParent($child);
        if (is_a($pid, 'PEAR_Error')) {
            return PEAR::raiseError('Parents not found: ' . $pid->getMessage());
        }
        $pname = $this->getName($pid);
        if ($getids) {
            $parents = array($pid => true);
        } else {
            $parents = array($pname => true);
        }

        if ($pid != '-1') {
            if ($getids) {
                $parents[$pid] = $this->getParents($pname, $getids);
            } else {
                $parents[$pname] = $this->getParents($pname, $getids);
            }
        }

        return $parents;
    }

    /**
     * Get a list of parents all the way up to the root object for
     * $child.
     *
     * @param integer $childId  The id of the child.
     * @param array   $parents  (optional) The array, as we build it up.
     *
     * @return array  A flat list of all of the parents of $child,
     *                hashed in $id => $name format.
     */
    function getParentList($childId, $parents = array())
    {
        $pid = $this->getParentById($childId);
        if (is_a($pid, 'PEAR_Error')) {
            return PEAR::raiseError('Parents not found: ' . $pid->getMessage());
        }

        if ($pid != '-1') {
            $parents[$pid] = $this->getName($pid);
            $parents = $this->getParentList($pid, $parents);
        }

        return $parents;
    }

    /**
     * Get a parent-id string (id:cid format) for the specified object.
     *
     * @param mixed $object  The object to return a parent string for.
     */
    function getParentIdString($object)
    {
        $pids = array();
        $ptree = $this->getParents($object, true);
        while ((list($id, $parent) = each($ptree)) && is_array($parent)) {
            array_unshift($pids, ':' . $id);
            $ptree = $parent;
        }

        return implode('', $pids);
    }

    /**
     * Get the number of children an object has, only counting immediate
     * children, not grandchildren, etc.
     *
     * @param optional mixed $parent  Either the object or the
     *                                name for which to count the
     *                                children, defaults to the root ('-1').
     *
     * @return integer
     */
    function getNumberOfChildren($parent = '-1')
    {
        if (is_a($parent, 'DataTreeObject')) {
            $parent = $parent->getName();
        }
        $this->_load($parent);
        $out = $this->_extractOneLevel($this->getId($parent));
        return is_array($out) ? count($out) : 0;
    }

    /**
     * Check if an object exists or not. The root element -1 always exists.
     *
     * @param mixed $object  The name of the object.
     *
     * @return boolean  True if the object exists, false otherwise.
     */
    function exists($object)
    {
        if (empty($object)) {
            return false;
        }
        if (is_a($object, 'DataTreeObject')) {
            $object = $object->getName();
        } elseif (is_array($object)) {
            $object = implode(':', $object);
        }

        if ($object == '-1') {
            return true;
        }

        $idMap = array_flip($this->_nameMap);
        if (isset($idMap[$object])) {
            return true;
        }

        $this->_load($object);
        $idMap = array_flip($this->_nameMap);
        return isset($idMap[$object]);
    }

    /**
     * Get the name of an object from its id.
     *
     * @param integer $id  The id for which to look up the name.
     *
     * @return string
     */
    function getName($id)
    {
        /* If no id or if id is a PEAR error, return null. */
        if (empty($id) || is_a($id, 'PEAR_Error')) {
            return null;
        }

        /* If checking name of root, return -1. */
        if ($id == '-1') {
            return '-1';
        }

        /* If found in the name map, return the name. */
        if (isset($this->_nameMap[$id])) {
            return $this->_nameMap[$id];
        }

        /* Not found in name map, try loading this id into the name
         * map. */
        $this->_loadById($id);

        /* If id loaded return the name, otherwise return null. */
        return isset($this->_nameMap[$id]) ?
            $this->_nameMap[$id] :
            null;
    }

    /**
     * Get the id of an object from its name.
     *
     * @param mixed $name  Either the object, an array containing the
     *                     path elements, or the object name for which
     *                     to look up the id.
     *
     * @return string
     */
    function getId($name)
    {
        /* Check if $name is not a string. */
        if (is_a($name, 'DataTreeObject')) {
            /* DataTreeObject, get the string name. */
            $name = $name->getName();
        } elseif (is_array($name)) {
            /* Path array, implode to get the string name. */
            $name = implode(':', $name);
        }

        /* If checking id of root, return -1. */
        if ($name == '-1') {
            return '-1';
        }

        /* Check if the name actually exists, if not return PEAR error. */
        if (!$this->exists($name)) {
            return PEAR::raiseError($name . ' does not exist');
        }

        /* Flip the name map to look up the id using the name as key. */
        $idMap = array_flip($this->_nameMap);
        return $idMap[$name];
    }

    /**
     * Get the order position of an object.
     *
     * @param mixed $child  Either the object or the name.
     *
     * @return mixed  The object's order position or a PEAR error on failure.
     */
    function getOrder($child)
    {
        if (is_a($child, 'DataTreeObject')) {
            $child = $child->getName();
        }
        $id = $this->getId($child);
        if (is_a($id, 'PEAR_Error')) {
            return $id;
        }

        return isset($this->_data[$id]['order']) ?
            $this->_data[$id]['order'] :
            null;
    }

    /**
     * Replace all occurences of ':' in an object name with '.'.
     *
     * @access public
     *
     * @param string $name  The name of the object.
     *
     * @return string  The encoded name.
     */
    function encodeName($name)
    {
        return str_replace(':', '.', $name);
    }

    /**
     * Get the short name of an object, returns only the last portion
     * of the full name. For display purposes only.
     *
     * @access public
     * @static
     *
     * @param string $name  The name of the object.
     *
     * @return string  The object's short name.
     */
    function getShortName($name)
    {
        /* If there are several components to the name, explode and
         * get the last one, otherwise just return the name. */
        if (strstr($name, ':')) {
            return array_pop(explode(':', $name));
        } else {
            return $name;
        }
    }

    /**
     * Add an object.
     *
     * @param string   $name  The short object name.
     * @param integer  $id    The new object's unique ID.
     * @param integer  $pid   The unique ID of the object's parent.
     * @param integer  $order The ordering data for the object.
     *
     * @access protected
     */
    function _add($name, $id, $pid, $order = '')
    {
        $this->_data[$id] = array('name' => $name,
                                  'parent' => $pid,
                                  'order' => $order);
        $this->_nameMap[$id] = $name;

        /* Shift along the order positions. */
        $this->_reorder($pid, $order, $id);

        return true;
    }

    /**
     * Sort two objects by their order field, and if that is the same,
     * alphabetically (case insensitive) by name.
     *
     * You never call this function; it's used in uasort() calls. Do
     * NOT use usort(); you'll lose key => value associations.
     *
     * @param array $a  The first object
     * @param array $b  The second object
     *
     * @return integer  1 if $a should be first,
     *                 -1 if $b should be first,
     *                  0 if they are entirely equal.
     */
    function _cmp($a, $b)
    {
        if ($a['order'] > $b['order']) {
            return 1;
        } elseif ($a['order'] < $b['order']) {
            return -1;
        } else {
            return strcasecmp($a['name'], $b['name']);
        }
    }

    /**
     * Attempts to return a concrete DataTree instance based on
     * $driver.
     *
     * @param mixed $driver  The type of concrete DataTree subclass to return.
     *                       This is based on the storage driver ($driver). The
     *                       code is dynamically included. If $driver is an array,
     *                       then we will look in $driver[0]/lib/DataTree/ for
     *                       the subclass implementation named $driver[1].php.
     * @param array $params  (optional) A hash containing any additional
     *                       configuration or connection parameters a subclass
     *                       might need.
     *                       here, we need 'groupid' = a string that defines
     *                       top-level groups of objects.
     *
     * @return object DataTree  The newly created concrete DataTree instance,
     *                          or false on an error.
     */
    function &factory($driver, $params = null)
    {
        $driver = basename($driver);

        if (is_null($params)) {
            $params = Horde::getDriverConfig('datatree', $driver);
        }

        if (empty($driver)) {
            $driver = 'null';
        }

        if (!empty($app)) {
            require_once $GLOBALS['registry']->getParam('fileroot', $app) . '/lib/DataTree/' . $driver . '.php';
        } else {
            include_once 'Horde/DataTree/' . $driver . '.php';
        }
        $class = 'DataTree_' . $driver;
        if (class_exists($class)) {
            return $ret = &new $class($params);
        } else {
            return PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }
    }

    /**
     * Attempts to return a reference to a concrete DataTree instance
     * based on $driver. It will only create a new instance if no
     * DataTree instance with the same parameters currently exists.
     *
     * This should be used if multiple DataTree sources (and, thus,
     * multiple DataTree instances) are required.
     *
     * This method must be invoked as: $var = &DataTree::singleton();
     *
     * @param mixed $driver           Type of concrete DataTree subclass to
     *                                return, based on storage driver ($driver).
     *                                The code is dynamically included. If
     *                                $driver is an array, then look in
     *                                $driver[0]/lib/DataTree/ for subclass
     *                                implementation named $driver[1].php.
     * @param optional array $params  A hash containing any additional
     *                                configuration or connection parameters a
     *                                subclass might need.
     *
     * @return object DataTree  The concrete DataTree reference, or false on an
     *                          error.
     */
    function &singleton($driver, $params = null)
    {
        static $instances;
        if (!isset($instances)) {
            $instances = array();
        }

        if (is_null($params)) {
            $params = Horde::getDriverConfig('datatree', $driver);
        }

        $signature = serialize(array($driver, $params));
        if (!isset($instances[$signature])) {
            $instances[$signature] = &DataTree::factory($driver, $params);
        }

        return $instances[$signature];
    }

}

/**
 * Class that can be extended to save arbitrary information as part of
 * a stored object. The Groups system makes use of this; the
 * DataTreeObject_Group class is an example of an extension of this
 * class with specialized methods.
 *
 * @author  Stephane Huther <shuther@bigfoot.com>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.1
 * @package Horde_DataTree
 */
class DataTreeObject {

    /**
     * Key-value hash that will be serialized.
     * @see getData()
     * @var array $data
     */
    var $data = array();

    /**
     * The unique name of this object. These names have the same
     * requirements as other object names - they must be unique,
     * etc.
     * @var string $name.
     */
    var $name;

    /**
     * If this object has ordering data, store it here.
     * @var integer $order
     */
    var $order = null;

    /**
     * DataTreeObject constructor. Just sets the $name parameter.
     *
     * @param string $name  The object name.
     */
    function DataTreeObject($name)
    {
        $this->name = $name;
    }

    /**
     * Get the name of this object.
     *
     * @return string The object name.
     */
    function getName()
    {
        return $this->name;
    }

    /**
     * Sets the name of this object.
     *
     * NOTE: Use with caution. This may throw out of sync the cached datatree
     * tables if not used properly.
     *
     * @param string $name  The name to set this object's name to.
     */
    function setName($name)
    {
        $this->name = $name;
    }

    /**
     * Get the short name of this object. For display purposes only.
     *
     * @return string  The object's short name.
     */
    function getShortName()
    {
        return DataTree::getShortName($this->name);
    }

    /**
     * Get a pointer/accessor to the data array.
     *
     * @return array  A reference to the internal data array.
     */
    function getData()
    {
        return $this->data;
    }

    /**
     * Get one of the attributes of the object, or null if it isn't
     * defined.
     *
     * @param string $attribute  The attribute to get.
     *
     * @return mixed  The value of the attribute, or null.
     */
    function get($attribute)
    {
        return isset($this->data[$attribute])
            ? $this->data[$attribute]
            : null;
    }

    /**
     * Set one of the attributes of the object.
     *
     * @param string $attribute  The attribute to set.
     * @param mixed  $value      The value for $attribute.
     */
    function set($attribute, $value)
    {
        $this->data[$attribute] = $value;
    }

}
