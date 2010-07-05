<?php
/**
 * @package Turba
 *
 * $Horde: turba/lib/Driver/kolab.php,v 1.5.10.26 2009-10-07 16:16:38 mrubinsk Exp $
 */

/** Kolab support class. */
require_once 'Horde/Kolab.php';

/**
 * Horde Turba driver for the Kolab IMAP Server.
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Thomas Jarosch <thomas.jarosch@intra2net.com>
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @author  Stuart Binge <omicron@mighty.co.za>
 * @package Turba
 */
class Turba_Driver_kolab extends Turba_Driver {

    /**
     * Our Kolab server connection.
     *
     * @var Kolab
     */
    var $_kolab = null;

    /**
     * The wrapper to decide between the Kolab implementation
     *
     * @var Turba_Driver_kolab_wrapper
     */
    var $_wrapper = null;

    var $_capabilities = array(
        'delete_addressbook' => true,
        'delete_all' => true,
    );

    /**
     * Attempts to open a Kolab Groupware folder.
     *
     * @return boolean  True on success, PEAR_Error on failure.
     */
    function _init()
    {
        $this->_kolab = &new Kolab();
        if (empty($this->_kolab->version)) {
            $wrapper = "Turba_Driver_kolab_wrapper_old";
        } else {
            $wrapper = "Turba_Driver_kolab_wrapper_new";
        }

        $this->_wrapper = &new $wrapper($this->name, $this->_kolab);
        $this->_wrapper->connect();        
    }

    /**
     * Searches the Kolab message store with the given criteria and returns a
     * filtered list of results. If the criteria parameter is an empty
     * array, all records will be returned.
     *
     * @param $criteria      Array containing the search criteria.
     * @param $fields        List of fields to return.
     *
     * @return               Hash containing the search results.
     */
    function _search($criteria, $fields)
    {
        return $this->_wrapper->_search($criteria, $fields);
    }

    /**
     * Read the given data from the Kolab message store and returns the
     * results.
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
        return $this->_wrapper->_read($key, $ids, $fields);
    }

    /**
     * Adds the specified object to the Kolab message store.
     */
    function _add($attributes)
    {
        return $this->_wrapper->_add($attributes);
    }

    /**
     * @see turba/lib/Turba_Driver#_canAdd()
     */
    function _canAdd()
    {
        return true;
    }

    /**
     * Removes the specified object from the Kolab message store.
     */
    function _delete($object_key, $object_id)
    {
        return $this->_wrapper->_delete($object_key, $object_id);
    }

    /**
     * Deletes all contacts from a specific address book.
     *
     * @return boolean  True if the operation worked.
     */
    function _deleteAll($sourceName = null)
    {
        return $this->_wrapper->_deleteAll($sourceName);
    }

    /**
     * Updates an existing object in the Kolab message store.
     *
     * @return string  The object id, possibly updated.
     */
    function _save($object_key, $object_id, $attributes)
    {
        return $this->_wrapper->_save($object_key, $object_id, $attributes);
    }

    /**
     * Create an object key for a new object.
     *
     * @param array $attributes  The attributes (in driver keys) of the
     *                           object being added.
     *
     * @return string  A unique ID for the new object.
     */
    function _makeKey($attributes)
    {
        if (isset($attributes['uid'])) {
            return $attributes['uid'];
        }
        return $this->generateUID();
    }

    /**
     * Create an object key for a new object.
     *
     * @return string  A unique ID for the new object.
     */
    function generateUID()
    {
        if (method_exists($this->_wrapper, 'generateUID')) {
            return $this->_wrapper->generateUID();
        } else {
            return parent::generateUID();
        }
    }

    /**
     * Creates a new Horde_Share
     *
     * @param array  The params for the share.
     *
     * @return mixed  The share object or PEAR_Error.
     * @since Turba 2.2
     */
    function &createShare($share_id, $params)
    {
        if (isset($params['params']['default']) && $params['params']['default'] === true) {
            $share_id = Auth::getAuth();
        }

        $result = &Turba::createShare($share_id, $params);
        return $result;
    }

