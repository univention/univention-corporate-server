<?php
/**
 * $Horde: turba/lib/Driver/vbook.php,v 1.8.2.8 2009-10-07 15:03:13 mrubinsk Exp $
 *
 * @package Horde
 */

/**
 * Turba directory driver implementation for virtual address books.
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Michael Rubinsky <mrubinsk@horde.org>
 * @since   Turba 2.2
 * @package Turba
 */
class Turba_Driver_vbook extends Turba_Driver {

    /**
     * Search type for this virtual address book.
     *
     * @var string
     */
    var $searchType;

    /**
     * The search criteria that defines this virtual address book.
     *
     * @var array
     */
    var $searchCriteria;

    /**
     * Return the owner to use when searching or creating contacts in
     * this address book.
     *
     * @return string
     */
    function _getContactOwner()
    {
        return $this->_driver->getContactOwner();
    }

    /**
     * Deletes all contacts from an address book. Not implemented for
     * virtual address books; just returns true so that the address
     * book can be deleted.
     *
     * @return boolean  True
     */
    function deleteAll($sourceName = null)
    {
        return true;
    }

    /**
     */
    function _init()
    {
        /* Grab a reference to the share for this vbook. */
        $this->_share = &$this->_params['share'];

        /* Load the underlying driver. */
        $this->_driver = &Turba_Driver::singleton($this->_params['source']);
        if (is_a($this->_driver, 'PEAR_Error')) {
            return $this->_driver;
        }

        if (!empty($this->_params['criteria'])) {
            $this->searchCriteria = $this->_params['criteria'];
        } else {
            $this->searchCriteria = array();
        }
        $this->searchType = count($this->searchCriteria) > 1 ? 'advanced' : 'basic';

        return true;
    }

    /**
     * Return all entries matching the combined searches represented by
     * $criteria and the vitural address book's search criteria.
     *
     * @param array $criteria  Array containing the search criteria.
     * @param array $fields    List of fields to return
     *
     * @return array  Hash containing the search results.
     */
    function _search($criteria, $fields)
    {
        /* Add the passed in search criteria to the vbook criteria
         * (which need to be mapped from turba fields to
         * driver-specific fields). */
        $criteria['AND'][] = $this->makeSearch($this->searchCriteria, 'AND', array());

        return $this->_driver->_search($criteria, $fields);
    }

    /**
     * Reads the requested entries from the underlying source.
     *
     * @param string $key    The primary key field to use.
     * @param mixed $ids     The ids of the contacts to load.
     * @param string $owner  Only return contacts owned by this user.
     * @param array $fields  List of fields to return.
     *
     * @return array  Hash containing the search results.
     */
    function _read($key, $ids, $owner, $fields)
    {
        return $this->_driver->_read($key, $ids, $owner, $fields);
    }

    /**
     * Not supported for virtual address books.
     */
    function _add($attributes)
    {
        return PEAR::raiseError(_("You cannot add new contacts to a virtual address book"));
    }

    /**
     * Not supported for virtual address books.
     */
    function _delete($object_key, $object_id)
    {
        return $this->_driver->_delete($object_key, $object_id);
    }

    /**
     * Not supported for virtual address books.
     */
    function _save($object_key, $object_id, $attributes)
    {
        return $this->_driver->_save($object_key, $object_id, $attributes);
    }

    /**
     * Check to see if the currently logged in user has requested permissions.
     *
     * @param integer $perm  The permissions to check against.
     *
     * @return boolean  True or False.
     */
    function hasPermission($perm)
    {
        return $this->_driver->hasPermission($perm);
    }

}
