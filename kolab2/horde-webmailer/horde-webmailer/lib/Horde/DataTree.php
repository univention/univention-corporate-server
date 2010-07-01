<?php
/**
 * @package Horde_DataTree
 *
 * $Horde: framework/DataTree/DataTree.php,v 1.151.2.24 2009-01-06 15:23:01 jan Exp $
 */

/** List every object in an array, similar to PEAR/html/menu.php. */
define('DATATREE_FORMAT_TREE', 1);

/** Get a full list - an array of keys. */
define('DATATREE_FORMAT_FLAT', 2);

/** The root element (top-level parent) of each DataTree group. */
define('DATATREE_ROOT', -1);

/** Build a normal select query. */
define('DATATREE_BUILD_SELECT', 0);

/** Build a count only query. */
define('DATATREE_BUILD_COUNT', 1);

/** Build an attribute only query. */
define('DATATREE_BUILD_VALUES', 2);

define('DATATREE_BUILD_VALUES_COUNT', 3);

/**
 * The DataTree:: class provides a common abstracted interface into the
 * various backends for the Horde DataTree system.
 *
 * A piece of data is just a title that is saved in the page for the null
 * driver or can be saved in a database to be accessed from everywhere. Every
 * stored object must have a different name (inside each groupid).
 *
 * Required values for $params:<pre>
 *   'group' -- Define each group of objects we want to build.</pre>
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Stephane Huther <shuther1@free.fr>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @package Horde_DataTree
 */
class DataTree {

    /**
     * Array of all data: indexed by id. The format is:
     *   array(id => 'name' => name, 'parent' => parent).
     *
     * @var array
     */
    var $_data = array();

    /**
     * A hash that can be used to map a full object name
     * (parent:child:object) to that object's unique ID.
     *
     * @var array
     */
    var $_nameMap = array();

     /**
     * Actual attribute sorting hash.
     *
     * @var array
     */
    var $_sortHash = null;

    /**
     * Hash containing connection parameters.
     *
     * @var array
     */
    var $_params = array();

    /**
     * Constructor.
     *
     * @param array $params  A hash containing any additional configuration or
     *                       connection parameters a subclass might need.
     *                       We always need 'group', a string that defines the
     *                       prefix for each set of hierarchical data.
     */
    function DataTree($params = array())
    {
        $this->_params = $params;
    }

    /**
     * Returns a parameter of this DataTree instance.
     *
     * @param string $param  The parameter to return.
     *
     * @return mixed  The parameter's value or null if it doesn't exist.
     */
    function getParam($param)
    {
        return isset($this->_params[$param]) ? $this->_params[$param] : null;
    }

    /**
     * Removes an object.
     *
     * @param string $object  The object to remove.
     * @param boolean $force  Force removal of every child object?
     *
     * @return TODO
     */
    function remove($object, $force = false)
    {
        if (is_a($object, 'DataTreeObject')) {
            $object = $object->getName();
        }

        if (!$this->exists($object)) {
            return PEAR::raiseError($object . ' does not exist');
        }

        $children = $this->getNumberOfChildren($object);
        if ($children) {
            /* TODO: remove children if $force == true */
            return PEAR::raiseError(sprintf(ngettext("Cannot remove, %d child exists.", "Cannot remove, %d children exist.", count($children)), count($children)));
        }

        $id = $this->getId($object);
        $pid = $this->getParent($object);
        $order = $this->_data[$id]['order'];
        unset($this->_data[$id], $this->_nameMap[$id]);

        // Shift down the order positions.
        $this->_reorder($pid, $order);

        return $id;
    }

    /**
     * Removes all DataTree objects owned by a certain user.
     *
     * @abstract
     *
     * @param string $user  A user name.
     *
     * @return TODO
     */
    function removeUserData($user)
    {
        return PEAR::raiseError('not supported');
    }

