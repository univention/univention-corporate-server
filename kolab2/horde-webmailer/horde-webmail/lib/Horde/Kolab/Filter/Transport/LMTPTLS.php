<?php
/**
 * $Horde: framework/Kolab_Filter/lib/Horde/Kolab/Filter/Transport/LMTPTLS.php,v 1.3.2.1 2009-02-20 22:37:15 wrobel Exp $
 *
 * @package Kolab_Filter
 */

/* Require the base class */
require_once 'Net/LMTP.php';

/**
 * Extended LMTP class with support for TLS.
 *
 * Copyright 2008-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @package Kolab_Filter
 */
class Net_LMTP_TLS extends Net_LMTP {

    /**
     * Attempt to do LMTP authentication.
     *
     * @param string The userid to authenticate as.
     * @param string The password to authenticate with.
     * @param string The requested authentication method.  If none is
     *               specified, the best supported method will be used.
     *
     * @return mixed Returns a PEAR_Error with an error message on any
     *               kind of failure, or true on success.
     * @access public
     */
    function auth($uid, $pwd , $method = '')
    {
        if (version_compare(PHP_VERSION, '5.1.0', '>=')) {
            if (!isset($this->_esmtp['STARTTLS'])) {
                return PEAR::raiseError('LMTP server does not support authentication');
            }
            if (PEAR::isError($result = $this->_put('STARTTLS'))) {
                return $result;
            }
            if (PEAR::isError($result = $this->_parseResponse(220))) {
                return $result;
            }
            if (PEAR::isError($result = $this->_socket->enableCrypto(true, STREAM_CRYPTO_METHOD_TLS_CLIENT))) {
                return $result;
            }
            elseif ($result !== true) {
                return PEAR::raiseError('STARTTLS failed');
            }

            /* Send LHLO again to recieve the AUTH string from the
             * LMTP server. */
            $this->_negotiate();
            if (empty($this->_esmtp['AUTH'])) {
                return PEAR::raiseError('LMTP server does not support authentication');
            }
        }

        /*
         * If no method has been specified, get the name of the best supported
         * method advertised by the LMTP server.
         */
        if (empty($method) || $method === true ) {
            if (PEAR::isError($method = $this->_getBestAuthMethod())) {
                /* Return the PEAR_Error object from _getBestAuthMethod(). */
                return $method;
            } 
        } else {
            $method = strtoupper($method);
        }

        switch ($method) {
            case 'DIGEST-MD5':
                $result = $this->_authDigest_MD5($uid, $pwd);
                break;
            case 'CRAM-MD5':
                $result = $this->_authCRAM_MD5($uid, $pwd);
                break;
            case 'LOGIN':
                $result = $this->_authLogin($uid, $pwd);
                break;
            case 'PLAIN':
                $result = $this->_authPlain($uid, $pwd);
                break;
            default : 
                $result = new PEAR_Error("$method is not a supported authentication method");
                break;
        }

        /* If an error was encountered, return the PEAR_Error object. */
        if (PEAR::isError($result)) {
            return $result;
        }

        /* RFC-2554 requires us to re-negotiate ESMTP after an AUTH. */
        if (PEAR::isError($error = $this->_negotiate())) {
            return $error;
        }

        return true;
    }
}
