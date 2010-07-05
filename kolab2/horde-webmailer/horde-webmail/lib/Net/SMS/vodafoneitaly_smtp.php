<?php
/**
 * Net_SMS_vodafoneitaly_smtp Class implements the SMTP API for accessing the
 * Vodafone Italy SMS gateway. Use of this gateway requires an email account
 * with Vodafone Italy (www.190.it).
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 * Copyright 2003-2007 Matteo Zambelli <mmzambe@hotmail.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * $Horde: framework/Net_SMS/SMS/vodafoneitaly_smtp.php,v 1.11.10.13 2009-01-06 15:23:28 jan Exp $
 *
 * @author Marko Djukic <marko@oblo.com>
 * @author Matteo Zambelli <mmzambe@hotmail.com>
 * @package Net_SMS
 */
class Net_SMS_vodafoneitaly_smtp extends Net_SMS {

    /**
     * An array of capabilities, so that the driver can report which operations
     * it supports and which it doesn't. Possible values are:<pre>
     *   auth        - The gateway require authentication before sending;
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
     * @param array $message  The array containing the message and its send
     *                        parameters.
     * @param string $to      The recipient.
     *
     * @return array  An array with the success status and additional
     *                information.
     */
    function _send($message, $to)
    {
        /* Since this only works for Italian numbers, this is hardcoded. */
        if (preg_match('/^.*?<?(\+?39)?(\d{10})>?/', $to, $matches)) {
            $headers['From'] = $this->_params['user'];
            $to = $matches[2] . '@sms.vodafone.it';

            $mailer = Mail::factory('mail');
            $result = $mailer->send($to, $headers, $message['text']);
            if (is_a($result, 'PEAR_Error')) {
                return array(0, $result->getMessage());
            } else {
                return array(1, null);
            }
        } else {
            return array(0, _("You need to provide an Italian phone number"));
        }
    }

    /**
     * Identifies this gateway driver and returns a brief description.
     *
     * @return array  Array of driver info.
     */
    function getInfo()
    {
        return array(
            'name' => _("Vodafone Italy via SMTP"),
            'desc' => _("This driver allows sending of messages via SMTP through the Vodafone Italy gateway, only to Vodafone numbers. It requires an email account with Vodafone Italy (http://www.190.it)."),
        );
    }

    /**
     * Returns the required parameters for this gateway driver.
     *
     * @return array  Array of required parameters.
     */
    function getParams()
    {
        return array('user' => array('label' => _("Username"),
                                     'type' => 'text'));
    }

    /**
     * Returns the parameters that can be set as default for sending messages
     * using this gateway driver and displayed when sending messages.
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
    }

}
