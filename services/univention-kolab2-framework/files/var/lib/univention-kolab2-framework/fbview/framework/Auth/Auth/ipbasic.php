<?php
/**
 * The Auth_ipbasic class provides access control based on CIDR masks
 * (client IP addresses). It is not meant for user-based systems, but
 * for times when you want a block of IPs to be able to access a site,
 * and that access is simply on/off - no preferences, etc. If you need
 * more sophisticated IP-based authentication, you should look at the
 * Auth_ipmap class which lets you map IP blocks to specific
 * usernames.
 *
 * Parameters:
 *   'blocks'     An array of CIDR masks which are allowed access.
 *
 * $Horde: framework/Auth/Auth/ipbasic.php,v 1.20 2004/05/25 08:50:11 mdjukic Exp $
 *
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_Auth
 */
class Auth_ipbasic extends Auth {

    /**
     * An array of capabilities, so that the driver can report which
     * operations it supports and which it doesn't.
     *
     * @var array $capabilities
     */
    var $capabilities = array('add'           => false,
                              'update'        => false,
                              'resetpassword' => false,
                              'remove'        => false,
                              'list'          => false,
                              'transparent'   => true);

    /**
     * Constructs a new Basic IP authentication object.
     *
     * @access public
     *
     * @param optional array $params  A hash containing parameters.
     */
    function Auth_ipbasic($params = array())
    {
        $this->_setParams($params);
    }

    /**
     * Set parameters for the Auth_ipbasic object.
     *
     * @access private
     *
     * @param array $params  Should contain 'blocks', an array of CIDR masks.
     */
    function _setParams($params)
    {
        if (empty($params['blocks'])) {
            $params['blocks'] = array();
        } elseif (!is_array($params['blocks'])) {
            $params['blocks'] = array($params['blocks']);
        }

        $this->_params = $params;
    }

    /**
     * Automatic authentication: Find out if the client matches an
     * allowed IP block.
     *
     * @access public
     *
     * @return boolean  Whether or not the client is allowed.
     */
    function transparent()
    {
        if (!isset($_SERVER['REMOTE_ADDR'])) {
            $this->_setAuthError(AUTH_REASON_MESSAGE, _("IP Address not available."));
            return false;
        }

        $client = $_SERVER['REMOTE_ADDR'];
        foreach ($this->_params['blocks'] as $cidr) {
            if ($this->_addressWithinCIDR($client, $cidr)) {
                $this->setAuth($cidr, array('transparent' => 1));
                return true;
            }
        }

        $this->_setAuthError(AUTH_REASON_MESSAGE, _("IP Address not within allowed CIDR block."));
        return false;
    }

    /**
     * Determine if an IP address is within a CIDR block.
     *
     * @access private
     *
     * @param string $address  The IP address to check.
     * @param string $cidr     The block (e.g. 192.168.0.0/16) to test against.
     *
     * @return boolean  Whether or not the address matches the mask.
     */
    function _addressWithinCIDR($address, $cidr)
    {
        $address = ip2long($address);
        list($quad, $bits) = explode('/', $cidr);
        $bits = intval($bits);
        $quad = ip2long($quad);

        return (($address >> (32 - $bits)) == ($quad >> (32 - $bits)));
    }

}
