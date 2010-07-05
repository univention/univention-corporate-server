<?php

require_once 'Net/IMSP/Auth.php';

/**
 * String of supported ACL rights.
 */
define('IMSP_ACL_RIGHTS', 'lrwcda');

/**
 * Net_IMSP_Book Class - provides api for dealing with IMSP
 * address books.
 *
 * Required parameters:<pre>
 *   'username'     Username to logon to IMSP server as.
 *   'password'     Password for current user.
 *   'auth_method'  The authentication method to use to login.
 *   'server'       The hostname of the IMSP server.
 *   'port'         The port of the IMSP server.</pre>
 *
 * $Horde: framework/Net_IMSP/IMSP/Book.php,v 1.16.2.28 2009-10-01 23:44:21 mrubinsk Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Rubinsky <mrubinsk@horde.org>
 * @package Net_IMSP
 */
class Net_IMSP_Book {

    /**
     * Sort order.
     *
     * @var string
     */
    var $sort = 'ascend';

    /**
     * Net_IMSP object.
     *
     * @var Net_IMSP
     */
    var $_imsp;

    /**
     * Parameter list.
     *
     * @var array
     */
    var $_params;

    /**
     * Constructor function.
     *
     * @param array $params Hash containing IMSP parameters.
     */
    function Net_IMSP_Book($params)
    {
        $this->_params = $params;
    }

    /**
     * Initialization function to be called after object is returned.
     * This allows errors to occur and not break the script.
     *
     * @return mixed  True on success PEAR_Error on failure.
     */
    function init()
    {
        if (!isset($this->_imsp)) {
            $auth = &Net_IMSP_Auth::singleton($this->_params['auth_method']);
            $this->_imsp = $auth->authenticate($this->_params);
        }

        if (is_a($this->_imsp, 'PEAR_Error')) {
            return $this->_imsp;
        }
        $this->_imsp->writeToLog('Net_IMSP_Book initialized.', __FILE__,
                                  __LINE__, PEAR_LOG_DEBUG);
        return true;
    }

    /**
     * Returns an array containing the names of all the address books
     * available to the logged in user.
     *
     * @return mixed Array of address book names or PEAR_Error.
     */
    function getAddressBookList()
    {
        $command_string = 'ADDRESSBOOK *';

        $result = $this->_imsp->imspSend($command_string);
        if (is_a($result,'PEAR_Error')) {
           return $this->_imsp->imspError('Connection to IMSP host failed.',
                                          __FILE__, __LINE__);
        }

        /* Iterate through the response and populate an array of
         * address book names. */
        $server_response = $this->_imsp->imspReceive();
        if (is_a($server_response, 'PEAR_Error')) {
            return $server_response;
        }
        $abooks = array();

        while (preg_match("/^\* ADDRESSBOOK/", $server_response)) {
            /* If this is an ADDRESSBOOK response, then this will explode as so:
             * [0] and [1] can be discarded
             * [2] = attributes
             * [3] = delimiter
             * [4] = address book name
             */

            /* First, check for a {} */
            if (preg_match(IMSP_OCTET_COUNT, $server_response, $tempArray)) {
                $abooks[] = $this->_imsp->receiveStringLiteral($tempArray[2]);
                /* Get the CRLF at end of ADDRESSBOOK response
                 * that the {} does not include. */
                $this->_imsp->receiveStringLiteral(2);
            } else {
                $parts = explode(' ', $server_response);
                $numParts = count($parts);
                $name = $parts[4];
                $firstChar = substr($name, 0, 1);
                if ($firstChar =="\"") {
                    $name = ltrim($name, "\"");
                    for ($i = 5; $i < $numParts; $i++) {
                        $name .= ' ' . $parts[$i];
                        $lastChar = substr($parts[$i], strlen($parts[$i]) - 1, 1);
                        if ($lastChar == "\"") {
                            $name = rtrim($name, "\"");
                            break;
                        }
                    }
                }
                $abooks[] = $name;
            }
            $server_response = $this->_imsp->imspReceive();
        }

        if ($server_response != 'OK') {
            return $this->_imsp->imspError('Did not receive the expected response from the server.',
                                           __FILE__, __LINE__);
        }

        $this->_imsp->writeToLog('ADDRESSBOOK command OK.', __FILE__, __LINE__,
                                  PEAR_LOG_INFO);
        return $abooks;
    }

