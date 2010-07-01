<?php
/**
 * Read-only Turba directory driver implementation for favourite
 * recipients. Relies on the contacts/favouriteRecipients API method.
 *
 * $Horde: turba/lib/Driver/favourites.php,v 1.5.2.3 2008-08-03 16:50:06 jan Exp $
 *
 * @author  Jan Schneider <jan@horde.org>
 * @since   Turba 2.1
 * @package Turba
 */
class Turba_Driver_favourites extends Turba_Driver {

    /**
     */
    function _init()
    {
        return true;
    }

    /**
     * Checks if the current user has the requested permissions on this
     * source.
     *
     * @param integer $perm  The permission to check for.
     *
     * @return boolean  True if the user has permission, otherwise false.
     */
     function hasPermission($perm)
     {
         switch ($perm) {
             case PERMS_EDIT: return false;
             case PERMS_DELETE: return false;
             default: return true;
         }
     }

    /**
     * Searches the favourites list with the given criteria and returns a
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
        $results = array();
        foreach ($this->_getAddressBook() as $key => $contact) {
            $found = !isset($criteria['OR']);
            foreach ($criteria as $op => $vals) {
                if ($op == 'AND') {
                    foreach ($vals as $val) {
                        if (isset($contact[$val['field']])) {
                            switch ($val['op']) {
                            case 'LIKE':
                                if (stristr($contact[$val['field']], $val['test']) === false) {
                                    continue 4;
                                }
                                $found = true;
                                break;
                            }
                        }
                    }
                } elseif ($op == 'OR') {
                    foreach ($vals as $val) {
                        if (isset($contact[$val['field']])) {
                            switch ($val['op']) {
                            case 'LIKE':
                                if (empty($val['test']) ||
                                    stristr($contact[$val['field']], $val['test']) !== false) {
                                    $found = true;
                                    break 3;
                                }
                            }
                        }
                    }
                }
            }
            if ($found) {
                $results[$key] = $contact;
            }
        }
        return $results;
    }

    /**
     * Reads the given data from the API method and returns the result's
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
        if (is_a($book, 'PEAR_Error')) {
            return $book;
        }

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

    function _getAddressBook()
    {
        global $registry;

        if (!$registry->hasMethod('contacts/favouriteRecipients')) {
            return PEAR::raiseError(_("No source for favourite recipients exists."));
        }

        $addresses = $registry->call('contacts/favouriteRecipients', array($this->_params['limit']));
        if (is_a($addresses, 'PEAR_Error')) {
            return $addresses;
        }

        $addressbook = array();
        foreach ($addresses as $address) {
            $addressbook[$address] = array('email' => $address);
        }

        return $addressbook;
    }

}
