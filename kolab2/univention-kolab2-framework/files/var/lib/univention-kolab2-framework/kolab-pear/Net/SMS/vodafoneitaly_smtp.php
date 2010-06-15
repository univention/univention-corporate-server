<?php
/**
 * Net_SMS_vodafoneitaly_smtp Class implements the SMTP API for accessing
 * the Vodafone Italy SMS gateway. Use of this gateway requires an email account
 * with Vodafone Italy (www.190.it).
 *
 * Copyright 2003-2004 Marko Djukic <marko@oblo.com>
 * Copyright 2003-2004 Matteo Zambelli <mmzambe@hotmail.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you did not
 * receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * $Horde: framework/Net_SMS/SMS/vodafoneitaly_smtp.php,v 1.11 2004/04/28 23:38:29 mdjukic Exp $
 *
 * @author Marko Djukic <marko@oblo.com>
 * @author Matteo Zambelli <mmzambe@hotmail.com>
 * @version $Revision: 1.1.2.1 $
 * @package Net_SMS
 */
class Net_SMS_vodafoneitaly_smtp extends Net_SMS {

    /**
     * An array of capabilities, so that the driver can report which operations
     * it supports and which it doesn't. Possible values are:
     *   auth        - The gateway require authentication before sending;
     *   batch       - Batch sending is supported;
     *   multi       - Sending of messages to multiple recipients is supported;
     *   receive     - Whether this driver is capable of receiving SMS;
     *   credit      - Is use of the gateway based on credits;
     *   addressbook - Are gateway addressbooks supported;
     *   lists       - Gateway support for distribution lists.
     *
     * @var array $capabilities
     */
    var $capabilities = array('auth'        => false,
                              'batch'       => false,
                              'multi'       => false,
                              'receive'     => false,
                              'credit'      => false,
                              'addressbook' => false,
                              'lists'       => false);

    /**
     * This function does the actual sending of the message.
     *
     * @access private
     *
     * @param array  $message  The array containing the message and its send
     *                         parameters.
     * @param string $to       The destination string.
     *
     * @return mixed  True on success or PEAR Error on failure.
     */
    function _send(&$message, $to)
    {
        if (!@include_once 'Mail.php') {
            return PEAR::raiseError(_("Missing required PEAR package Mail."));
        }
        $mailer = &Mail::factory('mail');

        /* Since this only works for Italian numbers, this is hardcoded. */
        if (preg_match('/^.*?<?(\+?39)?(\d{10})>?/', $to, $matches)) {
            $headers['From'] = $this->_params['user'];
            $to = $matches[2] . '@sms.vodafone.it';
            $result = $mailer->send($to, $headers, $message['text']);
            return $result;
        } else {
            return false;
        }
    }

    /**
     * Identifies this gateway driver and returns a brief description.
     *
     * @access public
     *
     * @return array  Array of driver info.
     */
    function getInfo()
    {
        $info['name'] = _("Vodafone Italy via SMTP");
        $info['desc'] = _("This driver allows sending of messages via SMTP through the Vodafone Italy gateway, only to Vodafone numbers. It requires an email account with Vodafone Italy (http://www.190.it).");

        return $info;
    }

    /**
     * Returns the required parameters for this gateway driver.
     *
     * @access public
     *
     * @return array  Array of required parameters.
     */
    function getParams()
    {
        $params = array();
        $params['user']       = array('label'  => _("Username"),
                                      'type'   => 'text');

        return $params;
    }

    /**
     * Returns the parameters that can be set as default for sending messages
     * using this gateway driver and displayed when sending messages.
     *
     * @access public
     *
     * @return array  Array of parameters that can be set as default.
     */
    function getDefaultSendParams()
    {
        return array();
    }

    /**
     * Returns the parameters for sending messages using this gateway driver,
     * displayed when sending messages. These are filtered out using the
     * default values set up when creating the gateway.
     *
     * @access public
     *
     * @return array  Array of required parameters.
     * @todo  Would be nice to use a time/date setup rather than minutes from
     *        now for the delivery time. Upload field for ringtones/logos?
     */
    function getSendParams($params)
    {
        return array();
    }

    /**
     * Returns a string representation of an error code.
     *
     * @access public
     *
     * @param int $error             The error code to look up.
     * @param optional string $text  An existing error text to use to raise a
     *                               PEAR Error.
     *
     * @return mixed  A textual message corrisponding to the error code or a
     *                PEAR Error if passed an existing error text.
     *
     * @todo  Check which of these are actually required and trim down the list.
     */
    function getError($error, $error_text = '')
    {
    }

}
