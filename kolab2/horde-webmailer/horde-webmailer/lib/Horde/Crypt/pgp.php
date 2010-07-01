<?php

require_once 'Horde/Crypt.php';

/**
 * Armor Header Lines - From RFC 2440
 *
 *  An Armor Header Line consists of the appropriate header line text
 *  surrounded by five (5) dashes ('-', 0x2D) on either side of the header
 *  line text. The header line text is chosen based upon the type of data that
 *  is being encoded in Armor, and how it is being encoded. Header line texts
 *  include the following strings:
 *
 *  All Armor Header Lines are prefixed with 'PGP'.
 *
 *  The Armor Tail Line is composed in the same manner as the Armor Header
 *  Line, except the string "BEGIN" is replaced by the string "END."
 */

/** Used for signed, encrypted, or compressed files. */
define('PGP_ARMOR_MESSAGE', 1);

/** Used for signed files. */
define('PGP_ARMOR_SIGNED_MESSAGE', 2);

/** Used for armoring public keys. */
define('PGP_ARMOR_PUBLIC_KEY', 3);

/** Used for armoring private keys. */
define('PGP_ARMOR_PRIVATE_KEY', 4);

/**
 * Used for detached signatures, PGP/MIME signatures, and natures following
 * clearsigned messages.
 */
define('PGP_ARMOR_SIGNATURE', 5);

/** Regular text contained in an PGP message. */
define('PGP_ARMOR_TEXT', 6);


/** The default public PGP keyserver to use. */
define('PGP_KEYSERVER_PUBLIC', 'pgp.mit.edu');

/**
 * The number of times the keyserver refuses connection before an error is
 * returned.
 */
define('PGP_KEYSERVER_REFUSE', 3);

/**
 * The number of seconds that PHP will attempt to connect to the keyserver
 * before it will stop processing the request.
 */
define('PGP_KEYSERVER_TIMEOUT', 10);


/**
 * Horde_Crypt_pgp:: provides a framework for Horde applications to interact
 * with the GNU Privacy Guard program ("GnuPG").  GnuPG implements the OpenPGP
 * standard (RFC 2440).
 *
 * GnuPG Website: http://www.gnupg.org/
 *
 * This class has been developed with, and is only guaranteed to work with,
 * Version 1.21 or above of GnuPG.
 *
 * $Horde: framework/Crypt/Crypt/pgp.php,v 1.85.2.30 2009-01-06 15:23:00 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @since   Horde 3.0
 * @package Horde_Crypt
 */
class Horde_Crypt_pgp extends Horde_Crypt {

    /**
     * Strings in armor header lines used to distinguish between the different
     * types of PGP decryption/encryption.
     *
     * @var array
     */
    var $_armor = array(
        'MESSAGE'            =>  PGP_ARMOR_MESSAGE,
        'SIGNED MESSAGE'     =>  PGP_ARMOR_SIGNED_MESSAGE,
        'PUBLIC KEY BLOCK'   =>  PGP_ARMOR_PUBLIC_KEY,
        'PRIVATE KEY BLOCK'  =>  PGP_ARMOR_PRIVATE_KEY,
        'SIGNATURE'          =>  PGP_ARMOR_SIGNATURE
    );

    /**
     * The list of PGP hash algorithms (from RFC 3156).
     *
     * @var array
     */
    var $_hashAlg = array(
        1  =>  'pgp-md5',
        2  =>  'pgp-sha1',
        3  =>  'pgp-ripemd160',
        5  =>  'pgp-md2',
        6  =>  'pgp-tiger192',
        7  =>  'pgp-haval-5-160',
        8  =>  'pgp-sha256',
        9  =>  'pgp-sha384',
        10 =>  'pgp-sha512',
        11 =>  'pgp-sha224',
    );

    /**
     * GnuPG program location/common options.
     *
     * @var array
     */
    var $_gnupg;

    /**
     * Filename of the temporary public keyring.
     *
     * @var string
     */
    var $_publicKeyring;

    /**
     * Filename of the temporary private keyring.
     *
     * @var string
     */
    var $_privateKeyring;

    /**
     * The existence of this property indicates that multiple recipient
     * encryption is available.
     *
     * @since Horde 3.1
     *
     * @deprecated
     *
     * @var boolean
     */
    var $multipleRecipientEncryption = true;

    /**
     * Constructor.
     *
     * @param array $params  Parameter array containing the path to the GnuPG
     *                       binary (key = 'program') and to a temporary
     *                       directory.
     */
    function Horde_Crypt_pgp($params = array())
    {
        $this->_tempdir = Util::createTempDir(true, $params['temp']);

        if (empty($params['program'])) {
            Horde::fatal(PEAR::raiseError(_("The location of the GnuPG binary must be given to the Crypt_pgp:: class.")), __FILE__, __LINE__);
        }

        /* Store the location of GnuPG and set common options. */
        $this->_gnupg = array(
            $params['program'],
            '--no-tty',
            '--no-secmem-warning',
            '--no-options',
            '--no-default-keyring',
            '--yes',
            '--homedir ' . $this->_tempdir
        );

        if (strncasecmp(PHP_OS, 'WIN', 3)) {
            array_unshift($this->_gnupg, 'LANG= ;');
        }
    }

    /**
     * Generates a personal Public/Private keypair combination.
     *
     * @param string $realname    The name to use for the key.
     * @param string $email       The email to use for the key.
     * @param string $passphrase  The passphrase to use for the key.
     * @param string $comment     The comment to use for the key.
     * @param integer $keylength  The keylength to use for the key.
     *
     * @return array  An array consisting of the public key and the private
     *                key, or PEAR_Error on error.
     * <pre>
     * Return array:
     * Key            Value
     * --------------------------
     * 'public'   =>  Public Key
     * 'private'  =>  Private Key
     * </pre>
     */
    function generateKey($realname, $email, $passphrase, $comment = '',
                         $keylength = 1024)
    {
        /* Check for secure connection. */
        $secure_check = $this->requireSecureConnection();
        if (is_a($secure_check, 'PEAR_Error')) {
            return $secure_check;
        }

        /* Create temp files to hold the generated keys. */
        $pub_file = $this->_createTempFile('horde-pgp');
        $secret_file = $this->_createTempFile('horde-pgp');

        /* Create the config file necessary for GnuPG to run in batch mode. */
        /* TODO: Sanitize input, More user customizable? */
        $input = array();
        $input[] = '%pubring ' . $pub_file;
        $input[] = '%secring ' . $secret_file;
        $input[] = 'Key-Type: DSA';
        $input[] = 'Key-Length: 1024';
        $input[] = 'Subkey-Type: ELG-E';
        $input[] = 'Subkey-Length: ' . $keylength;
        $input[] = 'Name-Real: ' . $realname;
        if (!empty($comment)) {
            $input[] = 'Name-Comment: ' . $comment;
        }
        $input[] = 'Name-Email: ' . $email;
        $input[] = 'Expire-Date: 0';
        $input[] = 'Passphrase: ' . $passphrase;
        $input[] = '%commit';

        /* Run through gpg binary. */
        $cmdline = array(
            '--gen-key',
            '--batch',
            '--armor'
        );
        $result = $this->_callGpg($cmdline, 'w', $input, true, true);

        /* Get the keys from the temp files. */
        $public_key = file($pub_file);
        $secret_key = file($secret_file);

        /* If either key is empty, something went wrong. */
        if (empty($public_key) || empty($secret_key)) {
            $msg = _("Public/Private keypair not generated successfully.");
            if (!empty($result->stderr)) {
                $msg .= ' ' . _("Returned error message:") . ' ' . $result->stderr;
            }
            return PEAR::raiseError($msg, 'horde.error');
        }

        return array('public' => $public_key, 'private' => $secret_key);
    }

