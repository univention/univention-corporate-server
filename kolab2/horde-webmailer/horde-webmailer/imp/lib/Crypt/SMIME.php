<?php

require_once 'Horde/Crypt/smime.php';

/**
 * Name of the S/MIME public key field in addressbook.
 */
define('IMP_SMIME_PUBKEY_FIELD', 'smimePublicKey');

/**
 * The IMP_SMIME:: class contains all functions related to handling
 * S/MIME messages within IMP.
 *
 * $Horde: imp/lib/Crypt/SMIME.php,v 1.45.2.25 2009-10-09 13:02:34 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @package IMP
 */
class IMP_SMIME extends Horde_Crypt_smime {

    /**
     * The list of available sources to search for keys.
     *
     * @var array
     */
    var $_sources = null;

    /**
     * Constructor.
     */
    function IMP_SMIME()
    {
        parent::Horde_Crypt_smime(array('temp' => Horde::getTempDir()));
    }

    /**
     * Add the personal public key to the prefs.
     *
     * @param mixed $key  The public key to add (either string or array).
     */
    function addPersonalPublicKey($key)
    {
        $GLOBALS['prefs']->setValue('smime_public_key', (is_array($key)) ? implode('', $key) : $key);
    }

    /**
     * Add the personal private key to the prefs.
     *
     * @param mixed $key  The private key to add (either string or array).
     */
    function addPersonalPrivateKey($key)
    {
        $GLOBALS['prefs']->setValue('smime_private_key', (is_array($key)) ? implode('', $key) : $key);
    }

    /**
     * Add the list of additional certs to the prefs.
     *
     * @param mixed $key  The private key to add (either string or array).
     */
    function addAdditionalCert($key)
    {
        $GLOBALS['prefs']->setValue('smime_additional_cert', (is_array($key)) ? implode('', $key) : $key);
    }

    /**
     * Get the personal public key from the prefs.
     *
     * @return string  The personal S/MIME public key.
     */
    function getPersonalPublicKey()
    {
        return $GLOBALS['prefs']->getValue('smime_public_key');
    }

    /**
     * Get the personal private key from the prefs.
     *
     * @return string  The personal S/MIME private key.
     */
    function getPersonalPrivateKey()
    {
        return $GLOBALS['prefs']->getValue('smime_private_key');
    }

    /**
     * Get any additional certificates from the prefs.
     *
     * @return string  Additional signing certs for inclusion.
     */
    function getAdditionalCert()
    {
        return $GLOBALS['prefs']->getValue('smime_additional_cert');
    }

    /**
     * Deletes the specified personal keys from the prefs.
     */
    function deletePersonalKeys()
    {
        $GLOBALS['prefs']->setValue('smime_public_key', '');
        $GLOBALS['prefs']->setValue('smime_private_key', '');
        $GLOBALS['prefs']->setValue('smime_additional_cert', '');
        $this->unsetPassphrase();
    }

    /**
     * Add a public key to an address book.
     *
     * @param string $cert  A public certificate to add.
     *
     * @return boolean  True on successful add.
     *                  Returns PEAR_Error or error.
     */
    function addPublicKey($cert)
    {
        /* Make sure the certificate is valid. */
        $key_info = openssl_x509_parse($cert);
        if (!is_array($key_info) || !isset($key_info['subject'])) {
            return PEAR::raiseError(_("Not a valid public key."), 'horde.error');
        }

        /* Add key to the user's address book. */
        $email = $this->getEmailFromKey($cert);
        if ($email === null) {
            return PEAR::raiseError(_("No email information located in the public key."), 'horde.error');
        }

        /* Get the name corresponding to this key. */
        if (isset($key_info['subject']['CN'])) {
            $name = $key_info['subject']['CN'];
        } elseif (isset($key_info['subject']['OU'])) {
            $name = $key_info['subject']['OU'];
        } else {
            return PEAR::raiseError(_("Not a valid public key."), 'horde.error');
        }

        $res = $GLOBALS['registry']->call('contacts/addField', array($email, $name, IMP_SMIME_PUBKEY_FIELD, $cert, $GLOBALS['prefs']->getValue('add_source')));
        if (is_a($res, 'PEAR_Error')) {
            return $res;
        }

        return $key_info;
    }

