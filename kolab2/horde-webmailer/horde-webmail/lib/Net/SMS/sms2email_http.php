<?php
/**
 * @package Net_SMS
 */

/**
 * HTTP_Request class.
 */
include_once 'HTTP/Request.php';

/**
 * Net_SMS_sms2email_http Class implements the HTTP API for accessing the
 * sms2email (www.sms2email.com) SMS gateway.
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * $Horde: framework/Net_SMS/SMS/sms2email_http.php,v 1.23.10.15 2009-01-06 15:23:28 jan Exp $
 *
 * @author Marko Djukic <marko@oblo.com>
 * @package Net_SMS
 */
class Net_SMS_sms2email_http extends Net_SMS {

    var $_base_url = 'horde.sms2email.com/horde/';

    /**
     * An array of capabilities, so that the driver can report which
     * operations it supports and which it doesn't. Possible values are:<pre>
     *   auth        - The gateway requires authentication before sending;
     *   batch       - Batch sending is supported;
     *   multi       - Sending of messages to multiple recipients is supported;
     *   receive     - Whether this driver is capable of receiving SMS;
     *   credit      - Is use of the gateway based on credits;
     *   addressbook - Are gateway addressbooks supported;
     *   lists       - Gateway support for distribution lists.
     * </pre>
     *
     * @var array
     */
    var $capabilities = array('auth'        => false,
                              'batch'       => 100,
                              'multi'       => true,
                              'receive'     => false,
                              'credit'      => true,
                              'addressbook' => true,
                              'lists'       => true);

    /**
     * This function does the actual sending of the message.
     *
     * @access private
     *
     * @param array $message  The array containing the message and its send
     *                        parameters.
     * @param array $to       The recipients.
     *
     * @return array  An array with the success status and additional
     *                information.
     */
    function _send($message, $to)
    {
        /* Set up the sending url. */
        $url = sprintf('postmsg.php?username=%s&password=%s&message=%s',
                       urlencode($this->_params['user']),
                       urlencode($this->_params['password']),
                       urlencode($message['text']));

        /* Check if source from is set. */
        if (!empty($message['send_params']['from'])) {
            $url .= '&orig=' . urlencode($message['send_params']['from']);
        }
        /* Check if message type is flash. */
        if (!empty($message['send_params']['msg_type']) &&
            $message['send_params']['msg_type'] == 'SMS_FLASH') {
            $url .= '&flash=1';
        }
        /* Check if delivery report url has been set. */
        if (!empty($this->_params['delivery_report'])) {
            $url .= '&dlurl=' . urlencode($this->_params['delivery_report']) .
                    'reportcode=%code&destinationnumber=%dest';
        }

        /* Loop through recipients and do some minimal validity checking. */
        if (is_array($to)) {
            foreach ($to as $key => $val) {
                if (preg_match('/^.*?<?\+?(\d{7,})(>|$)/', $val, $matches)) {
                    $to[$key] = $matches[1];
                } else {
                    /* FIXME: Silently drop bad recipients. This should be
                     * logged and/or reported. */
                    unset($to[$key]);
                }
            }
            $to = implode(',', $to);
        } else {
            if (preg_match('/^.*?<?\+?(\d{7,})(>|$)/', $to, $matches)) {
                $to = $matches[1];
            } else {
                return array(0, sprintf(_("Invalid recipient: \"%s\""), $to));
            }
        }

        /* Append the recipients of this message and call the url. */
        $url .= '&to_num=' . $to;
        $response = $this->_callURL($url);
        if (is_a($response, 'PEAR_Error')) {
            return array(0, $response->getMessage());
        }

        /* Parse the response, check for new lines in case of multiple
         * recipients. */
        $lines = explode("\n", $response);
        $response = array();

        if (count($lines) > 1) {
            /* Multiple recipients. */
            foreach ($lines as $line) {
                $parts = explode('To:', $line);
                $recipient = trim($parts[1]);
                if ($lines[0] == 'AQSMS-OK') {
                    $response[$recipient] = array(1, null);
                } else {
                    $response[$recipient] = array(0, $lines[0]);
                }
            }
        } else {
            /* Single recipient. */
            if ($lines[0] == 'AQSMS-OK') {
                $response[$to] = array(1, null);
            } else {
                $response[$to] = array(0, $lines[0]);
            }
        }

        return $response;
    }