    function checkDefaultShare(&$share, $srcConfig)
    {
        $params = @unserialize($share->get('params'));
        return isset($params['default']) ? $params['default'] : false;
    }

}

/**
 * Horde Turba wrapper to distinguish between both Kolab driver implementations.
 *
 * $Horde: turba/lib/Driver/kolab.php,v 1.5.10.26 2009-10-07 16:16:38 mrubinsk Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL). If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @package Turba
 */

class Turba_Driver_kolab_wrapper {

    /**
     * Indicates if the wrapper has connected or not
     *
     * @var boolean
     */
    var $_connected = false;

    /**
     * String containing the current addressbook name.
     *
     * @var string
     */
    var $_addressbook = '';

    /**
     * Our Kolab server connection.
     *
     * @var Kolab
     */
    var $_kolab = null;

    /**
     * Constructor
     *
     * @param string      $addressbook  The addressbook to load.
     * @param Horde_Kolab $kolab        The Kolab connection object
     */
    function Turba_Driver_kolab_wrapper($addressbook, &$kolab)
    {
        if ($addressbook && $addressbook[0] == '_') {
            $addressbook = substr($addressbook, 1);
        }
        $this->_addressbook = $addressbook;
        $this->_kolab = &$kolab;
    }

    /**
     * Connect to the Kolab backend
     *
     * @param int    $loader         The version of the XML
     *                               loader
     *
     * @return mixed True on success, a PEAR error otherwise
     */
    function connect($loader = 0)
    {
        if ($this->_connected) {
            return true;
        }

        $result = $this->_kolab->open($this->_addressbook, $loader);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $this->_connected = true;

        return true;
    }
}

/**
 * Horde Turba driver for the Kolab IMAP Server.
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @author  Stuart Binge <omicron@mighty.co.za>
 * @package Turba
 */
class Turba_Driver_kolab_wrapper_old extends Turba_Driver_kolab_wrapper {

    function _buildContact()
    {
        $k = &$this->_kolab;

        $contact = array(
            'uid' => $k->getUID(),
            'owner' => Auth::getAuth(),
            'job-title' => $k->getStr('job-title'),
            'organization' => $k->getStr('organization'),
            'body' => $k->getStr('body'),
            'web-page' => $k->getStr('web-page'),
            'nick-name' => $k->getStr('nick-name'),
        );

        $name = &$k->getRootElem('name');
        $contact['full-name'] = $k->getElemStr($name, 'full-name');
        $contact['given-name'] = $k->getElemStr($name, 'given-name');
        $contact['last-name'] = $k->getElemStr($name, 'last-name');

        $email = &$k->getRootElem('email');
        $contact['smtp-address'] = $k->getElemStr($email, 'smtp-address');

        $phones = &$k->getAllRootElems('phone');
        for ($i = 0, $j = count($phones); $i < $j; $i++) {
            $phone = &$phones[$i];
            $type = $k->getElemStr($phone, 'type');

            switch ($type) {
            case 'home1':
                $contact['home1'] = $k->getElemStr($phone, 'number');
                break;

            case 'business1':
                $contact['business1'] = $k->getElemStr($phone, 'number');
                break;

            case 'mobile':
                $contact['mobile'] = $k->getElemStr($phone, 'number');
                break;

            case 'businessfax':
                $contact['businessfax'] = $k->getElemStr($phone, 'number');
                break;
            }
        }

        $addresses = &$k->getAllRootElems('address');
        for ($i = 0, $j = count($addresses); $i < $j; $i++) {
            $address = &$addresses[$i];
            $type = $k->getElemStr($address, 'type');

            switch ($type) {
            case 'home':
                $contact['home-street'] = $k->getElemStr($address, 'street');
                $contact['home-locality'] = $k->getElemStr($address, 'locality');
                $contact['home-region'] = $k->getElemStr($address, 'region');
                $contact['home-postal-code'] = $k->getElemStr($address, 'postal-code');
                $contact['home-country'] = $k->getElemStr($address, 'country');
                break;

            case 'business':
                $contact['business-street'] = $k->getElemStr($address, 'street');
                $contact['business-locality'] = $k->getElemStr($address, 'locality');
                $contact['business-region'] = $k->getElemStr($address, 'region');
                $contact['business-postal-code'] = $k->getElemStr($address, 'postal-code');
                $contact['business-country'] = $k->getElemStr($address, 'country');
                break;
            }
        }

        return $contact;
    }

