<?php
/**
 * The Horde_Cipher:: class provides a common abstracted interface to
 * various Ciphers for encryption of arbitrary length pieces of data.
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * $Horde: framework/Cipher/Cipher.php,v 1.16.12.13 2009-03-04 20:34:27 slusarz Exp $
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @since   Horde 2.2
 * @package Horde_Cipher
 */
class Horde_Cipher {

    /**
     * The block mode for the cipher chaining
     *
     * @var string
     */
    var $_blockMode = 'cbc';

    /**
     * The initialization vector
     *
     * @var string
     */
    var $_iv = null;

    /**
     * Set the block mode for cipher chaining.
     *
     * @param string $blockMode  The new blockmode.
     */
    function setBlockMode($blockMode)
    {
        $this->_blockMode = $blockMode;
    }

    /**
     * Set the IV.
     *
     * @param string $iv  The new IV.
     */
    function setIV($iv)
    {
        $this->_iv = $iv;
    }

    /**
     * Encrypt a string.
     *
     * @param string $plaintext  The data to encrypt.
     *
     * @return string  The encrypted data.
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
     * Decrypt a string.
     *
     * @param string $ciphertext  The data to decrypt.
     *
     * @return string  The decrypted data.
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
     * Attempts to return a concrete Horde_Cipher instance.
     *
     * @param string $cipher  The type of concrete Horde_Cipher subclass to
     *                        return.
     * @param array $params   A hash containing any additional parameters a
     *                        subclass might need.
     *
     * @return Horde_Cipher  The newly created concrete Horde_Cipher instance,
     *                       or PEAR_Error on error.
     */
    function &factory($cipher, $params = null)
    {
        $driver = basename($cipher);
        $class = 'Horde_Cipher_' . $driver;
        if (!class_exists($class)) {
            include_once 'Horde/Cipher/' . $cipher . '.php';
        }

        if (class_exists($class)) {
            $cipher = new $class($params);
        } else {
            $cipher = PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }

        return $cipher;
    }

}