    /**
     * Returns the params needed to encrypt a message being sent to the
     * specified email address.
     *
     * @param string $address  The e-mail address of the recipient.
     *
     * @return array  The list of parameters needed by encrypt().
     *                Returns PEAR_Error object on error.
     */
    function _encryptParameters($address)
    {
        /* We can only encrypt if we are sending to a single person. */
        $addrOb = IMP::bareAddress($address, true);
        $key_addr = array_pop($addrOb);

        $public_key = $this->getPublicKey($key_addr);
        if (is_a($public_key, 'PEAR_Error')) {
            return $public_key;
        }

        return array('type' => 'message', 'pubkey' => $public_key, 'email'  => $address);
    }

    /**
     * Retrieves a public key by e-mail.
     *
     * The key will be retrieved through a hook or from the user's address
     * book(s).
     *
     * @param string $address  The e-mail address to search for.
     *
     * @return string  The requested public S/MIME key or PEAR_Error on failure.
     */
    function getPublicKey($address)
    {
        $key = Horde::callHook('_imp_hook_smime_key', array($address), 'imp');
        if ($key && !is_a($key, 'PEAR_Error')) {
            return $key;
        }

        $this->_getPublicKeySources();
        $key = $GLOBALS['registry']->call('contacts/getField', array($address, IMP_SMIME_PUBKEY_FIELD, $this->_sources, false, true));

        /* See if the address points to the user's public key. */
        if (is_a($key, 'PEAR_Error')) {
            require_once 'Horde/Identity.php';
            $identity = &Identity::singleton(array('imp', 'imp'));
            $personal_pubkey = $this->getPersonalPublicKey();
            if (!empty($personal_pubkey) && $identity->hasAddress($address)) {
                return $personal_pubkey;
            }
        }

        /* If more than one public key is returned, just return the first in
         * the array. There is no way of knowing which is the "preferred" key,
         * if the keys are different. */
        if (is_array($key)) {
            return reset($key);
        }

        return $key;
    }

    /**
     * Retrieves all public keys from a user's address book(s).
     *
     * @return array  All PGP public keys available.
     *                Returns PEAR_Error object on error.
     */
    function listPublicKeys()
    {
        $this->_getPublicKeySources();
        return (empty($this->_sources)) ? array() : $GLOBALS['registry']->call('contacts/getAllAttributeValues', array(IMP_SMIME_PUBKEY_FIELD, $this->_sources));
    }

    /**
     * Deletes a public key from a user's address book(s) by e-mail.
     *
     * @param string $email  The e-mail address to delete.
     *
     * @return PEAR_Error  Returns PEAR_Error object on error.
     */
    function deletePublicKey($email)
    {
        $this->_getPublicKeySources();
        return $GLOBALS['registry']->call('contacts/deleteField', array($email, IMP_SMIME_PUBKEY_FIELD, $this->_sources));
    }

    /**
     * Obtains a list of sources for public keys.
     *
     * @access private
     */
    function _getPublicKeySources()
    {
        /* Get the listing of all sources we search for public keys. */
        if ($this->_sources === null) {
            $this->_sources = array();
            if (($sources = $GLOBALS['prefs']->getValue('search_sources'))) {
                $this->_sources = explode("\t", $sources);
                if ((count($this->_sources) == 1) && empty($this->_sources[0])) {
                    $this->_sources = array();
                }
            }
        }
    }

    /**
     * Returns the parameters needed for signing a message.
     *
     * @access private
     *
     * @return array  The list of parameters needed by encrypt().
     */
    function _signParameters()
    {
        return array(
            'type' => 'signature',
            'pubkey' => $this->getPersonalPublicKey(),
            'privkey' => $this->getPersonalPrivateKey(),
            'passphrase' => $this->getPassphrase(),
            'sigtype' => 'detach',
            'certs' => $this->getAdditionalCert()
        );
    }

