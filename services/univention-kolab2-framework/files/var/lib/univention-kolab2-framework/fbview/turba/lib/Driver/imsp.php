<?php
/**
 * Turba directory driver implementation for an IMSP server.
 * For now, provides only for addressbooks named for the user.
 *
 * @author  Michael Rubinsky<mike@theupstairsroom.com>
 * @version 1.0
 * @package Turba
 */
class Turba_Driver_imsp extends Turba_Driver {

    /**
     * Handle for the IMSP connection.
     * @var object Net_IMSP $_imsp
     */
    var $_imsp;

    /**
     * The name of the addressbook.
     * @var string $_bookName
     */
    var $_bookName  = '';

    /**
     * Holds if we are authenticated.
     * @var boolean $_authenticated
     */
    var $_authenticated = '';

    /**
     * Holds name of the field indicating an IMSP group
     * @var string $_groupField
     */
    var $_groupField = '';

    /**
     * Holds value that $_groupField will have
     * if entry is an IMSP group.
     * @var string $_groupValue
     */
    var $_groupValue = '';

    /**
     * Constructs a new Turba imsp driver object.
     *
     * @param array $params  Hash containing additional configuration parameters.
     */
    function Turba_Driver_imsp($params)
    {
        $this->type         = 'imsp';
        $this->params       = $params;
        $this->_groupField  = $params['group_id_field'];
        $this->_groupValue  = $params['group_id_value'];
        $this->_bookName    = $params['name'];
    }

