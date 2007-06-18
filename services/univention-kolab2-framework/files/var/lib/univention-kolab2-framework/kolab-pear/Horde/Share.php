<?php

require_once 'Horde/DataTree.php';

/**
 * Horde_Share:: provides an interface to all shares a user might have.
 * Its methods take care of any site-specific restrictions configured in
 * in the application's prefs.php and conf.php files.
 *
 * $Horde: framework/Share/Share.php,v 1.90 2004/05/21 17:53:43 chuck Exp $
 *
 * Copyright 2002-2004 Joel Vandal <jvandal@infoteck.qc.ca>
 * Copyright 2002-2004 Infoteck Internet <webmaster@infoteck.qc.ca>
 * Copyright 2002-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Joel Vandal <jvandal@infoteck.qc.ca>
 * @author  Mike Cochrame <mike@graftonhall.co.nz>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Share
 */
class Horde_Share {

    /**
     * Pointer to a DataTree instance to manage/store shares
     *
     * @var object DataTree $_datatree
     */
    var $_datatree;

    /**
     * The application we're managing shares for.
     *
     * @var string $_app
     */
    var $_app;

    /**
     * The subclass of DataTreeObject to instantiate shares as.
     *
     * @var string $_shareObject
     */
    var $_shareObject = 'DataTreeObject_Share';

    /**
     * A cache of all shares that have been retrieved, so we don't hit
     * the backend again and again for them.
     *
     * @var array $_cache
     */
    var $_cache = array();

    /**
     * Cache used for listShares().
     *
     * @var array $_listcache
     */
    var $_listcache = array();

    /**
     * A list of objects that we're currently sorting, for reference
     * during the sorting algorithm.
     *
     * @var array $_sortList
     */
    var $_sortList;

    /**
     * Attempts to return a reference to a concrete Horde_Share
     * instance. It will only create a new instance if no Horde_Share
     * instance currently exists.
     *
     * This method must be invoked as:
     *   $var = &Horde_Share::singleton($app);
     *
     * @access public
     *
     * @param string $app    The applications that the shares relate to.
     *                       relate to.
     *
     * @return object Share  The concrete Share reference, or false on an
     *                       error.
     */
    function &singleton($app)
    {
        static $shares;

        if (!isset($shares[$app])) {
            $shares[$app] = new Horde_Share($app);
        }

        return $shares[$app];
    }

    /**
     * Constructor.
     * Reads all the user's shares from the prefs object or builds
     * a new share from the standard values given in prefs.php.
     *
     * @access public
     *
     * @param string $app   The applications that the shares relate ro.
     *                      relate to.
     */
    function Horde_Share($app)
    {
        global $conf, $registry;

        if (!isset($conf['datatree']['driver'])) {
            Horde::fatal('You must configure a DataTree backend to use Shares.');
        }

        $driver = $conf['datatree']['driver'];
        $this->_app = $app;
        $this->_datatree = &DataTree::singleton(
            $driver,
            array_merge(Horde::getDriverConfig('datatree', $driver), array('group' => 'horde.shares.' . $app))
        );
    }

    /**
     * Return a DataTreeObject_Share object corresponding to the given
     * share name, with the details retrieved appropriately.
     *
     * @access public
     *
     * @param string $name  The name of the share to retrieve.
     *
     * @return TODO
     */
    function &getShare($name)
    {
        if (isset($this->_cache[$name])) {
            return $this->_cache[$name];
        }

        $this->_cache[$name] = &$this->_datatree->getObject($name, $this->_shareObject);
        if (!is_a($this->_cache[$name], 'PEAR_Error')) {
            $this->_cache[$name]->setShareOb($this);
        }

        return $this->_cache[$name];
    }

    /**
     * Return a DataTreeObject_Share object corresponding to the given
     * unique ID, with the details retrieved appropriately.
     *
     * @access public
     *
     * @param string $cid  The id of the share to retrieve.
     *
     * @return TODO
     */
    function &getShareById($cid)
    {
        $share = $this->_datatree->getObjectById($cid, $this->_shareObject);
        if (!is_a($share, 'PEAR_Error')) {
            $share->setShareOb($this);
        }
        return $share;
    }

