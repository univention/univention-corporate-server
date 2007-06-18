<?php

require_once 'Horde/Crypt.php';

/**
 * Horde_Crypt_smime:: provides a framework for Horde applications to
 * interact with the OpenSSL library.
 *
 * $Horde: framework/Crypt/Crypt/smime.php,v 1.36 2004/04/29 20:05:01 slusarz Exp $
 *
 * Copyright 2002-2004 Mike Cochrane <mike@graftonhall.co.nz>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Crypt
 */
class Horde_Crypt_smime extends Horde_Crypt {

    /**
     * Object Identifers to name array.
     *
     * @var array $_oids
     */
     var $_oids = array(
        '2.5.4.3' => 'CommonName',
        '2.5.4.4' => 'Surname',
        '2.5.4.6' => 'Country',
        '2.5.4.7' => 'StateOrProvince',
        '2.5.4.8' => 'Location',
        '2.5.4.9' => 'StreetAddress',
        '2.5.4.10' => 'Organisation',
        '2.5.4.11' => 'OrganisationalUnit',
        '2.5.4.12' => 'Title',
        '2.5.4.20' => 'TelephoneNumber',
        '2.5.4.42' => 'GivenName',

        '2.5.29.14' => 'id-ce-subjectKeyIdentifier',

        '2.5.29.14' => 'id-ce-subjectKeyIdentifier',
        '2.5.29.15' => 'id-ce-keyUsage',
        '2.5.29.17' => 'id-ce-subjectAltName',
        '2.5.29.19' => 'id-ce-basicConstraints',
        '2.5.29.31' => 'id-ce-CRLDistributionPoints',
        '2.5.29.32' => 'id-ce-certificatePolicies',
        '2.5.29.35' => 'id-ce-authorityKeyIdentifier',
        '2.5.29.37' => 'id-ce-extKeyUsage',

        '1.2.840.113549.1.9.1' => 'Email',
        '1.2.840.113549.1.1.1' => 'RSAEncryption',
        '1.2.840.113549.1.1.2' => 'md2WithRSAEncryption',
        '1.2.840.113549.1.1.4' => 'md5withRSAEncryption',
        '1.2.840.113549.1.1.5' => 'SHA-1WithRSAEncryption',
        '1.2.840.10040.4.3' => 'id-dsa-with-sha-1',

        '1.3.6.1.5.5.7.3.2' => 'id_kp_clientAuth',

        '2.16.840.1.113730.1.1' => 'netscape-cert-type',
        '2.16.840.1.113730.1.2' => 'netscape-base-url',
        '2.16.840.1.113730.1.3' => 'netscape-revocation-url',
        '2.16.840.1.113730.1.4' => 'netscape-ca-revocation-url',
        '2.16.840.1.113730.1.7' => 'netscape-cert-renewal-url',
        '2.16.840.1.113730.1.8' => 'netscape-ca-policy-url',
        '2.16.840.1.113730.1.12' => 'netscape-ssl-server-name',
        '2.16.840.1.113730.1.13' => 'netscape-comment',
    );

    /**
     * Constructor.
     *
     * @access public
     *
     * @param optional array $params  Parameter array.
     *                                'temp' => location of temporary dir
     */
    function Horde_Crypt_smime($params = array())
    {
        $this->_tempdir = $params['temp'];
    }

    /**
     * Verify a passphrase for a given public/private keypair.
     *
     * @access public
     *
     * @param string $public_key   The user's public key.
     * @param string $private_key  The user's private key.
     * @param string $passphrase   The user's passphrase.
     *
     * @return boolean  Returns true on valid passphrase, false on invalid
     *                  passphrase.
     *                  Returns PEAR_Error on error.
     */
    function verifyPassphrase($public_key, $private_key, $passphrase)
    {
        /* Check for secure connection. */
        $secure_check = $this->requireSecureConnection();
        if (is_a($secure_check, 'PEAR_Error')) {
            return $secure_check;
        }

        /* Encrypt a test message. */
        $result = $this->encrypt('Test', array('type' => 'message', 'pubkey' => $public_key));
        if (is_a($result, 'PEAR_Error')) {
            return false;
        }

        /* Try to decrypt the message. */
        $result = $this->decrypt($result, array('type' => 'message', 'pubkey' => $public_key, 'privkey' => $private_key, 'passphrase' => $passphrase));
        if (is_a($result, 'PEAR_Error')) {
            return false;
        }

        return true;
    }

    /**
     * Encrypt text using SMIME.
     *
     * @access public
     *
     * @param string $text   The text to be encrypted.
     * @param array $params  The parameters needed for encryption.
     *                       See the individual _encrypt*() functions for
     *                       the parameter requirements.
     *
     * @return string  The encrypted message.
     *                 Returns PEAR_Error object on error.
     */
    function encrypt($text, $params = array())
    {
        /* Check for availability of OpenSSL PHP extension. */
        $openssl = $this->checkForOpenSSL();
        if (is_a($openssl, 'PEAR_Error')) {
            return $openssl;
        }

        if (array_key_exists('type', $params)) {
            if ($params['type'] === 'message') {
                return $this->_encryptMessage($text, $params);
            } elseif ($params['type'] === 'signature') {
                return $this->_encryptSignature($text, $params);
            }
        }
    }

