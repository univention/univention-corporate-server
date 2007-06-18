<?php
/**
 * The Horde_Cipher_BlockMode:: class provides a common abstracted
 * interface to various block mode handlers for cyphers.
 *
 * $Horde: framework/Cipher/Cipher/BlockMode.php,v 1.14 2004/01/01 15:14:09 jan Exp $
 *
 * Copyright 2002-2004 Mike Cochrane <mike@graftonhall.co.nz>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.2
 * @package Horde_Cipher
 */
class Horde_Cipher_BlockMode {

    /* String containing the initilization vector. */
    var $_iv = "\0\0\0\0\0\0\0\0";

    /**
     * Attempts to return a concrete CipherBlockMode instance based on $mode.
     *
     * @access public
     *
     * @param mixed $cipher           The type of concrete CipherBlockMode
     *                                subclass to return.
     * @param optional array $params  A hash containing any additional
     *                                parameters a subclass might need.
     *
     * @return object CipherBlockMode The newly created concrete Cipher
     *                                instance, or PEAR_Error on an error.
     */
    function &factory($mode, $params = null)
    {
        $mode = basename($mode);
        if (@file_exists(dirname(__FILE__) . '/BlockMode/' . $mode . '.php')) {
            require_once dirname(__FILE__) . '/BlockMode/' . $mode . '.php';
        }

        $class = 'Horde_Cipher_BlockMode_' . $mode;
        if (class_exists($class)) {
            return $ret = &new $class($params);
        } else {
            return PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }
    }

    /**
     * Set the iv
     *
     * @param String $iv    The new iv.
     */
    function setIV($iv)
    {
        $this->_iv = $iv;
    }

}
