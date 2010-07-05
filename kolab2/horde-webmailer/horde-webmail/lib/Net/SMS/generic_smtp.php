<?php
/**
 * Generic e-mail based SMS driver
 *
 * Copyright 2005-2007 WebSprockets, LLC
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * This driver interfaces with the email-to-sms gateways provided by many
 * carriers, particularly those based in the U.S.
 *
 * $Horde: framework/Net_SMS/SMS/generic_smtp.php,v 1.8.2.9 2008-05-14 21:39:40 jan Exp $
 *
 * @category   Networking
 * @package    Net_SMS
 * @author     Ian Eure <ieure@php.net>
 * @since      Horde 3.1
 * @since      Net_SMS 0.0.2
 */
class Net_SMS_generic_smtp extends Net_SMS {

    /**
     * Capabilities of this driver.
     *
     * @var array
     */
    var $capabilities = array(
        'auth'        => false,
        'batch'       => false,
        'multi'       => false,
        'receive'     => false,
        'credit'      => false,
        'addressbook' => false,
        'lists'       => false
    );

    /**
     * Driver parameters.
     *
     * @var array
     *
     * @access private
     */
    var $_params = array(
        'carrier'     => null,
        'mailBackend' => 'mail',
        'mailParams'  => array(),
        'mailHeaders' => array()
    );

    /**
     * Carrier email map.
     *
     * @var array
     *
     * @access private
     */
    var $_carriers = array(
        /* U.S. carriers. */
        'att'          => '%s@mmode.com',
        'cingular'     => '%s@mmode.com',
        'verizon'      => '%s@vtext.com',
        'boost'        => '%s@myboostmobile.com',
        'cellularone'  => '%s@mycellone.net',
        'cincybell'    => '%s@gocbw.com',
        'sprint'       => '%s@messaging.sprintpcs.com',
        'tmobile_us'   => '%s@tmomail.com',
        'suncom'       => '%s@tms.suncom.com',
        'aircel'       => '%s@airsms.com',
        'airtel'       => '%s@airtelmail.com',
        'bplmobile'    => '%s@bplmobile.com',
        'bellmobility' => '%s@txt.bellmobility.ca',
        'bluegrass'    => '%s@sms.bluecell.com',
        'cellforce'    => '%s@celforce.com',
        'cellularone'  => '%s@mycellone.net',
        /* German carriers. */
        'eplus'       => '%s@smsmail.eplus.de',
        'tmobile_de'  => '%s@t-mobile-sms.de',
        'vodafone_de' => '%s@vodafone-sms.de',
    );

    /**
     * Identifies this driver.
     *
     * @return array  Driver info.
     */
    function getInfo()
    {
        return array(
            'name' => _("Email-to-SMS Gateway"),
            'desc' => _("This driver allows sending of messages through an email-to-SMS gateway, for carriers which provide this service.")
        );
    }

    /**
     * Returns required parameters.
     *
     * @return array  Array of required parameters.
     */
    function getParams()
    {
        return array(
            'carrier'     => array('label' => _("Carrier"), 'type' => 'text'),
            'mailBackend' => array('label' => _("PEAR::Mail backend"), 'type' => 'text')
        );
    }

    /**
     * Sends the message.
     *
     * You may also specify the carrier with the 'carrier' key of the message
     * to avoid creating a new instance for each carrier, or fiddling with the
     * parameters.
     *
     * @access private
     *
     * @param array $message  Message to send.
     * @param string $to      The recipient.
     *
     * @return array  An array with the success status and additional
     *                information.
     */
    function _send($message, $to)
    {
        require_once 'Mail.php';
        $m = &Mail::factory($this->_params['mailBackend'],
                            $this->_params['mailParams']);

        if (isset($message['carrier'])) {
            $dest = $this->_getDest($to, $message['carrier']);
        } else {
            $dest = $this->_getDest($to);
        }

        $res = $m->send($dest, $this->_params['mailHeaders'], $message['text']);
        if (PEAR::isError($res)) {
            return array(0, $res->getMessage());
        } else {
            return array(1, null);
        }
    }

    /**
     * Returns destination e-mail address.
     *
     * @param string $phone  Phone number to send to.
     *
     * @return string  Destination address.
     */
    function _getDest($phone, $carrier = null)
    {
        $carrier = is_null($carrier) ? $this->_params['carrier'] : $carrier;
        return sprintf($this->_carriers[$carrier],
                       preg_replace('/[^0-9]/', '', $phone));
    }

    /**
     * Returns the address template for a carrier.
     *
     * @param string $carrier  Carrier name.
     *
     * @return mixed  Address template or false.
     */
    function getAddressTemplate($carrier)
    {
        if (!isset($this->_carriers[$carrier])) {
            return false;
        }
        return $this->_carriers[$carrier];
    }

    /**
     * Adds a carrier to the list.
     *
     * Address templates need to be in the form of an email address, with a
     * '%s' representing the place where the destination phone number goes.
     *
     * @param string $name  Carrier name.
     * @param string $addr  Address template.
     */
    function addCarrier($name, $addr)
    {
        $this->_carriers[$name] = $addr;
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