    /**
     * Decrypt text using smime.
     *
     * @access public
     *
     * @param string $text   The text to be smime decrypted.
     * @param array $params  The parameters needed for decryption.
     *                       See the individual _decrypt*() functions for
     *                       the parameter requirements.
     *
     * @return string  The decrypted message.
     *                 Returns PEAR_Error object on error.
     */
    function decrypt($text, $params = array())
    {
        /* Check for availability of OpenSSL PHP extension. */
        $openssl = $this->checkForOpenSSL();
        if (is_a($openssl, 'PEAR_Error')) {
            return $openssl;
        }

        if (array_key_exists('type', $params)) {
            if ($params['type'] === 'message') {
                return $this->_decryptMessage($text, $params);
            } elseif (($params['type'] === 'signature') ||
                      ($params['type'] === 'detached-signature')) {
                return $this->_decryptSignature($text, $params);
            }
        }
    }

    /**
     * Verify a signatures using smime.
     *
     * @access public
     *
     * @param string $text  The multipart/signed data to be verified.
     * @param mixed $certs  Either a single or array of root certificates.
     *
     * @return boolean  Returns true on success.
     *                  Returns PEAR_Error object on error.
     */
    function verify($text, $certs)
    {
        global $conf;

        /* Check for availability of OpenSSL PHP extension. */
        $openssl = $this->checkForOpenSSL();
        if (is_a($openssl, 'PEAR_Error')) {
            return $openssl;
        }

        /* Create temp files for input/output. */
        $input = $this->_createTempFile('horde-smime');
        $dummy = $this->_createTempFile('horde-smime');

        /* Write text to file */
        $fp = fopen($input, 'w+');
        fwrite($fp, $text);
        fclose($fp);

        $root_certs = array();
        if (!is_array($conf['utils']['openssl_cafile'])) {
            if (file_exists($conf['utils']['openssl_cafile'])) {
                $root_certs = array($conf['utils']['openssl_cafile']);
            }
        } else {
            foreach ($conf['utils']['openssl_cafile'] as $file) {
                if (file_exists($file)) {
                    $root_certs[] = $file;
                }
            }
        }

        $result = @openssl_pkcs7_verify($input, PKCS7_DETACHED, $dummy, $root_certs);

        /* Message verified */
        if ($result === true) {
            return true;
        }

        /* Try again without verfying the signer's cert */
        $result = openssl_pkcs7_verify($input, PKCS7_DETACHED | PKCS7_NOVERIFY, $dummy);

        if ($result === true || $result === -1) {
            return PEAR::raiseError(_("Message Verified Successfully but the signer's certificate could not be verified."), 'horde.warning');
        } elseif ($result === false) {
            return PEAR::raiseError(_("Verification failed - this message may have been tampered with."), 'horde.warning');
        }

        return PEAR::raiseError(_("There was an unknown error verifying this message."), 'horde.warning');
    }

    /**
     * Sign a MIME_Part using S/MIME.
     *
     * @access public
     *
     * @param object MIME_Part $mime_part  The MIME_Part object to sign.
     * @param array $params                The parameters required for
     *                                     signing.
     *
     * @return object MIME_Part  A MIME_Part object that is signed.
     *                           Returns PEAR_Error object on error.
     */
    function signMIMEPart($mime_part, $params)
    {
        require_once 'Horde/MIME/Part.php';
        require_once 'Horde/MIME/Structure.php';

        /* Sign the part as a message */
        $message = $this->encrypt($mime_part->toString(), $params);

        /* Break the result into its components */
        $mime_message = MIME_Structure::parseTextMIMEMessage($message);

        $smime_sign = $mime_message->getPart(2);
        $smime_sign->setDescription(_("S/MIME Cryptographic Signature"));
        $smime_sign->transferDecodeContents();
        $smime_sign->setTransferEncoding('base64');

        $smime_part = &new MIME_Part('multipart/signed');
        $smime_part->setContents('This is a cryptographically signed message in MIME format.' . "\n");
        $smime_part->addPart($mime_part);
        $smime_part->addPart($smime_sign);
        $smime_part->setContentTypeParameter('protocol', 'application/x-pkcs7-signature');
        $smime_part->setContentTypeParameter('micalg', 'sha1');

        return $smime_part;
    }

    /**
     * Encrypt a MIME_Part using S/MIME.
     *
     * @access public
     *
     * @param object MIME_Part $mime_part  The MIME_Part object to encrypt.
     * @param array $params                The parameters required for
     *                                     encryption.
     *
     * @return object MIME_Part  A MIME_Part object that is encrypted.
     *                           Returns PEAR_Error on error.
     */
    function encryptMIMEPart($mime_part, $params = array())
    {
        require_once 'Horde/MIME/Part.php';
        require_once 'Horde/MIME/Structure.php';

        /* Sign the part as a message */
        $message = $this->encrypt($mime_part->toString(), $params);

        /* Break the result into its components */
        $mime_message = MIME_Structure::parseTextMIMEMessage($message);

        $smime_part = $mime_message->getBasePart();
        $smime_part->setDescription(_('S/MIME Encrypted Message'));
        $smime_part->transferDecodeContents();
        $smime_part->setTransferEncoding('base64');

        return $smime_part;
    }

