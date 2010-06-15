<?php
/**
 * The Horde_Cipher:: class provides a common abstracted interface to
 * various Ciphers for encryption of arbitrary length pieces of data.
 *
 * Copyright 2002-2004 Mike Cochrane <mike@graftonhall.co.nz>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * $Horde: framework/Cipher/Cipher.php,v 1.16 2004/01/01 15:14:08 jan Exp $
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.2
 * @package Horde_Cipher
 */
class Horde_Cipher {

    /**
     * The block mode for the cipher chaining
     * @var string $_blockMode
     */
    var $_blockMode = 'CBC';

    /**
     * The initialization vector
     * @var string $_iv
     */
    var $_iv = null;

    /**
     * Set the block mode for cipher chaining
     *
     * @param String $blockMode The new blockmode
     */
    function setBlockMode($blockMode)
    {
        $this->_blockMode = $blockMode;
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

    /**
     * Encrypt a string
     *
     * @param String $plaintext     The data to encrypt
     *
     * @return String       The encrypted data
     */
    function encrypt($plaintext)
    {
        require_once dirname(__FILE__) . '/Cipher/BlockMode.php';
        $blockMode = &Horde_Cipher_BlockMode::factory($this->_blockMode);
        if (!is_null($this->_iv)) {
            $blockMode->setIV($this->_iv);
        }

        return $blockMode->encrypt($this, $plaintext);
    }

    /**
     * Decrypt a string
     *
     * @param String $ciphertext     The data to decrypt
     *
     * @return String       The decrypted data
     */
    function decrypt($ciphertext)
    {
        require_once dirname(__FILE__) . '/Cipher/BlockMode.php';
        $blockMode = &Horde_Cipher_BlockMode::factory($this->_blockMode);
        if (!is_null($this->_iv)) {
            $blockMode->setIV($this->_iv);
        }

        return $blockMode->decrypt($this, $ciphertext);
    }

    /**
     * Attempts to return a concrete Cipher instance based on $driver.
     *
     * @access public
     *
     * @param mixed $cipher           The type of concrete Cipher subclass to
     *                                return.
     * @param optional array $params  A hash containing any additional
     *                                parameters a subclass might need.
     *
     * @return object Cipher   The newly created concrete Cipher instance, or PEAR_Error
     *                         on an error.
     */
    function &factory($cipher, $params = null)
    {
        $driver = basename($cipher);

        if (@file_exists(dirname(__FILE__) . '/Cipher/' . $cipher . '.php')) {
            require_once dirname(__FILE__) . '/Cipher/' . $cipher . '.php';
        }

        $class = 'Horde_Cipher_' . $cipher;
        if (class_exists($class)) {
            return $ret = &new $class($params);
        } else {
            return PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }
    }

}