    /**
     * Verifies a signed message with a given public key.
     *
     * @param string $text  The text to verify.
     *
     * @return stdClass  See Horde_Crypt_smime::verify().
     */
    function verifySignature($text)
    {
        return $this->verify($text, empty($GLOBALS['conf']['utils']['openssl_cafile']) ? array() : $GLOBALS['conf']['utils']['openssl_cafile']);
    }


    /**
     * Decrypt a message with user's public/private keypair.
     *
     * @param string $text  The text to decrypt.
     *
     * @return string  See Horde_Crypt_smime::decrypt().
     *                 Returns PEAR_Error object on error.
     */
    function decryptMessage($text)
    {
        /* decrypt() returns a PEAR_Error object on error. */
        return $this->decrypt($text, array('type' => 'message', 'pubkey' => $this->getPersonalPublicKey(), 'privkey' => $this->getPersonalPrivateKey(), 'passphrase' => $this->getPassphrase()));
    }

    /**
     * Gets the user's passphrase from the session cache.
     *
     * @return mixed  The passphrase, if set.  Returns false if the passphrase
     *                has not been loaded yet.  Returns null if no passphrase
     *                is needed.
     */
    function getPassphrase()
    {
        $private_key = $GLOBALS['prefs']->getValue('smime_private_key');
        if (empty($private_key)) {
            return false;
        }

        if (isset($_SESSION['imp']['smime']['passphrase'])) {
            return Secret::read(Secret::getKey('imp'), $_SESSION['imp']['smime']['passphrase']);
        } elseif (isset($_SESSION['imp']['smime']['null_passphrase'])) {
            return ($_SESSION['imp']['smime']['null_passphrase']) ? null : false;
        } else {
            $res = $this->verifyPassphrase($private_key, null);
            if (!isset($_SESSION['imp']['smime'])) {
                $_SESSION['imp']['smime'] = array();
            }
            $_SESSION['imp']['smime']['null_passphrase'] = ($res) ? null : false;
            return $_SESSION['imp']['smime']['null_passphrase'];
        }
    }

    /**
     * Store's the user's passphrase in the session cache.
     *
     * @param string $passphrase  The user's passphrase.
     *
     * @return boolean  Returns true if correct passphrase, false if incorrect.
     */
    function storePassphrase($passphrase)
    {
        if ($this->verifyPassphrase($this->getPersonalPrivateKey(), $passphrase) === false) {
            return false;
        }

        if (!isset($_SESSION['imp']['smime'])) {
            $_SESSION['imp']['smime'] = array();
        }
        $_SESSION['imp']['smime']['passphrase'] = Secret::write(Secret::getKey('imp'), $passphrase);

        return true;
    }

    /**
     * Clear the passphrase from the session cache.
     */
    function unsetPassphrase()
    {
        unset($_SESSION['imp']['smime']['null_passphrase']);
        unset($_SESSION['imp']['smime']['passphrase']);
    }

    /**
     * Generates the javascript code for saving public keys.
     *
     * @param MIME_Part $mime_part  The MIME_Part containing the public key.
     *
     * @return string  The URL for saving public keys.
     */
    function savePublicKeyURL($mime_part)
    {
        if (empty($cache)) {
            require_once 'Horde/SessionObjects.php';
            $cacheSess = &Horde_SessionObjects::singleton();
            $oid = $cacheSess->storeOid($mime_part);
        }

        return $this->getJSOpenWinCode('save_attachment_public_key', false, array('cert' => $oid));
    }

    /**
     * Print out the link for the javascript S/MIME popup.
     *
     * @param integer $actionid  The actionID to perform.
     * @param mixed $reload      If true, reload base window on close. If text,
     *                           run this JS on close. If false, don't do
     *                           anything on close.
     * @param array $params      Additional parameters needed for the reload
     *                           page.
     *
     * @return string  The javascript link.
     */
    function getJSOpenWinCode($actionid, $reload = true, $params = array())
    {
        $params['actionID'] = $actionid;
        if (!empty($reload)) {
            require_once 'Horde/SessionObjects.php';
            $cacheSess = &Horde_SessionObjects::singleton();

            if (is_bool($reload)) {
                $params['reload'] = $cacheSess->storeOid(html_entity_decode(Util::removeParameter(Horde::selfUrl(true), array('actionID'))), false);
            } else {
                $params['passphrase_action'] = $cacheSess->storeOid($reload, false);
            }
        }

        return IMP::popupIMPString('smime.php', $params, 450, 200);
    }