    /**
     * Encrypt a message in SMIME format using a public key.
     *
     * @access private
     *
     * @param string $text   The text to be encrypted.
     * @param array $params  The parameters needed for encryption.
     * <pre>
     * Parameters:
     * ===========
     * 'type'    =>  'message' (REQUIRED)
     * 'pubkey'  =>  public key. (REQUIRED)
     * 'email'   =>  E-mail address of recipient. If not present, or not found
     *               in the public key, the first e-mail address found in the
     *               key will be used instead. (Optional)
     * </pre>
     *
     * @return string  The encrypted message.
     *                 Return PEAR_Error object on error.
     */
    function _encryptMessage($text, $params)
    {
        $email = null;

        /* Check for required parameters. */
        if (!array_key_exists('pubkey', $params)) {
            return PEAR::raiseError(_("A public SMIME key is required to encrypt a message."), 'horde.error');
        }

        /* Create temp files for input/output. */
        $input = $this->_createTempFile('horde-smime');
        $output = $this->_createTempFile('horde-smime');

        /* Store message in file. */
        $fp1 = fopen($input, 'w+');
        fputs($fp1, $text);
        fclose($fp1);

        if (array_key_exists('email', $params)) {
            $email = $params['email'];
        }

        /* If we have no email address at this point, use the first email
           address found in the public key. */
        if (empty($email)) {
            $key_info = openssl_x509_parse($params['pubkey']);
            if (is_array($key_info) && array_key_exists('subject', $key_info)) {
                if (array_key_exists('Email', $key_info['subject'])) {
                    $email = $key_info['subject']['Email'];
                } elseif (array_key_exists('emailAddress', $key_info['subject'])) {
                    $email = $key_info['subject']['emailAddress'];
                }
            } else {
                return PEAR::raiseError(_("Could not determine the recipient's e-mail address."), 'horde.error');
            }
        }

        /* Encrypt the document. */
        $res = openssl_pkcs7_encrypt($input, $output, $params['pubkey'], array('To' => $email));

        $result = file($output);
        if (empty($result)) {
            return PEAR::raiseError(_("Could not S/MIME encrypt message."), 'horde.error');
        }

        return implode('', $result);
    }

    /**
     * Sign a message in SMIME format using a private key.
     *
     * @access private
     *
     * @param string $text   The text to be signed.
     * @param array $params  The parameters needed for signing.
     * <pre>
     * Parameters:
     * ===========
     * 'certs'       =>  Additional signing certs (Optional)
     * 'passphrase'  =>  Passphrase for key (REQUIRED)
     * 'privkey'     =>  Private key (REQUIRED)
     * 'pubkey'      =>  Public key (REQUIRED)
     * 'sigtype'     =>  Determine the signature type to use. (Optional)
     *                   'cleartext'  --  Make a clear text signature
     *                   'detach'     --  Make a detached signature (DEFAULT)
     * 'type'        =>  'signature' (REQUIRED)
     * </pre>
     *
     * @return string  The signed message.
     *                 Return PEAR_Error object on error.
     */
    function _encryptSignature($text, $params)
    {
        /* Check for secure connection. */
        $secure_check = $this->requireSecureConnection();
        if (is_a($secure_check, 'PEAR_Error')) {
            return $secure_check;
        }

        /* Check for required parameters. */
        if (!array_key_exists('pubkey', $params) ||
            !array_key_exists('privkey', $params) ||
            !array_key_exists('passphrase', $params)) {
            return PEAR::raiseError(_("A public S/MIME key, private S/MIME key, and passphrase are required to sign a message."), 'horde.error');
        }

        /* Create temp files for input/output/certificates. */
        $input = $this->_createTempFile('horde-smime');
        $output = $this->_createTempFile('horde-smime');
        $certs = $this->_createTempFile('horde-smime');

        /* Store message in temporary file. */
        $fp = fopen($input, 'w+');
        fputs($fp, $text);
        fclose($fp);

        /* Store additional cert in temporary file. */
        $fp = fopen($certs, 'w+');
        fputs($fp, $params['certs']);
        fclose($fp);

        /* Determine the signature type to use. */
        $flags = PKCS7_DETACHED;
        if (array_key_exists('sigtype', $params) &&
            $params['sigtype'] == 'cleartext') {
            $flags = PKCS7_TEXT;
        }

        if (empty($params['certs'])) {
            openssl_pkcs7_sign($input, $output, $params['pubkey'], array($params['privkey'], $params['passphrase']), array(), $flags);
        } else {
            openssl_pkcs7_sign($input, $output, $params['pubkey'], array($params['privkey'], $params['passphrase']), array(), $flags, $certs);
        }

        if (!($result = file($output))) {
            return PEAR::raiseError(_("Could not S/MIME sign message."), 'horde.error');
        }

        return implode('', $result);
    }

    /**
     * Decrypt an SMIME encrypted message using a private/public keypair
     * and a passhprase.
     *
     * @access private
     *
     * @param string $text   The text to be decrypted.
     * @param array $params  The parameters needed for decryption.
     * <pre>
     * Parameters:
     * ===========
     * 'type'        =>  'message' (REQUIRED)
     * 'pubkey'      =>  public key. (REQUIRED)
     * 'privkey'     =>  private key. (REQUIRED)
     * 'passphrase'  =>  Passphrase for Key. (REQUIRED)
     * </pre>
     *
     * @return string  The decrypted message.
     *                 Returns PEAR_Error object on error.
     */
    function _decryptMessage($text, $params)
    {
        /* Check for secure connection. */
        $secure_check = $this->requireSecureConnection();
        if (is_a($secure_check, 'PEAR_Error')) {
            return $secure_check;
        }

        /* Check for required parameters. */
        if (!array_key_exists('pubkey', $params) ||
            !array_key_exists('privkey', $params) ||
            !array_key_exists('passphrase', $params)) {
            return PEAR::raiseError(_("A public S/MIME key, private S/MIME key, and passphrase are required to decrypt a message."), 'horde.error');
        }

        /* Create temp files for input/output. */
        $input = $this->_createTempFile('horde-smime');
        $output = $this->_createTempFile('horde-smime');

        /* Store message in file. */
        $fp1 = fopen($input, 'w+');
        fputs($fp1, trim($text));
        fclose($fp1);

        @openssl_pkcs7_decrypt($input, $output, $params['pubkey'], array($params['privkey'], $params['passphrase']));

        $result = file($output);

        if (empty($result)) {
            return PEAR::raiseError(_("Could not decrypt S/MIME data."), 'horde.error');
        }

        return implode('', $result);
    }

