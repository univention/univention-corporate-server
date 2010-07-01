<?php

require_once 'Horde/DataTree.php';

/**
 * Horde_Share_datatree:: provides the datatree backend for the horde share
 * driver.
 *
 * $Horde: framework/Share/Share/datatree.php,v 1.16.2.9 2009-01-06 15:23:36 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 * Copyright 2002-2007 Infoteck Internet <webmaster@infoteck.qc.ca>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Joel Vandal <joel@scopserv.com>
 * @author  Mike Cochrame <mike@graftonhall.co.nz>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @since   Horde 3.2
 * @package Horde_Share
 */
class Horde_Share_datatree extends Horde_Share {

    /**
     * The Horde_Share_Object subclass to instantiate objects as
     *
     * @var string
     */
    var $_shareObject = 'Horde_Share_Object_datatree';

    /**
     * Pointer to a DataTree instance to manage/store shares
     *
     * @var DataTree
     */
    var $_datatree;

    /**
     * Initializes the object.
     */
    function __wakeup()
    {
        if (empty($GLOBALS['conf']['datatree']['driver'])) {
            Horde::fatal('You must configure a DataTree backend to use Shares.', __FILE__, __LINE__);
        }

        $driver = $GLOBALS['conf']['datatree']['driver'];
        $this->_datatree = &DataTree::singleton(
            $driver,
            array_merge(Horde::getDriverConfig('datatree', $driver),
                        array('group' => 'horde.shares.' . $this->_app))
        );

        foreach (array_keys($this->_cache) as $name) {
            if (!is_a($this->_datatree, 'PEAR_Error')) {
                $this->_cache[$name]->setShareOb($this);
                $this->_cache[$name]->datatreeObject->setDataTree($this->_datatree);
            }
        }

        parent::__wakeup();
    }

    /**
     * Returns a Horde_Share_Object_datatree object corresponding to the given
     * share name, with the details retrieved appropriately.
     *
     * @param string $name  The name of the share to retrieve.
     *
     * @return Horde_Share_Object_datatree  The requested share.
     */
    function &_getShare($name)
    {
        $datatreeObject = $this->_datatree->getObject($name, 'DataTreeObject_Share');
        if (is_a($datatreeObject, 'PEAR_Error')) {
            return $datatreeObject;
        }
        $share = &new $this->_shareObject($datatreeObject);
        return $share;
    }

    /**
     * Returns a Horde_Share_Object_datatree object corresponding to the given
     * unique ID, with the details retrieved appropriately.
     *
     * @param string $cid  The id of the share to retrieve.
     *
     * @return Horde_Share_Object_datatree  The requested share.
     */
    function &_getShareById($id)
    {
        $datatreeObject = $this->_datatree->getObjectById($id, 'DataTreeObject_Share');
        if (is_a($datatreeObject, 'PEAR_Error')) {
            return $datatreeObject;
        }
        $share = &new $this->_shareObject($datatreeObject);
        return $share;
    }

    /**
     * Returns an array of Horde_Share_Object_datatree objects corresponding
     * to the given set of unique IDs, with the details retrieved
     * appropriately.
     *
     * @param array $cids  The array of ids to retrieve.
     *
     * @return array  The requested shares.
     */
    function &_getShares($ids)
    {
        $shares = array();
        $objects = &$this->_datatree->getObjects($ids, 'DataTreeObject_Share');
        if (is_a($objects, 'PEAR_Error')) {
            return $objects;
        }
        foreach (array_keys($objects) as $key) {
            if (is_a($objects[$key], 'PEAR_Error')) {
                return $objects[$key];
            }
            $shares[$key] = &new $this->_shareObject($objects[$key]);
        }
        return $shares;
    }

    /**
     * Lists *all* shares for the current app/share, regardless of
     * permissions.
     *
     * @return array  All shares for the current app/share.
     */
    function &_listAllShares()
    {
        $sharelist = $this->_datatree->get(DATATREE_FORMAT_FLAT, DATATREE_ROOT,
                                           true);
        if (is_a($sharelist, 'PEAR_Error') || !count($sharelist)) {
            // If we got back an error or an empty array, just return it.
            return $sharelist;
        }
        unset($sharelist[DATATREE_ROOT]);

        return $this->getShares(array_keys($sharelist));
    }