    /**
     * Return an array of DataTreeObject_Share objects corresponding
     * to the given set of unique IDs, with the details retrieved
     * appropriately.
     *
     * @access public
     *
     * @param array $cids  The array of ids to retrieve.
     *
     * @return TODO
     */
    function &getShares($cids)
    {
        $shares = $this->_datatree->getObjects($cids, $this->_shareObject);
        if (is_a($shares, 'PEAR_Error')) {
            return $shares;
        }

        $keys = array_keys($shares);
        foreach ($keys as $key) {
            if (is_a($shares[$key], 'PEAR_Error')) {
                return $shares[$key];
            }

            $this->_cache[$key] = &$shares[$key];
            $shares[$key]->setShareOb($this);
        }

        return $shares;
    }

    /**
     * Return a new share object.
     *
     * @access public
     *
     * @param string $name  The share's name.
     *
     * @return object DataTreeObject_Share  A new share object.
     */
    function &newShare($name)
    {
        if (empty($name)) {
            return PEAR::raiseError('Share names must be non-empty');
        }
        $share = &new $this->_shareObject($name);
        $share->setShareOb($this);
        return $share;
    }

    /**
     * Add a share to the shares system. The share must first be
     * created with Horde_Share::newShare(), and have any initial
     * details added to it, before this function is called.
     *
     * @access public
     *
     * @param object DataTreeObject_Share $share The new share object.
     *
     * @return TODO
     */
    function addShare($share)
    {
        if (!is_a($share, 'DataTreeObject_Share')) {
            return PEAR::raiseError('Shares must be DataTreeObject_Share objects or extend that class.');
        }

        $perm = &$GLOBALS['perms']->newPermission($share->getName());

        /* Give the owner full access */
        $perm->addUserPermission($share->get('owner'), PERMS_SHOW, false);
        $perm->addUserPermission($share->get('owner'), PERMS_READ, false);
        $perm->addUserPermission($share->get('owner'), PERMS_EDIT, false);
        $perm->addUserPermission($share->get('owner'), PERMS_DELETE, false);

        $share->setPermission($perm, false);

        return $this->_datatree->add($share);
    }

    /**
     * Store updated data - name, etc. - of a share to the backend
     * system.
     *
     * @access public
     *
     * @param object DataTreeObject_Share $share   The share to update.
     *
     * @return TODO
     */
    function updateShare($share)
    {
        if (!is_a($share, 'DataTreeObject_Share')) {
            return PEAR::raiseError('Shares must be DataTreeObject_Share objects or extend that class.');
        }
        return $this->_datatree->updateData($share);
    }

    /**
     * Remove a share from the shares system permanently.
     *
     * @param object DataTreeObject_Share $share  The share to remove.
     */
    function removeShare($share)
    {
        if (!is_a($share, 'DataTreeObject_Share')) {
            return PEAR::raiseError('Shares must be DataTreeObject_Share objects or extend that class.');
        }

        return $this->_datatree->remove($share);
    }

    /**
     * Check to see if $share has any child shares.
     *
     * @access public
     *
     * @param object DataTreeObject_Share $share  The share to remove.
     *
     * @return boolean  TODO
     */
    function hasChildren($share)
    {
        if (!is_a($share, 'DataTreeObject_Share')) {
            return PEAR::raiseError('Shares must be DataTreeObject_Share objects or extend that class.');
        }

        return (boolean)$this->_datatree->getNumberOfChildren($share);
    }

    /**
     * Get a $share's direct parent object.
     *
     * @access public
     *
     * @param string $share  Get the parent of this share.
     *
     * @return object DataTreeObject_Share  The parent share, if it exists.
     */
    function &getParent($child)
    {
        $id = $this->_datatree->getParent($child);
        if (is_a($id, 'PEAR_Error')) {
            return $id;
        }

        if (!$id || ($id == '-1')) {
            return PEAR::raiseError('Parent does not exist.');
        }

        return $this->getShareById($id);
    }

    /**
     * TODO
     *
     * @access public
     *
     * @param TODO
     *
     * @return TODO
     */
    function getShareId($share)
    {
        return $this->_datatree->getId($share->getName());
    }