    /**
     * Returns the current credit balance on the gateway.
     *
     * @access private
     *
     * @return integer  The credit balance available on the gateway.
     */
    function _getBalance()
    {
        /* Set up the url and call it. */
        $url = sprintf('postmsg.php?username=%s&password=%s&cmd=credit',
                       urlencode($this->_params['user']),
                       urlencode($this->_params['password']));
        $response = $this->_callURL($url);
        if (is_a($response, 'PEAR_Error')) {
            return $response;
        }

        /* Try splitting up the response. */
        $lines = explode('=', $response);

        if ($lines[0] == 'AQSMS-CREDIT') {
            return $lines[1];
        } else {
            return $this->getError($lines[0], _("Could not check balance. %s"));
        }
    }

    /**
     * Adds a contact to the gateway's addressbook.
     *
     * @param string $name     The name for this contact
     * @param integer $number  The contact's phone number.
     *
     * @return mixed  The remote contact ID on success or PEAR Error on
     *                failure.
     */
    function addContact($name, $number)
    {
        /* Set up the url and call it. */
        $url = sprintf('postcontacts.php?username=%s&password=%s&cmd=ADDCONTACT&name=%s&number=%s',
                       urlencode($this->_params['user']),
                       urlencode($this->_params['password']),
                       urlencode($name),
                       $number);
        $response = $this->_callURL($url);
        if (is_a($response, 'PEAR_Error')) {
            return $response;
        }

        /* Check if there was an error response. */
        if (substr($response, 0, 17) != 'AQSMS-CONTACTIDOK') {
            return $this->getError($response, _("Could not add contact. %s"));
        }

        /* Split up the response. */
        $lines = explode(',=', $response);
        return $lines[1];
    }

    /**
     * Updates a contact in the gateway's addressbook.
     *
     * @param integer $id      The contact's ID on the gateway.
     * @param string $name     The name for this contact
     * @param integer $number  The contact's phone number.
     *
     * @return mixed  True on success or PEAR Error on failure.
     */
    function updateContact($id, $name, $number)
    {
        /* Set up the url and call it. */
        $url = sprintf('postcontacts.php?username=%s&password=%s&cmd=UPDATECONTACT&id=%s&name=%s&number=%s',
                       urlencode($this->_params['user']),
                       urlencode($this->_params['password']),
                       $id,
                       urlencode($name),
                       $number);
        $response = $this->_callURL($url);
        if (is_a($response, 'PEAR_Error')) {
            return $response;
        }

        /* Parse the response. */
        if ($response == 'AQSMS-OK') {
            return true;
        } else {
            return $this->getError($response, _("Could not update contact. %s"));
        }
    }

    /**
     * Deletes a contact in the gateway's addressbook.
     *
     * @param integer $id  The contact's ID on the gateway.
     *
     * @return mixed  True on success or PEAR Error on failure.
     */
    function deleteContact($id)
    {
        /* Set up the url and call it. */
        $url = sprintf('postcontacts.php?username=%s&password=%s&cmd=DELETECONTACT&id=%s',
                       urlencode($this->_params['user']),
                       urlencode($this->_params['password']),
                       $id);
        $response = $this->_callURL($url);
        if (is_a($response, 'PEAR_Error')) {
            return $response;
        }

        /* Parse the response. */
        if ($response == 'AQSMS-OK') {
            return true;
        } else {
            return $this->getError($response, _("Could not delete contact. %s"));
        }
    }

    /**
     * Fetches the entire address book from the gateway.
     *
     * @return mixed  Array of contacts on success or PEAR Error on failure.
     *                Format of the returned contacts is for example:<code>
     *                   array(<uniqueid> => array('name'   => <name>,
     *                                             'number' => <number>),
     *                         <uniqueid> => array('name'   => <name>,
     *                                             'number' => <number>));
     * </code>
     */
    function getAddressBook()
    {
        /* Set up the url and call it. */
        $url = sprintf('postcontacts.php?username=%s&password=%s&cmd=GETADDRESSBOOK',
                       urlencode($this->_params['user']),
                       urlencode($this->_params['password']));
        $response = $this->_callURL($url);
        if (is_a($response, 'PEAR_Error')) {
            return $response;
        }

        /* Check if there was an error response. */
        if (substr($response, 0, 19) != 'AQSMS-ADDRESSBOOKOK') {
            return $this->getError($response, _("Could not retrieve address book. %s"));
        }

        /* Parse the response and construct the array. */
        list($response, $contacts_str) = explode(',', $response, 2);

        /* Check that the full address book list has been received. */
        $length = substr($response, 19);
        if (strlen($contacts_str) != $length) {
            return PEAR::raiseError(_("Could not fetch complete address book."));
        }
        $contacts_lines = explode("\n", $contacts_str);
        $contacts = array();
        /* Loop through lines and pick out the fields, make sure that the ""
         * are not included in the values, so get the line less 1 char on each
         * end and split for ",". */
        foreach ($contacts_lines as $line) {
            list($id, $name, $number) = explode('","', substr($line, 1, -1));
            $contacts[$id] = array('name' => $name, 'number' => $number);
        }

        return $contacts;
    }