    /**
     * Returns information on a PGP data block.
     *
     * @param string $pgpdata  The PGP data block.
     *
     * @return array  An array with information on the PGP data block. If an
     *                element is not present in the data block, it will
     *                likewise not be set in the array.
     * <pre>
     * Array Format:
     * -------------
     * [public_key]/[secret_key] => Array
     *   (
     *     [created] => Key creation - UNIX timestamp
     *     [expires] => Key expiration - UNIX timestamp (0 = never expires)
     *     [size]    => Size of the key in bits
     *   )
     *
     * [fingerprint] => Fingerprint of the PGP data (if available)
     *                  16-bit hex value (DEPRECATED)
     * [keyid] => Key ID of the PGP data (if available)
     *            16-bit hex value (as of Horde 3.2)
     *
     * [signature] => Array (
     *     [id{n}/'_SIGNATURE'] => Array (
     *         [name]        => Full Name
     *         [comment]     => Comment
     *         [email]       => E-mail Address
     *         [fingerprint] => 16-bit hex value (DEPRECATED)
     *         [keyid]       => 16-bit hex value (as of Horde 3.2)
     *         [created]     => Signature creation - UNIX timestamp
     *         [expires]     => Signature expiration - UNIX timestamp
     *         [micalg]      => The hash used to create the signature
     *         [sig_{hex}]   => Array [details of a sig verifying the ID] (
     *             [created]     => Signature creation - UNIX timestamp
     *             [expires]     => Signature expiration - UNIX timestamp
     *             [fingerprint] => 16-bit hex value (DEPRECATED)
     *             [keyid]       => 16-bit hex value (as of Horde 3.2)
     *             [micalg]      => The hash used to create the signature
     *         )
     *     )
     * )
     * </pre>
     *
     * Each user ID will be stored in the array 'signature' and have data
     * associated with it, including an array for information on each
     * signature that has signed that UID. Signatures not associated with a
     * UID (e.g. revocation signatures and sub keys) will be stored under the
     * special keyword '_SIGNATURE'.
     */
    function pgpPacketInformation($pgpdata)
    {
        $data_array = array();
        $keyid = '';
        $header = null;
        $input = $this->_createTempFile('horde-pgp');
        $sig_id = $uid_idx = 0;

        /* Store message in temporary file. */
        $fp = fopen($input, 'w+');
        fputs($fp, $pgpdata);
        fclose($fp);

        $cmdline = array(
            '--list-packets',
            $input
        );
        $result = $this->_callGpg($cmdline, 'r');

        foreach (explode("\n", $result->stdout) as $line) {
            /* Headers are prefaced with a ':' as the first character on the
               line. */
            if (strpos($line, ':') === 0) {
                $lowerLine = String::lower($line);

                /* If we have a key (rather than a signature block), get the
                   key's ID */
                if (strpos($lowerLine, ':public key packet:') !== false ||
                    strpos($lowerLine, ':secret key packet:') !== false) {
                    $cmdline = array(
                        '--with-colons',
                        $input
                    );
                    $data = $this->_callGpg($cmdline, 'r');
                    if (preg_match("/(sec|pub):.*:.*:.*:([A-F0-9]{16}):/", $data->stdout, $matches)) {
                        $keyid = $matches[2];
                    }
                }

                if (strpos($lowerLine, ':public key packet:') !== false) {
                    $header = 'public_key';
                } elseif (strpos($lowerLine, ':secret key packet:') !== false) {
                    $header = 'secret_key';
                } elseif (strpos($lowerLine, ':user id packet:') !== false) {
                    $uid_idx++;
                    $line = preg_replace_callback('/\\\\x([0-9a-f]{2})/', array($this, '_pgpPacketInformationHelper'), $line);
                    if (preg_match("/\"([^\<]+)\<([^\>]+)\>\"/", $line, $matches)) {
                        $header = 'id' . $uid_idx;
                        if (preg_match('/([^\(]+)\((.+)\)$/', trim($matches[1]), $comment_matches)) {
                            $data_array['signature'][$header]['name'] = trim($comment_matches[1]);
                            $data_array['signature'][$header]['comment'] = $comment_matches[2];
                        } else {
                            $data_array['signature'][$header]['name'] = trim($matches[1]);
                            $data_array['signature'][$header]['comment'] = '';
                        }
                        $data_array['signature'][$header]['email'] = $matches[2];
                        $data_array['signature'][$header]['keyid'] = $keyid;
                        // TODO: Remove in Horde 4
                        $data_array['signature'][$header]['fingerprint'] = $keyid;
                    }
                } elseif (strpos($lowerLine, ':signature packet:') !== false) {
                    if (empty($header) || empty($uid_idx)) {
                        $header = '_SIGNATURE';
                    }
                    if (preg_match("/keyid\s+([0-9A-F]+)/i", $line, $matches)) {
                        $sig_id = $matches[1];
                        $data_array['signature'][$header]['sig_' . $sig_id]['keyid'] = $matches[1];
                        $data_array['keyid'] = $matches[1];
                        // TODO: Remove these 2 entries in Horde 4
                        $data_array['signature'][$header]['sig_' . $sig_id]['fingerprint'] = $matches[1];
                        $data_array['fingerprint'] = $matches[1];
                    }
                } elseif (strpos($lowerLine, ':literal data packet:') !== false) {
                    $header = 'literal';
                } elseif (strpos($lowerLine, ':encrypted data packet:') !== false) {
                    $header = 'encrypted';
                } else {
                    $header = null;
                }
            } else {
                if ($header == 'secret_key' || $header == 'public_key') {
                    if (preg_match("/created\s+(\d+),\s+expires\s+(\d+)/i", $line, $matches)) {
                        $data_array[$header]['created'] = $matches[1];
                        $data_array[$header]['expires'] = $matches[2];
                    } elseif (preg_match("/\s+[sp]key\[0\]:\s+\[(\d+)/i", $line, $matches)) {
                        $data_array[$header]['size'] = $matches[1];
                    }
                } elseif ($header == 'literal' || $header == 'encrypted') {
                    $data_array[$header] = true;
                } elseif ($header) {
                    if (preg_match("/version\s+\d+,\s+created\s+(\d+)/i", $line, $matches)) {
                        $data_array['signature'][$header]['sig_' . $sig_id]['created'] = $matches[1];
                    } elseif (isset($data_array['signature'][$header]['sig_' . $sig_id]['created']) &&
                              preg_match('/expires after (\d+y\d+d\d+h\d+m)\)$/', $line, $matches)) {
                        $expires = $matches[1];
                        preg_match('/^(\d+)y(\d+)d(\d+)h(\d+)m$/', $expires, $matches);
                        list(, $years, $days, $hours, $minutes) = $matches;
                        $data_array['signature'][$header]['sig_' . $sig_id]['expires'] =
                            strtotime('+ ' . $years . ' years + ' . $days . ' days + ' . $hours . ' hours + ' . $minutes . ' minutes', $data_array['signature'][$header]['sig_' . $sig_id]['created']);
                    } elseif (preg_match("/digest algo\s+(\d{1})/", $line, $matches)) {
                        $micalg = $this->_hashAlg[$matches[1]];
                        $data_array['signature'][$header]['sig_' . $sig_id]['micalg'] = $micalg;
                        if ($header == '_SIGNATURE') {
                            /* Likely a signature block, not a key. */
                            $data_array['signature']['_SIGNATURE']['micalg'] = $micalg;
                        }
                        if ($sig_id == $keyid) {
                            /* Self signing signature - we can assume
                             * the micalg value from this signature is
                             * that for the key */
                            $data_array['signature']['_SIGNATURE']['micalg'] = $micalg;
                            $data_array['signature'][$header]['micalg'] = $micalg;
                        }
                    }
                }
            }
        }

        $keyid && $data_array['keyid'] = $keyid;
        // TODO: Remove for Horde 4
        $keyid && $data_array['fingerprint'] = $keyid;

        return $data_array;
    }