    /**
     * Convert a PEM format certificate to readable HTML version
     *
     * @access public
     *
     * @param string $cert   PEM format certificate
     *
     * @return string  HTML detailing the certificate.
     */
    function certToHTML($cert)
    {
        /* Commong Fields */
        $fieldnames['Email'] = _("Email Address");
        $fieldnames['CommonName'] = _("Common Name");
        $fieldnames['Organisation'] = _("Organisation");
        $fieldnames['OrganisationalUnit'] = _("Organisational Unit");
        $fieldnames['Country'] = _("Country");
        $fieldnames['StateOrProvince'] = _("State or Province");
        $fieldnames['Location'] = _("Location");
        $fieldnames['StreetAddress'] = _("Street Address");
        $fieldnames['TelephoneNumber'] = _("Telephone Number");
        $fieldnames['Surname'] = _("Surname");
        $fieldnames['GivenName'] = _("Given Name");

        /* Netscape Extensions */
        $fieldnames['netscape-cert-type'] = _('Netscape certificate type');
        $fieldnames['netscape-base-url'] = _('Netscape Base URL');
        $fieldnames['netscape-revocation-url'] = _('Netscape Revocation URL');
        $fieldnames['netscape-ca-revocation-url'] = _('Netscape CA Revocation URL');
        $fieldnames['netscape-cert-renewal-url'] = _('Netscape Renewal URL');
        $fieldnames['netscape-ca-policy-url'] = _('Netscape CA policy URL');
        $fieldnames['netscape-ssl-server-name'] = _('Netscape SSL server name');
        $fieldnames['netscape-comment'] = _('Netscape certificate comment');

        /* X590v3 Extensions */
        $fieldnames['id-ce-extKeyUsage'] = _('X509v3 Extended Key Usage');
        $fieldnames['id-ce-basicConstraints'] = _('X509v3 Basic Constraints');
        $fieldnames['id-ce-subjectAltName'] = _('X509v3 Subject Alternative Name');
        $fieldnames['id-ce-subjectKeyIdentifier'] = _('X509v3 Subject Key Identifier');
        $fieldnames['id-ce-certificatePolicies'] = _('Certificate Policies');
        $fieldnames['id-ce-CRLDistributionPoints'] = _('CRL Distribution Points');
        $fieldnames['id-ce-keyUsage'] = _('Key Usage');

        $text = '<pre class="fixed">';

        $cert_details = $this->parseCert($cert);
        if (!is_array($cert_details)) {
            return '<pre class="fixed">' . _('Unable to extract certificate details') . '</pre>';
        }
        $certificate = $cert_details['certificate'];

        /* Subject */
        if (array_key_exists('subject', $certificate)) {
            $text .= "<b>" . _("Subject") . ":</b>\n";

            foreach ($certificate['subject'] as $key => $value) {
                if (array_key_exists($key, $fieldnames)) {
                    $text .= sprintf("&nbsp;&nbsp;%s: %s\n", $fieldnames[$key], $value);
                } else {
                    $text .= sprintf("&nbsp;&nbsp;*%s: %s\n", $key, $value);
                }
            }

            $text .= "\n";
        }

        /* Issuer */
        if (array_key_exists('issuer', $certificate)) {
            $text .= "<b>" . _("Issuer") . ":</b>\n";

            foreach ($certificate['issuer'] as $key => $value) {
                if (array_key_exists($key, $fieldnames)) {
                    $text .= sprintf("&nbsp;&nbsp;%s: %s\n", $fieldnames[$key], $value);
                } else {
                    $text .= sprintf("&nbsp;&nbsp;*%s: %s\n", $key, $value);
                }
            }

            $text .= "\n";
        }

        /* Dates  */
        $text .= "<b>" . _("Validity") . ":</b>\n";
        $text .= sprintf("&nbsp;&nbsp;%s: %s\n", _("Not Before"), strftime("%x %X", $certificate['validity']['notbefore']));
        $text .= sprintf("&nbsp;&nbsp;%s: %s\n", _("Not After"), strftime("%x %X", $certificate['validity']['notafter']));
        $text .= "\n";

        /* Subject Public Key Info */
        $text .= "<b>" . _("Subject Public Key Info") . ":</b>\n";
        $text .= sprintf("&nbsp;&nbsp;%s: %s\n", _("Public Key Algorithm"), $certificate['subjectPublicKeyInfo']['algorithm']);
        if ($certificate['subjectPublicKeyInfo']['algorithm'] = 'rsaEncryption') {
            if (Util::extensionExists('bcmath')) {
                $modulus = $certificate['subjectPublicKeyInfo']['subjectPublicKey']['modulus'];
                $modulus_hex = '';
                while ($modulus != '0') {
                    $modulus_hex = dechex(bcmod($modulus, '16')) . $modulus_hex;
                    $modulus = bcdiv($modulus, '16', 0);
                }

                if (strlen($modulus_hex) > 64 && strlen($modulus_hex) < 128) {
                    str_pad($modulus_hex, 128, '0', STR_PAD_RIGHT);
                } else if (strlen($modulus_hex) > 128 && strlen($modulus_hex) < 256) {
                    str_pad($modulus_hex, 256, '0', STR_PAD_RIGHT);
                }

                $text .= "&nbsp;&nbsp;" . sprintf(_("RSA Public Key (%d bit)"), strlen($modulus_hex) * 4) . ":\n";

                $modulus_str = '';
                for ($i = 0; $i < strlen($modulus_hex); $i += 2) {
                    if (($i % 32) == 0) {
                        $modulus_str .= "\n&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;";
                    }
                    $modulus_str .= substr($modulus_hex, $i, 2) . ':';
                }

                $text .= sprintf("&nbsp;&nbsp;&nbsp;&nbsp;%s: %s\n", _("Modulus"), $modulus_str);
            }

            $text .= sprintf("&nbsp;&nbsp;&nbsp;&nbsp;%s: %s\n", _("Exponent"), $certificate['subjectPublicKeyInfo']['subjectPublicKey']['publicExponent']);
        }
        $text .= "\n";

        /* X509v3 extensions */
        if (array_key_exists('extensions', $certificate)) {
            $text .= "<b>" . _("X509v3 extensions") . ":</b>\n";

            foreach ($certificate['extensions'] as $key => $value) {
                if (is_array($value)) {
                    $value = _("Unsupported Extension");
                }
                if (array_key_exists($key, $fieldnames)) {
                    $text .= sprintf("&nbsp;&nbsp;%s:\n&nbsp;&nbsp;&nbsp;&nbsp;%s\n", $fieldnames[$key], wordwrap($value, 40, "\n&nbsp;&nbsp;&nbsp;&nbsp;"));
                } else {
                    $text .= sprintf("&nbsp;&nbsp;%s:\n&nbsp;&nbsp;&nbsp;&nbsp;%s\n", $key, wordwrap($value, 60, "\n&nbsp;&nbsp;&nbsp;&nbsp;"));
                }
            }

            $text .= "\n";
        }

        /* Certificate Details */
        $text .= "<b>" . _("Certificate Details") . ":</b>\n";
        $text .= sprintf("&nbsp;&nbsp;%s: %d\n", _("Version"), $certificate['version']);
        $text .= sprintf("&nbsp;&nbsp;%s: %d\n", _("Serial Number"), $certificate['serialNumber']);

        foreach ($cert_details['fingerprints'] as $hash => $fingerprint) {
            $label = sprintf(_("%s Fingerprint"), String::upper($hash));
            $fingerprint_str = '';
            for ($i = 0; $i < strlen($fingerprint); $i += 2) {
                $fingerprint_str .= substr($fingerprint, $i, 2) . ':';
            }
            $text .= sprintf("&nbsp;&nbsp;%s:\n&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;%s\n", $label, $fingerprint_str);
        }
        $text .= sprintf("&nbsp;&nbsp;%s: %s\n", _("Signature Algorithm"), $cert_details['signatureAlgorithm']);
        $text .= sprintf("&nbsp;&nbsp;%s:", _("Signature"));

        $sig_str = '';
        for ($i = 0; $i < strlen($cert_details['signature']); $i++) {
            if (($i % 16) == 0) {
                $sig_str .= "\n&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;";
            }
            $sig_str .= sprintf("%02x:", ord($cert_details['signature'][$i]));
        }

        $text .= $sig_str;
        $text .= "\n";

        $text .= '</pre>';
        return $text;
    }