    /**
     * Creates a new distribution list on the gateway.
     *
     * @param string $name    An arbitrary name for the new list.
     * @param array $numbers  A simple array of numbers to add to the list.
     *
     * @return mixed  Gateway ID for the created list on success or PEAR Error
     *                on failure.
     */
    function listCreate($name, $numbers)
    {
        /* Set up the url and call it. */
        $url = sprintf('postdistribution.php?username=%s&password=%s&cmd=ADDDISTLIST&name=%s&numlist=%s',
                       urlencode($this->_params['user']),
                       urlencode($this->_params['password']),
                       urlencode($name),
                       implode(',', $numbers));
        $response = $this->_callURL($url);
        if (is_a($response, 'PEAR_Error')) {
            return $response;
        }

        /* Check if there was an error response. */
        if (substr($response, 0, 16) != 'AQSMS-DISTITEMID') {
            return $this->getError($response, _("Could not create distribution list. %s"));
        }

        /* Parse the response and get the distribution list ID. */
        list($response, $id) = explode('=', $response);

        /* TODO: do we need to check the length of the id string? */

        return $id;
    }

    /**
     * Deletes a distribution list from the gateway.
     *
     * @param string $id  The gateway ID for the list to delete.
     *
     * @return mixed  True on success or PEAR Error on failure.
     */
    function listDelete($id)
    {
        /* Set up the url and call it. */
        $url = sprintf('postdistribution.php?username=%s&password=%s&cmd=DELETEDISTLIST&distid=%s',
                       urlencode($this->_params['user']),
                       urlencode($this->_params['password']),
                       $id);
        $response = $this->_callURL($url);
        if (is_a($response, 'PEAR_Error')) {
            return $response;
        }

        /* Check response. */
        if ($response == 'AQSMS-OK') {
            return true;
        } else {
            return $this->getError($response, _("Could not delete distribution list. %s"));
        }
    }

    /**
     * Updates a distribution list on the gateway.
     *
     * @param string $id       The gateway ID for the list to update.
     * @param string $name     The arbitrary name of the list. If different
     *                         from the original name that the list was created
     *                         under, the list will be renamed.
     * @param string $numbers  The new list of numbers in the list. If left
     *                         empty, the result will be the same as calling
     *                         the listRename() function.
     *
     * @return mixed  True on success or PEAR Error on failure.
     */
    function listUpdate($id, $name, $numbers = array())
    {
        /* Set up the url and call it. */
        $url = sprintf('postdistribution.php?username=%s&password=%s&cmd=UPDATELISTNAME&distid=%s&name=%s',
                       urlencode($this->_params['user']),
                       urlencode($this->_params['password']),
                       $id,
                       urlencode($name));

        /* Check if the list numbers need updating. */
        if (!empty($numbers)) {
            $url .= '&numbers=' . implode(',', $numbers);
        }

        $response = $this->_callURL($url);
        if (is_a($response, 'PEAR_Error')) {
            return $response;
        }

        /* Check response. */
        if ($response == 'AQSMS-OK') {
            return true;
        } else {
            return $this->getError($response, _("Could not update distribution list. %s"));
        }
    }

    /**
     * Renames a distribution list on the gateway. Does nothing other than
     * calling the listUpdate() function with just the $id and $name
     * variables.
     *
     * @param string $id    The gateway ID for the list to update.
     * @param string $name  The new arbitrary name for the list.
     *
     * @return mixed  True on success or PEAR Error on failure.
     */
    function listRename($id, $name)
    {
        return $this->listUpdate($id, $name);
    }