    function _pgpPacketInformationHelper($a)
    {
        return chr(hexdec($a[1]));
    }

    /**
     * Returns human readable information on a PGP key.
     *
     * @param string $pgpdata  The PGP data block.
     *
     * @return string  Tabular information on the PGP key.
     */
    function pgpPrettyKey($pgpdata)
    {
        $msg = '';
        $packet_info = $this->pgpPacketInformation($pgpdata);
        $fingerprints = $this->getFingerprintsFromKey($pgpdata);

        if (!empty($packet_info['signature'])) {
            /* Making the property names the same width for all
             * localizations .*/
            $leftrow = array(_("Name"), _("Key Type"), _("Key Creation"),
                             _("Expiration Date"), _("Key Length"),
                             _("Comment"), _("E-Mail"), _("Hash-Algorithm"),
                             _("Key ID"), _("Key Fingerprint"));
            $leftwidth = array_map('strlen', $leftrow);
            $maxwidth  = max($leftwidth) + 2;
            array_walk($leftrow, array($this, '_pgpPrettyKeyFormatter'), $maxwidth);

            foreach (array_keys($packet_info['signature']) as $uid_idx) {
                if ($uid_idx == '_SIGNATURE') {
                    continue;
                }
                $key_info = $this->pgpPacketSignatureByUidIndex($pgpdata, $uid_idx);

                if (!empty($key_info['keyid'])) {
                    $key_info['keyid'] = $this->_getKeyIDString($key_info['keyid']);
                } else {
                    $key_info['keyid'] = null;
                }

                $fingerprint = isset($fingerprints[$key_info['keyid']]) ? $fingerprints[$key_info['keyid']] : null;

                $msg .= $leftrow[0] . (isset($key_info['name']) ? stripcslashes($key_info['name']) : '') . "\n"
                    . $leftrow[1] . (($key_info['key_type'] == 'public_key') ? _("Public Key") : _("Private Key")) . "\n"
                    . $leftrow[2] . strftime("%D", $key_info['key_created']) . "\n"
                    . $leftrow[3] . (empty($key_info['key_expires']) ? '[' . _("Never") . ']' : strftime("%D", $key_info['key_expires'])) . "\n"
                    . $leftrow[4] . $key_info['key_size'] . " Bytes\n"
                    . $leftrow[5] . (empty($key_info['comment']) ? '[' . _("None") . ']' : $key_info['comment']) . "\n"
                    . $leftrow[6] . (empty($key_info['email']) ? '[' . _("None") . ']' : $key_info['email']) . "\n"
                    . $leftrow[7] . (empty($key_info['micalg']) ? '[' . _("Unknown") . ']' : $key_info['micalg']) . "\n"
                    . $leftrow[8] . (empty($key_info['keyid']) ? '[' . _("Unknown") . ']' : $key_info['keyid']) . "\n"
                    . $leftrow[9] . (empty($fingerprint) ? '[' . _("Unknown") . ']' : $fingerprint) . "\n\n";
            }
        }

        return $msg;
    }

    function _pgpPrettyKeyFormatter(&$s, $k, $m)
    {
        $s .= ':' . str_repeat(' ', $m - String::length($s));
    }

    function _getKeyIDString($keyid)
    {
        /* Get the 8 character key ID string. */
        if (strpos($keyid, '0x') === 0) {
            $keyid = substr($keyid, 2);
        }
        if (strlen($keyid) > 8) {
            $keyid = substr($keyid, -8);
        }
        return '0x' . $keyid;
    }

    /**
     * Returns only information on the first ID that matches the email address
     * input.
     *
     * @param string $pgpdata  The PGP data block.
     * @param string $email    An e-mail address.
     *
     * @return array  An array with information on the PGP data block. If an
     *                element is not present in the data block, it will
     *                likewise not be set in the array.
     * <pre>
     * Array Fields:
     * -------------
     * key_created  =>  Key creation - UNIX timestamp
     * key_expires  =>  Key expiration - UNIX timestamp (0 = never expires)
     * key_size     =>  Size of the key in bits
     * key_type     =>  The key type (public_key or secret_key)
     * name         =>  Full Name
     * comment      =>  Comment
     * email        =>  E-mail Address
     * fingerprint  =>  16-bit hex value (DEPRECATED)
     * keyid        =>  16-bit hex value
     * created      =>  Signature creation - UNIX timestamp
     * micalg       =>  The hash used to create the signature
     * </pre>
     */
    function pgpPacketSignature($pgpdata, $email)
    {
        $data = $this->pgpPacketInformation($pgpdata);
        $key_type = null;
        $return_array = array();

        /* Check that [signature] key exists. */
        if (!isset($data['signature'])) {
            return $return_array;
        }

        /* Store the signature information now. */
        if (($email == '_SIGNATURE') &&
            isset($data['signature']['_SIGNATURE'])) {
            foreach ($data['signature'][$email] as $key => $value) {
                $return_array[$key] = $value;
            }
        } else {
            $uid_idx = 1;

            while (isset($data['signature']['id' . $uid_idx])) {
                if ($data['signature']['id' . $uid_idx]['email'] == $email) {
                    foreach ($data['signature']['id' . $uid_idx] as $key => $val) {
                        $return_array[$key] = $val;
                    }
                    break;
                }
                $uid_idx++;
            }
        }

        return $this->_pgpPacketSignature($data, $return_array);
    }

    /**
     * Returns information on a PGP signature embedded in PGP data.  Similar
     * to pgpPacketSignature(), but returns information by unique User ID
     * Index (format id{n} where n is an integer of 1 or greater).
     *
     * @param string $pgpdata  See pgpPacketSignature().
     * @param string $uid_idx  The UID index.
     *
     * @return array  See pgpPacketSignature().
     */
    function pgpPacketSignatureByUidIndex($pgpdata, $uid_idx)
    {
        $data = $this->pgpPacketInformation($pgpdata);
        $key_type = null;
        $return_array = array();

        /* Search for the UID index. */
        if (!isset($data['signature']) ||
            !isset($data['signature'][$uid_idx])) {
            return $return_array;
        }

        /* Store the signature information now. */
        foreach ($data['signature'][$uid_idx] as $key => $value) {
            $return_array[$key] = $value;
        }

        return $this->_pgpPacketSignature($data, $return_array);
    }