    function _setPhone($type, &$phone, $attributes)
    {
        if (empty($attributes[$type])) {
            $this->_kolab->delRootElem($phone);
        } else {
            if ($phone === false) {
                $phone = &$this->_kolab->appendRootElem('phone');
                $this->_kolab->setElemStr($phone, 'type', $type);
            }
            $this->_kolab->setElemStr($phone, 'number', $attributes[$type]);
        }
    }

    function _setAddress($type, &$address, $attributes)
    {
        if (empty($attributes["$type-street"]) && empty($attributes["$type-locality"]) &&
            empty($attributes["$type-region"]) && empty($attributes["$type-postal-code"]) &&
            empty($attributes["$type-country"])) {
            $this->_kolab->delRootElem($address);
        } else {
            if ($address === false) {
                $address = &$this->_kolab->appendRootElem('address');
                $this->_kolab->setElemStr($address, 'type', $type);
            }
            $this->_kolab->setElemStr($address, 'street', $attributes["$type-street"]);
            $this->_kolab->setElemStr($address, 'locality', $attributes["$type-locality"]);
            $this->_kolab->setElemStr($address, 'region', $attributes["$type-region"]);
            $this->_kolab->setElemStr($address, 'postal-code', $attributes["$type-postal-code"]);
            $this->_kolab->setElemStr($address, 'country', $attributes["$type-country"]);
        }
    }

    function _createContact(&$xml, $attributes)
    {
        $k = &$this->_kolab;

        $name = &$k->initRootElem('name');
        if (!empty($attributes['full-name'])) {
            $k->setElemStr($name, 'full-name', $attributes['full-name']);
        }
        if (!empty($attributes['given-name'])) {
            $k->setElemStr($name, 'given-name', $attributes['given-name']);
        }
        if (!empty($attributes['last-name'])) {
            $k->setElemStr($name, 'last-name', $attributes['last-name']);
        }

        $email = &$k->initRootElem('email');
        $k->setElemStr($email, 'display-name', $attributes['full-name']);
        $k->setElemStr($email, 'smtp-address', $attributes['smtp-address']);

        if (!empty($attributes['job-title'])) {
            $k->setStr('job-title', $attributes['job-title']);
        }
        if (!empty($attributes['organization'])) {
            $k->setStr('organization', $attributes['organization']);
        }
        if (!empty($attributes['body'])) {
            $k->setStr('body', $attributes['body']);
        }
        if (!empty($attributes['web-page'])) {
            $k->setStr('web-page', $attributes['web-page']);
        }
        if (!empty($attributes['nick-name'])) {
            $k->setStr('nick-name', $attributes['nick-name']);
        }

        // Phones
        $phones = &$k->getAllRootElems('phone');
        $home = false;
        $bus = false;
        $mob = false;
        $fax = false;
        for ($i = 0, $j = count($phones); $i < $j; $i++) {
            $phone = &$phones[$i];
            $type = $k->getElemStr($phone, 'type');

            switch ($type) {
            case 'home1':
                $home = &$phone;
                break;

            case 'business1':
                $bus = &$phone;
                break;

            case 'mobile':
                $mob = &$phone;
                break;

            case 'businessfax':
                $fax = &$phone;
                break;
            }
        }

        $this->_setPhone('home1', $home, $attributes);
        $this->_setPhone('business1', $bus, $attributes);
        $this->_setPhone('mobile', $mob, $attributes);
        $this->_setPhone('businessfax', $fax, $attributes);

        // Addresses
        $home = false;
        $bus = false;
        $addresses = &$k->getAllRootElems('address');
        for ($i = 0, $j = count($addresses); $i < $j; $i++) {
            $address = &$addresses[$i];
            $type = $k->getElemStr($address, 'type');

            switch ($type) {
            case 'home':
                $home = &$address;
                break;

            case 'business':
                $bus = &$address;
                break;
            }
        }

        $this->_setAddress('home', $home, $attributes);
        $this->_setAddress('business', $bus, $attributes);
    }