    /**
     * Utility function to be used with uasort() (do NOT use usort;
     * you'll lose key => value associations) for sorting arrays of
     * Horde_Share:: objects.
     *
     * Usage: uasort($list, array('Horde_Share', '_sortShares'));
     *
     * @access private
     */
    function _sortShares($a, $b)
    {
        $aParts = explode(':', $a->getName());
        $bParts = explode(':', $b->getName());

        $min = min(count($aParts), count($bParts));
        $idA = '';
        $idB = '';
        for ($i = 0; $i < $min; $i++) {
            if ($idA) {
                $idA .= ':';
                $idB .= ':';
            }
            $idA .= $aParts[$i];
            $idB .= $bParts[$i];

            if ($idA != $idB) {
                $curA = $this->_sortList[$idA];
                $curB = $this->_sortList[$idB];
                return strnatcasecmp($curA->get('name'), $curB->get('name'));
            }
        }

        return count($aParts) > count($bParts);
    }

    /**
     * Check if a share exists in the system.
     *
     * @access public
     *
     * @param string $share  The share to check.
     *
     * @return boolean  True if the share exists, false otherwise.
     */
    function exists($share)
    {
        return $this->_datatree->exists($share);
    }

    /**
     * Return an array of all shares that $userid has access to.
     *
     * @param string $userid               The userid of the user to check
     *                                     access for.
     * @param optional integer $perm       The level of permissions required.
     * @param optional boolean $owner      Only return shares that $userid
     *                                     owns.
     * @param optional string $parent      The parent share to start
     *                                     searching at.
     * @param optional boolean $allLevels  Return all levels, or just the
     *                                     direct children of $parent?
     *                                     Defaults to all levels.
     *
     * @return array  The shares the user has access to.
     */
    function &listShares($userid, $perm = PERMS_SHOW, $owner = false,
                         $parent = '-1', $allLevels = true)
    {
        $key = serialize(array($this->_app, $userid, $perm, $owner));
        if (empty($this->_listcache[$key])) {
            if (!empty($userid)) {
                if ($owner) {
                    $criteria = array(
                        'AND' => array(
                            array('field' => 'name', 'op' => '=', 'test' => 'owner'),
                            array('field' => 'value', 'op' => '=', 'test' => $userid)));
                } else {
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

                    // If the user has any group memberships, check
                    // for those also.
                    require_once 'Horde/Group.php';
                    $group = &Group::singleton();
                    $groups = $group->getGroupMemberships($userid, true);
                    if (!is_a($groups, 'PEAR_Error') && count($groups)) {
                        // (name == perm_groups and key in ($groups) and val & $perm)
                        $criteria['OR'][] = array(
                            'AND' => array(
                                array('field' => 'name', 'op' => '=', 'test' => 'perm_groups'),
                                array('field' => 'key', 'op' => 'IN', 'test' => '(' . implode(', ', array_keys($groups)) . ')'),
                                array('field' => 'value', 'op' => '&', 'test' => $perm)));
                    }
                }
            } else {
                $criteria = array(
                    'AND' => array(
                        array('field' => 'name', 'op' => '=', 'test' => 'perm_guest'),
                        array('field' => 'value', 'op' => '&', 'test' => $perm)));
            }

            $sharelist = $this->_datatree->getByAttributes($criteria, $parent, $allLevels);
            if (is_a($sharelist, 'PEAR_Error') || !count($sharelist)) {
                /* If we got back an error or an empty array, pass it
                 * back to the caller. */
                return $sharelist;
            }

            /* Make sure getShares() didn't return an error. */
            $shares = &$this->getShares(array_keys($sharelist));
            if (is_a($shares, 'PEAR_Error')) {
                return $shares;
            }

            $this->_listcache[$key] = &$shares;
            $this->_sortList = $this->_listcache[$key];
            uasort($this->_listcache[$key], array($this, '_sortShares'));
            $this->_sortList = null;
        }

        return $this->_listcache[$key];
    }