    /**
     * Adds some data to the pgpPacketSignature*() function array.
     *
     * @access private
     *
     * @param array $data      See pgpPacketSignature().
     * @param array $retarray  The return array.
     *
     * @return array  The return array.
     */
    function _pgpPacketSignature($data, $retarray)
    {
        /* If empty, return now. */
        if (empty($retarray)) {
            return $retarray;
        }

        $key_type = null;

        /* Store any public/private key information. */
        if (isset($data['public_key'])) {
            $key_type = 'public_key';
        } elseif (isset($data['secret_key'])) {
            $key_type = 'secret_key';
        }

        if ($key_type) {
            $retarray['key_type'] = $key_type;
            if (isset($data[$key_type]['created'])) {
                $retarray['key_created'] = $data[$key_type]['created'];
            }
            if (isset($data[$key_type]['expires'])) {
                $retarray['key_expires'] = $data[$key_type]['expires'];
            }
            if (isset($data[$key_type]['size'])) {
                $retarray['key_size'] = $data[$key_type]['size'];
            }
        }

        return $retarray;
    }

    /**
     * Returns the short fingerprint (Key ID) of the key used to sign a block
     * of PGP data.
     *
     * @deprecated Use getSignersKeyID() instead.
     * @todo Remove for Horde 4
     *
     * @param string $text  The PGP signed text block.
     *
     * @return string  The short fingerprint of the key used to sign $text.
     */
    function getSignersFingerprint($text)
    {
        return $this->getSignersKeyID($text);
    }

    /**
     * Returns the key ID of the key used to sign a block of PGP data.
     *
     * @since Horde 3.2
     *
     * @param string $text  The PGP signed text block.
     *
     * @return string  The key ID of the key used to sign $text.
     */
    function getSignersKeyID($text)
    {
        $keyid = null;

        $input = $this->_createTempFile('horde-pgp');

        $fp = fopen($input, 'w+');
        fputs($fp, $text);
        fclose($fp);

        $cmdline = array(
            '--verify',
            $input
        );
        $result = $this->_callGpg($cmdline, 'r', null, true, true);
        if (preg_match('/gpg:\sSignature\smade.*ID\s+([A-F0-9]{8})\s+/', $result->stderr, $matches)) {
            $keyid = $matches[1];
        }

        return $keyid;
    }

    /**
     * Verify a passphrase for a given public/private keypair.
     *
     * @param string $public_key   The user's PGP public key.
     * @param string $private_key  The user's PGP private key.
     * @param string $passphrase   The user's passphrase.
     *
     * @return boolean  Returns true on valid passphrase, false on invalid
     *                  passphrase, and PEAR_Error on error.
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
     * Parses a message into text and PGP components.
     *
     * @param string $text  The text to parse.
     *
     * @return array  An array with the parsed text, returned in blocks of
     *                text corresponding to their actual order.
     * <pre>
     * Return array:
     * Key         Value
     * -------------------------------------------------
     * 'type'  =>  The type of data contained in block.
     *             Valid types are defined at the top of this class
     *             (the PGP_ARMOR_* constants).
     * 'data'  =>  The actual data for each section.
     * </pre>
     */
    function parsePGPData($text)
    {
        $data = array();

        $buffer = explode("\n", $text);

        /* Set $temp_array to be of type PGP_ARMOR_TEXT. */
        $temp_array = array();
        $temp_array['type'] = PGP_ARMOR_TEXT;

        foreach ($buffer as $value) {
            if (preg_match('/^-----(BEGIN|END) PGP ([^-]+)-----\s*$/', $value, $matches)) {
                if (isset($temp_array['data'])) {
                    $data[] = $temp_array;
                }
                unset($temp_array);
                $temp_array = array();

                if ($matches[1] === 'BEGIN') {
                    $temp_array['type'] = $this->_armor[$matches[2]];
                    $temp_array['data'][] = $value;
                } elseif ($matches[1] === 'END') {
                    $temp_array['type'] = PGP_ARMOR_TEXT;
                    $data[count($data) - 1]['data'][] = $value;
                }
            } else {
                $temp_array['data'][] = $value;
            }
        }

        if (isset($temp_array['data'])) {
            $data[] = $temp_array;
        }

        return $data;
    }

    /**
     * Returns a PGP public key from a public keyserver.
     *
     * @param string $keyid    The key ID of the PGP key.
     * @param string $server   The keyserver to use.
     * @param float $timeout   The keyserver timeout.
     * @param string $address  The email address of the PGP key. @since
     *                         Horde 3.2.
     *
     * @return string  The PGP public key, or PEAR_Error on error.
     */
    function getPublicKeyserver($keyid, $server = PGP_KEYSERVER_PUBLIC,
                                $timeout = PGP_KEYSERVER_TIMEOUT,
                                $address = null)
    {
        if (empty($keyid) && !empty($address)) {
            $keyid = $this->getKeyID($address, $server, $timeout);
            if (is_a($keyid, 'PEAR_Error')) {
                return $keyid;
            }
        }

        /* Connect to the public keyserver. */
        $uri = '/pks/lookup?op=get&search=' . $this->_getKeyIDString($keyid);
        $output = $this->_connectKeyserver('GET', $server, $uri, '', $timeout);
        if (is_a($output, 'PEAR_Error')) {
            return $output;
        }

        /* Strip HTML Tags from output. */
        if (($start = strstr($output, '-----BEGIN'))) {
            $length = strpos($start, '-----END') + 34;
            return substr($start, 0, $length);
        } else {
            return PEAR::raiseError(_("Could not obtain public key from the keyserver."), 'horde.error');
        }
    }

    /**
     * Sends a PGP public key to a public keyserver.
     *
     * @param string $pubkey  The PGP public key
     * @param string $server  The keyserver to use.
     * @param float $timeout  The keyserver timeout.
     *
     * @return PEAR_Error  PEAR_Error on error/failure.
     */
    function putPublicKeyserver($pubkey, $server = PGP_KEYSERVER_PUBLIC,
                                $timeout = PGP_KEYSERVER_TIMEOUT)
    {
        /* Get the key ID of the public key. */
        $info = $this->pgpPacketInformation($pubkey);

        /* See if the public key already exists on the keyserver. */
        if (!is_a($this->getPublicKeyserver($info['keyid'], $server, $timeout), 'PEAR_Error')) {
            return PEAR::raiseError(_("Key already exists on the public keyserver."), 'horde.warning');
        }

        /* Connect to the public keyserver. _connectKeyserver()
         * returns a PEAR_Error object on error and the output text on
         * success. */
        $pubkey = 'keytext=' . urlencode(rtrim($pubkey));
        $cmd = array(
            'Host: ' . $server . ':11371',
            'User-Agent: Horde Application Framework 3.2',
            'Content-Type: application/x-www-form-urlencoded',
            'Content-Length: ' . strlen($pubkey),
            'Connection: close',
            '',
            $pubkey
        );

        $result = $this->_connectKeyserver('POST', $server, '/pks/add', implode("\r\n", $cmd), $timeout);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
    }

