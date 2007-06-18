<?php
/**
 * The Secret:: class provides an API for encrypting and decrypting
 * small pieces of data with the use of a shared key.
 *
 * The Secret:: functions use the Horde Cipher:: class if mcrypt is not
 * available.
 *
 * $Horde: framework/Secret/Secret.php,v 1.40 2004/04/07 14:43:12 chuck Exp $
 *
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_Secret
 */
class Secret {

    /**
     * Take a small piece of data and encrypt it with a key.
     *
     * @access public
     *
     * @param string $key      The key to use for encryption.
     * @param string $message  The plaintext message.
     *
     * @return string  The ciphertext message.
     */
    function write($key, $message)
    {
        if (Util::extensionExists('mcrypt')) {
            $td = @mcrypt_module_open(MCRYPT_GOST, '', MCRYPT_MODE_ECB, '');
            if ($td) {
                $iv = mcrypt_create_iv(mcrypt_enc_get_iv_size($td), MCRYPT_RAND);
                @mcrypt_generic_init($td, $key, $iv);
                $encrypted_data = mcrypt_generic($td, $message);
                mcrypt_generic_deinit($td);

                return $encrypted_data;
            }
        }

        static $cipherCache;
        $cacheIdx = md5($key);

        if (!is_array($cipherCache) || !isset($cipherCache[$cacheIdx])) {
            require_once 'Horde/Cipher.php';

            $cipherCache[$cacheIdx] = &Horde_Cipher::factory('blowfish');
            $cipherCache[$cacheIdx]->setBlockMode('ofb64');
            $cipherCache[$cacheIdx]->setKey($key);
        }

        return $cipherCache[$cacheIdx]->encrypt($message);
    }

    /**
     * Decrypt a message encrypted with Secret::write().
     *
     * @access public
     *
     * @param string $key      The key to use for decryption.
     * @param string $message  The ciphertext message.
     *
     * @return string  The plaintext message.
     */
    function read($key, $ciphertext)
    {
        if (Util::extensionExists('mcrypt')) {
            $td = @mcrypt_module_open(MCRYPT_GOST, '', MCRYPT_MODE_ECB, '');
            if ($td) {
                $iv = mcrypt_create_iv(mcrypt_enc_get_iv_size($td), MCRYPT_RAND);
                @mcrypt_generic_init($td, $key, $iv);
                $decrypted_data = mdecrypt_generic($td, $ciphertext);
                mcrypt_generic_deinit($td);

                // Strip padding characters.
                return rtrim($decrypted_data, "\0");
            }
        }

        static $cipherCache;
        $cacheIdx = md5($key);

        if (!is_array($cipherCache) || !isset($cipherCache[$cacheIdx])) {
            require_once 'Horde/Cipher.php';

            $cipherCache[$cacheIdx] = &Horde_Cipher::factory('blowfish');
            $cipherCache[$cacheIdx]->setBlockMode('ofb64');
            $cipherCache[$cacheIdx]->setKey($key);
        }

        return $cipherCache[$cacheIdx]->decrypt($ciphertext);
    }

    /**
     * Generate a secret key (for encryption), either using a random
     * md5 string and storing it in a cookie if the user has cookies
     * enabled, or munging some known values if they don't.
     *
     * @access public
     *
     * @param optional string $keyname  The name of the key to set.
     *
     * @return string  The secret key that has been generated.
     */
    function setKey($keyname = 'generic')
    {
        global $conf;

        if (isset($_COOKIE) &&
            array_key_exists($conf['session']['name'], $_COOKIE)) {
            if (array_key_exists($keyname . '_key', $_COOKIE)) {
                $key = $_COOKIE[$keyname . '_key'];
            } else {
                $key = md5(mt_rand());
                $_COOKIE[$keyname . '_key'] = $key;
                setcookie($keyname . '_key', $key, null, $conf['cookie']['path'], $conf['cookie']['domain'], $conf['use_ssl'] == 1 ? 1 : 0);
            }
        } else {
            $key = md5(session_id() . $conf['server']['name']);
        }

        return $key;
    }

    /**
     * Return a secret key, either from a cookie, or if the cookie
     * isn't there, assume we are using a munged version of a known
     * base value.
     *
     * @access public
     *
     * @param optional string $keyname  The name of the key to get.
     *
     * @return string  The secret key.
     */
    function getKey($keyname = 'generic')
    {
        static $keycache;

        if (is_null($keycache)) {
            $keycache = array();
        }

        if (!array_key_exists($keyname, $keycache)) {
            if (array_key_exists($keyname . '_key', $_COOKIE)) {
                $keycache[$keyname] = $_COOKIE[$keyname . '_key'];
            } else {
                global $conf;
                $keycache[$keyname] = md5(session_id() . $conf['server']['name']);
                $_COOKIE[$keyname . '_key'] = $keycache[$keyname];
            }
        }

        return $keycache[$keyname];
    }

}