    /**
     * Fetches a listing of available distribution lists on the server.
     *
     * @return mixed  An array of lists on success or PEAR Error on failure.
     *                Format of the returned lists is for example:<code>
     *                   array(<uniqueid> => array('name'   => <name>),
     *                         <uniqueid> => array('name'   => <name>));
     * </code>
     */
    function getLists()
    {
        /* Set up the url and call it. */
        $url = sprintf('postdistribution.php?username=%s&password=%s&cmd=GETCOMPACTLIST',
                       urlencode($this->_params['user']),
                       urlencode($this->_params['password']));
        $response = $this->_callURL($url);
        if (is_a($response, 'PEAR_Error')) {
            return $response;
        }

        /* Check if there was an error response. */
        if (substr($response, 0, 22) != 'AQSMS-DISTRIBUTIONLIST') {
            return $this->getError($response, _("Could not retrieve distribution lists. %s"));
        }

        /* Parse the response and construct the array. */
        list($response, $lists_str) = explode(',', $response, 2);

        /* Check that the full list of distribution lists has been received. */
        $length = substr($response, 22);
        if (strlen($lists_str) != $length) {
            return PEAR::raiseError(_("Could not fetch the complete list of distribution lists."));
        }
        $lists_lines = explode("\n", $lists_str);
        $lists = array();
        /* Loop through lines and pick out the fields, make sure that the ""
         * are not included in the values, so get the line less 1 char on each
         * end and split for ",". */
        foreach ($lists_lines as $line) {
            list($id, $name, $count) = explode('","', substr($line, 1, -1));
            $lists[$id] = array('name'  => $name,
                                'count' => $count);
        }

        return $lists;
    }

    /**
     * Fetches a specific distribution list from the gateway.
     *
     * @param string  The ID of the distribution list to fetch.
     *
     * @return mixed  An array of numbers in the list on success or PEAR Error
     *                on failure.
     */
    function getList($id)
    {
        /* Set up the url and call it. */
        $url = sprintf('postdistribution.php?username=%s&password=%s&cmd=GETNUMBERSWITHID&distid=%s',
                       urlencode($this->_params['user']),
                       urlencode($this->_params['password']),
                       $id);
        $response = $this->_callURL($url);
        if (is_a($response, 'PEAR_Error')) {
            return $response;
        }

        /* Check if there was an error response. */
        if (substr($response, 0, 22) != 'AQSMS-DISTRIBUTIONLIST') {
            return $this->getError($response, _("Could not retrieve distribution list. %s"));
        }

        /* Parse the response and construct the array. */
        list($response, $list_str) = explode(',', $response, 2);

        /* Check that the full list of distribution lists has been received. */
        $length = substr($response, 22);
        if (strlen($list_str) != $length) {
            return PEAR::raiseError(_("Could not fetch complete distribution list."));
        }
        $list_str = trim($list_str);
        list($count, $numbers) = explode('","', $list_str);

        /* TODO: Anything useful that can be done with the count of numbers at
         * the start? */
        $count = substr($count, 1);

        /* Explode the list of numbers into an array and return. */
        $numbers = substr($numbers, 0, -1);
        return explode(',', $numbers);
    }

    /**
     * Identifies this gateway driver and returns a brief description.
     *
     * @return array  Array of driver info.
     */
    function getInfo()
    {
        return array(
            'name' => _("sms2email via HTTP"),
            'desc' => _("This driver allows sending of messages through the sms2email (http://sms2email.com) gateway, using the HTTP API"),
        );
    }

    /**
     * Returns the required parameters for this gateway driver. The settable
     * parameters for this gateway are:<pre>
     *   - user            - The username for authentication on the gateway;
     *   - password        - The password for authentication on the gateway;
     *   - ssl             - Whether or not to use SSL for communication with
     *                       the gateway.
     *   - delivery_report - A URL for a script which would accept delivery
     *                       report from the gateway.
     * </pre>
     *
     * @return array  Array of required parameters.
     */
    function getParams()
    {
        $params = array();
        $params['user']     = array('label' => _("Username"), 'type' => 'text');
        $params['password'] = array('label' => _("Password"), 'type' => 'text');
        $params['ssl']      = array('label'    => _("Use SSL"),
                                    'type'     => 'boolean',
                                    'required' => false);
        $params['delivery_report'] = array('label'    => _("URL for your script delivery status report"),
                                           'type'     => 'text',
                                           'required' => false);


        return $params;
    }

