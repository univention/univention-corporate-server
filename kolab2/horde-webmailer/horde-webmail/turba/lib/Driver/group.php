<?php
/**
 * Read-only Turba_Driver implementation for creating a Horde_Group based
 * address book.
 *
 * $Horde: turba/lib/Driver/group.php,v 1.2.2.1 2007-12-20 14:34:30 jan Exp $
 *
 * @author  Michael J. Rubinsky <mrubinsk@horde.org>
 * @since Turba 2.2
 * @package Turba
 */
class Turba_Driver_group extends Turba_Driver {

    /**
     * Constructor function.
     *
     * @param array $params  Array of parameters for this driver.
     *                       Basically, just passes the group id.
     *
     */
    function Turba_Driver_group($params)
    {
         $this->_gid = $params['gid'];
    }

    /**
     * Initialize the group driver.
     */
    function _init()
    {
        return true;
    }

    /**
     * Checks if the current user has the requested permissions on this
     * source.  This source is always read only.
     *
     * @param integer $perm  The permission to check for.
     *
     * @return boolean  True if the user has permission, otherwise false.
     */
    function hasPermission($perm)
    {
        switch ($perm) {
        case PERMS_EDIT:
        case PERMS_DELETE:
            return false;

        default:
            return true;
        }
    }

    /**
     * Searches the group list with the given criteria and returns a
     * filtered list of results. If the criteria parameter is an empty array,
     * all records will be returned.
     *
     * This method 'borrowed' from the favorites driver.
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
     * Read the data from the address book.
     * Again, this method taken from the favorites driver.
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

    function _getAddressBook()
    {
        require_once 'Horde/Group.php';
        require_once 'Horde/Identity.php';

        $groups = &Group::singleton();
        $members = $groups->listAllUsers($this->_gid);
        $addressbook = array();
        foreach ($members as $member) {
            $identity = &Identity::singleton('none', $member);
            $name = $identity->getValue('fullname');
            $email = $identity->getValue('from_addr');
            // We use the email as the key since we could have multiple users
            // with the same fullname, so no email = no entry in address book.
            if (!empty($email)) {
                $addressbook[$email] = array(
                                            'name' => ((!empty($name) ? $name : $member)),
                                            'email' => $identity->getValue('from_addr')
                                        );
            }
        }

        return $addressbook;
    }

}
