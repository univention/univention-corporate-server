<?php

require_once 'Horde/Kolab.php';
require_once 'Horde/Data.php';

/**
 * Horde Turba driver for the Kolab IMAP Server.
 * Copyright (C) 2003, 2004 Code Fusion, cc.
 *
 * $Horde: turba/lib/Driver/kolab.php,v 1.1 2004/04/21 19:05:03 chuck Exp $
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Stuart Bingë <s.binge@codefusion.co.za>
 * @version $Revision: 1.1.2.1 $
 * @package Turba
 */
class Turba_Driver_kolab extends Turba_Driver {

    /**
     * Our Kolab Cyrus server connection.
     *
     * @var object Kolab_Cyrus $_kc
     */
    var $_kc;

    function init()
    {
        $this->_params['folder'] = array_key_exists('folder', $this->_params)
            ? $this->_params['folder'] : 'Contacts';
        $this->_params['server'] = array_key_exists('server', $this->_params)
            ? $this->_params['server'] : $GLOBALS['conf']['kolab']['server'];
    }

    /**
     * Opens a connection to the Kolab Cyrus Server.
     *
     * @return mixed   True on success, PEAR_Error on failure.
     */
    function _open()
    {
        $this->_kc = new Kolab_Cyrus($this->_params['server']);

        $result = $this->_kc->openMailbox($this->_params['folder'], true);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return true;
    }

    /**
     * Closes the Kolab Cyrus connection.
     */
    function _close()
    {
        $this->_kc->disconnect();
    }