    /**
     * Returns the first matching key ID for an email address from a
     * public keyserver.
     *
     * @since Horde 3.2
     *
     * @param string $address  The email address of the PGP key.
     * @param string $server   The keyserver to use.
     * @param float $timeout   The keyserver timeout.
     *
     * @return string  The PGP key ID, or PEAR_Error on error.
     */
    function getKeyID($address, $server = PGP_KEYSERVER_PUBLIC,
                      $timeout = PGP_KEYSERVER_TIMEOUT)
    {
        /* Connect to the public keyserver. */
        $uri = '/pks/lookup?op=index&options=mr&search=' . urlencode($address);
        $output = $this->_connectKeyserver('GET', $server, $uri, '', $timeout);
        if (is_a($output, 'PEAR_Error')) {
            return $output;
        }

        if (($start = strstr($output, '-----BEGIN PGP PUBLIC KEY BLOCK'))) {
            /* The server returned the matching key immediately. */
            $length = strpos($start, '-----END PGP PUBLIC KEY BLOCK') + 34;
            $info = $this->pgpPacketInformation(substr($start, 0, $length));
            if (!empty($info['keyid']) &&
                (empty($info['public_key']['expires']) ||
                 $info['public_key']['expires'] > time())) {
                return $info['keyid'];
            }
        } elseif (strpos($output, 'pub:') !== false) {
            $output = explode("\n", $output);
            $keyids = array();
            foreach ($output as $line) {
                if (substr($line, 0, 4) == 'pub:') {
                    $line = explode(':', $line);
                    /* Ignore invalid lines and expired keys. */
                    if (count($line) != 7 ||
                        (!empty($line[5]) && $line[5] <= time())) {
                        continue;
                    }
                    $keyids[$line[4]] = $line[1];
                }
            }
            /* Sort by timestamp to use the newest key. */
            if (count($keyids)) {
                ksort($keyids);
                return array_pop($keyids);
            }
        }

        return PEAR::raiseError(_("Could not obtain public key from the keyserver."));
    }

    /**
     * Get the fingerprints from a key block.
     *
     * @param string $pgpdata  The PGP data block.
     *
     * @return array The fingerprints in $pgpdata indexed by key id.
     */
    function getFingerprintsFromKey($pgpdata)
    {
        $fingerprints = array();

        /* Store the key in a temporary keyring. */
        $keyring = $this->_putInKeyring($pgpdata);

        /* Options for the GPG binary. */
        $cmdline = array(
            '--fingerprint',
            $keyring,
        );

        $result = $this->_callGpg($cmdline, 'r');
        if (!$result || !$result->stdout) {
            return $fingerprints;
        }

        /* Parse fingerprints and key ids from output. */
        $lines = explode("\n", $result->stdout);
        $keyid = null;
        foreach ($lines as $line) {
            if (preg_match('/pub\s+\w+\/(\w{8})/', $line, $matches)) {
                $keyid = '0x' . $matches[1];
            } elseif ($keyid && preg_match('/^\s+[\s\w]+=\s*([\w\s]+)$/m', $line, $matches)) {
                $fingerprints[$keyid] = trim($matches[1]);
                $keyid = null;
            }
        }

        return $fingerprints;
    }

    /**
     * Connects to a public key server via HKP (Horrowitz Keyserver Protocol).
     *
     * @access private
     *
     * @param string $method   POST, GET, etc.
     * @param string $server   The keyserver to use.
     * @param string $uri      The URI to access (relative to the server).
     * @param string $command  The PGP command to run.
     * @param float $timeout   The timeout value.
     *
     * @return string  The text from standard output on success, or PEAR_Error
     *                 on error/failure.
     */
    function _connectKeyserver($method, $server, $resource, $command, $timeout)
    {
        $connRefuse = 0;
        $output = '';

        $port = '11371';
        if (!empty($GLOBALS['conf']['http']['proxy']['proxy_host'])) {
            $resource = 'http://' . $server . ':' . $port . $resource;

            $server = $GLOBALS['conf']['http']['proxy']['proxy_host'];
            if (!empty($GLOBALS['conf']['http']['proxy']['proxy_port'])) {
                $port = $GLOBALS['conf']['http']['proxy']['proxy_port'];
            } else {
                $port = 80;
            }
        }

        $command = $method . ' ' . $resource . ' HTTP/1.0' . ($command ? "\r\n" . $command : '');

        /* Attempt to get the key from the keyserver. */
        do {
            $connError = false;
            $errno = $errstr = null;

            /* The HKP server is located on port 11371. */
            $fp = @fsockopen($server, $port, $errno, $errstr, $timeout);
            if (!$fp) {
                $connError = true;
            } else {
                fputs($fp, $command . "\n\n");
                while (!feof($fp)) {
                    $output .= fgets($fp, 1024);
                }
                fclose($fp);
            }

            if ($connError) {
                if (++$connRefuse === PGP_KEYSERVER_REFUSE) {
                    if ($errno == 0) {
                        $output = PEAR::raiseError(_("Connection refused to the public keyserver."), 'horde.error');
                    } else {
                        $output = PEAR::raiseError(sprintf(_("Connection refused to the public keyserver. Reason: %s (%s)"), String::convertCharset($errstr, NLS::getExternalCharset()), $errno), 'horde.error');
                    }
                    break;
                }
            }
        } while ($connError);

        return $output;
    }

    /**
     * Encrypts text using PGP.
     *
     * @param string $text   The text to be PGP encrypted.
     * @param array $params  The parameters needed for encryption.
     *                       See the individual _encrypt*() functions for the
     *                       parameter requirements.
     *
     * @return string  The encrypted message, or PEAR_Error on error.
     */
    function encrypt($text, $params = array())
    {
        if (isset($params['type'])) {
            if ($params['type'] === 'message') {
                return $this->_encryptMessage($text, $params);
            } elseif ($params['type'] === 'signature') {
                return $this->_encryptSignature($text, $params);
            }
        }
    }