    /**
     * Returns the parameters that can be set as default for sending messages
     * using this gateway driver and displayed when sending messages.
     *
     * @return array  Array of parameters that can be set as default.
     */
    function getDefaultSendParams()
    {
        $params = array();
        $params['from'] = array(
            'label' => _("Source address"),
            'type' => 'text');

        $params['deliv_time'] = array(
            'label' => _("Delivery time"),
            'type' => 'enum',
            'params' => array(array('now' => _("immediate"), 'user' => _("user select"))));

        $types = array('SMS_TEXT' => _("Standard"), 'SMS_FLASH' => _("Flash"));
        $params['msg_type'] = array(
            'label' => _("Message type"),
            'type' => 'keyval_multienum',
            'params' => array($types));

        return $params;
    }

    /**
     * Returns the parameters for sending messages using this gateway driver,
     * displayed when sending messages. These are filtered out using the
     * default values set up when creating the gateway.
     *
     * @return array  Array of required parameters.
     * @todo  Would be nice to use a time/date setup rather than minutes from
     *        now for the delivery time. Upload field for ringtones/logos?
     */
    function getSendParams($params)
    {
        if (empty($params['from'])) {
            $params['from'] = array(
                'label' => _("Source address"),
                'type' => 'text');
        }

        if ($params['deliv_time'] == 'user') {
            $params['deliv_time'] = array(
                'label' => _("Delivery time"),
                'type' => 'int',
                'desc' => _("Value in minutes from now."));
        }

        if (count($params['msg_type']) > 1) {
            $params['msg_type'] = array(
                'label' => _("Message type"),
                'type' => 'enum',
                'params' => array($params['msg_type']));
        } else {
            $params['msg_type'] = $params['msg_type'][0];
        }

        return $params;
    }

    /**
     * Returns a string representation of an error code.
     *
     * @param integer $error  The error code to look up.
     * @param string $text    An existing error text to use to raise a
     *                        PEAR Error.
     *
     * @return mixed  A textual message corresponding to the error code or a
     *                PEAR Error if passed an existing error text.
     *
     * @todo  Check which of these are actually required and trim down the
     *        list.
     */
    function getError($error, $error_text = '')
    {
        $error = trim($error);

        /* An array of error codes returned by the gateway. */
        $errors = array(
            'AQSMS-NOAUTHDETAILS'        => _("No username and/or password sent."),
            'AQSMS-AUTHERROR'            => _("Incorrect username and/or password."),
            'AQSMS-NOMSG'                => _("No message supplied."),
            'AQSMS-NODEST'               => _("No destination supplied."),
            'AQSMS-NOCREDIT'             => _("Insufficient credit."),
            'AQSMS-NONAMESUPPLIED'       => _("No name specified."),
            'AQSMS-NONUMBERSUPPLIED'     => _("No number specified."),
            'AQSMS-ADDRESSBOOKERROR'     => _("There was an error performing the specified address book function. Please try again later."),
            'AQSMS-CONTACTIDERROR'       => _("The contact ID number was not specified, left blank or was not found in the database."),
            'AQSMS-CONTACTUPDATEERROR'   => _("There was an error updating the contact details. Please try again later."),
            'AQSMS-DISTIDERROR'          => _("The distribution list ID was either not specified, left blank or not found in the database."),
            'AQSMS-NODISTLISTSUPPLIED'   => _("The distribution list was not specified."),
            'AQSMS-INSUFFICIENTCREDITS'  => _("Insufficient credit to send to the distribution list."),
            'AQSMS-NONUMBERLISTSUPPLIED' => _("Numbers not specified for updating in distribution list."),
            'AQSMS-DISTLISTUPDATEERROR'  => _("There was an error updating the distribution list. Please try again later."));

        if (empty($error_text)) {
            return $errors[$error];
        } else {
            return PEAR::raiseError(sprintf($error_text, $errors[$error]));
        }
    }

    /**
     * Do the http call using a url passed to the function.
     *
     * @access private
     *
     * @param string $url  The url to call.
     *
     * @return mixed  The response on success or PEAR Error on failure.
     */
    function _callURL($url)
    {
        $options['method'] = 'POST';
        $options['timeout'] = 5;
        $options['allowRedirects'] = true;

        $url = (empty($this->_params['ssl']) ? 'http://' : 'https://') . $this->_base_url . $url;

        $http = new HTTP_Request($url, $options);
        @$http->sendRequest();
        if ($http->getResponseCode() != 200) {
            return PEAR::raiseError(sprintf(_("Could not open %s."), $url));
        }

        return $http->getResponseBody();
    }

}