    /**
     * Returns an array containing the names that match $search
     * critera in the address book named $abook.
     *
     * @param string $abook  Address book name to search.
     * @param array $search  Search criteria in the form of
     *                      'fieldName' => 'searchTerm' (may include * wild card).
     *
     * @return mixed Array of names of the entries that match or PEAR_Error.
     */
    function search($abook, $search)
    {
        //If no field => value pairs, assume we are searching name.
        $criteria = array();
        if (!is_array($search)) {
            $criteria['name'] = $search;
        } else {
            $criteria = $search;
        }

        $result = $this->_imsp->imspSend('SEARCHADDRESS ', true, false);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        // Do we need to send the abook name as {} ?
        if (preg_match(IMSP_MUST_USE_LITERAL, $abook)) {
            $biBook = sprintf("{%d}", strlen($abook));

            $result = $this->_imsp->imspSend($biBook, false, true);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            $result = $this->_imsp->imspReceive();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
            if (!preg_match("/^\+/", $result)) {
                return $this->_imsp->imspError('Did not receive expected command continuation response from IMSP server.',
                                               __FILE__,__LINE__);
            }
        }

        //Start parsing the search array.
        $result = $this->_imsp->imspSend("$abook", false, false);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $count = count($criteria);
        $current = 1;
        foreach ($criteria as $search_field => $search) {
            $result = $this->_imsp->imspSend(" $search_field ", false, false);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            // How about the search term as a {}.
            if (preg_match(IMSP_MUST_USE_LITERAL, $search)) {
                $biSearch = sprintf("{%d}", strlen($search));

                $result = $this->_imsp->imspSend($biSearch, false, true);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }
                $result = $this->_imsp->imspReceive();
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }
                if (!preg_match("/^\+/", $result)) {
                    return $this->_imsp->imspError('Did not receive expected command continuation response from IMSP server.',
                                                   __FILE__, __LINE__);
                }

                $result = $this->_imsp->imspSend($search, false, $current == $count);
                $current++;
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }
            } else {
                // Only send the CrLf if this is the last field/search atom.
                $result = $this->_imsp->imspSend('"' . $search . '"', false, $current == $count);
                $current++;
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }
            }
        }

        // Get the response.
        $server_response = $this->_imsp->imspReceive();
        $abookNames = Array();

        while (preg_match("/^\* SEARCHADDRESS/", $server_response)) {
            $chopped_response =
                preg_replace("/^\* SEARCHADDRESS/", '', $server_response);

            // Remove any lingering white space in front only.
            $chopped_response = ltrim($chopped_response);

            // Get rid of any lingering quotes.
            $temp = preg_replace("/\"/", '', $chopped_response);

            if (preg_match("/({)([0-9]{1,})(\}$)/", $temp, $tempArray)) {
                $dataSize = $tempArray[2];
                $temp = $this->_imsp->receiveStringLiteral($dataSize);

                /* Get the CRLF since {} does not include it. */
                $this->_imsp->receiveStringLiteral(2);
            }

            $abookNames[] = $temp;

            // Get the next response line from the server.
            $server_response = $this->_imsp->imspReceive();
        }

        // Should check for OK or BAD here just to be certain.
        switch ($server_response) {
        case 'BAD':
            return $this->_imsp->imspError('The IMSP server did not understand your request.' .  ": $command_text",
                                           __FILE__, __LINE__);

        case 'NO':
            return $this->_imsp->imspError('IMSP server is unable to perform your request.' . ": " . $this->_imsp->lastRawError,
                                           __FILE__, __LINE__);
        }

        /* This allows for no results */
        if (count($abookNames) < 1) {
            return $abookNames;
        }

        $this->_imsp->writeToLog('SEARCHADDRESS command OK', __FILE__, __LINE__,
                                 PEAR_LOG_INFO);

        // Determine the sort direction and perform the sort.
        switch ($this->sort) {
        case 'ascend':
            sort($abookNames);
            break;

        case 'descend':
            rsort($abookNames);
            break;
        }

        return $abookNames;
    }

    /**
     * Returns an associative array of a single address book entry.
     * Note that there will always be a 'name' field.
     *
     * @param string $abook       Name of the address book to search.
     * @param string $entryName  'name' attribute of the entry to retrieve
     *
     * @return mixed Array containing entry or PEAR_Error on failure / no match.
     */
    function getEntry($abook, $entryName)
    {
        $result = $this->_imsp->imspSend('FETCHADDRESS ', true, false);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (preg_match(IMSP_MUST_USE_LITERAL, $abook)) {
            $biBook = sprintf("{%d}", strlen($abook));

            $result = $this->_imsp->imspSend($biBook, false, true);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            if (!preg_match("/^\+/",
                            $this->_imsp->imspReceive())) {
                return $this->_imsp->imspError('Did not receive expected command continuation response from IMSP server.',
                                               __FILE__, __LINE__);
            }
        }

        $result = $this->_imsp->imspSend("$abook ", false, false);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (preg_match(IMSP_MUST_USE_LITERAL, $entryName)) {
            $biName = sprintf("{%d}", strlen($entryName));

            $result = $this->_imsp->imspSend($biName, false, true);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            if (!preg_match("/^\+/",
                            $this->_imsp->imspReceive())) {
                return $this->_imsp->imspError('Did not receive expected command continuation response from IMSP server.',
                                               __FILE__, __LINE__);
            }

            $result = $this->_imsp->imspSend($entryName, false, true);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        } else {
            $result = $this->_imsp->imspSend("\"$entryName\"", false, true);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $server_response = $this->_imsp->imspReceive();

        switch ($server_response) {
        case 'BAD':
            return $this->_imsp->imspError('The IMSP server did not understand your request.', __FILE__, __LINE__);
        case 'NO':
            return $this->_imsp->imspError('No entry in this address book matches your query.', __FILE__, __LINE__);
        }

        // Get the data in an associative array.
        $entry = $this->_parseFetchAddressResponse($server_response);

        //Get the next server response -- this *should* be the OK response.
        $server_response = $this->_imsp->imspReceive();

        if ($server_response != 'OK') {
            // Unexpected response throw error but still continue on.
            $this->_imsp->imspError('Did not receive the expected response from the server.',__FILE__, __LINE__);
        }

        $this->_imsp->writeToLog('FETCHADDRESS completed OK', __FILE__, __LINE__,
                                  PEAR_LOG_INFO);
        return $entry;
    }

    /**
     * Creates a new address book.
     *
     * @param string $abookName FULLY QUALIFIED name such 'jdoe.clients' etc...
     *
     * @return mixed True on success / PEAR_Error on failure.
     */
    function createAddressBook($abookName)
    {
        $command_text = 'CREATEADDRESSBOOK ';

        if (preg_match(IMSP_MUST_USE_LITERAL, $abookName)) {
            $biBook = sprintf("{%d}", strlen($abookName));

            $result = $this->_imsp->imspSend($command_text . $biBook, true, true);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            if (!preg_match("/^\+/",
                            $this->_imsp->imspReceive())) {

                return $this->_imsp->imspError('Did not receive expected command continuation response from IMSP server.',
                                               __FILE__, __LINE__);
            } else {
                $result = $this->_imsp->imspSend($abookName, false, true);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }
            }
        } else {
            $result = $this->_imsp->imspSend($command_text . $abookName,
                                             true, true);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $server_response = $this->_imsp->imspReceive();
        if (is_a($server_response, 'PEAR_Error')) {
            return $server_response;
        }

        switch ($server_response) {
        case 'OK':
            $this->_imsp->writeToLog('CREATEADDRESSBOOK completed OK', __FILE__,
                                     __LINE__, PEAR_LOG_INFO);
            return true;

        case 'NO':
            // Could not create abook.
            return $this->_imsp->imspError('IMSP server is unable to perform your request.', __FILE__, __LINE__);

        case 'BAD':
            return $this->_imsp->imspError('The IMSP server did not understand your request.', __FILE__, __LINE__);

        default:
            // Something unexpected.
            return $this->_imsp->imspError('Did not receive the expected response from the server.',
                                           __FILE__, __LINE__);
        }
    }

    /**
     * Deletes an address book completely!
     *
     * @param string $abookName Name of address book to delete.
     *
     * @return mixed true on success / PEAR_Error on failure
     */
    function deleteAddressBook($abookName)
    {
        $command_text = 'DELETEADDRESSBOOK ';

        // Check need for {}.
        if (preg_match(IMSP_MUST_USE_LITERAL, $abookName)) {
            $biBook = sprintf("{%d}", strlen($abookName));

            $result = $this->_imsp->imspSend($command_text . $biBook, true, true);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            if (!preg_match("/^\+/",
                            $this->_imsp->imspReceive())) {
                return $this->_imsp->imspError('Did not receive expected command continuation response from IMSP server.',
                                               __FILE__, __LINE__);
            } else {
                $result = $this->_imsp->imspSend($abookName, false, true);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }
            }

        } else {
            $result = $this->_imsp->imspSend($command_text . $abookName, true, true);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $server_response = $this->_imsp->imspReceive();
        if (is_a($server_response, 'PEAR_Error')) {
            return $server_response;
        }

        switch ($server_response) {
        case 'OK':
            $this->_imsp->writeToLog('DELETEADDRESSBOOK completed OK', __FILE__,
                                     __LINE__, PEAR_LOG_INFO);
            return true;

        case 'NO':
            // Could not DELETE abook.
            return $this->_imsp->imspError('IMSP server is unable to perform your request.', __FILE__, __LINE__);

        case 'BAD':
            return $this->_imsp->imspError('The IMSP server did not understand your request.', __FILE__, __LINE__);

        default:
            // Something unexpected.
            return $this->_imsp->imspError('Did not receive the expected response from the server.', __FILE__,
                                           __LINE__);
        }
    }

    /**
     * Renames an address book.
     *
     * @param string $abookOldName Old name.
     * @param string $abookNewName New address book name.
     *
     * @return mixed True / PEAR_Error
     */
    function renameAddressBook($abookOldName, $abookNewName)
    {
        $result = $this->_imsp->imspSend('RENAMEADDRESSBOOK ', true, false);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (preg_match(IMSP_MUST_USE_LITERAL, $abookOldName)) {
            $biOldName = sprintf("{%d}", strlen($abookOldName));

            $result = $this->_imsp->imspSend($biOldName, false, true);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            $this->_imsp->imspReceive();
        }

        $result = $this->_imsp->imspSend("$abookOldName ", false, false);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (preg_match(IMSP_MUST_USE_LITERAL, $abookNewName)) {
            $biNewName = sprintf("{%d}", strlen($abookNewName));

            $result = $this->_imsp->imspSend($biNewName, false, true);
            if (is_a($result, 'PEAR_Error')) {
               return $result;
            }

            $this->_imsp->imspReceive();
        }

        // CRLF since last part.
        $result = $this->_imsp->imspSend($abookNewName, false, true);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        // Get server response.
        $server_response = $this->_imsp->imspReceive();

        switch ($server_response) {
        case 'NO':
            return $this->_imsp->imspError('IMSP server is unable to perform your request.', __FILE__, __LINE__);

        case 'BAD':
            // Syntax problem.
            return $this->_imsp->imspError('The IMSP server did not understand your request.');

        case 'OK':
            $this->_imsp->writeToLog("Address book $abookOldName successfully
                                      changed to $abookNewName", __FILE__,
                                      __LINE__, PEAR_LOG_INFO);
            return true;

        default:
            return $this->_imsp->imspError('Did not receive the expected response from the server.', __FILE__,
                                           __LINE__);
        }
    }

    /**
     * Adds an address book entry to an address book.
     *
     * @param string $abook     Name of address book to add entry to.
     * @param array $entryInfo  Address book entry information -
     *                          there MUST be a field 'name' containing the
     *                          entry name.
     *
     * @return mixed True on success / PEAR_Error on failure.
     */
    function addEntry($abook, $entryInfo)
    {
        $command_text = '';

        if (getType($entryInfo) != 'array') {
            return $this->_imsp->imspError(IMSP_BAD_ARGUMENT, __FILE__, __LINE__);
        }

        // Lock the entry if it already exists.
        $result = $this->lockEntry($abook, $entryInfo['name']);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $result = $this->_imsp->imspSend('STOREADDRESS ', true, false);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        // Take care of the name.
        $entryName = $entryInfo['name'];

        // {} for book name?
        if (preg_match(IMSP_MUST_USE_LITERAL, $abook)) {
            $biBook = sprintf("{%d}", strlen($abook));

            $result = $this->_imsp->imspSend($biBook, false, true);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            $this->_imsp->imspReceive();
        }

        $this->_imsp->imspSend("$abook ", false, false);

        // Do we need {} for entry name as well?
        if (preg_match(IMSP_MUST_USE_LITERAL, $entryName)) {
            $biname = sprintf("{%d}", strlen($entryName));
            $this->_imsp->imspSend($biname, false, true);
            $this->_imsp->imspReceive();
            $this->_imsp->imspSend($entryName, false, false);
        } else {
            $this->_imsp->imspSend("\"$entryName\" ", false, false);
        }

        while (list($key, $value) = each($entryInfo)) {
            // Do not sent the key name 'name'.
            if ($key != 'name') {
                // Protect from extraneous white space
                $value = trim($value);

                // For some reason, tabs seem to break this.
                $value = preg_replace("/\t/", "\n\r", $value);

                // Check to see if we need {}
                if (preg_match(IMSP_MUST_USE_LITERAL, $value)) {
                    $command_text .= $key . sprintf(" {%d}", strlen($value));

                    $this->_imsp->imspSend($command_text, false, true);
                    $server_response = $this->_imsp->imspReceive();
                    $command_text = ''; //Clear the command_text buffer

                    if (!preg_match("/^\+/",
                                    $server_response)) {
                        return $this->_imsp->imspError('Did not receive the expected response from the server.',
                                                       __FILE__, __LINE__);
                    }

                    // Send the string of octets and be sure NOT to
                    // end with CRLF.
                    $this->_imsp->imspSend($value, false, false);

                } else {
                    // If we are here, then we do not need to send a
                    // {}.
                    $value = "\"" . $value . "\"";
                    $command_text .= $key . ' ' . $value . ' ';
                }
            }
        }

        // Send anything that is left of the command.
        $this->_imsp->imspSend($command_text, false, true);
        $server_response = $this->_imsp->imspReceive();

        switch ($server_response) {
        case 'NO':
            //Sorry...cannot do it.
            return $this->_imsp->imspError('IMSP server is unable to perform your request.', __FILE__, __LINE__);

        case 'BAD':
            //Sorry...did not understand you
            return $this->_imsp->imspError('The IMSP server did not understand your request.', __FILE__,
                                           __LINE__);
        }

        if ($server_response != 'OK') {
            // Cyrus-IMSP server sends a FETCHADDRESS Response here.
            // Do others?     This was not in the RFC.
            $dummy_array =
                $this->_parseFetchAddressResponse($server_response);

            $server_response = $this->_imsp->imspReceive();

            switch ($server_response) {
            case 'NO':
                return $this->_imsp->imspError('IMSP server is unable to perform your request.', __FILE__, __LINE__);
            case 'BAD':
                return $this->_imsp->imspError('The IMSP server did not understand your request.', __FILE__,
                                               __LINE__);
            case 'OK':
                $this->_imsp->writeToLog('STOREADDRESS Completed successfully.',
                                         __FILE__, __LINE__, PEAR_LOG_INFO);

                //we were successful...so release the lock on the entry
                if (!$this->unlockEntry($abook, $entryInfo['name'])) {
                    //could not release lock
                    return $this->_imsp->imspError('That address book entry is locked or read only for the current user.', __FILE__,
                                                   __LINE__);
                }

                return true;
            }
        }
    }

    /**
     * Deletes an abook entry.
     *
     * @param string $abook     Name of address book containing entry.
     * @param string $bookEntry Name of entry to delete.
     *
     * @return mixed True on success / PEAR_Error on failure.
     */
    function deleteEntry($abook, $bookEntry)
    {
        // Start the command.
        $result = $this->_imsp->imspSend('DELETEADDRESS ', true, false);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        // Need {} for book name?
        if (preg_match(IMSP_MUST_USE_LITERAL, $abook)) {
            $biBook = sprintf("{%d}", strlen($abook));

            $this->_imsp->imspSend($biBook, false, true);

            if (!preg_match("/^\+/",
                            $this->_imsp->imspReceive())) {

                return $this->_imsp->imspError('Did not receive expected command continuation response from IMSP server.',
                                               __FILE__, __LINE__);
            }

        }

        $this->_imsp->imspSend("$abook ", false, false);

        //How bout for the entry name?
        if (preg_match(IMSP_MUST_USE_LITERAL, $bookEntry)) {
            $biEntry = sprintf("{%d}", strlen($bookEntry));

            $this->_imsp->imspSend($biEntry, false, true);

            if (!preg_match("/^\+/",
                            $this->_imsp->imspReceive())) {
                return $this->_imsp->imspError('Did not receive expected command continuation response from IMSP server.',
                                               __FILE__, __LINE__);
            }

        } else {
            $bookEntry = $this->_imsp->quoteSpacedString($bookEntry);
        }

        $this->_imsp->imspSend($bookEntry, false, true);
        $server_response = $this->_imsp->imspReceive();

        switch ($server_response) {
        case 'NO':
            //Sorry..cannot do it
            return $this->_imsp->imspError('IMSP server is unable to perform your request.', __FILE__, __LINE__);
        case 'BAD':
            //Do not know what your talking about
            return $this->_imsp->imspError('The IMSP server did not understand your request.', __FILE__,
                                           __LINE__);
        case 'OK':
            $this->_imsp->writeToLog('DELETE Completed successfully.', __FILE__,
                                     __LINE__, PEAR_LOG_INFO);
            return true;
        }
    }

    /**
     * Attempts to acquire a semaphore on the address book entry.
     *
     * @param string $abook     Address book name
     * @param string $bookEntry Name of entry to lock
     *
     * @return mixed true or array on success and PEAR_Error on failure
     *               (server depending)
     */
    function lockEntry($abook, $bookEntry)
    {
        $result = $this->_imsp->imspSend('LOCK ADDRESSBOOK ', true, false);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        // Do we need a string literal?
        if (preg_match(IMSP_MUST_USE_LITERAL, $abook)) {
            $biBook = sprintf("{%d}", strlen($abook));

            $this->_imsp->imspSend($biBook, false, true);

            if (!preg_match("/^\+/",
                            $this->_imsp->imspReceive())) {
                return $this->_imsp->imspError('Did not receive expected command continuation response from IMSP server.',
                                               __FILE__, __LINE__);
            }
        }

        $this->_imsp->imspSend("$abook ", false, false);

        // What about the entry name?
        if (preg_match(IMSP_MUST_USE_LITERAL, $bookEntry)) {
            $biEntry = sprintf("{%d}", strlen($bookEntry));

            $this->_imsp->imspSend($biEntry, false, true);

            if (!preg_match("/^\+/",
                            $this->_imsp->imspReceive())) {
                return $this->_imsp->imspError('Did not receive expected command continuation response from IMSP server.',
                                               __FILE__, __LINE__);
            }

            $this->_imsp->imspSend($bookEntry, false, true);

        } else {
            $bookEntry = $this->_imsp->quoteSpacedString($bookEntry);
            $this->_imsp->imspSend("$bookEntry", false, true);
        }

        $server_response = $this->_imsp->imspReceive();

        do {

            switch ($server_response) {

            case 'NO':
                return $this->_imsp->imspError('That address book entry is locked or read only for the current user.',
                                               __FILE__, __LINE__);
            case 'BAD':
                return $this->_imsp->imspError('The IMSP server did not understand your request.', __FILE__,
                                               __LINE__);
            }

            //Check to see if this is a FETCHADDRESS resonse
            $dummy = $this->_parseFetchAddressResponse($server_response);

            if ($dummy) {
                $server_response = $this->_imsp->imspReceive();
            }

        } while ($server_response != 'OK');

        $this->_imsp->writeToLog("LOCK ADDRESSBOOK on $abook $bookEntry OK",
                                 __FILE__, __LINE__, PEAR_LOG_INFO);

        // Return either true or the FETCHADDRESS response if it exists.
        if (!$dummy) {
            return true;
        } else {
            return $dummy;
        }
    }

    /**
     * Unlocks a previously locked address book.
     *
     * @param string $abook     Name of address book containing locked entry.
     * @param string $bookEntry Name of entry to unlock.
     *
     * @return mixed True on success, PEAR_Error on failure.
     */
    function unlockEntry($abook, $bookEntry)
    {
        // Start sending command.
        $result = $this->_imsp->imspSend('UNLOCK ADDRESSBOOK ', true, false);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        // {} for book name?
        if (preg_match(IMSP_MUST_USE_LITERAL, $abook)) {
            $biBook = sprintf("{%d}", strlen($abook));

            $this->_imsp->imspSend($biBook, false, true);

            if (!preg_match("/^\+/",
                            $this->_imsp->imspReceive())) {
                return $this->_imsp->imspError('Did not receive expected command continuation response from IMSP server.',
                                               __FILE__, __LINE__);
            }

        }

        $this->_imsp->imspSend("$abook ", false, false);

        //How bout for entry name?
        if (preg_match(IMSP_MUST_USE_LITERAL, $bookEntry)) {
            $biEntry=sprintf("{%d}", strlen($bookEntry));
            $this->_imsp->imspSend($biEntry, false, true);

            if (!preg_match("/^\+/",
                            $this->_imsp->imspReceive())) {
                return $this->_imsp->imspError('Did not receive expected command continuation response from IMSP server.',
                                               __FILE__, __LINE__);
            }

            $this->_imsp->imspSend($bookEntry, false, true);

        } else {
            $bookEntry = $this->_imsp->quoteSpacedString($bookEntry);
            $this->_imsp->imspSend("$bookEntry", false, true);
        }

        $response = $this->_imsp->imspReceive();

        switch ($response) {
        case 'NO':
            return $this->_imsp->imspError('IMSP server is unable to perform your request.', __FILE__, __LINE__);

        case 'BAD':
            return $this->_imsp->imspError('The IMSP server did not understand your request.', __FILE__, __LINE__);

        case 'OK':
            $this->_imsp->writeToLog("UNLOCK ADDRESSBOOK on $abook $bookEntry OK",
                                     __FILE__, __LINE__, PEAR_LOG_INFO);
            return true;
        }
    }

    /**
     * Access Control List (ACL)  Methods.
     *
     * The following characters are recognized ACL characters: lrwcda
     * l - "lookup"  (see the name and existence of the address book)
     * r - "read"    (search and retrieve addresses from address book)
     * w - "write"   (create/edit new address book entries - not delete)
     * c - "create"  (create new address books under the current address book)
     * d - "delete"  (delete entries or entire book)
     * a - "admin"   (set ACL lists for this address book - usually only
     *               allowed for the owner of the address book)
     *
     * examples:
     *  "lr" would be read only for that user
     *  "lrw" would be read/write
     */

    /**
     * Sets an Access Control List for an abook.
     *
     * @param string $abook Name of address book.
     * @param string $ident Name of user for this acl.
     * @param string $acl   acl for this user/book.
     *
     * @return mixed True on success / PEAR_Error on failure.
     */
    function setACL($abook, $ident, $acl)
    {
        // Verify that $acl looks good.
        if (preg_match("/[^" . IMSP_ACL_RIGHTS . "]/", $acl)) {
            //error...acl list contained unrecoginzed options
            return $this->_imsp->imspError(IMSP_BAD_ARGUMENT, __FILE__, __LINE__);
        }

        // Begin sending command.
        $result = $this->_imsp->imspSend('SETACL ADDRESSBOOK ', true, false);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        // {} for book name?
        if (preg_match(IMSP_MUST_USE_LITERAL, $abook)) {
            $biBook = sprintf("{%d}", strlen($abook));
            $this->_imsp->imspSend($biBook, false, true);

            if (!preg_match("/^\+/",
                            $this->_imsp->imspReceive())) {
                return $this->_imsp->imspError('Did not receive expected command continuation response from IMSP server.',
                                               __FILE__, __LINE__);
            }

        }

        $this->_imsp->imspSend("$abook ", false, false);

        // {} for ident?
        if (preg_match(IMSP_MUST_USE_LITERAL, $ident)) {
            $biIdent = sprintf("{%d}", strlen($ident));
            $this->_imsp->imspSend($biIdent, false, true);

            if (!preg_match("/^\+/",
                            $this->_imsp->imspReceive())) {
                return $this->_imsp->imspError('Did not receive expected command continuation response from IMSP server.',
                                               __FILE__, __LINE__);
            }

        }

        $this->_imsp->imspSend("$ident ", false, false);

        // Now finish up with the actual ACL.
        $this->_imsp->imspSend($acl, false, true);
        $response = $this->_imsp->imspReceive();

        switch ($response) {
        case 'NO':
            // Could not set ACL.
            return $this->_imsp->imspError('IMSP server is unable to perform your request.',__FILE__, __LINE__);

        case 'BAD':
            // Bad syntax.
            return $this->_imsp->imspError('The IMSP server did not understand your request.',__FILE__, __LINE__);

        case 'OK':
            $this->_imsp->writeToLog("ACL set for $ident on $abook",
                                      __FILE__, __LINE__, PEAR_LOG_DEBUG);
            return true;

        default:
            // Do not know why we would make it down here.
            return $this->_imsp->imspError('Did not receive the expected response from the server.',
                                           __FILE__, __LINE__);
        }
    }

    /**
     * Retrieves an address book's ACL.
     *
     * @param string $abook Name of address book to retrieve acl for.
     *
     * @return mixed array containing acl for every user with access to
     *                     address book or PEAR_Error on failure.
     */
    function getACL($abook)
    {
        $result = $this->_imsp->imspSend('GETACL ADDRESSBOOK ', true, false);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        // {} for book name?
        if (preg_match(IMSP_MUST_USE_LITERAL, $abook)) {
            $biName = sprintf("{%d}", strlen($abook));
            $this->_imsp->imspSend($biName, false, true);

            if (!preg_match("/^\+/",
                            $this->_imsp->imspReceive())) {
                return $this->_imsp->imspError('Did not receive expected command continuation response from IMSP server.',
                                               __FILE__, __LINE__);
            }
        }

        $this->_imsp->imspSend($abook, false, true);

        // Get results.
        $response = $this->_imsp->imspReceive();

        switch ($response) {
        case 'NO':
            // Could not complete?
            return $this->_imsp->imspError('IMSP server is unable to perform your request.', __FILE__, __LINE__);

        case 'BAD':
            // Do not know what you said!
            return $this->_imsp->imspError('The IMSP server did not understand your request.', __FILE__, __LINE__);
        }

        // If we are here, we need to receive the * ACL Responses.
        do {
            /* Get an array of responses.
             * The [3] element should be the address book name
             * [4] and [5] will be user/group name and permissions */

            //the book name might be a literal
            if (preg_match(IMSP_OCTET_COUNT, $response, $tempArray)) {
                $data = $this->_imsp->receiveStringLiteral($tempArray[2]);
                //Get the rest
                $response = $this->_imsp->imspReceive();
            }

            $parts = explode(' ', $response);

            // Push the array if book was a literal
            if ($data) {
                array_unshift($parts, ' ', ' ', ' ', ' ');
            }
            // Address book name quoted?
            $numParts = count($parts);
            $name = $parts[3];
            $firstACLIdx = 4;
            $firstChar = substr($name, 0, 1);
            if ($firstChar == "\"") {
                for ($i = 4; $i < $numParts; $i++) {
                    $lastChar = substr($parts[$i], strlen($parts[$i]) - 1, 1);
                    $firstACLIdx++;
                    if ($lastChar == "\"") {
                        break;
                    }
                }
            }

            for ($i = $firstACLIdx; $i < count($parts); $i += 2) {
                $results[$parts[$i]] = $parts[$i+1];
            }

            $response = $this->_imsp->imspReceive();

        } while (preg_match("/^\* ACL ADDRESSBOOK/", $response));

        // Hopefully we can receive an OK response here
        if ($response != 'OK') {
            // Some weird problem
            return $this->_imsp->imspError('Did not receive the expected response from the server.',
                                           __FILE__, __LINE__);
        }

        $this->_imsp->writeToLog("GETACL on $abook completed.", __FILE__,
                                 __LINE__, PEAR_LOG_INFO);
        return $results;

    }

    /**
     * Deletes an ACL entry for an address book.
     *
     * @param string $abook Name of the address book.
     * @param string $ident Name of entry to remove acl for.
     *
     * @return mixed true on success, PEAR_Error on failure.
     */
    function deleteACL($abook, $ident)
    {
        $result = $this->_imsp->imspSend('DELETEACL ADDRESSBOOK ', true, false);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        // Do we need literal for address book name?
        if (preg_match(IMSP_MUST_USE_LITERAL, $abook)) {
            $biBook = sprintf("{%d}", strlen($abook));
            $this->_imsp->imspSend($biBook, false, true);

            if (!preg_match("/^\+/",
                            $this->_imsp->imspReceive())) {
                return $this->_imsp->imspError('Did not receive expected command continuation response from IMSP server.',
                                               __FILE__, __LINE__);
            }

        }

        $this->_imsp->imspSend("$abook ", false, false);

        // Literal for ident name?
        if (preg_match(IMSP_MUST_USE_LITERAL, $ident)) {
            $biIdent = sprintf("{%d}", strlen($ident));
            $this->_imsp->imspSend($biIdent, false, true);

            if (!preg_match("/^\+/",
                            $this->_imsp->imspReceive())) {
                return $this->_imsp->imspError('Did not receive expected command continuation response from IMSP server.',
                                               __FILE__, __LINE__);
            }

            $this->_imsp->imspSend($ident, false, true);
        } else {
            $this->_imsp->imspSend("\"$ident\"", false, true);
        }

        // Get results.
        $server_response = $this->_imsp->imspReceive();

        switch ($server_response) {
        case 'NO':
            return $this->_imsp->imspError('IMSP server is unable to perform your request.', __FILE__, __LINE__);

        case 'BAD':
            return $this->_imsp->imspError('The IMSP server did not understand your request.', __FILE__, __LINE__);

        case 'OK':
            $this->_imsp->writeToLog("DELETED ACL for $ident on $abook",
                                      __FILE__, __LINE__, PEAR_LOG_INFO);
            return true;

        default:
            return $this->_imsp->imspError('Did not receive the expected response from the server.',
                                           __FILE__, __LINE__);
        }
    }

    /**
     * Returns an ACL string containing the rights for the current user
     *
     * @param string $abook Name of address book to retrieve acl.
     *
     * @return mixed acl of current user or PEAR_Error on failure.
     */
    function myRights($abook)
    {
        $data = '';
        $result = $this->_imsp->imspSend('MYRIGHTS ADDRESSBOOK ', true, false);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (preg_match(IMSP_MUST_USE_LITERAL, $abook)) {
            $biBook = sprintf("{%d}", strlen($abook));
            $this->_imsp->imspSend($biBook, false, true);

            if (!preg_match("/^\+/",
                            $this->_imsp->imspReceive())) {
                return $this->_imsp->imspError('Did not receive expected command continuation response from IMSP server.',
                                               __FILE__, __LINE__);
            }

        }

        $this->_imsp->imspSend($abook, false, true);
        $server_response = $this->_imsp->imspReceive();

        switch ($server_response) {
        case 'NO':
            return $this->_imsp->imspError('IMSP server is unable to perform your request.', __FILE__, __LINE__);

        case 'BAD':
            return $this->_imsp->imspError('The IMSP server did not understand your request.', __FILE__, __LINE__);
        }

        if (!preg_match("/^\* MYRIGHTS ADDRESSBOOK/", $server_response)) {
            return $this->_imsp->imspError('Did not receive the expected response from the server.',
                                           __FILE__, __LINE__);
        }

        // {} for the abook name?
        if (preg_match(IMSP_OCTET_COUNT, $server_response, $tempArray)) {
            $data = $this->_imsp->receiveStringLiteral($tempArray[2]);
            // Get the rest.
            $server_response = $this->_imsp->imspReceive();
        }

        $parts = explode(' ', $server_response);

        // Push the array if we had a {}
        if ($data) {
            array_unshift($parts, ' ', ' ', ' ', ' ');
        }

        // Quoted address book name?
        $numParts = count($parts);
        $name = $parts[3];
        $firstACLIdx = 4;
        $firstChar = substr($name, 0, 1);
        if ($firstChar == "\"") {
            for ($i = 4; $i < $numParts; $i++) {
                $lastChar = substr($parts[$i], strlen($parts[$i]) - 1, 1);
                $firstACLIdx++;
                if ($lastChar == "\"") {
                    break;
                }
            }
        }

        $acl = $parts[$firstACLIdx];
        $server_response = $this->_imsp->imspReceive();

        if ($server_response != 'OK') {
            return $this->_imsp->imspError('Did not receive the expected response from the server.',
                                           __FILE__, __LINE__);
        } else {
            $this->_imsp->writeToLog("MYRIGHTS on $abook completed.",
                                      __FILE__, __LINE__, PEAR_LOG_INFO);
            return $acl;
        }
    }

    /**
     * Sets the log information in the Net_IMSP object.
     *
     * @param  array  Log parameters.
     *
     * @return mixed  True on success PEAR_Error on failure.
     */
    function setLogger($params)
    {
        if (isset($this->_imsp)) {
            return $this->_imsp->setLogger($params);
        } else {
            return PEAR::raiseError(_("The IMSP log could not be initialized."));
        }
    }

    /**
     * Parses a IMSP fetchaddress response text string into
     * key-value pairs
     *
     * @access private
     * @param  string  $server_response The raw fetchaddress response.
     *
     * @return array   Address book entry information as key=>value pairs.
     */
    function _parseFetchAddressResponse($server_response)
    {
        $abook = '';

        if (!preg_match("/^\* FETCHADDRESS /", $server_response)) {
            $this->_imsp->writeToLog('[ERROR] Did not receive a FETCHADDRESS response from server.',
                                     __FILE__, __LINE__, PEAR_LOG_ERR);

            $this->_imsp->exitCode = 'Did not receive the expected response from the server.';
            return false;
        }

        /* NOTES
         * Parse out the server response string
         *
         * After choping off the server command response tags and
         * explode()'ing the server_response string
         * the $parts array contains the chunks of the server returned data.
         *
         * The predifined 'name' field starts in $parts[1].
         * The server should return any single item of data
         * that contains spaces within it as a double quoted string.
         * So we can interpret the existence of a double quote at the beginning
         * of a chunk to mean that the next chunk(s) are part of
         * the same value.  A double quote at the end of a chunk signifies the
         * end of that value and the chunk following that can be interpreted
         * as a key name.
         *
         * We also need to watch for the server returning a {} response for the
         * value of the key as well. */

        // Was the address book name a  {}?
        if (preg_match("/(^\* FETCHADDRESS )({)([0-9]{1,})(\}$)/",
                       $server_response, $tempArray)) {
            $abook = $this->_imsp->receiveStringLiteral($tempArray[3]);
            $chopped_response = trim($this->_imsp->imspReceive());
        } else {
            // Take off the stuff from the beginning of the response
            $chopped_response = trim(preg_replace("/^\* FETCHADDRESS /",
                                                  '', $server_response));
        }

        $parts = explode(' ', $chopped_response);
        /* If addres book was sent as a {} then we must 'push' a blank
         * value to the start of this array so the rest of the routine
         * will work with the correct indexes. */
         if (!empty($abook)) {
            array_unshift($parts, ' ');
        }

        // Was the address book name quoted?
        $numOfParts = count($parts);
        $name = $parts[0];
        $firstNameIdx = 1;
        $firstChar = substr($name, 0, 1);
        if ($firstChar =="\"") {
            for ($i = 1; $i < $numOfParts; $i++) {
                $lastChar = substr($parts[$i], strlen($parts[$i]) - 1, 1);
                $firstNameIdx++;
                if ($lastChar == "\"") {
                    break;
                }
            }
        }

        // Now start working on the entry name
        $name = $parts[$firstNameIdx];
        $firstChar = substr($name,0,1);

        // Check to see if the first char of the name string is a double quote
        // so we know if we have to extract more of the name.
        if ($firstChar == "\"") {
            $name = ltrim($name, "\"");
            for ($i = $firstNameIdx + 1; $i < $numOfParts; $i++) {
                $name .=  ' ' . $parts[$i];
                $lastChar = substr($parts[$i], strlen($parts[$i]) - 1,1);
                if ($lastChar == "\"") {
                    $name = rtrim($name, "\"");
                    $nextKey = $i + 1;
                    break;
                }
            }

        // Check for {}
        } elseif (preg_match('/\{(\d+)\}/', $name, $matches)) {
            $name = $this->_imsp->receiveStringLiteral($matches[1]);
            $response=$this->_imsp->imspReceive();
            $parts = explode(' ', $response);
            $numOfParts = count($parts);
            $nextKey = 0;
        } else {
            // If only one chunk for 'name' then we just have to point
            // to the next chunk in the array...which will hopefully
            // be '2'
            $nextKey = $firstNameIdx + 1;
        }

        $lastChar = '';
        $entry['name'] = $name;

        // Start parsing the rest of the response.
        for ($i = $nextKey; $i < $numOfParts; $i += 2) {
            $key = $parts[$i];
            /* Check for {} */
            if (@preg_match(IMSP_OCTET_COUNT, $parts[$i+1], $tempArray)) {
                $server_data = $this->_imsp->receiveStringLiteral($tempArray[2]);
                $entry[$key] = $server_data;

                /* Read any remaining data from the stream and reset
                 * the counter variables so the loop will continue
                 * correctly. Note we set $i  to -2 because it will
                 * be incremented by 2 before the loop will run again */
                $parts = $this->_imsp->getServerResponseChunks();
                $i = -2;
                $numOfParts = count($parts);
            } else {
                // Not a string literal response
                @$entry[$key] = $parts[$i + 1];
                 // Check to see if the value started with a double
                 // quote.  We also need to check if the last char is a
                 // quote to make sure we REALLY have to check the next
                 // elements for a closing quote.
                if ((@substr($parts[$i + 1], 0, 1) == '"') &&
                    (substr($parts[$i + 1],
                     strlen($parts[$i + 1]) - 1, 1) != '"')) {

                    do {
                        $nextElement = $parts[$i+2];

                        // Was this element the last one?
                        $lastChar = substr($nextElement,
                                           strlen($nextElement) - 1, 1);
                        $entry[$key] .= ' ' . $nextElement;

                        // NOW, we can check the lastChar.
                        if ($lastChar == '"') {
                            $done = true;
                            $i++;
                        } else {
                            // Check to see if the next element is the
                            // last one. If so, the do loop will terminate.
                            $done = false;
                            $lastChar = substr($parts[$i+3],
                                               strlen($parts[$i+3]) - 1,1);
                            $i++;
                        }
                    } while ($lastChar != '"');

                    // Do we need to add the final element, or were
                    // there only two total?
                    if (!$done) {
                        $nextElement = $parts[$i+2];
                        $entry[$key] .= ' ' . $nextElement;
                        $i++;
                    }

                    // Remove the quotes sent back to us from the server.
                    if (substr($entry[$key], 0, 1) == '"') {
                        $entry[$key] = substr($entry[$key], 1,
                                              strlen($entry[$key]) - 2);
                    }

                    if (substr($entry[$key],
                               strlen($entry[$key]) - 1, 1) == '"') {

                        $entry[$key] = substr($entry[$key], 0,
                                              strlen($entry[$key]) - 2);
                    }
                } elseif ((@substr($parts[$i + 1], 0, 1) == '"') && 
                          (substr($parts[$i + 1], -1, 1) == '"')) {
                    // Remove the quotes sent back to us from the server.
                    if (substr($entry[$key], 0, 1) == '"') {
                        $entry[$key] = substr($entry[$key], 1,
                                              strlen($entry[$key]) - 2);
                    }

                    if (substr($entry[$key], -1, 1) == '"') {
                        $entry[$key] = substr($entry[$key], 0,
                                              strlen($entry[$key]) - 2);
                    }
                }
            }
        }
        return $entry;
    }

}