    /**
     * List *all* shares for the current app/share, regardless of
     * permissions. This is for admin functionality and scripting
     * tools, and shouldn't be called from user-level code!
     *
     * @access public
     *
     * @param optional boolean $parent  Start the listing at a certain point
     *                                  in the tree.
     *                                  Defaults to '-1', the root.
     *
     * @return array  All shares for the current app/share.
     */
    function listAllShares($parent = '-1')
    {
        $sharelist = $this->_datatree->get(DATATREE_FORMAT_FLAT, $parent, true);
        if (is_a($sharelist, 'PEAR_Error') || !count($sharelist)) {
            // If we got back an error or an empty array, just
            // return it.
            return $sharelist;
        }
        unset($sharelist[$parent]);

        $shares = &$this->getShares(array_keys($sharelist));
        if (is_a($shares, 'PEAR_Error')) {
            return $shares;
        }

        $this->_sortList = $shares;
        uasort($shares, array($this, '_sortShares'));
        $this->_sortList = null;

        return $shares;
    }

    /**
     * TODO
     *
     * @access public
     *
     * @param TODO
     * @param TODO
     *
     * @return TODO
     */
    function getPermissions($share, $user = null)
    {
        if (!is_a($share, 'DataTreeObject_share')) {
            $share = &$this->getShare($share);
        }

        $perm = &$share->getPermission();
        return $GLOBALS['perms']->getPermissions($perm, $user);
    }

    /**
     * Returns the Identity for a particular share owner.
     *
     * @access public
     *
     * @param mixed $share  The share to fetch the Identity for - either
     *                      the string name, or the DataTreeObject_Share
     *                      object.
     *
     * @return string  The preference's value.
     */
    function &getIdentityByShare($share)
    {
        if (!is_a($share, 'DataTreeObject_Share')) {
            $share = $this->getShare($share);
            if (is_a($share, 'PEAR_Error')) {
                return null;
            }
        }

        require_once 'Horde/Identity.php';
        $owner = $share->get('owner');
        return $ret = &Identity::singleton('none', $owner);
    }

}

/**
 * Extension of the DataTreeObject class for storing Share information
 * in the DataTree driver. If you want to store specialized Share
 * information, you should extend this class instead of extending
 * DataTreeObject directly.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Share
 */
class DataTreeObject_Share extends DataTreeObject {

    /**
     * The Horde_Share object which this share came from - needed for
     * updating data in the backend to make changes stick, etc.
     *
     * @var object Horde_Share $_shareOb
     */
    var $_shareOb;

    /**
     * The DataTreeObject_Share constructor. Just makes sure to call
     * the parent constructor so that the share's is is set properly.
     *
     * @access public
     *
     * @param string $id  The id of the share.
     */
    function DataTreeObject_Share($id)
    {
        parent::DataTreeObject($id);
        if (is_null($this->data)) {
            $this->data = array();
        }
    }

    /**
     * Associates a Share object with this share.
     *
     * @access public
     *
     * @param object Share $shareOb The Share object.
     */
    function setShareOb(&$shareOb)
    {
        $this->_shareOb = &$shareOb;
    }

    /**
     * TODO
     *
     * @access public
     *
     * @return TODO
     */
    function getId()
    {
        return $this->_shareOb->getShareId($this);
    }

    /**
     * Get this share's parent object.
     *
     * @access public
     *
     * @return object DataTreeObject_Share  The parent share, if it exists.
     */
    function &getParent()
    {
        return $this->_shareOb->getParent($this);
    }

    /**
     * Gives a user certain privileges for this share.
     *
     * @access public
     *
     * @param string $userid       The userid of the user.
     * @param integer $permission  A PERMS_* constant.
     */
    function addUserPermission($userid, $permission)
    {
        $perm = &$this->getPermission();
        $perm->addUserPermission($userid, $permission, false);
        $this->setPermission($perm);
    }

    /**
     * Removes a certain privileges from a user.
     *
     * @access public
     *
     * @param string $userid       The userid of the user.
     * @param integer $permission  A PERMS_* constant.
     */
    function removeUserPermission($userid, $permission)
    {
        $perm = &$this->getPermission();
        $perm->removeUserPermission($userid, $permission, false);
        $this->setPermission($perm);
    }

    /**
     * Gives a group certain privileges for this share.
     *
     * @access public
     *
     * @param string $group        The group to add permissions for.
     * @param integer $permission  A PERMS_* constant.
     */
    function addGroupPermission($group, $permission)
    {
        $perm = &$this->getPermission();
        $perm->addGroupPermission($group, $permission, false);
        $this->setPermission($perm);
    }