    /**
     * Decrypts text using PGP.
     *
     * @param string $text   The text to be PGP decrypted.
     * @param array $params  The parameters needed for decryption.
     *                       See the individual _decrypt*() functions for the
     *                       parameter requirements.
     *
     * @return string  The decrypted message, or PEAR_Error on error.
     */
    function decrypt($text, $params = array())
    {
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
     * Returns whether a text has been encrypted symmetrically.
     *
     * @since Horde 3.2
     *
     * @param string $text  The PGP encrypted text.
     *
     * @return boolean  True if the text is symmetricallly encrypted.
     */
    function encryptedSymmetrically($text)
    {
        $cmdline = array(
            '--decrypt',
            '--batch'
        );
        $result = $this->_callGpg($cmdline, 'w', $text, true, true, true);
        return strpos($result->stderr, 'gpg: encrypted with 1 passphrase') !== false;
    }

    /**
     * Creates a temporary gpg keyring.
     *
     * @access private
     *
     * @param string $type  The type of key to analyze. Either 'public'
     *                      (Default) or 'private'
     *
     * @return string  Command line keystring option to use with gpg program.
     */
    function _createKeyring($type = 'public')
    {
        $type = String::lower($type);

        if ($type === 'public') {
            if (empty($this->_publicKeyring)) {
                $this->_publicKeyring = $this->_createTempFile('horde-pgp');
            }
            return '--keyring ' . $this->_publicKeyring;
        } elseif ($type === 'private') {
            if (empty($this->_privateKeyring)) {
                $this->_privateKeyring = $this->_createTempFile('horde-pgp');
            }
            return '--secret-keyring ' . $this->_privateKeyring;
        }
    }

    /**
     * Adds PGP keys to the keyring.
     *
     * @access private
     *
     * @param mixed $keys   A single key or an array of key(s) to add to the
     *                      keyring.
     * @param string $type  The type of key(s) to add. Either 'public'
     *                      (Default) or 'private'
     *
     * @return string  Command line keystring option to use with gpg program.
     */
    function _putInKeyring($keys = array(), $type = 'public')
    {
        $type = String::lower($type);

        if (!is_array($keys)) {
            $keys = array($keys);
        }

        /* Create the keyrings if they don't already exist. */
        $keyring = $this->_createKeyring($type);

        /* Store the key(s) in the keyring. */
        $cmdline = array(
            '--allow-secret-key-import',
            '--fast-import',
            $keyring
        );
        $this->_callGpg($cmdline, 'w', array_values($keys));

        return $keyring;
    }

    /**
     * Encrypts a message in PGP format using a public key.
     *
     * @access private
     *
     * @param string $text   The text to be encrypted.
     * @param array $params  The parameters needed for encryption.
     * <pre>
     * Parameters:
     * ===========
     * 'type'       => 'message' (REQUIRED)
     * 'symmetric'  => Whether to use symmetric instead of asymmetric
     *                 encryption (defaults to false)
     * 'recips'     => An array with the e-mail address of the recipient as
     *                 the key and that person's public key as the value.
     *                 (REQUIRED if 'symmetric' is false)
     * 'passphrase' => The passphrase for the symmetric encryption (REQUIRED if
     *                 'symmetric' is true)
     * 'pubkey'     => PGP public key. (Optional) (DEPRECATED)
     * 'email'      => E-mail address of recipient. If not present, or not
     *                 found in the public key, the first e-mail address found
     *                 in the key will be used instead. (Optional) (DEPRECATED)
     * </pre>
     *
     * @return string  The encrypted message, or PEAR_Error on error.
     */
    function _encryptMessage($text, $params)
    {
        $email = null;

        if (empty($params['symmetric']) && !isset($params['recips'])) {
            /* Check for required parameters. */
            if (!isset($params['pubkey'])) {
                return PEAR::raiseError(_("A public PGP key is required to encrypt a message."), 'horde.error');
            }

            /* Get information on the key. */
            if (isset($params['email'])) {
                $key_info = $this->pgpPacketSignature($params['pubkey'], $params['email']);
                if (!empty($key_info)) {
                    $email = $key_info['email'];
                }
            }

            /* If we have no email address at this point, use the first email
               address found in the public key. */
            if (empty($email)) {
                $key_info = $this->pgpPacketInformation($params['pubkey']);
                if (isset($key_info['signature']['id1']['email'])) {
                    $email = $key_info['signature']['id1']['email'];
                } else {
                    return PEAR::raiseError(_("Could not determine the recipient's e-mail address."), 'horde.error');
                }
            }

            $params['recips'] = array($email => $params['pubkey']);
        }

        /* Create temp files for input. */
        $input = $this->_createTempFile('horde-pgp');
        $fp = fopen($input, 'w+');
        fputs($fp, $text);
        fclose($fp);

        /* Build command line. */
        $cmdline = array(
            '--armor',
            '--batch',
            '--always-trust'
        );
        if (empty($params['symmetric'])) {
            /* Store public key in temporary keyring. */
            $keyring = $this->_putInKeyring(array_values($params['recips']));

            $cmdline[] = $keyring;
            $cmdline[] = '--encrypt';
            foreach (array_keys($params['recips']) as $val) {
                $cmdline[] = '--recipient ' . $val;
            }
        } else {
            $cmdline[] = '--symmetric';
            $cmdline[] = '--passphrase-fd 0';
        }
        $cmdline[] = $input;

        /* Encrypt the document. */
        $result = $this->_callGpg($cmdline, 'w', empty($params['symmetric']) ? null : $params['passphrase'], true, true);
        if (empty($result->output)) {
            $error = preg_replace('/\n.*/', '', $result->stderr);
            return PEAR::raiseError(_("Could not PGP encrypt message: ") . $error, 'horde.error');
        }

        return $result->output;
    }

    /**
     * Signs a message in PGP format using a private key.
     *
     * @access private
     *
     * @param string $text   The text to be signed.
     * @param array $params  The parameters needed for signing.
     * <pre>
     * Parameters:
     * ===========
     * 'type'        =>  'signature' (REQUIRED)
     * 'pubkey'      =>  PGP public key. (REQUIRED)
     * 'privkey'     =>  PGP private key. (REQUIRED)
     * 'passphrase'  =>  Passphrase for PGP Key. (REQUIRED)
     * 'sigtype'     =>  Determine the signature type to use. (Optional)
     *                   'cleartext'  --  Make a clear text signature
     *                   'detach'     --  Make a detached signature (DEFAULT)
     * </pre>
     *
     * @return string  The signed message, or PEAR_Error on error.
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
            !isset($params['passphrase'])) {
            return PEAR::raiseError(_("A public PGP key, private PGP key, and passphrase are required to sign a message."), 'horde.error');
        }

        /* Create temp files for input. */
        $input = $this->_createTempFile('horde-pgp');

        /* Encryption requires both keyrings. */
        $pub_keyring = $this->_putInKeyring(array($params['pubkey']));
        $sec_keyring = $this->_putInKeyring(array($params['privkey']), 'private');

        /* Store message in temporary file. */
        $fp = fopen($input, 'w+');
        fputs($fp, $text);
        fclose($fp);

        /* Determine the signature type to use. */
        $cmdline = array();
        if (isset($params['sigtype']) &&
            $params['sigtype'] == 'cleartext') {
            $sign_type = '--clearsign';
        } else {
            $sign_type = '--detach-sign';
        }

        /* Additional GPG options. */
        $cmdline += array(
            '--armor',
            '--batch',
            '--passphrase-fd 0',
            $sec_keyring,
            $pub_keyring,
            $sign_type,
            $input
        );

        /* Sign the document. */
        $result = $this->_callGpg($cmdline, 'w', $params['passphrase'], true, true);
        if (empty($result->output)) {
            $error = preg_replace('/\n.*/', '', $result->stderr);
            return PEAR::raiseError(_("Could not PGP sign message: ") . $error, 'horde.error');
        } else {
            return $result->output;
        }
    }

