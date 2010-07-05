<?php

require_once 'Horde/Crypt.php';

/**
 * Horde_Crypt_smime:: provides a framework for Horde applications to
 * interact with the OpenSSL library and implement S/MIME.
 *
 * $Horde: framework/Crypt/Crypt/smime.php,v 1.49.2.23 2009-12-14 19:40:34 slusarz Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @package Horde_Crypt
 */
class Horde_Crypt_smime extends Horde_Crypt {

    /**
     * Object Identifers to name array.
     *
     * @var array
     */
    var $_oids = array(
        '2.5.4.3' => 'CommonName',
        '2.5.4.4' => 'Surname',
        '2.5.4.6' => 'Country',
        '2.5.4.7' => 'Location',
        '2.5.4.8' => 'StateOrProvince',
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
     * @param array $params  Parameter array.
     *                       'temp' => Location of temporary directory.
     */
    function Horde_Crypt_smime($params)
    {
        $this->_tempdir = $params['temp'];
    }

    /**
     * Verify a passphrase for a given private key.
     *
     * @param string $private_key  The user's private key.
     * @param string $passphrase   The user's passphrase.
     *
     * @return boolean  Returns true on valid passphrase, false on invalid
     *                  passphrase.
     *                  Returns PEAR_Error on error.
     */
    function verifyPassphrase($private_key, $passphrase)
    {
        if (is_null($passphrase)) {
            $res = openssl_pkey_get_private($private_key);
        } else {
            $res = openssl_pkey_get_private($private_key, $passphrase);
        }

        return is_resource($res);
    }

    /**
     * Encrypt text using S/MIME.
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

        if (isset($params['type'])) {
            if ($params['type'] === 'message') {
                return $this->_encryptMessage($text, $params);
            } elseif ($params['type'] === 'signature') {
                return $this->_encryptSignature($text, $params);
            }
        }
    }

    /**
     * Decrypt text via S/MIME.
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

        if (isset($params['type'])) {
            if ($params['type'] === 'message') {
                return $this->_decryptMessage($text, $params);
            } elseif (($params['type'] === 'signature') ||
                      ($params['type'] === 'detached-signature')) {
                return $this->_decryptSignature($text, $params);
            }
        }
    }

    /**
     * Verify a signature using via S/MIME.
     *
     * @param string $text  The multipart/signed data to be verified.
     * @param mixed $certs  Either a single or array of root certificates.
     *
     * @return stdClass  Object with the following elements:
     *                   'result' -> Returns true on success;
     *                               PEAR_Error object on error.
     *                   'cert' -> The certificate of the signer stored
     *                             in the message (in PEM format).
     *                   'email' -> The email of the signing person.
     */
    function verify($text, $certs)
    {
        /* Check for availability of OpenSSL PHP extension. */
        $openssl = $this->checkForOpenSSL();
        if (is_a($openssl, 'PEAR_Error')) {
            return $openssl;
        }

        /* Create temp files for input/output. */
        $input = $this->_createTempFile('horde-smime');
        $output = $this->_createTempFile('horde-smime');

        /* Write text to file */
        $fp = fopen($input, 'w+');
        fwrite($fp, $text);
        fclose($fp);

        $root_certs = array();
        if (!is_array($certs)) {
            $certs = array($certs);
        }
        foreach ($certs as $file) {
            if (file_exists($file)) {
                $root_certs[] = $file;
            }
        }

        $ob = new stdClass;

        if (!empty($root_certs)) {
            $result = openssl_pkcs7_verify($input, 0, $output, $root_certs);
            /* Message verified */
            if ($result === true) {
                $ob->result = true;
                $ob->cert = file_get_contents($output);
                $ob->email = $this->getEmailFromKey($ob->cert);
                return $ob;
            }
        }

        /* Try again without verfying the signer's cert */
        $result = openssl_pkcs7_verify($input, PKCS7_NOVERIFY, $output);

        if ($result === true) {
            $ob->result = PEAR::raiseError(_("Message Verified Successfully but the signer's certificate could not be verified."), 'horde.warning');
        } elseif ($result == -1) {
            $ob->result = PEAR::raiseError(_("Verification failed - an unknown error has occurred."), 'horde.error');
        } else {
            $ob->result = PEAR::raiseError(_("Verification failed - this message may have been tampered with."), 'horde.error');
        }

        $ob->cert = file_get_contents($output);
        $ob->email = $this->getEmailFromKey($ob->cert);

        return $ob;
    }

    /**
     * Extract the contents from signed S/MIME data.
     *
     * @param string $data     The signed S/MIME data.
     * @param string $sslpath  The path to the OpenSSL binary.
     *
     * @return string  The contents embedded in the signed data.
     *                 Returns PEAR_Error on error.
     */
    function extractSignedContents($data, $sslpath)
    {
        /* Check for availability of OpenSSL PHP extension. */
        $openssl = $this->checkForOpenSSL();
        if (is_a($openssl, 'PEAR_Error')) {
            return $openssl;
        }

        /* Create temp files for input/output. */
        $input = $this->_createTempFile('horde-smime');
        $output = $this->_createTempFile('horde-smime');

        /* Write text to file. */
        $fp = fopen($input, 'w');
        fwrite($fp, $data);
        fclose($fp);
        unset($data);

        exec($sslpath . ' smime -verify -noverify -nochain -in ' . $input . ' -out ' . $output);

        $ret = file_get_contents($output);
        return $ret
            ? $ret
            : PEAR::raiseError(_("OpenSSL error: Could not extract data from signed S/MIME part."), 'horde.error');
    }

    /**
     * Sign a MIME_Part using S/MIME.
     *
     * @param MIME_Part $mime_part  The MIME_Part object to sign.
     * @param array $params         The parameters required for signing.
     *
     * @return MIME_Part  A MIME_Part object that is signed.
     *                    Returns PEAR_Error object on error.
     */
    function signMIMEPart($mime_part, $params)
    {
        require_once 'Horde/MIME/Part.php';
        require_once 'Horde/MIME/Structure.php';

        /* Sign the part as a message */
        $message = $this->encrypt($mime_part->toCanonicalString(), $params);

        /* Break the result into its components */
        $mime_message = MIME_Structure::parseTextMIMEMessage($message);

        $smime_sign = $mime_message->getPart(2);
        $smime_sign->setDescription(_("S/MIME Cryptographic Signature"));
        $smime_sign->transferDecodeContents();
        $smime_sign->setTransferEncoding('base64');

        $smime_part = new MIME_Part('multipart/signed');
        $smime_part->setContents('This is a cryptographically signed message in MIME format.' . "\n");
        $smime_part->addPart($mime_part);
        $smime_part->addPart($smime_sign);
        $smime_part->setContentTypeParameter('protocol', 'application/pkcs7-signature');
        $smime_part->setContentTypeParameter('micalg', 'sha1');

        return $smime_part;
    }

    /**
     * Encrypt a MIME_Part using S/MIME.
     *
     * @param MIME_Part $mime_part  The MIME_Part object to encrypt.
     * @param array $params         The parameters required for encryption.
     *
     * @return MIME_Part  A MIME_Part object that is encrypted.
     *                    Returns PEAR_Error on error.
     */
    function encryptMIMEPart($mime_part, $params = array())
    {
        require_once 'Horde/MIME/Part.php';
        require_once 'Horde/MIME/Structure.php';

        /* Sign the part as a message */
        $message = $this->encrypt($mime_part->toCanonicalString(), $params);
        if (is_a($message, 'PEAR_Error')) {
            return $message;
        }

        /* Get charset for mime part description. */
        $charset = NLS::getEmailCharset();

        /* Break the result into its components */
        $mime_message = MIME_Structure::parseTextMIMEMessage($message);

        $smime_part = $mime_message->getBasePart();
        $smime_part->setCharset($charset);
        $smime_part->setDescription(String::convertCharset(_("S/MIME Encrypted Message"), NLS::getCharset(), $charset));
        $smime_part->transferDecodeContents();
        $smime_part->setTransferEncoding('base64');
        $smime_part->setDisposition('inline');

        /* By default, encrypt() produces a message with type
         * 'application/x-pkcs7-mime' and no 'smime-type' parameter. Per
         * RFC 2311, the more correct MIME type is 'application/pkcs7-mime'
         * and the smime-type should be 'enveloped-data'. */
        $smime_part->setType('application/pkcs7-mime');
        $smime_part->setContentTypeParameter('smime-type', 'enveloped-data');

        return $smime_part;
    }

    /**
     * Encrypt a message in S/MIME format using a public key.
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
        if (!isset($params['pubkey'])) {
            return PEAR::raiseError(_("A public S/MIME key is required to encrypt a message."), 'horde.error');
        }

        /* Create temp files for input/output. */
        $input = $this->_createTempFile('horde-smime');
        $output = $this->_createTempFile('horde-smime');

        /* Store message in file. */
        $fp1 = fopen($input, 'w+');
        fputs($fp1, $text);
        fclose($fp1);

        if (isset($params['email'])) {
            $email = $params['email'];
        } else {
            $email = $this->getEmailFromKey($params['pubkey']);
            if (is_null($email)) {
                return PEAR::raiseError(_("Could not determine the recipient's e-mail address."), 'horde.error');
            }
        }

        /* Encrypt the document. */
        if (openssl_pkcs7_encrypt($input, $output, $params['pubkey'], array('To' => $email))) {
            $result = file_get_contents($output);
            if (!empty($result)) {
                return $this->_fixContentType($result, 'encrypt');
            }
        }

        return PEAR::raiseError(_("Could not S/MIME encrypt message."), 'horde.error');
    }

