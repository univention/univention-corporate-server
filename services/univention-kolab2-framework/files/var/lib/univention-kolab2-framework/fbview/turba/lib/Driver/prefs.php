<?php
/**
 * Turba directory driver implementation for Horde Preferences - very
 * simple, lightweight container.
 *
 * $Horde: turba/lib/Driver/prefs.php,v 1.8 2004/04/05 03:11:41 chuck Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Turba 1.2
 * @package Turba
 */
class Turba_Driver_prefs extends Turba_Driver {

    /**
     * Return all entries - searching isn't implemented here for
     * now. The parameters are simply ignored.
     *
     * @param $criteria      Array containing the search criteria.
     * @param $fields        List of fields to return.
     *
     * @return               Hash containing the search results.
     */
    function search($criteria, $fields)
    {
        return array_values($this->_getAddressBook());
    }

    /**
     * Read the given data from the SQL database and returns
     * the result's fields.
     *
     * @param $criteria      Search criteria.
     * @param $ids            Data identifiers.
     * @param $fields        List of fields to return.
     *
     * @return               Hash containing the search results.
     */
    function read($criteria, $ids, $fields)
    {
        $book = $this->_getAddressBook();
        $results = array();
        if (!is_array($ids)) {
            $ids = array($ids);
        }
        foreach ($ids as $id) {
            if (isset($book[$id])) {
                $results[] = $book[$id];
            }
        }

        return $results;
    }

    /**
     * Adds the specified object to the SQL database.
     */
    function addObject($attributes)
    {
        $book = $this->_getAddressBook();
        $book[$attributes['id']] = $attributes;
        $this->_setAddressbook($book);

        return true;
    }

    /**
     * Deletes the specified object from the SQL database.
     */
    function removeObject($object_key, $object_id)
    {
        $book = $this->_getAddressBook();
        unset($book[$object_id]);
        $this->_setAddressbook($book);

        return true;
    }

    /**
     * Saves the specified object in the SQL database.
     */
    function setObject($object_key, $object_id, $attributes)
    {
        $book = $this->_getAddressBook();
        $book[$object_id] = $attributes;
        $this->_setAddressBook($book);
    }

    /**
     * Create an object key for a new object.
     *
     * @param array $attributes  The attributes (in driver keys) of the
     *                           object being added.
     *
     * @return string  A unique ID for the new object.
     */
    function makeKey($attributes)
    {
        return md5(mt_rand());
    }

    function _getAddressBook()
    {
        global $prefs;

        $val = $prefs->getValue('prefbooks');
        if (!empty($val)) {
            $prefbooks = unserialize($val);
            return $prefbooks[$this->_params['name']];
        } else {
            return array();
        }
    }

    function _setAddressBook($addressbook)
    {
        global $prefs;

        $val = $prefs->getValue('prefbooks');
        if (!empty($val)) {
            $prefbooks = unserialize($val);
        } else {
            $prefbooks = array();
        }

        $prefbooks[$this->_params['name']] = $addressbook;
        $prefs->setValue('prefbooks', serialize($prefbooks));
        $prefs->store();
    }

}