    /**
     * Decrypts an PGP encrypted message using a private/public keypair and a
     * passhprase.
     *
     * @access private
     *
     * @param string $text   The text to be decrypted.
     * @param array $params  The parameters needed for decryption.
     * <pre>
     * Parameters:
     * ===========
     * 'type'        =>  'message' (REQUIRED)
     * 'pubkey'      =>  PGP public key. (REQUIRED for asymmetric encryption)
     * 'privkey'     =>  PGP private key. (REQUIRED for asymmetric encryption)
     * 'passphrase'  =>  Passphrase for PGP Key. (REQUIRED)
     * </pre>
     *
     * @return stdClass  An object with the following properties, or PEAR_Error
     *                   on error:
     * <pre>
     * 'message'     -  The decrypted message.
     * 'sig_result'  -  The result of the signature test.
     * </pre>
     */
    function _decryptMessage($text, $params)
    {
        /* Check for secure connection. */
        $secure_check = $this->requireSecureConnection();
        if (is_a($secure_check, 'PEAR_Error')) {
            return $secure_check;
        }

        $good_sig_flag = false;

        /* Check for required parameters. */
        if (!isset($params['passphrase']) && empty($params['no_passphrase'])) {
            return PEAR::raiseError(_("A passphrase is required to decrypt a message."), 'horde.error');
        }

        /* Create temp files. */
        $input = $this->_createTempFile('horde-pgp');

        /* Store message in file. */
        $fp = fopen($input, 'w+');
        fputs($fp, $text);
        fclose($fp);

        /* Build command line. */
        $cmdline = array(
            '--always-trust',
            '--armor',
            '--batch'
        );
        if (empty($param['no_passphrase'])) {
            $cmdline[] = '--passphrase-fd 0';
        }
        if (!empty($params['pubkey']) && !empty($params['privkey'])) {
            /* Decryption requires both keyrings. */
            $pub_keyring = $this->_putInKeyring(array($params['pubkey']));
            $sec_keyring = $this->_putInKeyring(array($params['privkey']), 'private');
            $cmdline[] = $sec_keyring;
            $cmdline[] = $pub_keyring;
        }
        $cmdline[] = '--decrypt';
        $cmdline[] = $input;

        /* Decrypt the document now. */
        if (empty($params['no_passphrase'])) {
            $result = $this->_callGpg($cmdline, 'w', $params['passphrase'], true, true);
        } else {
            $result = $this->_callGpg($cmdline, 'r', null, true, true);
        }
        if (empty($result->output)) {
            $error = preg_replace('/\n.*/', '', $result->stderr);
            return PEAR::raiseError(_("Could not decrypt PGP data: ") . $error, 'horde.error');
        }

        /* Create the return object. */
        $ob = new stdClass;
        $ob->message = $result->output;

        /* Check the PGP signature. */
        $sig_check = $this->_checkSignatureResult($result->stderr);
        if (is_a($sig_check, 'PEAR_Error')) {
            $ob->sig_result = $sig_check;
        } else {
            $ob->sig_result = ($sig_check) ? $result->stderr : '';
        }

        return $ob;
    }

    /**
     * Decrypts an PGP signed message using a public key.
     *
     * @access private
     *
     * @param string $text   The text to be verified.
     * @param array $params  The parameters needed for verification.
     * <pre>
     * Parameters:
     * ===========
     * 'type'       =>  'signature' or 'detached-signature' (REQUIRED)
     * 'pubkey'     =>  PGP public key. (REQUIRED)
     * 'signature'  =>  PGP signature block. (REQUIRED for detached signature)
     * </pre>
     *
     * @return string  The verification message from gpg. If no signature,
     *                 returns empty string, and PEAR_Error on error.
     */
    function _decryptSignature($text, $params)
    {
        /* Check for required parameters. */
        if (!isset($params['pubkey'])) {
            return PEAR::raiseError(_("A public PGP key is required to verify a signed message."), 'horde.error');
        }
        if (($params['type'] === 'detached-signature') &&
            !isset($params['signature'])) {
            return PEAR::raiseError(_("The detached PGP signature block is required to verify the signed message."), 'horde.error');
        }

        $good_sig_flag = 0;

        /* Create temp files for input. */
        $input = $this->_createTempFile('horde-pgp');

        /* Store public key in temporary keyring. */
        $keyring = $this->_putInKeyring($params['pubkey']);

        /* Store the message in a temporary file. */
        $fp = fopen($input, 'w+');
        fputs($fp, $text);
        fclose($fp);

        /* Options for the GPG binary. */
        $cmdline = array(
            '--armor',
            '--always-trust',
            '--batch',
            '--charset ' . NLS::getCharset(),
            $keyring,
            '--verify'
        );

        /* Extra stuff to do if we are using a detached signature. */
        if ($params['type'] === 'detached-signature') {
            $sigfile = $this->_createTempFile('horde-pgp');
            $cmdline[] = $sigfile . ' ' . $input;

            $fp = fopen($sigfile, 'w+');
            fputs($fp, $params['signature']);
            fclose($fp);
        } else {
            $cmdline[] = $input;
        }

        /* Verify the signature.  We need to catch standard error output,
         * since this is where the signature information is sent. */
        $result = $this->_callGpg($cmdline, 'r', null, true, true);
        $sig_result = $this->_checkSignatureResult($result->stderr);
        if (is_a($sig_result, 'PEAR_Error')) {
            return $sig_result;
        } else {
            return ($sig_result) ? $result->stderr : '';
        }
    }

    /**
     * Checks signature result from the GnuPG binary.
     *
     * @access private
     *
     * @param string $result  The signature result.
     *
     * @return boolean  True if signature is good.
     */
    function _checkSignatureResult($result)
    {
        /* Good signature:
         *   gpg: Good signature from "blah blah blah (Comment)"
         * Bad signature:
         *   gpg: BAD signature from "blah blah blah (Comment)" */
        if (strpos($result, 'gpg: BAD signature') !== false) {
            return PEAR::raiseError($result, 'horde.error');
        } elseif (strpos($result, 'gpg: Good signature') !== false) {
            return true;
        } else {
            return false;
        }
    }

    /**
     * Signs a MIME_Part using PGP.
     *
     * @param MIME_Part $mime_part  The MIME_Part object to sign.
     * @param array $params         The parameters required for signing.
     *                              @see _encryptSignature().
     *
     * @return MIME_Part  A MIME_Part object that is signed according to RFC
     *                    2015/3156, or PEAR_Error on error.
     */
    function signMIMEPart($mime_part, $params = array())
    {
        include_once 'Horde/MIME/Part.php';

        $params = array_merge($params, array('type' => 'signature', 'sigtype' => 'detach'));

        /* RFC 2015 Requirements for a PGP signed message:
         * + Content-Type params 'micalg' & 'protocol' are REQUIRED.
         * + The digitally signed message MUST be constrained to 7 bits.
         * + The MIME headers MUST be a part of the signed data. */

        $mime_part->strict7bit(true);
        $msg_sign = $this->encrypt($mime_part->toCanonicalString(), $params);
        if (is_a($msg_sign, 'PEAR_Error')) {
            return $msg_sign;
        }

        /* Add the PGP signature. */
        $charset = NLS::getEmailCharset();
        $pgp_sign = new MIME_Part('application/pgp-signature', $msg_sign, $charset, 'inline');
        $pgp_sign->setDescription(String::convertCharset(_("PGP Digital Signature"), NLS::getCharset(), $charset));

        /* Get the algorithim information from the signature. Since we are
         * analyzing a signature packet, we need to use the special keyword
         * '_SIGNATURE' - see Horde_Crypt_pgp. */
        $sig_info = $this->pgpPacketSignature($msg_sign, '_SIGNATURE');

        /* Setup the multipart MIME Part. */
        $part = new MIME_Part('multipart/signed');
        $part->setContents('This message is in MIME format and has been PGP signed.' . "\n");
        $part->addPart($mime_part);
        $part->addPart($pgp_sign);
        $part->setContentTypeParameter('protocol', 'application/pgp-signature');
        $part->setContentTypeParameter('micalg', $sig_info['micalg']);

        return $part;
    }