    /**
     * Returns an array of all shares that $userid has access to.
     *
     * @param string $userid     The userid of the user to check access for.
     * @param integer $perm      The level of permissions required.
     * @param mixed $attributes  Restrict the shares counted to those
     *                           matching $attributes. An array of
     *                           attribute/values pairs or a share owner
     *                           username.
     *
     * @return array  The shares the user has access to.
     */
    function &_listShares($userid, $perm = PERMS_SHOW, $attributes = null,
                          $from = 0, $count = 0, $sort_by = null,
                          $direction = 0)
    {
        $key = serialize(array($userid, $perm, $attributes));
        if (empty($this->_listCache[$key])) {
            $criteria = $this->_getShareCriteria($userid, $perm, $attributes);
            $sharelist = $this->_datatree->getByAttributes($criteria,
                                                           DATATREE_ROOT,
                                                           true, 'id', $from,
                                                           $count, $sort_by,
                                                           null, $direction);
            if (is_a($sharelist, 'PEAR_Error')) {
                return $sharelist;
            }
            $this->_listCache[$key] = array_keys($sharelist);
        }

        return $this->_listCache[$key];
    }

    /**
     * Returns the number of shares that $userid has access to.
     *
     * @since Horde 3.2
     *
     * @param string $userid     The userid of the user to check access for.
     * @param integer $perm      The level of permissions required.
     * @param mixed $attributes  Restrict the shares counted to those
     *                           matching $attributes. An array of
     *                           attribute/values pairs or a share owner
     *                           username.
     *
     * @return integer  The number of shares
     */
    function _countShares($userid, $perm = PERMS_SHOW, $attributes = null)
    {
        $criteria = $this->_getShareCriteria($userid, $perm, $attributes);
        return $this->_datatree->countByAttributes($criteria, DATATREE_ROOT, true, 'id');
    }

    /**
     * Returns a new share object.
     *
     * @param string $name  The share's name.
     *
     * @return Horde_Share_Object_datatree  A new share object.
     */
    function &_newShare($name)
    {
        $datatreeObject = new DataTreeObject_Share($name);
        $datatreeObject->setDataTree($this->_datatree);
        $share = &new $this->_shareObject($datatreeObject);
        return $share;
    }

    /**
     * Adds a share to the shares system.
     *
     * The share must first be created with
     * Horde_Share_datatreee::_newShare(), and have any initial details added
     * to it, before this function is called.
     *
     * @param Horde_Share_Object_datatree $share  The new share object.
     */
    function _addShare(&$share)
    {
        return $this->_datatree->add($share->datatreeObject);
    }

    /**
     * Removes a share from the shares system permanently.
     *
     * @param Horde_Share_Object_datatree $share  The share to remove.
     */
    function _removeShare(&$share)
    {
        return $this->_datatree->remove($share->datatreeObject);
    }

    /**
     * Checks if a share exists in the system.
     *
     * @param string $share  The share to check.
     *
     * @return boolean  True if the share exists.
     */
    function _exists($share)
    {
        return $this->_datatree->exists($share);
    }

