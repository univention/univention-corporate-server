<?php
/**
 * Turba directory driver implementation for Horde Preferences - very simple,
 * lightweight container.
 *
 * $Horde: turba/lib/Driver/prefs.php,v 1.10.10.7 2009-10-07 16:16:38 mrubinsk Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Turba 1.2
 * @package Turba
 */
class Turba_Driver_prefs extends Turba_Driver {

    /**
     */
    function _init()
    {
        return true;
    }

    /**
     * Returns all entries - searching isn't implemented here for now. The
     * parameters are simply ignored.
     *
     * @param array $criteria  Array containing the search criteria.
     * @param array $fields    List of fields to return.
     *
     * @return array  Hash containing the search results.
     */
    function _search($criteria, $fields)
    {
        return array_values($this->_getAddressBook());
    }

    /**
     * Reads the given data from the preferences and returns the result's
     * fields.
     *
     * @param array $criteria  Search criteria.
     * @param string $id       Data identifier.
     * @param array $fields    List of fields to return.
     *
     * @return  Hash containing the search results.
     */
    function _read($criteria, $ids, $fields)
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
     * Adds the specified object to the preferences.
     */
    function _add($attributes)
    {
        $book = $this->_getAddressBook();
        $book[$attributes['id']] = $attributes;
        $this->_setAddressbook($book);

        return true;
    }

    /**
     * @see turba/lib/Turba_Driver#_canAdd()
     */
    function _canAdd()
    {
        return true;
    }

    /**
     * Deletes the specified object from the preferences.
     */
    function _delete($object_key, $object_id)
    {
        $book = $this->_getAddressBook();
        unset($book[$object_id]);
        $this->_setAddressbook($book);

        return true;
    }

    /**
     * Saves the specified object in the preferences.
     */
    function _save($object_key, $object_id, $attributes)
    {
        $book = $this->_getAddressBook();
        $book[$object_id] = $attributes;
        $this->_setAddressBook($book);
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