    /**
     * Encrypts a MIME_Part using PGP.
     *
     * @param MIME_Part $mime_part  The MIME_Part object to encrypt.
     * @param array $params         The parameters required for encryption.
     *                              @see _encryptMessage().
     *
     * @return MIME_Part  A MIME_Part object that is encrypted according to RFC
     *                    2015/3156, or PEAR_Error on error.
     */
    function encryptMIMEPart($mime_part, $params = array())
    {
        include_once 'Horde/MIME/Part.php';

        $params = array_merge($params, array('type' => 'message'));

        $signenc_body = $mime_part->toCanonicalString();
        $message_encrypt = $this->encrypt($signenc_body, $params);
        if (is_a($message_encrypt, 'PEAR_Error')) {
            return $message_encrypt;
        }

        /* Set up MIME Structure according to RFC 2015. */
        $charset = NLS::getEmailCharset();
        $part = new MIME_Part('multipart/encrypted', null, $charset);
        $part->setContents('This message is in MIME format and has been PGP encrypted.' . "\n");
        $part->addPart(new MIME_Part('application/pgp-encrypted', "Version: 1\n", null));
        $part->addPart(new MIME_Part('application/octet-stream', $message_encrypt, null, 'inline'));
        $part->setContentTypeParameter('protocol', 'application/pgp-encrypted');
        $part->setDescription(String::convertCharset(_("PGP Encrypted Data"), NLS::getCharset(), $charset));

        return $part;
    }

    /**
     * Signs and encrypts a MIME_Part using PGP.
     *
     * @param MIME_Part $mime_part   The MIME_Part object to sign and encrypt.
     * @param array $sign_params     The parameters required for signing.
     *                               @see _encryptSignature().
     * @param array $encrypt_params  The parameters required for encryption.
     *                               @see _encryptMessage().
     *
     * @return MIME_Part  A MIME_Part object that is signed and encrypted
     *                    according to RFC 2015/3156, or PEAR_Error on error.
     */
    function signAndEncryptMIMEPart($mime_part, $sign_params = array(),
                                    $encrypt_params = array())
    {
        include_once 'Horde/MIME/Part.php';

        /* RFC 2015 requires that the entire signed message be encrypted.  We
         * need to explicitly call using Horde_Crypt_pgp:: because we don't
         * know whether a subclass has extended these methods. */
        $part = $this->signMIMEPart($mime_part, $sign_params);
        if (is_a($part, 'PEAR_Error')) {
            return $part;
        }
        $part = $this->encryptMIMEPart($part, $encrypt_params);
        if (is_a($part, 'PEAR_Error')) {
            return $part;
        }
        $part->setContents('This message is in MIME format and has been PGP signed and encrypted.' . "\n");

        $charset = NLS::getEmailCharset();
        $part->setCharset($charset);
        $part->setDescription(String::convertCharset(_("PGP Signed/Encrypted Data"), NLS::getCharset(), $charset));

        return $part;
    }

    /**
     * Generates a MIME_Part object, in accordance with RFC 2015/3156, that
     * contains a public key.
     *
     * @param string $key  The public key.
     *
     * @return MIME_Part  A MIME_Part object that contains the public key.
     */
    function publicKeyMIMEPart($key)
    {
        include_once 'Horde/MIME/Part.php';

        $charset = NLS::getEmailCharset();
        $part = new MIME_Part('application/pgp-keys', $key, $charset);
        $part->setDescription(String::convertCharset(_("PGP Public Key"), NLS::getCharset(), $charset));

        return $part;
    }

    /**
     * Function that handles interfacing with the GnuPG binary.
     *
     * @access private
     *
     * @param array $options   Options and commands to pass to GnuPG.
     * @param string $mode     'r' to read from stdout, 'w' to write to stdin.
     * @param array $input     Input to write to stdin.
     * @param boolean $output  If true, collect and store output in object returned.
     * @param boolean $stderr  If true, collect and store stderr in object returned.
     * @param boolean $verbose If true, run GnuPG with quiet flag.
     *
     * @return stdClass  Class with members output, stderr, and stdout.
     */
    function _callGpg($options, $mode, $input = array(), $output = false,
                      $stderr = false, $verbose = false)
    {
        $data = new stdClass;
        $data->output = null;
        $data->stderr = null;
        $data->stdout = null;

        /* Verbose output? */
        if (!$verbose) {
            array_unshift($options, '--quiet');
        }

        /* Create temp files for output. */
        if ($output) {
            $output_file = $this->_createTempFile('horde-pgp', false);
            array_unshift($options, '--output ' . $output_file);

            /* Do we need standard error output? */
            if ($stderr) {
                $stderr_file = $this->_createTempFile('horde-pgp', false);
                $options[] = '2> ' . $stderr_file;
            }
        }

        /* Silence errors if not requested. */
        if (!$output || !$stderr) {
            $options[] = '2> /dev/null';
        }

        /* Build the command line string now. */
        $cmdline = implode(' ', array_merge($this->_gnupg, $options));

        if ($mode == 'w') {
            $fp = popen($cmdline, 'w');
            $win32 = !strncasecmp(PHP_OS, 'WIN', 3);

            if (!is_array($input)) {
                $input = array($input);
            }
            foreach ($input as $line) {
                if ($win32 && (strpos($line, "\x0d\x0a") !== false)) {
                    $chunks = explode("\x0d\x0a", $line);
                    foreach ($chunks as $chunk) {
                        fputs($fp, $chunk . "\n");
                    }
                } else {
                    fputs($fp, $line . "\n");
                }
            }
        } elseif ($mode == 'r') {
            $fp = popen($cmdline, 'r');
            while (!feof($fp)) {
                $data->stdout .= fgets($fp, 1024);
            }
        }
        pclose($fp);

        if ($output) {
            $data->output = file_get_contents($output_file);
            unlink($output_file);
            if ($stderr) {
                $data->stderr = file_get_contents($stderr_file);
                unlink($stderr_file);
            }
        }

        return $data;
    }

    /**
     * Generates a revocation certificate.
     *
     * @since Horde 3.2
     *
     * @param string $key         The private key.
     * @param string $email       The email to use for the key.
     * @param string $passphrase  The passphrase to use for the key.
     *
     * @return string  The revocation certificate, or PEAR_Error on error.
     */
    function generateRevocation($key, $email, $passphrase)
    {
        $keyring = $this->_putInKeyring($key, 'private');

        /* Prepare the canned answers. */
        $input = array();
        $input[] = 'y'; // Really generate a revocation certificate
        $input[] = '0'; // Refuse to specify a reason
        $input[] = '';  // Empty comment
        $input[] = 'y'; // Confirm empty comment
        if (!empty($passphrase)) {
            $input[] = $passphrase;
        }

        /* Run through gpg binary. */
        $cmdline = array(
            $keyring,
            '--command-fd 0',
            '--gen-revoke' . ' ' . $email,
        );
        $results = $this->_callGpg($cmdline, 'w', $input, true);

        /* If the key is empty, something went wrong. */
        if (empty($results->output)) {
            return PEAR::raiseError(_("Revocation key not generated successfully."), 'horde.error');
        }

        return $results->output;
    }

}