    /**
     * Returns an array of criteria for querying shares.
     * @access protected
     *
     * @param string  $userid      The userid of the user to check access for.
     * @param integer $perm        The level of permissions required.
     * @param mixed   $attributes  Restrict the shares returned to those who
     *                             have these attribute values.
     *
     * @return array  The criteria tree for fetching this user's shares.
     */
    function _getShareCriteria($userid, $perm = PERMS_SHOW, $attributes = null)
    {
        if (!empty($userid)) {
            $criteria = array(
                'OR' => array(
                    // (owner == $userid)
                    array(
                        'AND' => array(
                            array('field' => 'name', 'op' => '=', 'test' => 'owner'),
                            array('field' => 'value', 'op' => '=', 'test' => $userid))),

                    // (name == perm_users and key == $userid and val & $perm)
                    array(
                        'AND' => array(
                            array('field' => 'name', 'op' => '=', 'test' => 'perm_users'),
                            array('field' => 'key', 'op' => '=', 'test' => $userid),
                            array('field' => 'value', 'op' => '&', 'test' => $perm))),

                    // (name == perm_creator and val & $perm)
                    array(
                        'AND' => array(
                            array('field' => 'name', 'op' => '=', 'test' => 'perm_creator'),
                            array('field' => 'value', 'op' => '&', 'test' => $perm))),

                    // (name == perm_default and val & $perm)
                    array(
                        'AND' => array(
                            array('field' => 'name', 'op' => '=', 'test' => 'perm_default'),
                            array('field' => 'value', 'op' => '&', 'test' => $perm)))));

            // If the user has any group memberships, check for those also.
            require_once 'Horde/Group.php';
            $group = &Group::singleton();
            $groups = $group->getGroupMemberships($userid, true);
            if (!is_a($groups, 'PEAR_Error') && $groups) {
                // (name == perm_groups and key in ($groups) and val & $perm)
                $criteria['OR'][] = array(
                    'AND' => array(
                        array('field' => 'name', 'op' => '=', 'test' => 'perm_groups'),
                        array('field' => 'key', 'op' => 'IN', 'test' => array_keys($groups)),
                        array('field' => 'value', 'op' => '&', 'test' => $perm)));
            }
        } else {
            $criteria = array(
                'AND' => array(
                     array('field' => 'name', 'op' => '=', 'test' => 'perm_guest'),
                     array('field' => 'value', 'op' => '&', 'test' => $perm)));
        }

        if (is_array($attributes)) {
            // Build attribute/key filter.
            foreach ($attributes as $key => $value) {
                $criteria = array(
                    'AND' => array(
                        $criteria,
                        array(
                            'JOIN' => array(
                                'AND' => array(
                                    array('field' => 'name', 'op' => '=', 'test' => $key),
                                    array('field' => 'value', 'op' => '=', 'test' => $value))))));
            }
        } elseif (!is_null($attributes)) {
            // Restrict to shares owned by the user specified in the
            // $attributes string.
            $criteria = array(
                'AND' => array(
                    $criteria,
                    array(
                        'JOIN' => array(
                            array('field' => 'name', 'op' => '=', 'test' => 'owner'),
                            array('field' => 'value', 'op' => '=', 'test' => $attributes)))));
        }

        return $criteria;
    }

}

/**
 * Extension of the Horde_Share_Object class for storing share information in
 * the DataTree driver.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @author  Jan Schneider <jan@horde.org>
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @since   Horde 3.2
 * @package Horde_Share
 */
class Horde_Share_Object_datatree extends Horde_Share_Object {

    /**
     * The actual storage object that holds the data.
     *
     * @var mixed
     */
    var $datatreeObject;

    /**
     * Constructor.
     *
     * @param DataTreeObject_Share $datatreeObject  A DataTreeObject_Share
     *                                              instance.
     */
    function Horde_Share_Object_datatree($datatreeObject)
    {
        if (is_a($datatreeObject, 'PEAR_Error')) {
            debug_context();
        }
        $this->datatreeObject = $datatreeObject;
    }

    /**
     * Sets an attribute value in this object.
     *
     * @param string $attribute  The attribute to set.
     * @param mixed $value       The value for $attribute.
     *
     * @return mixed  True if setting the attribute did succeed, a PEAR_Error
     *                otherwise.
     */
    function _set($attribute, $value)
    {
        return $this->datatreeObject->set($attribute, $value);
    }

    /**
     * Returns one of the attributes of the object, or null if it isn't
     * defined.
     *
     * @param string $attribute  The attribute to retrieve.
     *
     * @return mixed  The value of the attribute, or an empty string.
     */
    function _get($attribute)
    {
        return $this->datatreeObject->get($attribute);
    }

    /**
     * Returns the ID of this share.
     *
     * @return string  The share's ID.
     */
    function _getId()
    {
        return $this->datatreeObject->getId();
    }

    /**
     * Returns the name of this share.
     *
     * @return string  The share's name.
     */
    function _getName()
    {
        return $this->datatreeObject->getName();
    }