    /**
     * Converts Turba search criteria into a comparable IMAP search string
     *
     * @param array $criteria      The search criteria.
     *
     * @return string  The IMAP search string corresponding to $criteria.
     */
    function turbaToImap($criteria)
    {
        $values = array_values($criteria);
        $values = $values[0];
        $query = "";

        for ($current = 0; $current < count($values); $current++) {
            $temp = $values[$current];

            while (!empty($temp) && !array_key_exists('field', $temp)) {
                $temp = array_values($temp);
                $temp = $temp[0];
            }

            if (empty($temp)) continue;

            $searchkey = $temp['field'];
            $searchval = $temp['test'];

            switch ($searchkey) {
                case 'owner':
                    $query .= 'FROM "' . $searchval . '" ';
                    break;

                case 'name':
                case 'firstname':
                case 'lastname':
                    $query .= 'BODY "N:" ';
                    if (!empty($searchval))
                        $query .= 'BODY "' . $searchval . '" ';
                    break;

                case 'email':
                    $query .= 'BODY "EMAIL:" ';
                    if (!empty($searchval))
                        $query .= 'BODY "' . $searchval . '" ';
                    break;

                case 'title':
                    $query .= 'BODY "TITLE:" ';
                    if (!empty($searchval))
                        $query .= 'BODY "' . $searchval . '" ';
                    break;

                case 'company':
                    $query .= 'BODY "ORG:" ';
                    if (!empty($searchval))
                        $query .= 'BODY "' . $searchval . '" ';
                    break;

                case 'homeAddress':
                case 'homeCity':
                case 'homeProvince':
                case 'homePostalCode':
                case 'homeCountry':
                    $query .= 'BODY "ADR:" BODY "TYPE" BODY "HOME" ';
                    if (!empty($searchval))
                        $query .= 'BODY "' . $searchval . '" ';
                    break;

                case 'workAddress':
                case 'workCity':
                case 'workProvince':
                case 'workPostalCode':
                case 'workCountry':
                    $query .= 'BODY "ADR:" BODY "TYPE" BODY "WORK" ';
                    if (!empty($searchval))
                        $query .= 'BODY "' . $searchval . '" ';
                    break;

                case 'homePhone':
                    $query .= 'BODY "TEL:" BODY "TYPE" BODY "HOME" ';
                    if (!empty($searchval))
                        $query .= 'BODY "' . $searchval . '" ';
                    break;

                case 'workPhone':
                    $query .= 'BODY "TEL:" BODY "TYPE" BODY "WORK" ';
                    if (!empty($searchval))
                        $query .= 'BODY "' . $searchval . '" ';
                    break;

                case 'cellPhone':
                    $query .= 'BODY "TEL:" BODY "TYPE" BODY "CELL" ';
                    if (!empty($searchval))
                        $query .= 'BODY "' . $searchval . '" ';
                    break;

                case 'fax':
                    $query .= 'BODY "TEL:" BODY "TYPE" BODY "FAX" ';
                    if (!empty($searchval))
                        $query .= 'BODY "' . $searchval . '" ';
                    break;

                case 'notes':
                    $query .= 'BODY "NOTE:" ';
                    if (!empty($searchval))
                        $query .= 'BODY "' . $searchval . '" ';
                    break;

                case 'website':
                    $query .= 'BODY "URL:" ';
                    if (!empty($searchval))
                        $query .= 'BODY "' . $searchval . '" ';
                    break;

                case 'nickname':
                    $query .= 'BODY "NICKNAME:" ';
                    if (!empty($searchval))
                        $query .= 'BODY "' . $searchval . '" ';
                    break;

                default:
                    if (!empty($searchkey))
                        $query .= 'BODY "' . $searchkey . '" ';
                    if (!empty($searchval))
                        $query .= 'BODY "' . $searchval . '" ';
            }
        }

        return $query;
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
    function search($criteria, $fields)
    {
        $query = Turba_Driver_kolab::turbaToImap($criteria);

        $result = $this->_open();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $results = array();

        $msgs = $this->_kc->getMessageList(SORTDATE, false, $query);
        foreach ($msgs as $msg) {
            $object = $this->_kc->getObject($msg, "text/x-vcard");
            if ($object === false) continue;

            $contact = $this->loadVCard($object);
            if ($contact === false) continue;

            $card = array();
            foreach ($fields as $field) {
                $card[$field] = (isset($contact[$field]) ? $contact[$field] : '');
            }
            $results[] = $card;
        }

        $this->_close();

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
    function read($criteria, $id, $fields)
    {
        if ($criteria != 'uid') return array();

        $result = $this->_open();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $results = array();

        if (!is_array($id)) $id = array($id);

        foreach ($id as $i) {
            $matches = $this->_kc->getMessageList(SORTDATE, false, "BODY \"UID:\" BODY \"$i\"");
            foreach ($matches as $msg) {
                $object = $this->_kc->getObject($msg, "text/x-vcard");
                if ($object === false) continue;

                $contact = $this->loadVCard($object);
                if ($contact === false) continue;

                $card = array();
                foreach ($fields as $field) {
                    $card[$field] = (isset($contact[$field]) ? $contact[$field] : '');
                }
                $results[] = $card;
            }
        }

        $this->_close();

        return $results;
    }

    /**
     * Adds the specified object to the Kolab message store.
     */
    function addObject($attributes)
    {
        $result = $this->_open();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $result = $this->_kc->addObject(
            $attributes['uid'],
            $this->createVCard($attributes, NULL),
            'text/x-vcard',
            'kolab-contact-entry.vcard',
            'Turba'
        );

        $this->_close();

        return $result;
    }

    /**
     * Removes the specified object from the Kolab message store.
     */
    function removeObject($object_key, $object_id)
    {
        if ($object_key != 'uid') return false;

        $result = $this->_open();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $matches = $this->_kc->getMessageList(SORTDATE, false, "BODY \"UID:\" BODY \"$object_id\"");
        $this->_kc->deleteMessages($matches);

        $this->_close();

        return true;
    }

    /**
     * Updates an existing object in the Kolab message store.
     *
     * @return string  The object id, possibly updated.
     */
    function setObject($object_key, $object_id, $attributes)
    {
        if ($object_key != 'uid') return false;

        $result = $this->_open();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $matches = $this->_kc->getMessageList(SORTDATE, false, "BODY \"UID:\" BODY \"$object_id\"");
        $vcard = '';
        foreach ($matches as $msg) {
            $vcard = $this->_kc->getObject($msg, "text/x-vcard");
            if ($vcard === false) {
                $vcard = '';
                continue;
            }

            $this->_kc->deleteMessages($msg);
        }

        $result = $this->_kc->addObject(
            $attributes['uid'],
            $this->createVCard($attributes, $vcard),
            'text/x-vcard',
            'kolab-contact-entry.vcard',
            'Turba'
        );

        $this->_close();

        return is_a('PEAR_Error', $result) ? $result : $attributes['uid'];
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
        return md5(uniqid(mt_rand(), true));
    }

    /**
     * Converts a text VCARD representation into a Turba attribute hash
     *
     * @param string $text  The text representation of the VCARD object.
     *
     * @return array  A hash of turba attributes for the VCARD object.
     */
    function loadVCard($text)
    {
        $vcard = &Horde_Data::singleton('vcard');
        $data = $vcard->importData($text);
        if (is_a('PEAR_Error', $data)) {
            return $data;
        }

        $data = $data[0];
        $contact = $vcard->toHash($data);

        foreach ($data['params'] as $item) {
            switch ($item['name']) {
            case 'UID':
                $contact['uid'] = $vcard->read($item);
            }
        }

        $contact['owner'] = Kolab::getUser();

        return $contact;
    }

    /**
     * Converts a Turba attribute hash into a text VCARD representation.
     *
     * @param string $attributes  The turba attribute hash.
     * @param string $text (optional)  If specified, this is used as the 'base'
     *                                 VCARD object, with the neccessary
     *                                 properties being overridden by $attributes.
     *
     * @return string  The text VCARD representation.
     */
    function createVCard($attributes, $text = '')
    {
        $vcard = &Horde_Data::singleton('vcard');
        $data = array();
        if (!empty($text)) {
            $data = $vcard->importData($text);
            if (is_a('PEAR_Error', $data)) {
                return $data;
            }
        }

        $hash = $vcard->fromHash($attributes);
        $hash['AGENT'] = 'Horde/Turba/Kolab';
        $hash['CLASS'] = 'PRIVATE';
        $hash['PROFILE'] = 'VCARD';
        $hash['UID'] = $attributes['uid'];
        if (!empty($data)) {
            $hash = array_merge($data, $hash);
        }

        return $vcard->exportData($hash);
    }
}