    /**
     * Removes a certain privileges from a group.
     *
     * @access public
     *
     * @param string $group         The group to remove permissions from.
     * @param constant $permission  A PERMS_* constant.
     */
    function removeGroupPermission($group, $permission)
    {
        $perm = &$this->getPermission();
        $perm->removeGroupPermission($group, $permission, false);
        $this->setPermission($perm);
    }

    /**
     * Checks to see if a user has a given permission.
     *
     * @access public
     *
     * @param string $userid            The userid of the user.
     * @param integer $priv             A PERMS_* constant to test for.
     * @param optional string $creator  The creator of the event.
     *
     * @return boolean  Whether or not $userid has $permission.
     */
    function hasPermission($userid, $permission, $creator = null)
    {
        if ($userid == $this->get('owner')) {
            return true;
        }

        if ($this->get('type') == 0) {
            return false;
        }

        return $GLOBALS['perms']->hasPermission($this->getPermission(), $userid, $permission, $creator);
    }

    /**
     * Remove a user from this share
     *
     * @access public
     *
     * @param string $userid  The userid of the user to remove
     */
    function removeUser($userid)
    {
        /* Remove all $userid's permissions. */
        $perm = &$this->getPermission();
        $perm->removeUserPermission($userid, PERMS_SHOW, false);
        $perm->removeUserPermission($userid, PERMS_READ, false);
        $perm->removeUserPermission($userid, PERMS_EDIT, false);
        $perm->removeUserPermission($userid, PERMS_DELETE, false);
    }

    /**
     * Returns an array containing all the userids of the users with
     * access to this share.
     *
     * @access public
     *
     * @param optional integer $perm_level  List only users with this permission
     *                                      level. Defaults to all users.
     *
     * @return array  The users with access to this share.
     */
    function listUsers($perm_level = null)
    {
        $perm = &$this->getPermission();
        return array_keys($perm->getUserPermissions($perm_level));
    }

    /**
     * Returns an array containing all the groupids of the groups
     * with access to this share.
     *
     * @access public
     *
     * @param optional integer $perm_level  List only users with this permission
     *                                      level. Defaults to all users.
     *
     * @return array  The users with access to this share.
     */
    function listGroups($perm_level = null)
    {
        $perm = &$this->getPermission();
        return array_keys($perm->getGroupPermissions($perm_level));
    }

    /**
     * TODO
     *
     * @access public
     *
     * @param TODO
     * @param optional boolean $update  TODO
     *
     * @return TODO
     */
    function setPermission(&$perm, $update = true)
    {
        $this->data['perm'] = $perm->getData();
        if ($update) {
            return $this->_shareOb->updateShare($this);
        }
        return true;
    }

    /**
     * TODO
     *
     * @access public
     *
     * @return TODO
     */
    function &getPermission()
    {
        $perm = &new DataTreeObject_Permission($this->getName());
        $perm->data = isset($this->data['perm']) ? $this->data['perm'] : array();

        return $perm;
    }

    /**
     * Force all children of this share to inherit the permissions set
     * on this share.
     *
     * @access public
     *
     * @return TODO
     */
    function inheritPermissions()
    {
        $perm = &$this->getPermission();
        $children = $this->_shareOb->listAllShares($this->getName());
        if (is_a($children, 'PEAR_Error')) {
            return $children;
        }

        foreach ($children as $child) {
            $child->setPermission($perm);
        }

        return true;
    }

    /**
     * Save any changes to this object to the backend permanently.
     *
     * @access public
     *
     * @return mixed  Either true or a PEAR_Error on error.
     */
    function save()
    {
        return $this->_shareOb->updateShare($this);
    }

    /**
     * Map this object's attributes from the data array into a format
     * that we can store in the attributes storage backend.
     *
     * @access private
     *
     * @param optional boolean $permsonly  Only process permissions? Lets
     *                                     subclasses override part of this
     *                                     method while handling their
     *                                     additional attributes seperately.
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
     * Take in a list of attributes from the backend and map it to our
     * internal data array.
     *
     * @access public
     *
     * @param array $attributes            The list of attributes from the
     *                                     backend (attribute name, key, and
     *                                     value).
     * @param optional boolean $permsonly  Only process permissions? Lets
     *                                     subclasses override part of this
     *                                     method while handling their
     *                                     additional attributes seperately.
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