    /**
     * Sign a message in S/MIME format using a private key.
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
        if (!isset($params['pubkey']) ||
            !isset($params['privkey']) ||
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

        /* Store additional certs in temporary file. */
        if (!empty($params['certs'])) {
            $fp = fopen($certs, 'w+');
            fputs($fp, $params['certs']);
            fclose($fp);
        }

        /* Determine the signature type to use. */
        if (isset($params['sigtype']) && ($params['sigtype'] == 'cleartext')) {
            $flags = PKCS7_TEXT;
        } else {
            $flags = PKCS7_DETACHED;
        }

        $privkey = (is_null($params['passphrase'])) ? $params['privkey'] : array($params['privkey'], $params['passphrase']);

        if (empty($params['certs'])) {
            $res = openssl_pkcs7_sign($input, $output, $params['pubkey'], $privkey, array(), $flags);
        } else {
            $res = openssl_pkcs7_sign($input, $output, $params['pubkey'], $privkey, array(), $flags, $certs);
        }

        if (!$res) {
            return PEAR::raiseError(_("Could not S/MIME sign message."), 'horde.error');
        }

        $data = file_get_contents($output);
        return $this->_fixContentType($data, 'signature');
    }

    /**
     * Decrypt an S/MIME encrypted message using a private/public keypair
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
        if (!isset($params['pubkey']) ||
            !isset($params['privkey']) ||
            !array_key_exists('passphrase', $params)) {
            return PEAR::raiseError(_("A public S/MIME key, private S/MIME key, and passphrase are required to decrypt a message."), 'horde.error');
        }

        /* Create temp files for input/output. */
        $input = $this->_createTempFile('horde-smime');
        $output = $this->_createTempFile('horde-smime');

        /* Store message in file. */
        $fp = fopen($input, 'w+');
        fputs($fp, trim($text));
        fclose($fp);

        $privkey = (is_null($params['passphrase'])) ? $params['privkey'] : array($params['privkey'], $params['passphrase']);
        if (openssl_pkcs7_decrypt($input, $output, $params['pubkey'], $privkey)) {
            return file_get_contents($output);
        }

        return PEAR::raiseError(_("Could not decrypt S/MIME data."), 'horde.error');
    }

    /**
     * Sign and Encrypt a MIME_Part using S/MIME.
     *
     * @param MIME_Part $mime_part   The MIME_Part object to sign and encrypt.
     * @param array $sign_params     The parameters required for signing. See
     *                               _encryptSignature().
     * @param array $encrypt_params  The parameters required for encryption.
     *                               See _encryptMessage().
     *
     * @return MIME_Part  A MIME_Part object that is signed and encrypted.
     *                    Returns PEAR_Error on error.
     */
    function signAndEncryptMIMEPart($mime_part, $sign_params = array(),
                                    $encrypt_params = array())
    {
        include_once 'Horde/MIME/Part.php';

        $part = $this->signMIMEPart($mime_part, $sign_params);
        if (is_a($part, 'PEAR_Error')) {
            return $part;
        }
        $part = $this->encryptMIMEPart($part, $encrypt_params);
        if (is_a($part, 'PEAR_Error')) {
            return $part;
        }

        return $part;
    }

    /**
     * Convert a PEM format certificate to readable HTML version
     *
     * @param string $cert   PEM format certificate
     *
     * @return string  HTML detailing the certificate.
     */
    function certToHTML($cert)
    {
        /* Common Fields */
        $fieldnames = array(
            'Email' => _("Email Address"),
            'CommonName' => _("Common Name"),
            'Organisation' => _("Organisation"),
            'OrganisationalUnit' => _("Organisational Unit"),
            'Country' => _("Country"),
            'StateOrProvince' => _("State or Province"),
            'Location' => _("Location"),
            'StreetAddress' => _("Street Address"),
            'TelephoneNumber' => _("Telephone Number"),
            'Surname' => _("Surname"),
            'GivenName' => _("Given Name")
        );

        /* Netscape Extensions */
        $fieldnames += array(
            'netscape-cert-type' => _("Netscape certificate type"),
            'netscape-base-url' => _("Netscape Base URL"),
            'netscape-revocation-url' => _("Netscape Revocation URL"),
            'netscape-ca-revocation-url' => _("Netscape CA Revocation URL"),
            'netscape-cert-renewal-url' => _("Netscape Renewal URL"),
            'netscape-ca-policy-url' => _("Netscape CA policy URL"),
            'netscape-ssl-server-name' => _("Netscape SSL server name"),
            'netscape-comment' => _("Netscape certificate comment")
        );

        /* X590v3 Extensions */
        $fieldnames += array(
            'id-ce-extKeyUsage' => _("X509v3 Extended Key Usage"),
            'id-ce-basicConstraints' => _("X509v3 Basic Constraints"),
            'id-ce-subjectAltName' => _("X509v3 Subject Alternative Name"),
            'id-ce-subjectKeyIdentifier' => _("X509v3 Subject Key Identifier"),
            'id-ce-certificatePolicies' => _("Certificate Policies"),
            'id-ce-CRLDistributionPoints' => _("CRL Distribution Points"),
            'id-ce-keyUsage' => _("Key Usage")
        );

        $cert_details = $this->parseCert($cert);
        if (!is_array($cert_details)) {
            return '<pre class="fixed">' . _("Unable to extract certificate details") . '</pre>';
        }
        $certificate = $cert_details['certificate'];

        $text = '<pre class="fixed">';

        /* Subject (a/k/a Certificate Owner) */
        if (isset($certificate['subject'])) {
            $text .= "<strong>" . _("Certificate Owner") . ":</strong>\n";

            foreach ($certificate['subject'] as $key => $value) {
                if (isset($fieldnames[$key])) {
                    $text .= sprintf("&nbsp;&nbsp;%s: %s\n", $fieldnames[$key], $value);
                } else {
                    $text .= sprintf("&nbsp;&nbsp;*%s: %s\n", $key, $value);
                }
            }
            $text .= "\n";
        }

        /* Issuer */
        if (isset($certificate['issuer'])) {
            $text .= "<strong>" . _("Issuer") . ":</strong>\n";

            foreach ($certificate['issuer'] as $key => $value) {
                if (isset($fieldnames[$key])) {
                    $text .= sprintf("&nbsp;&nbsp;%s: %s\n", $fieldnames[$key], $value);
                } else {
                    $text .= sprintf("&nbsp;&nbsp;*%s: %s\n", $key, $value);
                }
            }
            $text .= "\n";
        }

        /* Dates  */
        $text .= "<strong>" . _("Validity") . ":</strong>\n";
        $text .= sprintf("&nbsp;&nbsp;%s: %s\n", _("Not Before"), strftime("%x %X", $certificate['validity']['notbefore']));
        $text .= sprintf("&nbsp;&nbsp;%s: %s\n", _("Not After"), strftime("%x %X", $certificate['validity']['notafter']));
        $text .= "\n";

        /* Certificate Owner - Public Key Info */
        $text .= "<strong>" . _("Public Key Info") . ":</strong>\n";
        $text .= sprintf("&nbsp;&nbsp;%s: %s\n", _("Public Key Algorithm"), $certificate['subjectPublicKeyInfo']['algorithm']);
        if ($certificate['subjectPublicKeyInfo']['algorithm'] == 'rsaEncryption') {
            if (Util::extensionExists('bcmath')) {
                $modulus = $certificate['subjectPublicKeyInfo']['subjectPublicKey']['modulus'];
                $modulus_hex = '';
                while ($modulus != '0') {
                    $modulus_hex = dechex(bcmod($modulus, '16')) . $modulus_hex;
                    $modulus = bcdiv($modulus, '16', 0);
                }

                if ((strlen($modulus_hex) > 64) &&
                    (strlen($modulus_hex) < 128)) {
                    str_pad($modulus_hex, 128, '0', STR_PAD_RIGHT);
                } elseif ((strlen($modulus_hex) > 128) &&
                          (strlen($modulus_hex) < 256)) {
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
        if (isset($certificate['extensions'])) {
            $text .= "<strong>" . _("X509v3 extensions") . ":</strong>\n";

            foreach ($certificate['extensions'] as $key => $value) {
                if (is_array($value)) {
                    $value = _("Unsupported Extension");
                }
                if (isset($fieldnames[$key])) {
                    $text .= sprintf("&nbsp;&nbsp;%s:\n&nbsp;&nbsp;&nbsp;&nbsp;%s\n", $fieldnames[$key], wordwrap($value, 40, "\n&nbsp;&nbsp;&nbsp;&nbsp;"));
                } else {
                    $text .= sprintf("&nbsp;&nbsp;%s:\n&nbsp;&nbsp;&nbsp;&nbsp;%s\n", $key, wordwrap($value, 60, "\n&nbsp;&nbsp;&nbsp;&nbsp;"));
                }
            }

            $text .= "\n";
        }

        /* Certificate Details */
        $text .= "<strong>" . _("Certificate Details") . ":</strong>\n";
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

        return $text . $sig_str . "\n</pre>";
    }

    /**
     * Extract the contents of a PEM format certificate to an array.
     *
     * @param string $cert  PEM format certificate
     *
     * @return array  Array containing all extractable information about
     *                the certificate.
     */
    function parseCert($cert)
    {
        $cert_split = preg_split('/(-----((BEGIN)|(END)) CERTIFICATE-----)/', $cert);
        if (!isset($cert_split[1])) {
            $raw_cert = base64_decode($cert);
        } else {
            $raw_cert = base64_decode($cert_split[1]);
        }

        $cert_data = $this->_parseASN($raw_cert);

        if (!is_array($cert_data) ||
            ($cert_data[0] == 'UNKNOWN') ||
            ($cert_data[1][0] == 'UNKNOWN') ||
            /* Bug #8751: Check for required number of fields. The ASN
             * parsing code doesn't seem to be able to handle v1 data - it
             * combines the version and serial number fields.
             * openssl_x509_parse() works, but doesn't have a stable API.
             * Since v1 is such an old standard anyway, best just to abort
             * here. */
            (count($cert_data[1][0][1]) != 7)) {
            return false;
        }

        $cert_details = array();
        $cert_details['fingerprints']['md5'] = md5($raw_cert);
        $cert_details['fingerprints']['sha1'] = sha1($raw_cert);

        $cert_details['certificate']['extensions'] = array();
        $cert_details['certificate']['version'] = $cert_data[1][0][1][0][1] + 1;
        $cert_details['certificate']['serialNumber'] = $cert_data[1][0][1][1][1];
        $cert_details['certificate']['signature'] = $cert_data[1][0][1][2][1][0][1];
        $cert_details['certificate']['issuer'] = $cert_data[1][0][1][3][1];
        $cert_details['certificate']['validity'] = $cert_data[1][0][1][4][1];
        $cert_details['certificate']['subject'] = @$cert_data[1][0][1][5][1];
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
            if (($val[11] == '-') || ($val[9] == '+')) {
                // handle time zone offset here
                $seconds = 0;
            } elseif (String::upper($val[11]) == 'Z') {
                $seconds = 0;
            } else {
                $seconds = substr($val, 10, 2);
                if (($val[11] == '-') || ($val[9] == '+')) {
                    // handle time zone offset here
                }
            }
            $cert_details['certificate']['validity'][$key] = mktime ($hour, $minute, $seconds, $month, $day, $year);
        }

        // Split the Public Key into components.
        $subjectPublicKeyInfo = array();
        $subjectPublicKeyInfo['algorithm'] = $cert_details['certificate']['subjectPublicKeyInfo'][0][1][0][1];
        if ($subjectPublicKeyInfo['algorithm'] == 'rsaEncryption') {
            $subjectPublicKey = $this->_parseASN($cert_details['certificate']['subjectPublicKeyInfo'][1][1]);
            $subjectPublicKeyInfo['subjectPublicKey']['modulus'] = $subjectPublicKey[1][0][1];
            $subjectPublicKeyInfo['subjectPublicKey']['publicExponent'] = $subjectPublicKey[1][1][1];
        }
        $cert_details['certificate']['subjectPublicKeyInfo'] = $subjectPublicKeyInfo;

        if (isset($cert_data[1][0][1][7]) &&
            is_array($cert_data[1][0][1][7][1])) {
            foreach ($cert_data[1][0][1][7][1] as $ext) {
                $oid = $ext[1][0][1];
                $cert_details['certificate']['extensions'][$oid] = $ext[1][1];
            }
        }

        $i = 9;

        while (isset($cert_data[1][0][1][$i]) &&
               is_array($cert_data[1][0][1][$i][1])) {
            $oid = $cert_data[1][0][1][$i][1][0][1];
            $cert_details['certificate']['extensions'][$oid] = $cert_data[1][0][1][$i][1][1];
            ++$i;
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
                $val = $this->_parseASN($val[1]);
                $cert_details['certificate']['extensions'][$oid] = $val[1];
                break;

            case 'id-ce-subjectAltName':
                $val = $this->_parseASN($val[1]);
                $cert_details['certificate']['extensions'][$oid] = '';
                foreach ($val[1] as $name) {
                    if (!empty($cert_details['certificate']['extensions'][$oid])) {
                        $cert_details['certificate']['extensions'][$oid] .= ', ';
                    }
                    $cert_details['certificate']['extensions'][$oid] .= $name[1];
                }
                break;

            case 'netscape-cert-type':
                $val = $this->_parseASN($val[1]);
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
                $val = $this->_parseASN($val[1]);
                $val = $val[1];

                $newVal = '';
                if ($val[0][1] != 'sequence') {
                    $val = array($val);
                } else {
                    $val = $val[1][1];
                }
                foreach ($val as $usage) {
                    if ($usage[1] == 'id_kp_clientAuth') {
                        $newVal .= empty($newVal) ? 'TLS Web Client Authentication' : ', TLS Web Client Authentication';
                    } else {
                        $newVal .= empty($newVal) ? $usage[1] : ', ' . $usage[1];
                    }
                }
                $cert_details['certificate']['extensions'][$oid] = $newVal;
                break;

            case 'id-ce-subjectKeyIdentifier':
                $val = $this->_parseASN($val[1]);
                $val = $val[1];

                $newVal = '';

                for ($i = 0; $i < strlen($val); $i++) {
                    $newVal .= sprintf("%02x:", ord($val[$i]));
                }
                $cert_details['certificate']['extensions'][$oid] = $newVal;
                break;

            case 'id-ce-authorityKeyIdentifier':
                $val = $this->_parseASN($val[1]);
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
     * @access private
     *
     * @param string $data  ASN.1 formated data
     *
     * @return array  Array contained the extracted values.
     */
    function _parseASN($data)
    {
        $result = array();

        while (strlen($data) > 1) {
            $class = ord($data[0]);
            switch ($class) {
            case 0x30:
                // Sequence
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

            case 0x31:
                // Set of
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

            case 0x01:
                // Boolean type
                $boolean_value = (ord($data[2]) == 0xff);
                $data = substr($data, 3);
                $result[] = array('boolean', $boolean_value);
                break;

            case 0x02:
                // Integer type
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

            case 0x03:
                // Bitstring type
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

            case 0x04:
                // Octetstring type
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

            case 0x05:
                // Null type
                $data = substr($data, 2);
                $result[] = array('null', null);
                break;

            case 0x06:
                // Object identifier type
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

                if (isset($this->_oids[$plain])) {
                    $result[] = array('oid', $this->_oids[$plain]);
                } else {
                    $result[] = array('oid', $plain);
                }

                break;

            case 0x12:
            case 0x13:
            case 0x14:
            case 0x15:
            case 0x16:
            case 0x81:
            case 0x80:
                // Character string type
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

            case 0x17:
                // Time types
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

            case 0x82:
                // X509v3 extensions?
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

            case 0xa0:
            case 0xa3:
                // Extensions
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

            default:
                // Unknown
                $result[] = array('UNKNOWN', dechex($data));
                $data = '';
                break;
            }
        }

        return (count($result) > 1) ? $result : array_pop($result);
    }

    /**
     * Decrypt an S?MIME signed message using a public key.
     *
     * @access private
     *
     * @param string $text   The text to be verified.
     * @param array $params  The parameters needed for verification.
     *
     * @return string  The verification message.
     *                 Returns PEAR_Error object on error.
     */
    function _decryptSignature($text, $params)
    {
        return PEAR::raiseError('_decryptSignature() ' . _("not yet implemented"));
    }

    /**
     * Check for the presence of the OpenSSL extension to PHP.
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

    /**
     * Extract the email address from a public key.
     *
     * @param string $key  The public key.
     *
     * @return mixed Returns the first email address found, or null if
     * there are none.
     */
    function getEmailFromKey($key)
    {
        $key_info = openssl_x509_parse($key);
        if (!is_array($key_info)) {
            return null;
        }

        if (isset($key_info['subject'])) {
            if (isset($key_info['subject']['Email'])) {
                return $key_info['subject']['Email'];
            } elseif (isset($key_info['subject']['emailAddress'])) {
                return $key_info['subject']['emailAddress'];
            }
        }

        // Check subjectAltName per http://www.ietf.org/rfc/rfc3850.txt
        if (isset($key_info['extensions']['subjectAltName'])) {
            $names = preg_split('/\s*,\s*/', $key_info['extensions']['subjectAltName'], -1, PREG_SPLIT_NO_EMPTY);
            foreach ($names as $name) {
                if (strpos($name, ':') === false) {
                    continue;
                }
                list($kind, $value) = explode(':', $name, 2);
                if (String::lower($kind) == 'email') {
                    return $value;
                }
            }
        }

        return null;
    }

    /**
     * Convert a PKCS 12 encrypted certificate package into a private key,
     * public key, and any additional keys.
     *
     * @param string $text   The PKCS 12 data.
     * @param array $params  The parameters needed for parsing.
     * <pre>
     * Parameters:
     * ===========
     * 'sslpath' => The path to the OpenSSL binary. (REQUIRED)
     * 'password' => The password to use to decrypt the data. (Optional)
     * 'newpassword' => The password to use to encrypt the private key.
     *                  (Optional)
     * </pre>
     *
     * @return stdClass  An object.
     *                   'private' -  The private key in PEM format.
     *                   'public'  -  The public key in PEM format.
     *                   'certs'   -  An array of additional certs.
     *                   Returns PEAR_Error on error.
     */
    function parsePKCS12Data($pkcs12, $params)
    {
        /* Check for availability of OpenSSL PHP extension. */
        $openssl = $this->checkForOpenSSL();
        if (is_a($openssl, 'PEAR_Error')) {
            return $openssl;
        }

        if (!isset($params['sslpath'])) {
            return PEAR::raiseError(_("No path to the OpenSSL binary provided. The OpenSSL binary is necessary to work with PKCS 12 data."), 'horde.error');
        }
        $sslpath = escapeshellcmd($params['sslpath']);

        /* Create temp files for input/output. */
        $input = $this->_createTempFile('horde-smime');
        $output = $this->_createTempFile('horde-smime');

        $ob = new stdClass;

        /* Write text to file */
        $fp = fopen($input, 'w+');
        fwrite($fp, $pkcs12);
        fclose($fp);

        /* Extract the private key from the file first. */
        $cmdline = $sslpath . ' pkcs12 -in ' . $input . ' -out ' . $output . ' -nocerts';
        if (isset($params['password'])) {
            $cmdline .= ' -passin stdin';
            if (!empty($params['newpassword'])) {
                $cmdline .= ' -passout stdin';
            } else {
                $cmdline .= ' -nodes';
            }
            $fd = popen($cmdline, 'w');
            fwrite($fd, $params['password'] . "\n");
            if (!empty($params['newpassword'])) {
                fwrite($fd, $params['newpassword'] . "\n");
            }
            pclose($fd);
        } else {
            $cmdline .= ' -nodes';
            exec($cmdline);
        }
        $ob->private = trim(file_get_contents($output));
        if (empty($ob->private)) {
            return PEAR::raiseError(_("Password incorrect"), 'horde.error');
        }

        /* Extract the client public key next. */
        $cmdline = $sslpath . ' pkcs12 -in ' . $input . ' -out ' . $output . ' -nokeys -clcerts';
        if (isset($params['password'])) {
            $cmdline .= ' -passin stdin';
            $fd = popen($cmdline, 'w');
            fwrite($fd, $params['password'] . "\n");
            pclose($fd);
        } else {
            exec($cmdline);
        }
        $ob->public = trim(file_get_contents($output));

        /* Extract the CA public key next. */
        $cmdline = $sslpath . ' pkcs12 -in ' . $input . ' -out ' . $output . ' -nokeys -cacerts';
        if (isset($params['password'])) {
            $cmdline .= ' -passin stdin';
            $fd = popen($cmdline, 'w');
            fwrite($fd, $params['password'] . "\n");
            pclose($fd);
        } else {
            exec($cmdline);
        }
        $ob->certs = trim(file_get_contents($output));

        return $ob;
    }

    /**
     * The Content-Type parameters PHP's openssl_pkcs7_* functions return are
     * deprecated.  Fix these headers to the correct ones (see RFC 2311).
     *
     * @access private
     *
     * @param string $text  The PKCS7 data.
     * @param string $type  Is this 'message' or 'signature' data?
     *
     * @return string  The PKCS7 data with the correct Content-Type parameter.
     */
    function _fixContentType($text, $type)
    {
        if ($type == 'message') {
            $from = 'application/x-pkcs7-mime';
            $to = 'application/pkcs7-mime';
        } else {
            $from = 'application/x-pkcs7-signature';
            $to = 'application/pkcs7-signature';
        }
        return str_replace('Content-Type: ' . $from, 'Content-Type: ' . $to, $text);
    }

}
