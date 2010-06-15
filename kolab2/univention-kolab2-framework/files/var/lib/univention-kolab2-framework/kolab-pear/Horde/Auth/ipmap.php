<?php

require_once dirname(__FILE__) . '/ipbasic.php';

/**
 * The Auth_ipmap class provides access control based on CIDR masks.
 *
 * Parameters:
 *   NONE
 *
 * $Horde: framework/Auth/Auth/ipmap.php,v 1.13 2004/05/25 08:50:11 mdjukic Exp $
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
class Auth_ipmap extends Auth_ipbasic {

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
     * Constructs a new IP-mapping authentication object.
     *
     * @access public
     *
     * @param optional array $params  A hash containing parameters.
     */
    function Auth_ipmap($params = array())
    {
        $this->_setParams($params);
    }

    /**
     * Set parameters for the Auth_ipbasic object.
     *
     * @access private
     *
     * @param array $params  A hash containing parameter information.
     */
    function _setParams($params)
    {
    }

}