    /**
     * Move an object to a new parent.
     *
     * @param mixed $object      The object to move.
     * @param string $newparent  The new parent object. Defaults to the root.
     *
     * @return mixed  True on success, PEAR_Error on error.
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
            $pid = DATATREE_ROOT;
        }

        $this->_data[$cid]['parent'] = $pid;

        return true;
    }

    /**
     * Change an object's name.
     *
     * @param mixed  $old_object       The old object.
     * @param string $new_object_name  The new object name.
     *
     * @return mixed  True on success, PEAR_Error on error.
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
     * Changes the order of the children of an object.
     *
     * @abstract
     *
     * @param string $parent  The full id path of the parent object.
     * @param mixed $order    If an array it specifies the new positions for
     *                        all child objects.
     *                        If an integer and $cid is specified, the position
     *                        where the child specified by $cid is inserted. If
     *                        $cid is not specified, the position gets deleted,
     *                        causing the following positions to shift up.
     * @param integer $cid    See $order.
     *
     * @return TODO
     */
    function reorder($parents, $order = null, $cid = null)
    {
        return PEAR::raiseError('not supported');
    }

    /**
     * Change order of children of an object.
     *
     * @param string $pid     The parent object id string path.
     * @param mixed $order    Specific new order position or an array containing
     *                        the new positions for the given parent.
     * @param integer $cid    If provided indicates insertion of a new child to
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
                    if ($this->_data[$c_key]['parent'] == $pid &&
                        $this->_data[$c_key]['order'] > $order) {
                        --$this->_data[$c_key]['order'];
                    }
                }
            } else {
                // We have an id so shuffle up.
                foreach ($this->_data as $c_key => $c_val) {
                    if ($c_key != $cid &&
                        $this->_data[$c_key]['parent'] == $pid &&
                        $this->_data[$c_key]['order'] >= $order) {
                        ++$this->_data[$c_key]['order'];
                    }
                }
            }
        } elseif (is_array($order) && count($order)) {
            // Multi update.
            foreach ($order as $order_position => $cid) {
                $this->_data[$cid]['order'] = $order_position;
            }
        }
    }

    /**
     * Explicitly set the order for a datatree object.
     *
     * @abstract
     *
     * @param integer $id     The datatree object id to change.
     * @param integer $order  The new order.
     *
     * @return TODO
     */
    function setOrder($id, $order)
    {
        return PEAR::raiseError('not supported');
    }

    /**
     * Dynamically determines the object class.
     *
     * @param array $attributes  The set of attributes that contain the class
     *                           information. Defaults to DataTreeObject.
     *
     * @return TODO
     */
    function _defineObjectClass($attributes)
    {
        $class = 'DataTreeObject';
        if (!is_array($attributes)) {
            return $class;
        }

        foreach ($attributes as $attr) {
            if ($attr['name'] == 'DataTree') {
                switch ($attr['key']) {
                case 'objectClass':
                    $class = $attr['value'];
                    break;

                case 'objectType':
                    $result = explode('/', $attr['value']);
                    $class = $GLOBALS['registry']->callByPackage($result[0], 'defineClass', array('type' => $result[1]));
                    break;
                }
            }
        }

        return $class;
    }

    /**
     * Returns a DataTreeObject (or subclass) object of the data in the
     * object defined by $object.
     *
     * @param string $object  The object to fetch: 'parent:sub-parent:name'.
     * @param string $class   Subclass of DataTreeObject to use. Defaults to
     *                        DataTreeObject. Null forces the driver to look
     *                        into the attributes table to determine the
     *                        subclass to use. If none is found it uses
     *                        DataTreeObject.
     *
     * @return TODO
     */
    function &getObject($object, $class = 'DataTreeObject')
    {
        if (empty($object)) {
            $error = PEAR::raiseError('No object requested.');
            return $error;
        }

        $this->_load($object);
        if (!$this->exists($object)) {
            $error = PEAR::raiseError($object . ' not found.');
            return $error;
        }

        return $this->_getObject($this->getId($object), $object, $class);
    }

    /**
     * Returns a DataTreeObject (or subclass) object of the data in the
     * object with the ID $id.
     *
     * @param integer $id    An object id.
     * @param string $class  Subclass of DataTreeObject to use. Defaults to
     *                       DataTreeObject. Null forces the driver to look
     *                       into the attributes table to determine the
     *                       subclass to use. If none is found it uses
     *                       DataTreeObject.
     *
     * @return TODO
     */
    function &getObjectById($id, $class = 'DataTreeObject')
    {
        if (empty($id)) {
            $object = PEAR::raiseError('No id requested.');
            return $object;
        }

        $result = $this->_loadById($id);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return $this->_getObject($id, $this->getName($id), $class);
    }