    /**
     * Searches the Kolab message store with the given criteria and returns a
     * filtered list of results. If the criteria parameter is an empty
     * array, all records will be returned.
     *
     * @param $criteria      Array containing the search criteria.
     * @param $fields        List of fields to return.
     *
     * @return               Hash containing the search results.
     */
    function _search($criteria, $fields)
    {
        $result = $this->connect();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (!is_callable(array($this->_kolab, 'listObjectsInFolder'))) {
            Horde::logMessage('The Framework Kolab package must be upgraded', __FILE__, __LINE__, PEAR_LOG_ERR);
            return PEAR::raiseError(_("Unable to search."));
        }

        $results = array();
        $folders = $this->_kolab->listFolders();
        foreach ($folders as $folder) {
            if ($folder[1] != 'contact') {
                continue;
            }

            $msg_list = $this->_kolab->listObjectsInFolder($folder[0]);
            if (is_a($msg_list, 'PEAR_Error') || empty($msg_list)) {
                return $msg_list;
            }

            foreach ($msg_list as $msg) {
                $result = $this->_kolab->loadObject($msg, true);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }

                $contact = $this->_buildContact();

                if ($this->_matchCriteria($contact, $criteria) == false) {
                    continue;
                }

                $card = array();
                foreach ($fields as $field) {
                    $card[$field] = (isset($contact[$field]) ? $contact[$field] : '');
                }

                $results[] = $card;
            }
        }

