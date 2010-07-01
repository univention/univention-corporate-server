<?php

include_once 'Net/SMPP/Client.php';

/**
 * SMPP based SMS driver.
 *
 * This driver interfaces with the email-to-sms gateways provided by many
 * carriers, particularly those based in the U.S.
 *
 * $Horde: framework/Net_SMS/SMS/generic_smpp.php,v 1.2.2.1 2007-12-20 13:49:23 jan Exp $
 *
 * Copyright 2005-2007 WebSprockets, LLC
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @category   Networking
 * @package    Net_SMS
 * @author     Ian Eure <ieure@php.net>
 * @link       http://pear.php.net/package/Net_SMS
 * @since      Net_SMS 0.2.0
 * @since      Horde 3.2
 */
class Net_SMS_generic_smpp extends Net_SMS {

    /**
     * Capabilities of this driver
     *
     * @var  array
     */
    var $capabilities = array(
        'auth'        => true,
        'batch'       => false,
        'multi'       => false,
        'receive'     => false,
        'credit'      => false,
        'addressbook' => false,
        'lists'       => false
    );

    /**
     * Driver parameters
     *
     * @var     array
     * @access  private
     */
    var $_params = array(
        'host'         => null,
        'port'         => 0,
        'vendor'       => null,
        'bindParams'   => array(),
        'submitParams' => array()
    );

    /**
     * Net_SMPP_Client instance
     *
     * @var     Net_SMPP_Client
     * @access  private
     */
    var $_client = null;

    /**
     * Constructor.
     *
     * @param array $params  Parameters.
     */
    function Net_SMS_generic_smpp($params = null)
    {
        parent::Net_SMS($params);
        $this->_client =& new Net_SMPP_Client($this->_params['host'], $this->_params['port']);
        if (!is_null($this->_params['vendor'])) {
            Net_SMPP::setVendor($this->_params['vendor']);
        }
    }

    /**
     * Identifies this driver.
     *
     * @return array  Driver info.
     */
    function getInfo()
    {
        return array(
            'name' => _("SMPP Gateway"),
            'desc' => _("This driver allows sending of messages through an SMPP gateway.")
        );
    }

    /**
     * Get required paramaters
     *
     * @return array  Array of required parameters.
     */
    function getParams()
    {
        return array(
            'host' => array(
                'label' => _("Host"), 'type' => 'text'),
            'port' => array(
                'label' => _("Port"), 'type' => 'int'),
//             'bindParams' => array(
//                 'label' => _('bind_transmitter paramaters'), 'type' => 'array'),
//             'submitParams' => array(
//                 'label' => _('submit_sm parameters'), 'type' => 'array'
//             )
        );
    }

    /**
     * Sends the message.
     *
     * @access  private
     *
     * @param array $message  Message to send.
     * @param string $to      The recipient.
     *
     * @return array  An array with the success status and additional
     *                information.
     */
    function _send($message, $to)
    {
        $pdu =& Net_SMPP::PDU('submit_sm', $this->_params['submitParams']);
        $pdu->destination_addr = $to;
        $pdu->short_message = $message['text'];
        if (count($message) > 1) {
            // Other params to set
            $v = $message;
            unset($v['text']);
            $pdu->set($v);
            unset($v);
        }

        $res =& $this->_client->sendPDU($pdu);

        // Error sending?
        if ($res === false) {
            return array(0, _("Error sending PDU"));
        }

        $resp =& $this->_client->readPDU();
        if ($resp === false) {
            return array(0, _("Could not read response PDU"));
        }
        if ($resp->isError()) {
            return array(0, sprintf(_("Sending failed: %s") . $resp->statusDesc()));
        }

        // Success!
        return array(1, $resp->message_id);
    }

    /**
     * Authenticates with the SMSC.
     *
     * This method connects to the SMSC (if not already connected) and
     * authenticates with the bind_transmitter command (if not already bound).
     *
     * @access  protected
     */
    function _authenticate()
    {
        if ($this->_client->state == NET_SMPP_CLIENT_STATE_CLOSED) {
            $res = $this->_client->connect();
            if ($res === false) {
                return false;
            }
        }

        if ($this->_client->state == NET_SMPP_CLIENT_STATE_OPEN) {
            $resp =& $this->_client->bind($this->_params['bindParams']);
            if ($resp === false || (is_object($resp) && $resp->isError())) {
                return false;
            }
        }

        return true;
    }

    /**
     * Accepts an object.
     *
     * @see Net_SMPP_Client::accept()
     *
     * @return mixed  {@link Net_SMPP_Client::accept()}'s return value
     */
    function accept(&$obj)
    {
        return $this->_client->accept($obj);
    }

    /**
     * Returns a list of parameters specific for this driver.
     *
     * @return array Default sending parameters.
     */
    function getDefaultSendParams()
    {
        return array();
    }

}