    /**
     * Helper function for getObject() and getObjectById().
     *
     * @access private
     */
    function &_getObject($id, $name, $class)
    {
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
            $error = PEAR::raiseError($class . ' not found.');
            return $error;
        }

        $dataOb = new $class($name);
        $dataOb->setDataTree($this);

        /* If the class has a _fromAttributes method, load data from
         * the attributes backend. */
        if ($use_attributes) {
            $dataOb->_fromAttributes($attributes);
        } else {
            /* Otherwise load it from the old data storage field. */
            $dataOb->setData($this->getData($id));
        }

        $dataOb->setOrder($this->getOrder($name));
        return $dataOb;
    }

    /**
     * Returns an array of DataTreeObject (or subclass) objects
     * corresponding to the objects in $ids, with the object
     * names as the keys of the array.
     *
     * @param array $ids     An array of object ids.
     * @param string $class  Subclass of DataTreeObject to use. Defaults to
     *                       DataTreeObject. Null forces the driver to look
     *                       into the attributes table to determine the
     *                       subclass to use. If none is found it uses
     *                       DataTreeObject.
     *
     * @return TODO
     */
    function &getObjects($ids, $class = 'DataTreeObject')
    {
        $result = $this->_loadById($ids);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $defineClass = is_null($class);
        $attributes = $defineClass || is_callable(array($class, '_fromAttributes'));

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

                $objects[$name] = new $class($name);
                $objects[$name]->setDataTree($this);
                if ($attributes) {
                    $objects[$name]->_fromAttributes($data[$id]);
                } else {
                    $objects[$name]->setData($data[$id]);
                }
                $objects[$name]->setOrder($this->getOrder($name));
            }
        }

        return $objects;
    }

    /**
     * Export a list of objects.
     *
     * @param constant $format       Format of the export
     * @param string   $startleaf    The name of the leaf from which we start
     *                               the export tree.
     * @param boolean  $reload       Re-load the requested chunk? Defaults to
     *                               false (only what is currently loaded).
     * @param string   $rootname     The label to use for the root element.
     *                               Defaults to DATATREE_ROOT.
     * @param integer  $maxdepth     The maximum number of levels to return.
     *                               Defaults to DATATREE_ROOT, which is no
     *                               limit.
     * @param boolean  $loadTree     Load a tree starting at $root, or just the
     *                               requested level and direct parents?
     *                               Defaults to single level.
     * @param string   $sortby_name  Attribute name to use for sorting.
     * @param string   $sortby_key   Attribute key to use for sorting.
     * @param integer  $direction    Sort direction:
     *                                0 - ascending
     *                                1 - descending
     *
     * @return mixed  The tree representation of the objects, or a PEAR_Error
     *                on failure.
     */
    function get($format, $startleaf = DATATREE_ROOT, $reload = false,
                 $rootname = DATATREE_ROOT, $maxdepth = -1, $loadTree = false,
                 $sortby_name = null, $sortby_key = null, $direction = 0)
    {
        $out = array();

        /* Set sorting hash */
        if (!is_null($sortby_name)) {
            $this->_sortHash = DataTree::sortHash($startleaf, $sortby_name, $sortby_key, $direction);
        }

        $this->_load($startleaf, $loadTree, $reload, $sortby_name, $sortby_key, $direction);

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
            if (!empty($out[DATATREE_ROOT])) {
                $out[DATATREE_ROOT] = $rootname;
            }
            break;

        default:
            return PEAR::raiseError('Not supported');
        }

        if (!is_null($this->_sortHash)) {
            /* Reset sorting hash. */
            $this->_sortHash = null;

            /* Reverse since the attribute sorting combined with tree up-ward
             * sorting produces a reversed object order. */
            $out = array_reverse($out, true);
        }

        return $out;
    }

    /**
     * Counts objects.
     *
     * @param string $startleaf  The name of the leaf from which we start
     *                           counting.
     *
     * @return integer  The number of the objects below $startleaf.
     */
    function count($startleaf = DATATREE_ROOT)
    {
        return $this->_count($startleaf);
    }

    /**
     * Create attribute sort hash
     *
     * @since Horde 3.1
     *
     * @param string  $root         The name of the leaf from which we start
     *                              the export tree.
     * @param string  $sortby_name  Attribute name to use for sorting.
     * @param string  $sortby_key   Attribute key to use for sorting.
     * @param integer $direction    Sort direction:
     *                              0 - ascending
     *                              1 - descending
     *
     * @return string  The sort hash.
     */
    function sortHash($root, $sortby_name = null, $sortby_key = null,
                      $direction = 0)
    {
        return sprintf('%s-%s-%s-%s', $root, $sortby_name, $sortby_key, $direction);
    }

    /**
     * Export a list of objects just like get() above, but uses an
     * object id to fetch the list of objects.
     *
     * @param constant $format    Format of the export.
     * @param string  $startleaf  The id of the leaf from which we start the
     *                            export tree.
     * @param boolean $reload     Reload the requested chunk? Defaults to
     *                            false (only what is currently loaded).
     * @param string  $rootname   The label to use for the root element.
     *                            Defaults to DATATREE_ROOT.
     * @param integer $maxdepth   The maximum number of levels to return
     *                            Defaults to -1, which is no limit.
     *
     * @return mixed  The tree representation of the objects, or a PEAR_Error
     *                on failure.
     */
    function getById($format, $startleaf = DATATREE_ROOT, $reload = false,
                     $rootname = DATATREE_ROOT, $maxdepth = -1)
    {
        $this->_loadById($startleaf);
        $out = array();

        switch ($format) {
        case DATATREE_FORMAT_TREE:
            $this->_extractAllLevelTree($out, $startleaf, $maxdepth);
            break;

        case DATATREE_FORMAT_FLAT:
            $this->_extractAllLevelList($out, $startleaf, $maxdepth);
            if (!empty($out[DATATREE_ROOT])) {
                $out[DATATREE_ROOT] = $rootname;
            }
            break;

        default:
            return PEAR::raiseError('Not supported');
        }

        return $out;
    }

    /**
     * Returns a list of all groups (root nodes) of the data tree.
     *
     * @abstract
     *
     * @return mixed  The group IDs or PEAR_Error on error.
     */
    function getGroups()
    {
        return PEAR::raiseError('not supported');
    }

    /**
     * Retrieve data for an object from the datatree_data field.
     *
     * @abstract
     *
     * @param integer $cid  The object id to fetch, or an array of object ids.
     *
     * @return TODO
     */
    function getData($cid)
    {
        return PEAR::raiseError('not supported');
    }

    /**
     * Import a list of objects. Used by drivers to populate the internal
     * $_data array.
     *
     * @param array $data      The data to import.
     * @param string $charset  The charset to convert the object name from.
     *
     * @return TODO
     */
    function set($data, $charset = null)
    {
        $cids = array();
        foreach ($data as $id => $cat) {
            if (!is_null($charset)) {
                $cat[1] = String::convertCharset($cat[1], $charset);
            }
            $cids[$cat[0]] = $cat[1];
            $cparents[$cat[0]] = $cat[2];
            $corders[$cat[0]] = $cat[3];
            $sorders[$cat[0]] = $id;
        }

        foreach ($cids as $id => $name) {
            $this->_data[$id]['name'] = $name;
            $this->_data[$id]['order'] = $corders[$id];
            if (!is_null($this->_sortHash)) {
                $this->_data[$id]['sorter'][$this->_sortHash] = $sorders[$id];
            }
            if (!empty($cparents[$id])) {
                $parents = explode(':', substr($cparents[$id], 1));
                $par = $parents[count($parents) - 1];
                $this->_data[$id]['parent'] = $par;

                if (!empty($this->_nameMap[$par])) {
                    // If we've already loaded the direct parent of
                    // this object, use that to find the full name.
                    $this->_nameMap[$id] = $this->_nameMap[$par] . ':' . $name;
                } else {
                    // Otherwise, run through parents one by one to
                    // build it up.
                    $this->_nameMap[$id] = '';
                    foreach ($parents as $parID) {
                        if (!empty($cids[$parID])) {
                            $this->_nameMap[$id] .= ':' . $cids[$parID];
                        }
                    }
                    $this->_nameMap[$id] = substr($this->_nameMap[$id], 1) . ':' . $name;
                }
            } else {
                $this->_data[$id]['parent'] = DATATREE_ROOT;
                $this->_nameMap[$id] = $name;
            }
        }

        return true;
    }

    /**
     * Extract one level of data for a parent leaf, sorted first by
     * their order and then by name. This function is a way to get a
     * collection of $leaf's children.
     *
     * @param string $leaf  Name of the parent from which to start.
     *
     * @return array  TODO
     */
    function _extractOneLevel($leaf = DATATREE_ROOT)
    {
        $out = array();
        foreach ($this->_data as $id => $vals) {
            if ($vals['parent'] == $leaf) {
                $out[$id] = $vals;
            }
        }

        uasort($out, array($this, (is_null($this->_sortHash)) ? '_cmp' : '_cmpSorted'));

        return $out;
    }

    /**
     * Extract all levels of data, starting from a given parent
     * leaf in the datatree.
     *
     * @access private
     *
     * @note If nothing is returned that means there is no child, but
     * don't forget to add the parent if any subsequent operations are
     * required!
     *
     * @param array $out         This is an iterating function, so $out is
     *                           passed by reference to contain the result.
     * @param string $parent     The name of the parent from which to begin.
     * @param integer $maxdepth  Max of levels of depth to check.
     *
     * @return TODO
     */
    function _extractAllLevelTree(&$out, $parent = DATATREE_ROOT,
                                  $maxdepth = -1)
    {
        if ($maxdepth == 0) {
            return false;
        }

        $out[$parent] = true;

        $k = $this->_extractOneLevel($parent);
        foreach (array_keys($k) as $object) {
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
     * @access private
     *
     * @param array $out         This is an iterating function, so $out is
     *                           passed by reference to contain the result.
     * @param string $parent     The name of the parent from which to begin.
     * @param integer $maxdepth  Max number of levels of depth to check.
     *
     * @return TODO
     */
    function _extractAllLevelList(&$out, $parent = DATATREE_ROOT,
                                  $maxdepth = -1)
    {
        if ($maxdepth == 0) {
            return false;
        }

        // This is redundant most of the time, so make sure we need to
        // do it.
        if (empty($out[$parent])) {
            $out[$parent] = $this->getName($parent);
        }

        foreach (array_keys($this->_extractOneLevel($parent)) as $object) {
            $out[$object] = $this->getName($object);
            $this->_extractAllLevelList($out, $object, $maxdepth - 1);
        }
    }

    /**
     * Returns a child's direct parent ID.
     *
     * @param mixed $child  Either the object, an array containing the
     *                      path elements, or the object name for which
     *                      to look up the parent's ID.
     *
     * @return mixed  The unique ID of the parent or PEAR_Error on error.
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
        return $this->getParentById($id);
    }

    /**
     * Get a $child's direct parent ID.
     *
     * @param integer $childId  Get the parent of this object.
     *
     * @return mixed  The unique ID of the parent or PEAR_Error on error.
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
     * @param mixed $child     The name of the child
     * @param boolean $getids  If true, return parent IDs; otherwise, return
     *                         names.
     *
     * @return mixed  [child] [parent] in a tree format or PEAR_Error.
     */
    function getParents($child, $getids = false)
    {
        $pid = $this->getParent($child);
        if (is_a($pid, 'PEAR_Error')) {
            return PEAR::raiseError('Parents not found: ' . $pid->getMessage());
        }
        $pname = $this->getName($pid);
        $parents = ($getids) ? array($pid => true) : array($pname => true);

        if ($pid != DATATREE_ROOT) {
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
     * @param array $parents    The array, as we build it up.
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

        if ($pid != DATATREE_ROOT) {
            $parents[$pid] = $this->getName($pid);
            $parents = $this->getParentList($pid, $parents);
        }

        return $parents;
    }

    /**
     * Get a parent ID string (id:cid format) for the specified object.
     *
     * @param mixed $object  The object to return a parent string for.
     *
     * @return string|PEAR_Error  The ID "path" to the parent object or
     *                            PEAR_Error on failure.
     */
    function getParentIdString($object)
    {
        $ptree = $this->getParents($object, true);
        if (is_a($ptree, 'PEAR_Error')) {
            return $ptree;
        }

        $pids = '';
        while ((list($id, $parent) = each($ptree)) && is_array($parent)) {
            $pids = ':' . $id . $pids;
            $ptree = $parent;
        }

        return $pids;
    }

    /**
     * Get the number of children an object has, only counting immediate
     * children, not grandchildren, etc.
     *
     * @param mixed $parent  Either the object or the name for which to count
     *                       the children, defaults to the root
     *                       (DATATREE_ROOT).
     *
     * @return integer
     */
    function getNumberOfChildren($parent = DATATREE_ROOT)
    {
        if (is_a($parent, 'DataTreeObject')) {
            $parent = $parent->getName();
        }
        $this->_load($parent);
        $out = $this->_extractOneLevel($this->getId($parent));

        return is_array($out) ? count($out) : 0;
    }

    /**
     * Check if an object exists or not. The root element DATATREE_ROOT always
     * exists.
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

        if ($object == DATATREE_ROOT) {
            return true;
        }

        if (array_search($object, $this->_nameMap) !== false) {
            return true;
        }

        // Consult the backend directly.
        return $this->_exists($object);
    }

    /**
     * Get the name of an object from its id.
     *
     * @param integer $id  The id for which to look up the name.
     *
     * @return string  TODO
     */
    function getName($id)
    {
        /* If no id or if id is a PEAR error, return null. */
        if (empty($id) || is_a($id, 'PEAR_Error')) {
            return null;
        }

        /* If checking name of root, return DATATREE_ROOT. */
        if ($id == DATATREE_ROOT) {
            return DATATREE_ROOT;
        }

        /* If found in the name map, return the name. */
        if (isset($this->_nameMap[$id])) {
            return $this->_nameMap[$id];
        }

        /* Not found in name map, consult the backend. */
        return $this->_getName($id);
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

        /* If checking id of root, return DATATREE_ROOT. */
        if ($name == DATATREE_ROOT) {
            return DATATREE_ROOT;
        }

        /* Flip the name map to look up the id using the name as key. */
        if (($id = array_search($name, $this->_nameMap)) !== false) {
            return $id;
        }

        /* Not found in name map, consult the backend. */
        $id = $this->_getId($name);
        if (is_null($id)) {
            return PEAR::raiseError($name . ' does not exist');
        }
        return $id;
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
        $this->_loadById($id);

        return isset($this->_data[$id]['order']) ?
            $this->_data[$id]['order'] :
            null;
    }

    /**
     * Replace all occurences of ':' in an object name with '.'.
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
     * Get the short name of an object, returns only the last portion of the
     * full name. For display purposes only.
     *
     * @static
     *
     * @param string $name  The name of the object.
     *
     * @return string  The object's short name.
     */
    function getShortName($name)
    {
        /* If there are several components to the name, explode and get the
         * last one, otherwise just return the name. */
        if (strpos($name, ':') !== false) {
            $name = explode(':', $name);
            $name = array_pop($name);
        }
        return $name;
    }

    /**
     * Returns a tree sorted by the specified attribute name and/or key.
     *
     * @abstract
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
        return PEAR::raiseError('not supported');
    }

    /**
     * Adds an object.
     *
     * @abstract
     *
     * @param mixed $object        The object to add (string or
     *                             DataTreeObject).
     * @param boolean $id_as_name  True or false to indicate if object ID is to
     *                             be used as object name. Used in situations
     *                             where there is no available unique input for
     *                             object name.
     *
     * @return TODO
     */
    function add($object, $id_as_name = false)
    {
        return PEAR::raiseError('not supported');
    }

    /**
     * Add an object.
     *
     * @private
     *
     * @param string   $name  The short object name.
     * @param integer  $id    The new object's unique ID.
     * @param integer  $pid   The unique ID of the object's parent.
     * @param integer  $order The ordering data for the object.
     *
     * @access protected
     *
     * @return TODO
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
     * Retrieve data for an object from the horde_datatree_attributes
     * table.
     *
     * @abstract
     *
     * @param integer | array $cid  The object id to fetch,
     *                              or an array of object ids.
     *
     * @return array  A hash of attributes, or a multi-level hash
     *                of object ids => their attributes.
     */
    function getAttributes($cid)
    {
        return PEAR::raiseError('not supported');
    }

    /**
     * Returns the number of objects matching a set of attribute criteria.
     *
     * @abstract
     *
     * @see buildAttributeQuery()
     *
     * @param array   $criteria   The array of criteria.
     * @param string  $parent     The parent node to start searching from.
     * @param boolean $allLevels  Return all levels, or just the direct
     *                            children of $parent? Defaults to all levels.
     * @param string  $restrict   Only return attributes with the same
     *                            attribute_name or attribute_id.
     *
     * @return TODO
     */
    function countByAttributes($criteria, $parent = DATATREE_ROOT,
                               $allLevels = true, $restrict = 'name')
    {
        return PEAR::raiseError('not supported');
    }

    /**
     * Returns a set of object ids based on a set of attribute criteria.
     *
     * @abstract
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
     *
     * @return TODO
     */
    function getByAttributes($criteria, $parent = DATATREE_ROOT,
                             $allLevels = true, $restrict = 'name', $from = 0,
                             $count = 0, $sortby_name = null,
                             $sortby_key = null, $direction = 0)
    {
        return PEAR::raiseError('not supported');
    }

    /**
     * Sorts IDs by attribute values. IDs without attributes will be added to
     * the end of the sorted list.
     *
     * @abstract
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
        return PEAR::raiseError('not supported');
    }

    /**
     * Update the data in an object. Does not change the object's
     * parent or name, just serialized data or attributes.
     *
     * @abstract
     *
     * @param DataTree $object  A DataTree object.
     *
     * @return TODO
     */
    function updateData($object)
    {
        return PEAR::raiseError('not supported');
    }

    /**
     * Sort two objects by their order field, and if that is the same,
     * alphabetically (case insensitive) by name.
     *
     * You never call this function; it's used in uasort() calls. Do
     * NOT use usort(); you'll lose key => value associations.
     *
     * @private
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
     * Sorts two objects by their sorter hash field.
     *
     * You never call this function; it's used in uasort() calls. Do NOT use
     * usort(); you'll lose key => value associations.
     *
     * @since Horde 3.1
     *
     * @private
     *
     * @param array $a  The first object
     * @param array $b  The second object
     *
     * @return integer  1 if $a should be first,
     *                 -1 if $b should be first,
     *                  0 if they are entirely equal.
     */
    function _cmpSorted($a, $b)
    {
        return intval($a['sorter'][$this->_sortHash] < $b['sorter'][$this->_sortHash]);
    }

    /**
     * Attempts to return a concrete DataTree instance based on $driver.
     *
     * @param mixed $driver  The type of concrete DataTree subclass to return.
     *                       This is based on the storage driver ($driver). The
     *                       code is dynamically included. If $driver is an array,
     *                       then we will look in $driver[0]/lib/DataTree/ for
     *                       the subclass implementation named $driver[1].php.
     * @param array $params  A hash containing any additional configuration or
     *                       connection parameters a subclass might need.
     *                       Here, we need 'group' = a string that defines
     *                       top-level groups of objects.
     *
     * @return DataTree  The newly created concrete DataTree instance, or false
     *                   on an error.
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

        include_once 'Horde/DataTree/' . $driver . '.php';
        $class = 'DataTree_' . $driver;
        if (class_exists($class)) {
            $dt = new $class($params);
            $result = $dt->_init();
            if (is_a($result, 'PEAR_Error')) {
                include_once 'Horde/DataTree/null.php';
                $dt = new DataTree_null($params);
            }
        } else {
            $dt = PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }

        return $dt;
    }

    /**
     * Attempts to return a reference to a concrete DataTree instance based on
     * $driver.
     *
     * It will only create a new instance if no DataTree instance with the same
     * parameters currently exists.
     *
     * This should be used if multiple DataTree sources (and, thus, multiple
     * DataTree instances) are required.
     *
     * This method must be invoked as: $var = &DataTree::singleton();
     *
     * @param mixed $driver  Type of concrete DataTree subclass to return,
     *                       based on storage driver ($driver). The code is
     *                       dynamically included. If $driver is an array, then
     *                       look in $driver[0]/lib/DataTree/ for subclass
     *                       implementation named $driver[1].php.
     * @param array $params  A hash containing any additional configuration or
     *                       connection parameters a subclass might need.
     *
     * @return DataTree  The concrete DataTree reference, or false on an error.
     */
    function &singleton($driver, $params = null)
    {
        static $instances = array();

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
 * Class that can be extended to save arbitrary information as part of a stored
 * object.
 *
 * @author  Stephane Huther <shuther1@free.fr>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 2.1
 * @package Horde_DataTree
 */
class DataTreeObject {

    /**
     * This object's DataTree instance.
     *
     * @var DataTree
     */
    var $datatree;

    /**
     * Key-value hash that will be serialized.
     *
     * @see getData()
     * @var array
     */
    var $data = array();

    /**
     * The unique name of this object.
     * These names have the same requirements as other object names - they must
     * be unique, etc.
     *
     * @var string
     */
    var $name;

    /**
     * If this object has ordering data, store it here.
     *
     * @var integer
     */
    var $order = null;

    /**
     * DataTreeObject constructor.
     * Just sets the $name parameter.
     *
     * @param string $name  The object name.
     */
    function DataTreeObject($name)
    {
        $this->setName($name);
    }

    /**
     * Sets the {@link DataTree} instance used to retrieve this object.
     *
     * @param DataTree $datatree  A {@link DataTree} instance.
     */
    function setDataTree(&$datatree)
    {
        $this->datatree = &$datatree;
    }

    /**
     * Gets the name of this object.
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
     * Gets the short name of this object.
     * For display purposes only.
     *
     * @return string  The object's short name.
     */
    function getShortName()
    {
        return DataTree::getShortName($this->name);
    }

    /**
     * Gets the ID of this object.
     *
     * @return string  The object's ID.
     */
    function getId()
    {
        return $this->datatree->getId($this);
    }

    /**
     * Gets the data array.
     *
     * @return array  The internal data array.
     */
    function getData()
    {
        return $this->data;
    }

    /**
     * Sets the data array.
     *
     * @param array  The data array to store internally.
     */
    function setData($data)
    {
        $this->data = $data;
    }

    /**
     * Sets the order of this object in its object collection.
     *
     * @param integer $order
     */
    function setOrder($order)
    {
        $this->order = $order;
    }

    /**
     * Returns this object's parent.
     *
     * @param string $class   Subclass of DataTreeObject to use. Defaults to
     *                        DataTreeObject. Null forces the driver to look
     *                        into the attributes table to determine the
     *                        subclass to use. If none is found it uses
     *                        DataTreeObject.
     *
     * @return DataTreeObject  This object's parent
     */
    function &getParent($class = 'DataTreeObject')
    {
        $id = $this->datatree->getParent($this);
        if (is_a($id, 'PEAR_Error')) {
            return $id;
        }
        return $this->datatree->getObjectById($id, $class);
    }

    /**
     * Returns a child of this object.
     *
     * @param string $name         The child's name.
     * @param boolean $autocreate  If true and no child with the given name
     *                             exists, one gets created.
     */
    function &getChild($name, $autocreate = true)
    {
        $name = $this->getShortName() . ':' . $name;

        /* If the child shouldn't get created, we don't check for its
         * existance to return the "not found" error of
         * getObject(). */
        if (!$autocreate || $this->datatree->exists($name)) {
            $child = &$this->datatree->getObject($name);
        } else {
            $child = new DataTreeObject($name);
            $child->setDataTree($this->datatree);
            $this->datatree->add($child);
        }

        return $child;
    }

    /**
     * Saves any changes to this object to the backend permanently. New objects
     * are added instead.
     *
     * @return boolean|PEAR_Error  PEAR_Error on failure.
     */
    function save()
    {
        if ($this->datatree->exists($this)) {
            return $this->datatree->updateData($this);
        } else {
            return $this->datatree->add($this);
        }
    }

    /**
     * Delete this object from the backend permanently.
     *
     * @return boolean|PEAR_Error  PEAR_Error on failure.
     */
    function delete()
    {
        return $this->datatree->remove($this);
    }

    /**
     * Gets one of the attributes of the object, or null if it isn't defined.
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
     * Sets one of the attributes of the object.
     *
     * @param string $attribute  The attribute to set.
     * @param mixed $value       The value for $attribute.
     */
    function set($attribute, $value)
    {
        $this->data[$attribute] = $value;
    }

}
