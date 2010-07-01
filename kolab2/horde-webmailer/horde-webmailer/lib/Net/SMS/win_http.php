<?php
/**
 * @package Net_SMS
 */

/**
 * HTTP_Request class.
 */
include_once 'HTTP/Request.php';

/**
 * Net_SMS_win_http Class implements the HTTP API for accessing the WIN
 * (www.winplc.com) SMS gateway.
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * $Horde: framework/Net_SMS/SMS/win_http.php,v 1.9.2.7 2009-01-06 15:23:28 jan Exp $
 *
 * @author Marko Djukic <marko@oblo.com>
 * @package Net_SMS
 */
class Net_SMS_win_http extends Net_SMS {

    var $_base_url = 'gateway3.go2mobile.net:10030/gateway/v3/gateway.aspx';

    /**
     * An array of capabilities, so that the driver can report which operations
     * it supports and which it doesn't. Possible values are:<pre>
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
                              'credit'      => false,
                              'addressbook' => false,
                              'lists'       => false);

    /**
     * This function does the actual sending of the message.
     *
     * @access private
     *
     * @param array $message  The array containing the message and its send
     *                        parameters.
     * @param array $to       The destination string.
     *
     * @return array  An array with the success status and additional
     *                information.
     */
    function _send($message, $to)
    {
        /* Start the XML. */
        $xml = '<SMSMESSAGE><TEXT>' . $message['text'] . '</TEXT>';

        /* Check if source from is set. */
        if (!empty($message['send_params']['from'])) {
            $xml .= '<SOURCE_ADDR>' . $message['send_params']['from'] . '</SOURCE_ADDR>';
        }

        /* Loop through recipients and do some minimal validity checking. */
        if (is_array($to)) {
            foreach ($to as $key => $val) {
                if (preg_match('/^.*?<?(\+?\d{7,})(>|$)/', $val, $matches)) {
                    $to[$key] = $matches[1];
                } else {
                    /* If a recipient is invalid stop all further sending. */
                    return array(0, sprintf(_("Invalid recipient: \"%s\""), $val));
                }
            }

            $to = implode('</DESTINATION_ADDR><DESTINATION_ADDR>', $to);
        } else {
            if (preg_match('/^.*?<?(\+?\d{7,})(>|$)/', $to, $matches)) {
                $to = $matches[1];
            } else {
                return array(0, sprintf(_("Invalid recipient: \"%s\""), $to));
            }
        }
        $xml .= '<DESTINATION_ADDR>' . $to . '</DESTINATION_ADDR>';

        /* TODO: Should we have something more intelligent? Could actually
         * be part of send parameters. */
        $xml .= '<TRANSACTIONID>' . time() . '</TRANSACTIONID>';

        /* TODO: Add some extra tags, just tacked on for now. */
        $xml .= '<TYPEID>2</TYPEID><SERVICEID>1</SERVICEID></SMSMESSAGE>';

        /* Send this message. */
        $response = $this->_post($xml);
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
     * Identifies this gateway driver and returns a brief description.
     *
     * @return array  Array of driver info.
     */
    function getInfo()
    {
        return array(
            'name' => _("WIN via HTTP"),
            'desc' => _("This driver allows sending of messages through the WIN (http://winplc.com) gateway, using the HTTP API"),
        );
    }

    /**
     * Returns the required parameters for this gateway driver. The settable
     * parameters for this gateway are:
     *   - user            - The username for authentication on the gateway;
     *   - password        - The password for authentication on the gateway;
     *
     * @return array  Array of required parameters.
     */
    function getParams()
    {
        $params = array();
        $params['user']     = array('label' => _("Username"), 'type' => 'text');
        $params['password'] = array('label' => _("Password"), 'type' => 'text');

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

        $params['cost_id'] = array(
            'label' => _("Cost ID"),
            'type' => 'int');

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

        if (empty($params['cost_id'])) {
            $params['deliv_time'] = array(
                'label' => _("Cost ID"),
                'type' => 'int');
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
     * @param string $xml  The XML information passed to the gateway.
     *
     * @return mixed  The response on success or PEAR Error on failure.
     */
    function _post($xml)
    {
        $options['method'] = 'POST';
        $options['timeout'] = 5;
        $options['allowRedirects'] = true;

        /* Wrap the xml with the standard tags. */
        $xml = '<?xml version="1.0" standalone="no"?><!DOCTYPE WIN_DELIVERY_2_SMS SYSTEM "winbound_messages_v1.dtd"><WIN_DELIVERY_2_SMS>' . $xml . '</WIN_DELIVERY_2_SMS>';

        $http = new HTTP_Request($this->_base_url, $options);

        /* Add the authentication values to POST. */
        $http->addPostData('User', $this->_params['user']);
        $http->addPostData('Password', $this->_params['password']);

        /* Add the XML and send the request. */
        $http->addPostData('WIN_XML', $xml);
        @$http->sendRequest();
        if ($http->getResponseCode() != 200) {
            return PEAR::raiseError(sprintf(_("Could not open %s."), $this->_base_url));
        }

        return $http->getResponseBody();
    }

}