        return $results;
    }

    /**
     * Read the given data from the Kolab message store and returns the
     * result's fields.
     *
     * @param $criteria      Search criteria.
     * @param $id            Data identifier.
     * @param $fields        List of fields to return.
     *
     * @return               Hash containing the search results.
     */
    function _read($criteria, $id_list, $fields)
    {
        $result = $this->connect();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if ($criteria != 'uid') {
            return array();
        }

        if (!is_array($id_list)) {
            $id_list = array($id_list);
        }

        $results = array();
        foreach ($id_list as $id) {
            $result = $this->_kolab->loadObject($id);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            $contact = $this->_buildContact($result);
            $card = array();
            foreach ($fields as $field) {
                $card[$field] = (isset($contact[$field]) ? $contact[$field] : '');
            }

            $results[] = $card;
        }

        return $results;
    }

    /**
     * Adds the specified object to the Kolab message store.
     */
    function _add($attributes)
    {
        $result = $this->connect();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $xml = &$this->_kolab->newObject($attributes['uid']);
        if (is_a($xml, 'PEAR_Error')) {
            return $xml;
        }

        $this->_createContact($xml, $attributes);

        return $this->_kolab->saveObject();
    }

    /**
     * Removes the specified object from the Kolab message store.
     */
    function _delete($object_key, $object_id)
    {
        $result = $this->connect();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if ($object_key != 'uid') {
            return false;
        }

        return $this->_kolab->removeObjects($object_id);
    }

    /**
     * Deletes all contacts from a specific address book.
     *
     * @return boolean  True if the operation worked.
     */
    function _deleteAll($sourceName = null)
    {
        $result = $this->connect();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if ($sourceName != null) {
            Horde::logMessage('deleteAll only working for current share. Called for $sourceName', __FILE__, __LINE__, PEAR_LOG_ERR);
            return PEAR::raiseError(sprintf(_("Cannot delete all address book entries for %s"), $sourceName));
        }

        return $this->_kolab->removeAllObjects();
    }

    /**
     * Updates an existing object in the Kolab message store.
     *
     * @return string  The object id, possibly updated.
     */
    function _save($object_key, $object_id, $attributes)
    {
        $result = $this->connect();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if ($object_key != 'uid') {
            return PEAR::raiseError('key must be uid');
        }

        $xml = &$this->_kolab->loadObject($object_id);
        if (is_a($xml, 'PEAR_Error')) {
            return $xml;
        }

        $this->_createContact($xml, $attributes);

        $result = $this->_kolab->saveObject();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return $object_id;
    }

    /**
     * Checks whether a contact matches a given criteria.
     *
     * @param array $contact       The contact.
     * @param array $criteria      The criteria.
     *
     * @return boolean  Wether the passed string corresponding to $criteria.
     *
     * @access private
     */
    function _matchCriteria($contact, $criteria)
    {
        $values = array_values($criteria);
        $values = $values[0];
        $ok = true;

        for ($current = 0; $current < count($values); ++$current) {
            $temp = $values[$current];

            while (!empty($temp) && !array_key_exists('field', $temp)) {
                $temp = array_values($temp);
                $temp = $temp[0];
            }

            if (empty($temp)) {
                continue;
            }

            $searchkey = $temp['field'];
            $searchval = $temp['test'];

            if (stristr($contact[$searchkey], $searchval) == false) {
                $ok = $ok && false;
            } else {
                $ok = $ok && true;
            }
        }

        return $ok;
    }
}

/**
 * New Horde Turba driver for the Kolab IMAP Server.
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @author  Thomas Jarosch <thomas.jarosch@intra2net.com>
 * @package Turba
 */
class Turba_Driver_kolab_wrapper_new extends Turba_Driver_kolab_wrapper {

    /**
     * Internal cache of Kronolith_Event_kolab_new. eventID/UID is key
     *
     * @var array
     */
    var $_contacts_cache;

    /**
     * Shortcut to the imap connection
     *
     * @var Kolab_IMAP
     */
    var $_store = null;

    /**
     * Connect to the Kolab backend
     *
     * @return mixed True on success, a PEAR error otherwise
     */
    function connect()
    {
        $result = parent::connect(1);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $this->_store = &$this->_kolab->_storage;

        /* Fetch the contacts first */
        $raw_contacts = $this->_store->getObjectArray();
        if (!$raw_contacts) {
            $raw_contacts = array();
        }
        $contacts = array();
        foreach ($raw_contacts as $id => $contact) {
            if (isset($contact['email'])) {
                unset($contact['email']);
            }
            if (isset($contact['picture'])) {
                $name = $contact['picture'];
                if (isset($contact['_attachments'][$name])) {
                    $contact['photo'] =  $this->_store->_data->getAttachment($contact['_attachments'][$name]['key']);
                    $contact['phototype'] = $contact['_attachments'][$name]['type'];
                }
            }

            $contacts[$id] = $contact;
        }

        /* Now we retrieve distribution-lists */
        $result = $this->_store->setObjectType('distribution-list');
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        $groups = $this->_store->getObjectArray();
        if (!$groups) {
            $groups = array();
        }

        /* Revert to the original state */
        $result = $this->_store->setObjectType('contact');
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        /* Store the results in our cache */
        $this->_contacts_cache = array_merge($contacts, $groups);

        return true;
    }