    /**
     * Saves the current attribute values.
     */
    function _save()
    {
        return $this->datatreeObject->save();
    }

    /**
     * Checks to see if a user has a given permission.
     *
     * @param string $userid       The userid of the user.
     * @param integer $permission  A PERMS_* constant to test for.
     * @param string $creator      The creator of the event.
     *
     * @return boolean  Whether or not $userid has $permission.
     */
    function hasPermission($userid, $permission, $creator = null)
    {
        if ($userid == $this->datatreeObject->get('owner')) {
            return true;
        }

        return $GLOBALS['perms']->hasPermission($this->getPermission(),
                                                $userid, $permission, $creator);
    }

    /**
     * Sets the permission of this share.
     *
     * @param Horde_Permission $perm  Permission object.
     * @param boolean $update         Should the share be saved
     *                                after this operation?
     *
     * @return boolean  True if no error occured, PEAR_Error otherwise
     */
    function setPermission(&$perm, $update = true)
    {
        $this->datatreeObject->data['perm'] = $perm->getData();
        if ($update) {
            return $this->datatreeObject->save();
        }
        return true;
    }

    /**
     * Returns the permission of this share.
     *
     * @return Horde_Permission  Permission object that represents the
     *                           permissions on this share
     */
    function &getPermission()
    {
        $perm = new Horde_Permission($this->datatreeObject->getName());
        $perm->data = isset($this->datatreeObject->data['perm'])
            ? $this->datatreeObject->data['perm']
            : array();

        return $perm;
    }

}

/**
 * Extension of the DataTreeObject class for storing Share information in the
 * DataTree driver. If you want to store specialized Share information, you
 * should extend this class instead of extending DataTreeObject directly.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.0
 * @package Horde_Share
 */
class DataTreeObject_Share extends DataTreeObject {

    /**
     * Returns the properties that need to be serialized.
     *
     * @return array  List of serializable properties.
     */
    function __sleep()
    {
        $properties = get_object_vars($this);
        unset($properties['datatree']);
        $properties = array_keys($properties);
        return $properties;
    }

    /**
     * Maps this object's attributes from the data array into a format that we
     * can store in the attributes storage backend.
     *
     * @access protected
     *
     * @param boolean $permsonly  Only process permissions? Lets subclasses
     *                            override part of this method while handling
     *                            their additional attributes seperately.
     *
     * @return array  The attributes array.
     */
    function _toAttributes($permsonly = false)
    {
        // Default to no attributes.
        $attributes = array();

        foreach ($this->data as $key => $value) {
            if ($key == 'perm') {
                foreach ($value as $type => $perms) {
                    if (is_array($perms)) {
                        foreach ($perms as $member => $perm) {
                            $attributes[] = array('name' => 'perm_' . $type,
                                                  'key' => $member,
                                                  'value' => $perm);
                        }
                    } else {
                        $attributes[] = array('name' => 'perm_' . $type,
                                              'key' => '',
                                              'value' => $perms);
                    }
                }
            } elseif (!$permsonly) {
                $attributes[] = array('name' => $key,
                                      'key' => '',
                                      'value' => $value);
            }
        }

        return $attributes;
    }

    /**
     * Takes in a list of attributes from the backend and maps it to our
     * internal data array.
     *
     * @access protected
     *
     * @param array $attributes   The list of attributes from the backend
     *                            (attribute name, key, and value).
     * @param boolean $permsonly  Only process permissions? Lets subclasses
     *                            override part of this method while handling
     *                            their additional attributes seperately.
     */
    function _fromAttributes($attributes, $permsonly = false)
    {
        // Initialize data array.
        $this->data['perm'] = array();

        foreach ($attributes as $attr) {
            if (substr($attr['name'], 0, 4) == 'perm') {
                if (!empty($attr['key'])) {
                    $this->data['perm'][substr($attr['name'], 5)][$attr['key']] = $attr['value'];
                } else {
                    $this->data['perm'][substr($attr['name'], 5)] = $attr['value'];
                }
            } elseif (!$permsonly) {
                $this->data[$attr['name']] = $attr['value'];
            }
        }
    }

}