    /**
     * Initialize the IMSP connection and check for error.
     */
    function init()
    {
        global $prefs;
        global $conf;

        require_once 'Net/IMSP.php';
        $this->_imsp = &Net_IMSP::singleton('Book', $this->params);
        $result = $this->_imsp->init();
        if (is_a($result, 'PEAR_Error')) {
            $this->_authenticated = false;
            return $result;
        }

        if (!empty($conf['log'])) {
            $logParams = $conf['log'];
            $result = $this->_imsp->setLogger($conf['log']);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $this->_authenticated = true;
        return true;
    }

    /**
     * Returns all entries matching $critera. (For now, only supports
     * ONE search critera that will NOT match strictly. Currently,
     * only supports searching * on one IMSP field (no AND or OR
     * searches are supported yet).
     *
     * @param array $criteria  Array containing the search criteria.
     * @param array $fields    List of fields to return.
     *
     * @return array  Hash containing the search results.
     */
    function search($criteria, $fields)
    {
        if (!$this->_authenticated) {
            return array();
        }

        /* Ensure we have something to return. */
        $results = array();
        $noGroups = false;

        /* Get the search criteria. */
        $temp = array_values($criteria);
        if (count($criteria)) {
            $searchField = $temp[0][0]['field'];
            $searchValue = $temp[0][0]['test'];
        } else {
            $searchField = 'name';
            $searchValue = '';
        }



        /* Make sure the searchvalue isn't FullName, since fullname is
         * created dynamically. */
        if ($searchField == 'fullname') {
            $searchField = 'name';
        }

        /**
         * Are we searching for only Turba_Groups or Turba_Objects?
         * This is needed so the 'Show Lists' and 'Show Contacts' links
         * work correctly in Turba.
         */
        if ($searchField == '__type') {
            switch ($searchValue) {
            case 'Group':
                $searchField = $this->_groupField;
                $searchValue = $this->_groupValue;
                break;
            case 'Object':
                $searchField = 'name';
                $searchValue = '';
                $noGroups = true;
                break;
            }
        }

        /* If there is no searchValue than only use the wildcard. */
        if (strlen($searchValue) > 0 ) {
            $searchValue = $searchValue . '*';
        } else {
            $searchValue = '*';
        }

        $names = $this->_imsp->search($this->_bookName, $searchValue,
                                      $searchField);

        if (is_a($names, 'PEAR_Error')) {
            $GLOBALS['notification']->push($names, 'horde.error');
        } else {
            $namesCount = count($names);
            for ($i = 0; $i < $namesCount; $i++) {
                $temp = $this->read('name', array($names[$i]), $fields);
                $result = $temp[0];
                if (is_a($result, 'PEAR_Error')) {
                    $GLOBALS['notification']->push($results, 'horde.error');
                } elseif (($noGroups) && (isset($result[$this->_groupField])) &&
                          ($result[$this->_groupField]) == $this->_groupValue) {
                    unset($result);
                } else {
                    $results[] = $result;
                }
            }

            Horde::logMessage(sprintf('IMSP returned %s results',
                                      count($results)) ,__FILE__, __LINE__, LOG_DEBUG);
        }

        return array_values($results);
    }

    /**
     * Read the given data from the imsp database and returns the
     * result's fields.
     *
     * @param array $criteria  (Ignored: Always 'name' for imsp) Search criteria.
     * @param array $id        Array of data identifiers.
     * @param array $fields    List of fields to return.
     *
     * @return array  Hash containing the search results.
     */
    function read($criteria, $id, $fields)
    {
        $results = array();
        if (!$this->_authenticated) {
            return $results;
        }
        $id = array_values($id);
        $idCount = count($id);
        for ($i = 0; $i < $idCount; $i++) {
            $temp = $this->_imsp->getEntry($this->_bookName, $id[$i]);
            if (is_a($temp, 'PEAR_Error')) {
                $result = array();
            } else {
                $temp['fullname'] = $temp['name'];
                $isIMSPGroup = false;

                if ((isset($temp[$this->_groupField])) &&
                    ($temp[$this->_groupField] == $this->_groupValue)) {
                    $isIMSPGroup = true;
                }

                if ($isIMSPGroup) {
                    //IMSP Group
                    if (isset($temp['email'])) {
                        $emailList = $this->_getGroupEmails($temp['email']);
                        $count = count($emailList);
                        for ($j = 0; $j < $count; $j++) {
                            $memberName = $this->_imsp->search
                                ($this->_bookName,trim($emailList[$j]),'email');

                            if (count($memberName)) {
                                $members[] = $memberName[0];
                            }
                        }

                        $temp['__members'] = serialize($members);
                    }

                    $temp['__type'] = 'Group';
                    $temp['email'] = null;
                    $result = $temp;

                } else {
                    //IMSP Contact
                    $count = count($fields);
                    for ($j = 0; $j < $count; $j++) {
                        if (isset($temp[$fields[$j]])) {
                            $result[$fields[$j]] = $temp[$fields[$j]];
                        }
                    }

                }

            }

            $results[] = $result;

        }

        return $results;
    }

    /**
     * Adds the specified object to the imsp database.
     */
    function addObject($attributes)
    {
        /* We need to map out Turba_Groups back to IMSP groups before
         * writing out to the server. We need to array_values() it in
         * case an entry was deleted from the group. */
        if ($attributes['__type'] == 'Group') {
            /* We may have a newly created group. */
            $attributes[$this->_groupField] = $this->_groupValue;
            if (!isset($attributes['__members'])) {
                $attributes['__members'] = '';
                $attributes['email'] = ' ';
            }

            $temp = unserialize($attributes['__members']);
            if (is_array($temp)) {
                $members = array_values($temp);
            } else {
                $members = array();
            }

            if (count($members)) {
                $result = $this->read('name', $members, array('email'));
                $count = count($result);
                for ($i = 0; $i < $count; $i++) {
                    $contact = sprintf("%s<%s>\n", $members[$i],
                                        $result[$i]['email']);
                    $attributes['email'] .= $contact;
                }
            }
        }

        unset($attributes['__members']);
        unset($attributes['__type']);
        unset($attributes['fullname']);
        return $this->_imsp->addEntry($this->_bookName, $attributes);
    }

    /**
     * Deletes the specified object from the imsp database.
     */
    function removeObject($object_key, $object_id)
    {
        return $this->_imsp->deleteEntry($this->_bookName, $object_id);
    }

    /**
     * Saves the specified object in the imsp database.
     *
     * @param string $object_key  (Ignored) name of the field
     *                            in $attributes[] to treat as key.
     * @param string $object_id   (Ignored) the value of the key field.
     * @param array  $attributes  Contains the field names and values of the entry.
     *
     * @return string  The object id, possibly updated.
     */
    function setObject($object_key, $object_id, $attributes)
    {
        // Should we check if the key changed, because IMSP will just
        // write out a new entry without removing the previous one.
        // This will change the key though and cause the entry not to
        // display on the "success" screen.
        /*if ($attributes['name'] != $this->makeKey($attributes)) {
            $this->removeObject($object_key, $attributes['name']);
            $attributes['name'] = $this->makeKey($attributes);
        }*/

        $result = $this->addObject($attributes);
        return is_a($result, 'PEAR_Error') ? $result : $object_id;
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
        return $attributes['fullname'];
    }

    /**
     * Parses out $emailText into an array of pure email addresses
     * suitable for searching the IMSP datastore with.
     *
     * @param $emailText string single string containing email addressses.
     * @return array of pure email address.
     */
    function _getGroupEmails($emailText)
    {
        $result = preg_match_all("(\w[-._\w]*\w@\w[-._\w]*\w\.\w{2,3})",
                                 $emailText, $matches);

        return $matches[0];
    }

}