    /**
     * Extract the contents of a PEM format certificate to an array.
     *
     * @access public
     *
     * @param string $cert   PEM format certificate
     *
     * @return array  Array containing all extractable information about
     *                 the certificate.
     */
    function parseCert($cert)
    {
        $cert_split = preg_split('/(-----((BEGIN)|(END)) CERTIFICATE-----)/', $cert);
        if (!isset($cert_split[1])) {
            $raw_cert = base64_decode($cert);
        } else {
            $raw_cert = base64_decode($cert_split[1]);
        }

        $cert_data = Horde_Crypt_smime::_parseASN($raw_cert);
        if (!is_array($cert_data) or $cert_data[0] == 'UNKNOWN') {
            return false;
        }

        $cert_details = array();
        $cert_details['fingerprints']['md5'] = md5($raw_cert);
        if (Util::extensionExists('mhash')) {
            $cert_details['fingerprints']['sha1'] = bin2hex(mhash(MHASH_SHA1, $raw_cert));
        }

        $cert_details['certificate']['extensions']   = array();
        $cert_details['certificate']['version']      = $cert_data[1][0][1][0][1] + 1;
        $cert_details['certificate']['serialNumber'] = $cert_data[1][0][1][1][1];
        $cert_details['certificate']['signature']    = $cert_data[1][0][1][2][1][0][1];
        $cert_details['certificate']['issuer']       = $cert_data[1][0][1][3][1];
        $cert_details['certificate']['validity']     = $cert_data[1][0][1][4][1];
        $cert_details['certificate']['subject']      = @$cert_data[1][0][1][5][1];
        $cert_details['certificate']['subjectPublicKeyInfo'] = $cert_data[1][0][1][6][1];

        $cert_details['signatureAlgorithm'] = $cert_data[1][1][1][0][1];
        $cert_details['signature'] = $cert_data[1][2][1];

        // issuer
        $issuer = array();
        foreach ($cert_details['certificate']['issuer'] as $value) {
            $issuer[$value[1][1][0][1]] = $value[1][1][1][1];
        }
        $cert_details['certificate']['issuer'] = $issuer;

        // subject
        $subject = array();
        foreach ($cert_details['certificate']['subject'] as $value) {
            $subject[$value[1][1][0][1]] = $value[1][1][1][1];
        }
        $cert_details['certificate']['subject'] = $subject;

        // validity
        $vals = $cert_details['certificate']['validity'];
        $cert_details['certificate']['validity'] = array();
        $cert_details['certificate']['validity']['notbefore'] = $vals[0][1];
        $cert_details['certificate']['validity']['notafter'] = $vals[1][1];
        foreach ($cert_details['certificate']['validity'] as $key => $val) {
            $year = substr($val, 0, 2);
            $month = substr($val, 2, 2);
            $day = substr($val, 4, 2);
            $hour = substr($val, 6, 2);
            $minute = substr($val, 8, 2);
            if ($val[11] == '-' || $val[9] == '+') {
                // handle time zone offset here
                $seconds = 0;
            } else if (String::upper($val[11]) == 'Z') {
                $seconds = 0;
            } else {
                $seconds = substr($val, 10, 2);
                if ($val[11] == '-' || $val[9] == '+') {
                    // handle time zone offset here
                }
            }
            $cert_details['certificate']['validity'][$key] = mktime ($hour, $minute, $seconds, $month, $day, $year);

        }


        // Split the Public Key into components.
        $subjectPublicKeyInfo = array();
        $subjectPublicKeyInfo['algorithm'] = $cert_details['certificate']['subjectPublicKeyInfo'][0][1][0][1];
        if ($certificate['subjectPublicKeyInfo']['algorithm'] = 'rsaEncryption') {
            $subjectPublicKey = Horde_Crypt_smime::_parseASN($cert_details['certificate']['subjectPublicKeyInfo'][1][1]);
            $subjectPublicKeyInfo['subjectPublicKey']['modulus'] = $subjectPublicKey[1][0][1];
            $subjectPublicKeyInfo['subjectPublicKey']['publicExponent'] = $subjectPublicKey[1][1][1];
        }
        $cert_details['certificate']['subjectPublicKeyInfo'] = $subjectPublicKeyInfo;

        if (isset($cert_data[1][0][1][7]) && is_array($cert_data[1][0][1][7][1])) {
            foreach($cert_data[1][0][1][7][1] as $ext) {
                $oid = $ext[1][0][1];
                $cert_details['certificate']['extensions'][$oid] = $ext[1][1];
            }
        }

        $i = 9;
        while (isset($cert_data[1][0][1][$i])) {
            $oid = $cert_data[1][0][1][$i][1][0][1];
            $cert_details['certificate']['extensions'][$oid] = $cert_data[1][0][1][$i][1][1];
            $i++;
        }

        foreach ($cert_details['certificate']['extensions'] as $oid => $val) {
            switch ($oid) {
                case 'netscape-base-url':
                case 'netscape-revocation-url':
                case 'netscape-ca-revocation-url':
                case 'netscape-cert-renewal-url':
                case 'netscape-ca-policy-url':
                case 'netscape-ssl-server-name':
                case 'netscape-comment':
                    $val = Horde_Crypt_smime::_parseASN($val[1]);
                    $cert_details['certificate']['extensions'][$oid] = $val[1];

                    break;

                case 'id-ce-subjectAltName':
                    $val = Horde_Crypt_smime::_parseASN($val[1]);
                    $cert_details['certificate']['extensions'][$oid] = '';
                    foreach ($val[1] as $name) {
                        if (!empty($cert_details['certificate']['extensions'][$oid])) {
                            $cert_details['certificate']['extensions'][$oid] .= ', ';
                        }
                        $cert_details['certificate']['extensions'][$oid] .= $name[1];
                    }
                    break;

                case 'netscape-cert-type':
                    $val = Horde_Crypt_smime::_parseASN($val[1]);
                    $val = ord($val[1]);
                    $newVal = '';

                    if ($val & 0x80) {
                        $newVal .= empty($newVal) ? 'SSL client' : ', SSL client';
                    }
                    if ($val & 0x40) {
                        $newVal .= empty($newVal) ? 'SSL server' : ', SSL server';
                    }
                    if ($val & 0x20) {
                        $newVal .= empty($newVal) ? 'S/MIME' : ', S/MIME';
                    }
                    if ($val & 0x10) {
                        $newVal .= empty($newVal) ? 'Object Signing' : ', Object Signing';
                    }
                    if ($val & 0x04) {
                        $newVal .= empty($newVal) ? 'SSL CA' : ', SSL CA';
                    }
                    if ($val & 0x02) {
                        $newVal .= empty($newVal) ? 'S/MIME CA' : ', S/MIME CA';
                    }
                    if ($val & 0x01) {
                        $newVal .= empty($newVal) ? 'Object Signing CA' : ', Object Signing CA';
                    }

                    $cert_details['certificate']['extensions'][$oid] = $newVal;
                    break;

                case 'id-ce-extKeyUsage':
                    $val = Horde_Crypt_smime::_parseASN($val[1]);
                    $val = $val[1];

                    $newVal = '';
                    if ($val[0][1] != 'sequence') {
                        $val = array($val);
                    } else {
                        $val = $val[1][1];
                    }
                    foreach ($val as $usage) {
                        if ($usage[1] = 'id_kp_clientAuth') {
                            $newVal .= empty($newVal) ? 'TLS Web Client Authentication' : ', TLS Web Client Authentication';
                        } else {
                            $newVal .= empty($newVal) ? $usage[1] : ', ' . $usage[1];
                        }
                    }
                    $cert_details['certificate']['extensions'][$oid] = $newVal;
                    break;

                case 'id-ce-subjectKeyIdentifier':
                    $val = Horde_Crypt_smime::_parseASN($val[1]);
                    $val = $val[1];

                    $newVal = '';

                    for ($i = 0; $i < strlen($val); $i++) {
                        $newVal .= sprintf("%02x:", ord($val[$i]));
                    }
                    $cert_details['certificate']['extensions'][$oid] = $newVal;
                    break;

                case 'id-ce-authorityKeyIdentifier':
                    $val = Horde_Crypt_smime::_parseASN($val[1]);
                    if ($val[0] == 'string') {
                        $val = $val[1];

                        $newVal = '';
                        for ($i = 0; $i < strlen($val); $i++) {
                            $newVal .= sprintf("%02x:", ord($val[$i]));
                        }
                        $cert_details['certificate']['extensions'][$oid] = $newVal;
                    } else {
                        $cert_details['certificate']['extensions'][$oid] = _("Unsupported Extension");
                    }
                    break;

                case 'id-ce-basicConstraints':
                case 'default':
                    $cert_details['certificate']['extensions'][$oid] = _("Unsupported Extension");
                    break;
            }
        }

        return $cert_details;
    }