    /**
     * Searches the Kolab message store with the given criteria and returns a
     * filtered list of results. If the criteria parameter is an empty
     * array, all records will be returned.
     *
     * @param $criteria      Array containing the search criteria.
     * @param $fields        List of fields to return.
     *
     * @return               Hash containing the search results.
     */
    function _search($criteria, $fields)
    {
        $result = $this->connect();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (!count($criteria)) {
            return $this->_contacts_cache;
        }

        // keep only entries matching criteria
        $ids = array();
        foreach ($criteria as $key => $criteria) {
            $ids[] = $this->_doSearch($criteria, strval($key), $this->_contacts_cache);
        }
        $ids = $this->_removeDuplicated($ids);

        /* Now we have a list of names, get the rest. */
        $result = $this->_read('uid', $ids, $fields);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        Horde::logMessage(sprintf('Kolab returned %s results',
                                  count($result)), __FILE__, __LINE__, PEAR_LOG_DEBUG);
        return array_values($result);
    }

    /**
     * Applies the filter criteria to a list of entries
     *
     * @param $criteria      Array containing the search criteria.
     * @param $fields        List of fields to return.
     *
     * @return array         Array containing the ids of the selected entries
     */
    function _doSearch($criteria, $glue, &$entries)
    {
        $ids = array();
        foreach ($criteria as $key => $vals) {
            if (!empty($vals['OR'])) {
                $ids[] = $this->_doSearch($vals['OR'], 'OR', $entries);
            } elseif (!empty($vals['AND'])) {
                $ids[] = $this->_doSearch($vals['AND'], 'AND', $entries);
            } else {
                /* If we are here, and we have a ['field'] then we
                 * must either do the 'AND' or the 'OR' search. */
                if (isset($vals['field'])) {
                    $ids[] = $this->_selectEntries($vals, $entries);
                } else {
                    foreach ($vals as $test) {
                        if (!empty($test['OR'])) {
                            $ids[] = $this->_doSearch($test['OR'], 'OR');
                        } elseif (!empty($test['AND'])) {
                            $ids[] = $this->_doSearch($test['AND'], 'AND');
                        } else {
                            $ids[] = $this->_doSearch(array($test), $glue);
                        }
                    }
                }
            }
        }

        if ($glue == 'AND') {
            $ids = $this->_getAND($ids);
        } elseif ($glue == 'OR') {
            $ids = $this->_removeDuplicated($ids);
        }

        return $ids;
    }

