<?php
/**
 * The Turba_Driver:: class provides a common abstracted interface to the
 * various directory search drivers.  It includes functions for searching,
 * adding, removing, and modifying directory entries.
 *
 * $Horde: turba/lib/Driver/share.php,v 1.11.2.7 2009-10-07 16:16:38 mrubinsk Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jon Parise <jon@csh.rit.edu>
 * @package Turba
 */
class Turba_Driver_share extends Turba_Driver {

    /**
     * Horde_Share object for this source.
     *
     * @var Horde_Share
     */
    var $_share;

    /**
     * Underlying driver object for this source.
     *
     * @var Turba_Driver
     */
    var $_driver;

    /**
     * Checks if this backend has a certain capability.
     *
     * @param string $capability  The capability to check for.
     *
     * @return boolean  Supported or not.
     */
    function hasCapability($capability)
    {
        return $this->_driver->hasCapability($capability);
    }

    /**
     * Checks if the current user has the requested permissions on this
     * address book.
     *
     * @param integer $perm  The permission to check for.
     *
     * @return boolean  True if the user has permission, otherwise false.
     */
    function hasPermission($perm)
    {
        return $this->_share->hasPermission(Auth::getAuth(), $perm);
    }

    /**
     * Return the name of this address book.
     *
     * @string Address book name
     */
    function getName()
    {
        $share_parts = explode(':', $this->_share->getName());
        return array_pop($share_parts);
    }

    /**
     * Return the owner to use when searching or creating contacts in
     * this address book.
     *
     * @return string
     */
    function _getContactOwner()
    {
        $params = @unserialize($this->_share->get('params'));
        if (!empty($params['name'])) {
            return $params['name'];
        }
        return PEAR::raiseError(_("Unable to find contact owner."));
    }

    /**
     * Initialize
     */
    function _init()
    {
        $this->_share = &$this->_params['config']['params']['share'];
        $this->_driver = &Turba_Driver::factory('_' . $this->name, $this->_params['config']);
        if (is_a($this->_driver, 'PEAR_Error')) {
            return $this->_driver;
        }
        $this->_driver->_contact_owner = $this->_getContactOwner();
    }

    /**
     * Searches the address book with the given criteria and returns a
     * filtered list of results. If the criteria parameter is an empty array,
     * all records will be returned.
     *
     * @param array $criteria  Array containing the search criteria.
     * @param array $fields    List of fields to return.
     *
     * @return array  Hash containing the search results.
     */
    function _search($criteria, $fields)
    {
        return $this->_driver->_search($criteria, $fields);
    }

    /**
     * Reads the given data from the address book and returns the
     * results.
     *
     * @param string $key    The primary key field to use.
     * @param mixed $ids     The ids of the contacts to load.
     * @param string $owner  Only return contacts owned by this user.
     * @param array $fields  List of fields to return.
     *
     * @return array  Hash containing the search results.
     */
    function _read($key, $ids, $owner, $fields, $blob_fields = array())
    {
        return $this->_driver->_read($key, $ids, $owner, $fields, $blob_fields);
    }

    /**
     * Adds the specified object to the SQL database.
     */
    function _add($attributes, $blob_fields = array())
    {
        return $this->_driver->_add($attributes, $blob_fields);
    }

    /**
     * @see turba/lib/Turba_Driver#_canAdd()
     */
    function _canAdd()
    {
        return $this->_driver->canAdd();
    }

    /**
     * Deletes the specified object from the SQL database.
     */
    function _delete($object_key, $object_id)
    {
        return $this->_driver->_delete($object_key, $object_id);
    }

    /**
     * Deletes all contacts from a specific address book.
     *
     * @return boolean  True if the operation worked.
     */
    function _deleteAll($sourceName = null)
    {
        if (is_null($sourceName)) {
            $sourceName = $this->getName();
        }
        return $this->_driver->_deleteAll($sourceName);
    }

    /**
     * Saves the specified object in the SQL database.
     *
     * @return string  The object id, possibly updated.
     */
    function _save($object_key, $object_id, $attributes, $blob_fields = array())
    {
        return $this->_driver->_save($object_key, $object_id, $attributes, $blob_fields);
    }

    /**
     * Stub for removing all data for a specific user - to be overridden
     * by child class.
     */
    function removeUserData($user)
    {
        $this->_deleteAll();
        $GLOBALS['turba_shares']->removeShare($this->_share);
        unset($this->_share);
        return true;
    }

    function _makeKey($attributes)
    {
        return $this->_driver->_makeKey($attributes);
    }

    function _getTimeObjectTurbaList($start, $end, $field)
    {
        return $this->_driver->_getTimeObjectTurbaList($start, $end, $field);
    }

}