    /**
     * Attempt to parse ASN.1 formated data.
     *
     * @access public
     *
     * @param string $data   ASN.1 formated data
     *
     * @return array  Array contained the extracted values..
     */
    function _parseASN($data)
    {
        $result = array();

        while (strlen($data) > 1) {
            $class = ord($data[0]);
            switch ($class) {
                // Sequence
                case 0x30:
                    $len = ord($data[1]);
                    $bytes = 0;
                    if ($len & 0x80) {
                        $bytes = $len & 0x0f;
                        $len = 0;
                        for ($i = 0; $i < $bytes; $i++) {
                            $len = ($len << 8) | ord($data[$i + 2]);
                        }
                    }
                    $sequence_data = substr($data, 2 + $bytes, $len);
                    $data = substr($data, 2 + $bytes + $len);

                    $values = $this->_parseASN($sequence_data);
                    if (!is_array($values) || is_string($values[0])) {
                        $values = array($values);
                    }
                    $sequence_values = array();
                    $i = 0;
                    foreach ($values as $val) {
                        if ($val[0] == 'extension') {
                            $sequence_values['extensions'][] = $val;
                        } else {
                            $sequence_values[$i++] = $val;
                        }
                    }
                    $result[] = array('sequence', $sequence_values);

                    break;

                // Set of
                case 0x31:
                    $len = ord($data[1]);
                    $bytes = 0;
                    if ($len & 0x80) {
                        $bytes = $len & 0x0f;
                        $len = 0;
                        for ($i = 0; $i < $bytes; $i++) {
                            $len = ($len << 8) | ord($data[$i + 2]);
                        }
                    }
                    $sequence_data = substr($data, 2 + $bytes, $len);
                    $data = substr($data, 2 + $bytes + $len);

                    $result[] = array('set', $this->_parseASN($sequence_data));

                    break;

                // Boolean type
                case 0x01:
                    $boolean_value = (ord($data[2]) == 0xff);
                    $data = substr($data, 3);

                    $result[] = array('boolean', $boolean_value);

                    break;

                // Integer type
                case 0x02:
                    $len = ord($data[1]);
                    $bytes = 0;
                    if ($len & 0x80) {
                        $bytes = $len & 0x0f;
                        $len = 0;
                        for ($i = 0; $i < $bytes; $i++) {
                            $len = ($len << 8) | ord($data[$i + 2]);
                        }
                    }

                    $integer_data = substr($data, 2 + $bytes, $len);
                    $data = substr($data, 2 + $bytes + $len);

                    $value = 0;
                    if ($len <= 4) {
                        /* Method works fine for small integers */
                        for ($i = 0; $i < strlen($integer_data); $i++) {
                            $value = ($value << 8) | ord($integer_data[$i]);
                        }
                    } else {
                        /* Method works for arbitrary length integers */
                        if (Util::extensionExists('bcmath')) {
                            for ($i = 0; $i < strlen($integer_data); $i++) {
                                $value = bcadd(bcmul($value, 256), ord($integer_data[$i]));
                            }
                        } else {
                            $value = -1;
                        }
                    }
                    $result[] = array('integer(' . $len . ')', $value);

                    break;

                // Bitstring type
                case 0x03:
                    $len = ord($data[1]);
                    $bytes = 0;
                    if ($len & 0x80) {
                        $bytes = $len & 0x0f;
                        $len = 0;
                        for ($i = 0; $i < $bytes; $i++) {
                            $len = ($len << 8) | ord($data[$i + 2]);
                        }
                    }
                    $bitstring_data = substr($data, 3 + $bytes, $len);
                    $data = substr($data, 2 + $bytes + $len);

                    $result[] = array('bit string', $bitstring_data);

                    break;

                // Octetstring type
                case 0x04:
                    $len = ord($data[1]);
                    $bytes = 0;
                    if ($len & 0x80) {
                        $bytes = $len & 0x0f;
                        $len = 0;
                        for ($i = 0; $i < $bytes; $i++) {
                            $len = ($len << 8) | ord($data[$i + 2]);
                        }
                    }
                    $octectstring_data = substr($data, 2 + $bytes, $len);
                    $data = substr($data, 2 + $bytes + $len);

                    $result[] = array('octet string', $octectstring_data);

                    break;

                // Null type
                case 0x05:
                    $data = substr($data, 2);

                    $result[] = array('null', null);

                    break;

                // Object identifier type
                case 0x06:
                    $len = ord($data[1]);
                    $bytes = 0;
                    if ($len & 0x80) {
                        $bytes = $len & 0x0f;
                        $len = 0;
                        for ($i = 0; $i < $bytes; $i++) {
                            $len = ($len << 8) | ord($data[$i + 2]);
                        }
                    }
                    $oid_data = substr($data, 2 + $bytes, $len);
                    $data = substr($data, 2 + $bytes + $len);

                    // Unpack the OID
                    $plain  = floor(ord($oid_data[0]) / 40);
                    $plain .= '.' . ord($oid_data[0]) % 40;

                    $value = 0;
                    $i = 1;
                    while ($i < strlen($oid_data)) {
                        $value = $value << 7;
                        $value = $value | (ord($oid_data[$i]) & 0x7f);

                        if (!(ord($oid_data[$i]) & 0x80)) {
                            $plain .= '.' . $value;
                            $value = 0;
                        }
                        $i++;
                    }

                    if (array_key_exists($plain, $this->_oids)) {
                        $result[] = array('oid', $this->_oids[$plain]);
                    } else {
                        $result[] = array('oid', $plain);
                    }

                    break;

                // Character string type
                case 0x12:
                case 0x13:
                case 0x14:
                case 0x15:
                case 0x16:
                case 0x81:
                case 0x80:
                    $len = ord($data[1]);
                    $bytes = 0;
                    if ($len & 0x80) {
                        $bytes = $len & 0x0f;
                        $len = 0;
                        for ($i = 0; $i < $bytes; $i++) {
                            $len = ($len << 8) | ord($data[$i + 2]);
                        }
                    }
                    $string_data = substr($data, 2 + $bytes, $len);
                    $data = substr($data, 2 + $bytes + $len);

                    $result[] = array('string', $string_data);

                    break;

                // Time types
                case 0x17:
                    $len = ord($data[1]);
                    $bytes = 0;
                    if ($len & 0x80) {
                        $bytes = $len & 0x0f;
                        $len = 0;
                        for ($i = 0; $i < $bytes; $i++) {
                            $len = ($len << 8) | ord($data[$i + 2]);
                        }
                    }
                    $time_data = substr($data, 2 + $bytes, $len);
                    $data = substr($data, 2 + $bytes + $len);

                    $result[] = array('utctime', $time_data);

                    break;

                // X509v3 extensions?
                case 0x82:
                    $len = ord($data[1]);
                    $bytes = 0;
                    if ($len & 0x80) {
                        $bytes = $len & 0x0f;
                        $len = 0;
                        for ($i = 0; $i < $bytes; $i++) {
                            $len = ($len << 8) | ord($data[$i + 2]);
                        }
                    }
                    $sequence_data = substr($data, 2 + $bytes, $len);
                    $data = substr($data, 2 + $bytes + $len);

                    $result[] = array('extension', 'X509v3 extensions');
                    $result[] = $this->_parseASN($sequence_data);

                    break;

                // Extensions
                case 0xa0:
                case 0xa3:
                    $extension_data = substr($data, 0, 2);
                    $data = substr($data, 2);

                    $result[] = array('extension', dechex($extension_data));

                    break;

                case 0xe6:
                    $extension_data = substr($data, 0, 1);
                    $data = substr($data, 1);

                    $result[] = array('extension', dechex($extension_data));

                    break;

                case 0xa1:
                    $extension_data = substr($data, 0, 1);
                    $data = substr($data, 6);

                    $result[] = array('extension', dechex($extension_data));

                    break;

                // Unknown
                default:
                    $result[] = array('UNKNOWN', dechex($data));
                    $data = '';
                    break;
            }
        }
        return (count($result) > 1) ? $result : array_pop($result);
    }

    /**
     * Decrypt an SMIME signed message using a public key.
     *
     * @access private
     *
     * @param string $text   The text to be verified.
     * @param array $params  The parameters needed for verification.
     * <pre>
     * Parameters:
     * ===========
     * 'type'       =>  'signature' or 'detached-signature' (REQUIRED)
     * 'pubkey'     =>  public key. (REQUIRED)
     * 'signature'  =>  signature block. (REQUIRED for detached signature)
     * </pre>
     *
     * @return string  The verification message from gpg.
     *                 If no signature, returns empty string.
     *                 Returns PEAR_Error object on error.
     */
    function _decryptSignature($text, $params)
    {
        return PEAR::raiseError('_decryptSignature() ' . _("not yet implemented"));
    }

    /**
     * Check for the presence of the OpenSSL extension to PHP.
     *
     * @access public
     *
     * @return boolean  Returns true if the openssl extension is available.
     *                  Returns a PEAR_Error if not.
     */
    function checkForOpenSSL()
    {
        if (!Util::extensionExists('openssl')) {
            return PEAR::raiseError(_("The openssl module is required for the Horde_Crypt_smime:: class."));
        }
    }

}