    /**
     * Applies one filter criterium to a list of entries
     *
     * @param $test          Test criterium
     * @param $entries       List of fields to return.
     *
     * @return array         Array containing the ids of the selected entries
     */
    function _selectEntries($test, &$entries)
    {
        $ids = array();

        if (!isset($test['field'])) {
            Horde::logMessage('Search field not set. Returning all entries.',
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
            foreach ($entries as $entry) {
                $ids[] = $entry['uid'];
            }
        } else {
            $field = $test['field'];
            if (isset($test['test'])) {
                $value = $test['test'];
            } else {
                $value = '';
            }
            // Special emails hack
            if ($field == 'email') {
                $field = 'emails';
                $test['op'] = 'LIKE';
                $test['begin'] = false;
            }
            if (!isset($test['op']) || $test['op'] == '=') {
                foreach ($entries as $entry) {
                    if (isset($entry[$field]) && $entry[$field] == $value) {
                        $ids[] = $entry['uid'];
                    }
                }
            } else {
                // 'op' is LIKE
                if (!empty($test['begin'])) {
                    $begin = true;
                } else {
                    $begin = false;
                }

                // PHP 4 compatibility
                $has_stripos = function_exists('stripos');
                if (!$has_stripos) {
                    $value = strtolower($value);
                }

                foreach ($entries as $entry) {
                    if (empty($value)) {
                        $ids[] = $entry['uid'];
                    } else if (isset($entry[$field])) {
                        if ($has_stripos) {
                            $pos = stripos($entry[$field], $value);
                        } else {
                            $pos = strpos(strtolower($entry[$field]), $value);
                        }

                        if ($pos === false) {
                            continue;
                        }
                        if (!$begin || $pos == 0) {
                            $ids[] = $entry['uid'];
                        }
                    }
                }
            }
        }

        return $ids;
    }

    /**
     * Returns only those names that are duplicated in $ids
     *
     * @param array $ids  A nested array of arrays containing names
     *
     * @return array  Array containing the 'AND' of all arrays in $ids
     */
    function _getAND($ids)
    {
        $results = array();
        $matched = array();
        /* If there is only 1 array, simply return it. */
        if (count($ids) < 2) {
            return $ids[0];
        } else {
            for ($i = 0; $i < count($ids); $i++) {
                if (is_array($ids[$i])) {
                    $results = array_merge($results, $ids[$i]);
                }
            }
        }
        $search = array_count_values($results);
        foreach ($search as $key => $value) {
            if ($value == count($ids)) {
                $matched[] = $key;
            }
        }

        return $matched;
    }

    /**
     * Returns an array with all duplicate names removed.
     *
     * @param array $ids  Nested array of arrays containing names.
     *
     * @return array  Array containg the 'OR' of all arrays in $ids.
     */
    function _removeDuplicated($ids)
    {
        $unames = array();
        for ($i = 0; $i < count($ids); $i++) {
            if (is_array($ids[$i])) {
                $unames = array_merge($unames, $ids[$i]);
            }
        }
        return array_unique($unames);
    }

    /**
     * Read the given data from the Kolab message store and returns the
     * result's fields.
     *
     * @param string $key    The primary key field to use (always 'uid' for Kolab).
     * @param $ids           Data identifiers
     * @param $fields        List of fields to return.
     *
     * @return               Hash containing the search results.
     */
    function _read($key, $ids, $fields)
    {
        $result = $this->connect();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $results = array();

        if (!is_array($ids)) {
            $ids = array($ids);
        }

        $count = count($fields);
        foreach ($ids as $id) {
            if (in_array($id, array_keys($this->_contacts_cache))) {
                $object = $this->_contacts_cache[$id];

                $object_type = $this->_contacts_cache[$id]['__type'];
                if (!isset($object['__type']) || $object['__type'] == 'Object') {
                    if ($count) {
                        $result = array();
                        foreach ($fields as $field) {
                            if (isset($object[$field])) {
                                $result[$field] = $object[$field];
                            }
                        }
                        $results[] = $result;
                    } else {
                        $results[] = $object;
                    }
                } else {
                    $member_ids = array();
                    if (isset($object['member'])) {
                        foreach ($object['member'] as $member) {
                            if (isset($member['uid'])) {
                                $member_ids[] = $member['uid'];
                                continue;
                            }
                            $display_name = $member['display-name'];
                            $smtp_address = $member['smtp-address'];
                            $criteria = array(
                                'AND' => array(
                                    array(
                                        'field' => 'full-name',
                                        'op' => 'LIKE',
                                        'test' => $display_name,
                                        'begin' => false,
                                    ),
                                    array(
                                        'field' => 'emails',
                                        'op' => 'LIKE',
                                        'test' => $smtp_address,
                                        'begin' => false,
                                    ),
                                ),
                            );
                            $fields = array('uid');

                            // we expect only one result here!!!
                            $contacts = $this->_search($criteria, $fields);

                            // and drop everything else except the first search result
                            $member_ids[] = $contacts[0]['uid'];
                        }
                        $object['__members'] = serialize($member_ids);
                        unset($object['member']);
                    }
                    $results[] = $object;;
                }
            }
        }


        return $results;
    }

    /**
     * Adds the specified object to the Kolab message store.
     */
    function _add($attributes)
    {
        $result = $this->connect();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $attributes['full-name'] = $attributes['last-name'];
        if (isset($attributes['middle-names'])) {
            $attributes['full-name'] = $attributes['middle-names'] . ' ' . $attributes['full-name'];
        }
        if (isset($attributes['given-name'])) {
            $attributes['full-name'] = $attributes['given-name'] . ' ' . $attributes['full-name'];
        }

        $result = $this->_store($attributes);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        return true;
    }

    /**
     * Updates an existing object in the Kolab message store.
     *
     * @return string  The object id, possibly updated.
     */
    function _save($object_key, $object_id, $attributes)
    {
        $result = $this->connect();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if ($object_key != 'uid') {
            return PEAR::raiseError(sprintf('Key for saving must be \'uid\' not %s!', $object_key));
        }

        return $this->_store($attributes, $object_id);
    }

    /**
     * Stores an object in the Kolab message store.
     *
     * @return string  The object id, possibly updated.
     */
    function _store($attributes, $object_id = null)
    {
        $group = false;
        if (isset($attributes['__type']) && $attributes['__type'] == 'Group') {
            $group = true;
            $result = $this->_store->setObjectType('distribution-list');
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
            $this->_convertMembers($attributes);
        }

        if (isset($attributes['photo']) && isset($attributes['phototype'])) {
            $attributes['_attachments']['photo.attachment'] = array('type' => $attributes['phototype'],
                                                                    'content' => $attributes['photo']);
            $attributes['picture'] = 'photo.attachment';
            unset($attributes['photo']);
            unset($attributes['phototype']);
        }

        $result = $this->_store->save($attributes, $object_id);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if ($group) {
            $result = $this->_store->setObjectType('contact');
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        return $object_id;
    }

    function _convertMembers(&$attributes)
    {
        if (isset($attributes['__members'])) {
            $member_ids = unserialize($attributes['__members']);
            $attributes['member'] = array();
            foreach ($member_ids as $member_id) {
                if (isset($this->_contacts_cache[$member_id])) {
                    $member = $this->_contacts_cache[$member_id];
                    $mail = array('uid' => $member_id);
                    if (!empty($member['full-name'])) {
                        $mail['display-name'] = $member['full-name'];
                    }
                    if (!empty($member['emails'])) {
                        $emails = explode(',', $member['emails']);
                        $mail['smtp-address'] = trim($emails[0]);
                        if (!isset($mail['display-name'])) {
                            $mail['display-name'] = $mail['smtp-address'];
                        }
                    }
                    $attributes['member'][] = $mail;
                }
            }
            unset($attributes['__members']);
        }
    }


    /**
     * Removes the specified object from the Kolab message store.
     */
    function _delete($object_key, $object_id)
    {
        $result = $this->connect();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if ($object_key != 'uid') {
            return PEAR::raiseError(sprintf('Key for saving must be a UID not %s!', $object_key));
        }

        if (!in_array($object_id, array_keys($this->_contacts_cache))) {
            return PEAR::raiseError(sprintf(_("Object with UID %s does not exist!"), $object_id));
        }

        $group = false;
        if (isset($this->_contacts_cache[$object_id]['__type'])
            && $this->_contacts_cache[$object_id]['__type'] == 'Group') {
            $group = true;
        }

        if ($group) {
            $result = $this->_store->setObjectType('distribution-list');
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $result = $this->_store->delete($object_id);

        if ($group) {
            $result = $this->_store->setObjectType('contact');
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        return $result;
    }

    /**
     * Deletes all contacts from a specific address book.
     *
     * @return boolean  True if the operation worked.
     */
    function _deleteAll($sourceName = null)
    {
        $result = $this->connect();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        /* Delete contacts */
        $result = $this->_store->deleteAll();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        /* Delete groups */
        $result = $this->_store->setObjectType('distribution-list');
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        $result = $this->_store->deleteAll();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        /* Revert to the original state */
        return $this->_store->setObjectType('contact');
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return true;
    }

    /**
     * Create an object key for a new object.
     *
     * @return string  A unique ID for the new object.
     */
    function generateUID()
    {
        $result = $this->connect();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        do {
            $key = md5(uniqid(mt_rand(), true));
        } while(in_array($key, array_keys($this->_contacts_cache)));

        return $key;
    }
}