    /**
     * Encrypt a MIME_Part using S/MIME using IMP defaults.
     *
     * @param MIME_Part $mime_part  The MIME_Part object to encrypt.
     * @param mixed $to_address     The e-mail address of the key to use for
     *                              encryption.
     *
     * @return MIME_Part  See Horde_Crypt_smime::encryptMIMEPart(). Returns
     *                    PEAR_Error on error.
     */
    function IMPencryptMIMEPart($mime_part, $to_address)
    {
        $params = $this->_encryptParameters($to_address);
        if (is_a($params, 'PEAR_Error')) {
            return $params;
        }
        return $this->encryptMIMEPart($mime_part, $params);
    }

    /**
     * Sign a MIME_Part using S/MIME using IMP defaults.
     *
     * @param MIME_Part $mime_part  The MIME_Part object to sign.
     *
     * @return MIME_Part  See Horde_Crypt_smime::signMIMEPart(). Returns
     *                    PEAR_Error on error.
     */
    function IMPsignMIMEPart($mime_part)
    {
        return $this->signMIMEPart($mime_part, $this->_signParameters());
    }

    /**
     * Sign and encrypt a MIME_Part using S/MIME using IMP defaults.
     *
     * @param MIME_Part $mime_part  The MIME_Part object to sign and encrypt.
     * @param string $to_address    The e-mail address of the key to use for
     *                              encryption.
     *
     * @return MIME_Part  See Horde_Crypt_smime::signAndencryptMIMEPart().
     *                    Returns PEAR_Error on error.
     */
    function IMPsignAndEncryptMIMEPart($mime_part, $to_address)
    {
        $encrypt_params = $this->_encryptParameters($to_address);
        if (is_a($encrypt_params, 'PEAR_Error')) {
            return $encrypt_params;
        }
        return $this->signAndEncryptMIMEPart($mime_part, $this->_signParameters(), $encrypt_params);
    }

    /**
     * Store the public/private/additional certificates in the preferences
     * from a given PKCS 12 file.
     *
     * @param string $pkcs12    The PKCS 12 data.
     * @param string $password  The password of the PKCS 12 file.
     * @param string $pkpass    The password to use to encrypt the private key.
     *
     * @return boolean  True on success, PEAR_Error on error.
     */
    function addFromPKCS12($pkcs12, $password, $pkpass = null)
    {
        $openssl = IMP_SMIME::checkForOpenSSL();
        if (is_a($openssl, 'PEAR_Error')) {
            return $openssl;
        }

        $sslpath = (empty($GLOBALS['conf']['utils']['openssl_binary'])) ? null : $GLOBALS['conf']['utils']['openssl_binary'];
        $params = array('sslpath' => $sslpath, 'password' => $password);
        if (!empty($pkpass)) {
            $params['newpassword'] = $pkpass;
        }
        $res = $this->parsePKCS12Data($pkcs12, $params);
        if (is_a($res, 'PEAR_Error')) {
            return $res;
        }

        $this->addPersonalPrivateKey($res->private);
        $this->addPersonalPublicKey($res->public);
        $this->addAdditionalCert($res->certs);

        return true;
    }

    /**
     * Extract the contents from signed S/MIME data.
     *
     * @param string $data  The signed S/MIME data.
     *
     * @return string  The contents embedded in the signed data.
     *                 Returns PEAR_Error on error.
     */
    function extractSignedContents($data)
    {
        $sslpath = (empty($GLOBALS['conf']['utils']['openssl_binary'])) ? null : $GLOBALS['conf']['utils']['openssl_binary'];
        return parent::extractSignedContents($data, $sslpath);
    }

}
