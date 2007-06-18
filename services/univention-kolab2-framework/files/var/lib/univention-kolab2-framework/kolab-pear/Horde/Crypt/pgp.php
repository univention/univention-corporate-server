<?php

require_once 'Horde/Crypt.php';

/* Armor Header Lines - From RFC 2440

   An Armor Header Line consists of the appropriate header line text
   surrounded by five (5) dashes ('-', 0x2D) on either side of the
   header line text. The header line text is chosen based upon the
   type of data that is being encoded in Armor, and how it is being
   encoded. Header line texts include the following strings:

   All Armor Header Lines are prefixed with 'PGP'.

   The Armor Tail Line is composed in the same manner as the Armor
   Header Line, except the string "BEGIN" is replaced by the string
   "END." */

/** @constant PGP_ARMOR_MESSAGE Used for signed, encrypted, or compressed files. */
define('PGP_ARMOR_MESSAGE', 1);

/** @constant PGP_ARMOR_SIGNED_MESSAGE Used for signed files. */
define('PGP_ARMOR_SIGNED_MESSAGE', 2);

/** @constant PGP_ARMOR_PUBLIC_KEY Used for armoring public keys. */
define('PGP_ARMOR_PUBLIC_KEY', 3);

/** @constant PGP_ARMOR_PRIVATE_KEY Used for armoring private keys. */
define('PGP_ARMOR_PRIVATE_KEY', 4);

/** @constant PGP_ARMOR_SIGNATURE Used for detached signatures, PGP/MIME signatures, and natures following clearsigned messages. */
define('PGP_ARMOR_SIGNATURE', 5);

/** @constant PGP_ARMOR_TEXT Regular text contained in an PGP message. */
define('PGP_ARMOR_TEXT', 6);


/** @constant PGP_PUBLIC_KEYSERVER The default public PGP keyserver to use. */
define('PGP_KEYSERVER_PUBLIC', 'wwwkeys.pgp.net');

/** @constant PGP_KEYSERVER_REFUSE The number of times the keyserver refuses connection before an error is returned. */
define('PGP_KEYSERVER_REFUSE', 3);

/** @constant PGP_KEYSERVER_TIMEOUT The number of seconds that PHP will attempt to connect to the keyserver before it will stop processing the request. */
define('PGP_KEYSERVER_TIMEOUT', 10);


/**
 * Horde_Crypt_pgp:: provides a framework for Horde applications to
 * interact with the GNU Privacy Guard program ("GnuPG").  GnuPG implements
 * the OpenPGP standard (RFC 2440).
 *
 * GnuPG Website: http://www.gnupg.org/
 *
 * This class has been developed with, and is only guaranteed to work with,
 * Version 1.21 or above of GnuPG.
 *
 * $Horde: framework/Crypt/Crypt/pgp.php,v 1.71 2004/04/29 20:07:31 slusarz Exp $
 *
 * Copyright 2002-2004 Michael Slusarz <slusarz@bigworm.colorado.edu>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Slusarz <slusarz@bigworm.colorado.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Crypt
 */
class Horde_Crypt_pgp extends Horde_Crypt {

    /**
     * Strings in armor header lines used to distinguish between the
     * different types of PGP decryption/encryption.
     *
     * @var array $_armor
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
     * @var array $_hashAlg
     */
    var $_hashAlg = array(
        1  =>  'pgp-md5',
        2  =>  'pgp-sha1',
        3  =>  'pgp-ripemd160',
        5  =>  'pgp-md2',
        6  =>  'pgp-tiger192',
        7  =>  'pgp-hava1-5-160'
    );

    /**
     * GnuPG program location/common options.
     *
     * @var array $_gnupg
     */
    var $_gnupg;

    /**
     * Filename of the temporary public keyring.
     *
     * @var string $_publicKeyring
     */
    var $_publicKeyring;

    /**
     * Filename of the temporary private keyring.
     *
     * @var string $_privateKeyring
     */
    var $_privateKeyring;


    /**
     * Constructor.
     *
     * @access public
     *
     * @param array $params  Parameter array containing the path to the GnuPG
     *                       binary (key = 'program') and to a temporary
     *                       directory.
     */
    function Horde_Crypt_pgp($params = array())
    {
        $this->_tempdir = Util::createTempDir(true, $params['temp']);

        if (empty($params['program'])) {
            Horde::fatal(new PEAR_Error(_("The location of the GnuPG binary must be given to the Crypt_pgp:: class.")), __FILE__, __LINE__);
        }

        /* Store the location of GnuPG and set common options. */
        $this->_gnupg = array(
            'LANG= ;',
            $params['program'],
            '--no-tty',
            '--no-secmem-warning',
            '--no-options',
            '--no-default-keyring',
            '--quiet',
            '--yes',
            '--homedir ' . $this->_tempdir
        );
    }

    /**
     * Generate a personal Public/Private keypair combination.
     *
     * @access public
     *
     * @param string $realname             The name to use for the key.
     * @param string $email                The email to use for the key.
     * @param string $passphrase           The passphrase to use for the key.
     * @param optional string $comment     The comment to use for the key.
     * @param optional integer $keylength  The keylength to use for the key.
     *
     * @return array  An array consisting of the public key and the private
     *                key.
     *                Returns PEAR_Error object on error.
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
        $input[] = "%pubring " . $pub_file;
        $input[] = "%secring " . $secret_file;
        $input[] = "Key-Type: DSA";
        $input[] = "Key-Length: " . $keylength;
        $input[] = "Subkey-Type: ELG-E";
        $input[] = "Subkey-Length: " . $keylength;
        $input[] = "Name-Real: " . $realname;
        if (!empty($comment)) {
            $input[] = "Name-Comment: " . $comment;
        }
        $input[] = "Name-Email: " . $email;
        $input[] = "Expire-Date: 0";
        $input[] = "Passphrase: " . $passphrase;
        $input[] = "%commit";

        /* Run through gpg binary. */
        $cmdline = array(
            '--gen-key',
            '--batch',
            '--armor'
        );
        $this->_callGpg($cmdline, 'w', $input);

        /* Get the keys from the temp files. */
        $public_key = file($pub_file);
        $secret_key = file($secret_file);

        /* If either key is empty, something went wrong. */
        if (empty($public_key) || empty($secret_key)) {
            return PEAR::raiseError(_("Public/Private keypair not generated successfully."), 'horde.error');
        }

        return array('public' => $public_key, 'private' => $secret_key);
    }

    /**
     * Return information on a PGP data block.
     *
     * @access public
     *
     * @param string $pgpdata  The PGP data block.
     *
     * @return array  An array with information on the PGP data block.
     *                If an element is not present in the data block,
     *                it will likewise not be set in the array.
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
     *                  16-bit hex value
     *
     * [signature] => Array (
     *     [id{n}/'_SIGNATURE'] => Array (
     *         [name]        => Full Name
     *         [comment]     => Comment
     *         [email]       => E-mail Address
     *         [fingerprint] => 16-bit hex value
     *         [created]     => Signature creation - UNIX timestamp
     *         [micalg]      => The hash used to create the signature
     *         [sig_{hex}]   => Array [details of a sig verifying the ID] (
     *             [created]     => Signature creation - UNIX timestamp
     *             [fingerprint] => 16-bit hex value
     *             [micalg]      => The hash used to create the signature
     *         )
     *     )
     * )
     *
     * Each user ID will be stored in the array 'signature' and have data
     * associated with it, including an array for information on each
     * signature that has signed that UID. Signatures not associated with
     * a UID (e.g. revocation signatures and sub keys) will be stored under
     * the special keyword '_SIGNATURE'.
     * </pre>
     */
    function pgpPacketInformation($pgpdata)
    {
        $data_array = array();
        $fingerprint = '';
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
            /* Headers are prefaced with a ':' as the first character
               on the line. */
            if (strpos($line, ':') === 0) {
                /* If we have a key (rather than a signature block), get the
                   key's fingerprint */
                if (stristr($line, ':public key packet:') ||
                    stristr($line, ':secret key packet:')) {
                    $cmdline = array(
                        '--with-colons',
                        $input
                    );
                    $data = $this->_callGpg($cmdline, 'r');
                    if (preg_match("/(sec|pub):.*:.*:.*:([A-F0-9]{16}):/", $data->stdout, $matches)) {
                        $fingerprint = $matches[2];
                    }
                }

                if (stristr($line, ':public key packet:')) {
                    $header = 'public_key';
                } elseif (stristr($line, ':secret key packet:')) {
                    $header = 'secret_key';
                } elseif (stristr($line, ':user ID packet:')) {
                    $uid_idx++;
                    $line = preg_replace_callback('/\\\\x([0-9a-f]{2})/', create_function('$a', 'return chr(hexdec($a[1]));'), $line);
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
                        $data_array['signature'][$header]['fingerprint'] = $fingerprint;
                    }
                } elseif (stristr($line, ':signature packet:')) {
                    if (empty($header) || empty($uid_idx)) {
                        $header = '_SIGNATURE';
                    }
                    if (preg_match("/keyid\s+([0-9A-F]+)/i", $line, $matches)) {
                        $sig_id = $matches[1];
                        $data_array['signature'][$header]['sig_' . $sig_id]['fingerprint'] = $matches[1];
                        $data_array['fingerprint'] = $matches[1];
                    }
                } else {
                    $header = null;
                }
            } else {
                if (($header == 'secret_key') || ($header == 'public_key')) {
                    if (preg_match("/created\s+(\d+),\s+expires\s+(\d+)/i", $line, $matches)) {
                        $data_array[$header]['created'] = $matches[1];
                        $data_array[$header]['expires'] = $matches[2];
                    } elseif (preg_match("/\s+[sp]key\[0\]:\s+\[(\d+)/i", $line, $matches)) {
                        $data_array[$header]['size'] = $matches[1];
                    }
                } elseif ($header) {
                    if (preg_match("/version\s+\d+,\s+created\s+(\d+)/i", $line, $matches)) {
                        $data_array['signature'][$header]['sig_' . $sig_id]['created'] = $matches[1];
                    } elseif (preg_match("/digest algo\s+(\d{1})/", $line, $matches)) {
                        $micalg = $this->_hashAlg[$matches[1]];
                        $data_array['signature'][$header]['sig_' . $sig_id]['micalg'] = $micalg;
                        if ($header == '_SIGNATURE') {
                            /* Likely a signature block, not a key. */
                            $data_array['signature']['_SIGNATURE']['micalg'] = $micalg;
                        }
                        if ($sig_id == $fingerprint){
                            /* Self signing signature - we can assume the
                               micalg value from this signature is that for
                               the key */
                            $data_array['signature']['_SIGNATURE']['micalg'] = $micalg;
                            $data_array['signature'][$header]['micalg'] = $micalg;
                        }
                    }
                }
            }
        }

        $fingerprint && $data_array['fingerprint'] = $fingerprint;

        return $data_array;
    }

    /**
     * Returns human readable information on a PGP key.
     *
     * @access public
     *
     * @param string $pgpdata  The PGP data block.
     *
     * @return string  Tabular information on the PGP key.
     */
    function pgpPrettyKey($pgpdata)
    {
        $msg = '';
        $packet_info = $this->pgpPacketInformation($pgpdata);

        if (!empty($packet_info)) {

            /* Making the property names the same width for all localizations .*/
            $leftrow = array(_("Name"), _("Key Type"), _("Key Creation"),
                             _("Expiration Date"), _("Key Length"),
                             _("Comment"), _("E-Mail"), _("Hash-Algorithm"),
                             _("Key Fingerprint"));
            $leftwidth = array_map('strlen', $leftrow);
            $maxwidth  = max($leftwidth) + 2;
            array_walk($leftrow, create_function('&$s, $k, $m', '$s = $s . ":" . str_repeat(" ", $m - String::length($s));'), $maxwidth);

            foreach (array_keys($packet_info['signature']) as $uid_idx) {
                if ($uid_idx == '_SIGNATURE') continue;
                $key_info = $this->pgpPacketSignatureByUidIndex($pgpdata, $uid_idx);
                $msg .= $leftrow[0] . stripcslashes($key_info['name']) . "\n";
                $msg .= $leftrow[1] . (($key_info['key_type'] == 'public_key') ? _("Public Key") : _("Private Key")) . "\n";
                $msg .= $leftrow[2] . strftime("%D", $key_info['key_created']) . "\n";
                $msg .= $leftrow[3] . (empty($key_info['key_expires']) ? '[' . _("Never") . ']' : strftime("%D", $key_info['key_expires'])) . "\n";
                $msg .= $leftrow[4] . $key_info['key_size'] . " Bytes\n";
                $msg .= $leftrow[5] . (empty($key_info['comment']) ? '[' . _("None") . ']' : $key_info['comment']) . "\n";
                $msg .= $leftrow[6] . $key_info['email'] . "\n";
                $msg .= $leftrow[7] . (empty($key_info['micalg']) ? '[' . _("Unknown") . ']' : $key_info['micalg']) . "\n";
                $msg .= $leftrow[8] . (empty($key_info['fingerprint']) ? '[' . _("Unknown") . ']' : $key_info['fingerprint']) . "\n\n";
            }
        }

        return $msg;
    }

    /**
     * Returns only information on the first ID that matches the email
     * address input.
     *
     * @access public
     *
     * @param string $pgpdata  The PGP data block.
     * @param string $email    An e-mail address.
     *
     * @return array  An array with information on the PGP data block.
     *                If an element is not present in the data block,
     *                it will likewise not be set in the array.
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
     * fingerprint  =>  16-bit hex value
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
        if (!array_key_exists('signature', $data)) {
            return $return_array;
        }

        /* Store the signature information now. */
        if (($email == '_SIGNATURE') &&
            array_key_exists('_SIGNATURE', $data['signature'])) {
            foreach ($data['signature'][$email] as $key => $value) {
                $return_array[$key] = $value;
            }
        } else {
            $uid_idx = 1;

            while (array_key_exists ('id' . $uid_idx, $data['signature'])){
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
     * Return information on a PGP signature embedded in PGP data.
     * Similar to pgpPacketSignature(), but returns information by
     * unique User ID Index (format id{n} where n is an integer of
     * 1 or greater).
     *
     * @access public
     *
     * @param string $pgpdata   See pgpPacketSignature().
     * @param integer $uid_idx  The UID index.
     *
     * @return array  See pgpPacketSignature().
     */
    function pgpPacketSignatureByUidIndex($pgpdata, $uid_idx)
    {
        $data = $this->pgpPacketInformation($pgpdata);
        $key_type = null;
        $return_array = array();

        /* Search for the UID index. */
        if (!array_key_exists('signature', $data) ||
            !array_key_exists($uid_idx, $data['signature'])) {
            return $return_array;
        }

        /* Store the signature information now. */
        foreach ($data['signature'][$uid_idx] as $key => $value) {
            $return_array[$key] = $value;
        }

        return $this->_pgpPacketSignature($data, $return_array);
    }

    /**
     * Add some data to the pgpPacketSignature*() function array.
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
        if (empty($retarray)){
            return $retarray;
        }

        $key_type = null;

        /* Store any public/private key information. */
        if (array_key_exists('public_key', $data)) {
            $key_type = 'public_key';
        } elseif (array_key_exists('secret_key', $data)) {
            $key_type = 'secret_key';
        }

        if (!is_null($key_type)) {
            $retarray['key_type'] = $key_type;
            if (array_key_exists('created', $data[$key_type])) {
                $retarray['key_created'] = $data[$key_type]['created'];
            }
            if (array_key_exists('expires', $data[$key_type])) {
                $retarray['key_expires'] = $data[$key_type]['expires'];
            }
            if (array_key_exists('size', $data[$key_type])) {
                $retarray['key_size'] = $data[$key_type]['size'];
            }
        }

        return $retarray;
    }

    /**
     * Gets the short fingerprint (Key ID) of the key used to sign a
     * block of PGP data.
     *
     * @access public
     *
     * @param string $text  The PGP signed text block.
     *
     * @return string   The short fingerprint of the key used to sign $text.
     */
    function getSignersFingerprint($text)
    {
        $fingerprint = null;

        $input = $this->_createTempFile('horde-pgp');

        $fp = fopen($input, 'w+');
        fputs($fp, $text);
        fclose($fp);

        $cmdline = array(
            '--verify',
            $input,
            '2>&1'
        );
        $result = $this->_callGpg($cmdline, 'r');
        if (preg_match("/gpg:\sSignature\smade.*ID\s+([A-F0-9]{8})\s+/", $result->stdout, $matches)) {
            $fingerprint = $matches[1];
        }

        return $fingerprint;
    }

    /**
     * Verify a passphrase for a given public/private keypair.
     *
     * @access public
     *
     * @param string $public_key   The user's PGP public key.
     * @param string $private_key  The user's PGP private key.
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
     * Parse a message into text and PGP components.
     *
     * @access public
     *
     * @param string $text  The text to parse.
     *
     * @return array  An array with the parsed text, returned in blocks of
     *                text corresponding to their actual order.
     * <pre>
     * Return array:
     * Key       Value
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
            if (preg_match("/^-----(BEGIN|END) PGP ([^-]+)-----\s*$/", $value, $matches)) {
                if (array_key_exists('data', $temp_array)) {
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

        if (array_key_exists('data', $temp_array)) {
            $data[] = $temp_array;
        }

        return $data;
    }

    /**
     * Get a PGP public key from a public keyserver.
     *
     * @access public
     *
     * @param string $fprint           The fingerprint of the PGP key.
     * @param optional string $server  The keyserver to use.
     * @param optional float $timeout  The keyserver timeout.
     *
     * @return string  The PGP public key.
     *                 Returns PEAR_Error object on error/failure.
     */
    function getPublicKeyserver($fprint, $server = PGP_KEYSERVER_PUBLIC,
                                $timeout = PGP_KEYSERVER_TIMEOUT)
    {
        /* Get the 8 character fingerprint string. */
        if (strpos($fprint, '0x') === 0) {
            $fprint = substr($fprint, 2);
        }
        if (strlen($fprint) > 8) {
            $fprint = substr($fprint, 8);
        }
        $fprint = '0x' . $fprint;

        /* Connect to the public keyserver. */
        $cmd = 'GET /pks/lookup?op=get&exact=on&search=' . $fprint . ' HTTP/1.0';
        $output = $this->_connectKeyserver($cmd, $server, $timeout);
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
     * @access public
     *
     * @param string $pubkey           The PGP public key
     * @param optional string $server  The keyserver to use.
     * @param optional float $timeout  The keyserver timeout.
     *
     * @return object PEAR_Error  Returns PEAR_Error object on error/failure.
     */
    function putPublicKeyserver($pubkey, $server = PGP_KEYSERVER_PUBLIC,
                                $timeout = PGP_KEYSERVER_TIMEOUT)
    {
        /* Get the fingerprint of the public key. */
        $info = $this->pgpPacketInformation($pubkey);

        /* See if the public key already exists on the keyserver. */
        if (!is_a($this->getPublicKeyserver($info['fingerprint'], $server, $timeout), 'PEAR_Error')) {
            return PEAR::raiseError(_("Key already exists on the public keyserver."), 'horde.warning');
        }

        /* Connect to the public keyserver. _connectKeyserver() returns a
           PEAR_Error object on error and the output text on success. */
        $pubkey = 'keytext=' . urlencode(rtrim($pubkey));
        $cmd = "POST /pks/add HTTP/1.0\nContent-Length: " . strlen($pubkey) . "\n\n" . $pubkey . "\n";
        $result = $this->_connectKeyserver($cmd, $server, $timeout);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
    }

    /**
     * Connect to a public key server via HKP (Horrowitz Keyserver Protocol).
     *
     * @access private
     *
     * @param string $command  The PGP command to run.
     * @param string $server   The keyserver to use.
     * @param float $timeout   The timeout value.
     *
     * @return mixed  Returns the text from standard output on success.
     *                Returns PEAR_Error object on error/failure.
     */
    function _connectKeyserver($command, $server, $timeout)
    {
        $connRefuse = 0;
        $output = '';

        /* Attempt to get the key from the keyserver. */
        do {
            $connError = false;
            $errno = $errstr = null;

            /* The HKP server is located on port 11371. */
            $fp = @fsockopen($server, '11371', $errno, $errstr, $timeout);
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
                    $output = PEAR::raiseError(sprintf(_("Connection refused to the public keyserver. Reason: %s (%s)"), String::convertCharset($errstr, NLS::getCharset(true)), $errno), 'horde.error');
                    break;
                }
            }
        } while ($connError);

        return $output;
    }

    /**
     * Encrypt text using PGP.
     *
     * @access public
     *
     * @param string $text   The text to be PGP encrypted.
     * @param array $params  The parameters needed for encryption.
     *                       See the individual _encrypt*() functions for
     *                       the parameter requirements.
     *
     * @return string  The encrypted message.
     *                 Returns PEAR_Error object on error.
     */
    function encrypt($text, $params = array())
    {
        if (array_key_exists('type', $params)) {
            if ($params['type'] === 'message') {
                return $this->_encryptMessage($text, $params);
            } elseif ($params['type'] === 'signature') {
                return $this->_encryptSignature($text, $params);
            }
        }
    }

    /**
     * Decrypt text using PGP.
     *
     * @access public
     *
     * @param string $text   The text to be PGP decrypted.
     * @param array $params  The parameters needed for decryption.
     *                       See the individual _decrypt*() functions for
     *                       the parameter requirements.
     *
     * @return string  The decrypted message.
     *                 Returns PEAR_Error object on error.
     */
    function decrypt($text, $params = array())
    {
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
     * Creates a temporary gpg keyring.
     *
     * @access private
     *
     * @param optional string $type  The type of key to analyze.
     *                               Either 'public' (Default) or 'private'
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
     * Add PGP keys to the keyring.
     *
     * @access private
     *
     * @param mixed $keys            A single key or an array of key(s) to
     *                               add to the keyring.
     * @param optional string $type  The type of key(s) to add.
     *                               Either 'public' (Default) or 'private'
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
     * Encrypt a message in PGP format using a public key.
     *
     * @access private
     *
     * @param string $text   The text to be encrypted.
     * @param array $params  The parameters needed for encryption.
     * <pre>
     * Parameters:
     * ===========
     * 'type'    =>  'message' (REQUIRED)
     * 'pubkey'  =>  PGP public key. (REQUIRED)
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
            return PEAR::raiseError(_("A public PGP key is required to encrypt a message."), 'horde.error');
        }

        /* Get information on the key. */
        if (array_key_exists('email', $params)) {
            $key_info = $this->pgpPacketSignature($params['pubkey'], $params['email']);
            if (!empty($key_info)) {
                $email = $key_info['email'];
            }
        }

        /* If we have no email address at this point, use the first email
           address found in the public key. */
        if (empty($email)) {
            $key_info = $this->pgpPacketInformation($params['pubkey']);
            if (array_key_exists('signature', $key_info)) {
                $email = $key_info['signature']['id1']['email'];
            } else {
                return PEAR::raiseError(_("Could not determine the recipient's e-mail address."), 'horde.error');
            }
        }

        /* Store public key in temporary keyring. */
        $keyring = $this->_putInKeyring($params['pubkey']);

        /* Encrypt the document. */
        $cmdline = array(
            '--armor',
            '--batch',
            '--always-trust',
            '--recipient ' . $email,
            $keyring,
            '--encrypt'
        );
        $result = $this->_callGpg($cmdline, 'w', $text, true);
        if (empty($result->output)) {
            return PEAR::raiseError(_("Could not PGP encrypt message."), 'horde.error');
        }

        return $result->output;
    }

    /**
     * Sign a message in PGP format using a private key.
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
        if (array_key_exists('sigtype', $params) &&
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
        $result = $this->_callGpg($cmdline, 'w', $params['passphrase'], true);
        if (empty($result->output)) {
            return PEAR::raiseError(_("Could not PGP sign message."), 'horde.error');
        } else {
            return $result->output;
        }
    }

    /**
     * Decrypt an PGP encrypted message using a private/public keypair
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
     * 'pubkey'      =>  PGP public key. (REQUIRED)
     * 'privkey'     =>  PGP private key. (REQUIRED)
     * 'passphrase'  =>  Passphrase for PGP Key. (REQUIRED)
     * </pre>
     *
     * @return object stdClass  An object.
     *                          'message'     -  The decrypted message.
     *                          'sig_result'  -  The result of the signature
     *                                           test.
     *                          Returns PEAR_Error object on error.
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
        if (!isset($params['pubkey']) ||
            !isset($params['privkey']) ||
            !isset($params['passphrase'])) {
            return PEAR::raiseError(_("A public PGP key, private PGP key, and passphrase are required to decrypt a message."), 'horde.error');
        }

        /* Create temp files. */
        $input = $this->_createTempFile('horde-pgp');

        /* Decryption requires both keyrings. */
        $pub_keyring = $this->_putInKeyring(array($params['pubkey']));
        $sec_keyring = $this->_putInKeyring(array($params['privkey']), 'private');

        /* Store message in file. */
        $fp = fopen($input, 'w+');
        fputs($fp, $text);
        fclose($fp);

        /* Decrypt the document now. */
        $cmdline = array(
            '--always-trust',
            '--armor',
            '--batch',
            '--passphrase-fd 0', 
            $sec_keyring,
            $pub_keyring,
            '--decrypt',
            $input
        );
        $result = $this->_callGpg($cmdline, 'w', $params['passphrase'], true, true);
        if (empty($result->output)) {
            return PEAR::raiseError(_("Could not decrypt PGP data."), 'horde.error');
        }

        /* Create the return object. */
        $ob = &new stdClass;
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
     * Decrypt an PGP signed message using a public key.
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
     * @return string  The verification message from gpg.
     *                 If no signature, returns empty string.
     *                 Returns PEAR_Error object on error.
     */
    function _decryptSignature($text, $params)
    {
        /* Check for required parameters. */
        if (!array_key_exists('pubkey', $params)) {
            return PEAR::raiseError(_("A public PGP key is required to verify a signed message."), 'horde.error');
        }
        if (($params['type'] === 'detached-signature') &&
            !array_key_exists('signature', $params)) {
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
        $cmdline[] = '2>&1';

        /* Verify the signature.
           We need to catch standard error output, since this is where
           the signature information is sent. */
        $result = $this->_callGpg($cmdline, 'r');
        $sig_result = $this->_checkSignatureResult($result->stdout);
        if (is_a($sig_result, 'PEAR_Error')) {
            return $sig_result;
        } else {
            return ($sig_result) ? $result->stdout : '';
        }
    }

    /**
     * Check signature result from the GnuPG binary.
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
             gpg: Good signature from "blah blah blah (Comment)"
           Bad signature:
             gpg: BAD signature from "blah blah blah (Comment)" */
        if (strstr($result, 'gpg: BAD signature')) {
            return PEAR::raiseError($result, 'horde.error');
        } elseif (strstr($result, 'gpg: Good signature')) {
            return true;
        } else {
            return false;
        }
    }

    /**
     * Sign a MIME_Part using PGP.
     *
     * @access public
     *
     * @param object MIME_Part $mime_part  The MIME_Part object to sign.
     * @param array $params                The parameters required for
     *                                     signing.
     *                                     See _encryptSignature().
     *
     * @return object MIME_Part  A MIME_Part object that is signed according
     *                           to RFC 2015/3156.
     *                           Returns PEAR_Error object on error.
     */
    function signMIMEPart($mime_part, $params = array())
    {
        include_once 'Horde/MIME/Part.php';

        $params = array_merge($params, array('type' => 'signature', 'sigtype' => 'detach'));

        /* RFC 2015 Requirements for a PGP signed message:
           + Content-Type params 'micalg' & 'protocol' are REQUIRED.
           + The digitally signed message MUST be constrained to 7 bits.
           + The MIME headers MUST be a part of the signed data. */

        $mime_part->strict7bit(true);
        $msg_sign = $this->encrypt($mime_part->toCanonicalString(), $params);
        if (is_a($msg_sign, 'PEAR_Error')) {
            return $msg_sign;
        }

        /* Add the PGP signature. */
        $pgp_sign = &new MIME_Part('application/pgp-signature', $msg_sign, null, 'inline');
        $pgp_sign->setDescription(_("PGP Digital Signature"));

        /* Get the algorithim information from the signature. Since we are
           analyzing a signature packet, we need to use the special keyword
           '_SIGNATURE' - see Horde_Crypt_pgp. */
        $sig_info = $this->pgpPacketSignature($msg_sign, '_SIGNATURE');

        /* Setup the multipart MIME Part. */
        $part = &new MIME_Part('multipart/signed');
        $part->setContents('This message is in MIME format and has been PGP signed.' . "\n");
        $part->addPart($mime_part);
        $part->addPart($pgp_sign);
        $part->setContentTypeParameter('protocol', 'application/pgp-signature');
        $part->setContentTypeParameter('micalg', $sig_info['micalg']);

        return $part;
    }

    /**
     * Encrypt a MIME_Part using PGP.
     *
     * @access public
     *
     * @param object MIME_Part $mime_part  The MIME_Part object to encrypt.
     * @param array $params                The parameters required for
     *                                     encryption. See _encryptMessage().
     *
     * @return object MIME_Part  A MIME_Part object that is encrypted
     *                           according to RFC 2015/3156.
     *                           Returns PEAR_Error on error.
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
        $part = &new MIME_Part('multipart/encrypted');
        $part->setContents('This message is in MIME format and has been PGP encrypted.' . "\n");
        $part->addPart(new MIME_Part('application/pgp-encrypted', "Version: 1\n", null));
        $part->addPart(new MIME_Part('application/octet-stream', $message_encrypt, null, 'inline'));
        $part->setContentTypeParameter('protocol', 'application/pgp-encrypted');
        $part->setDescription(_("PGP Encrypted Data"));

        return $part;
    }

    /**
     * Sign and Encrypt a MIME_Part using PGP.
     *
     * @access public
     *
     * @param object MIME_Part $mime_part  The MIME_Part object to sign and
     *                                     encrypt.
     * @param array $sign_params           The parameters required for
     *                                     signing. See _encryptSignature().
     * @param array $encrypt_params        The parameters required for
     *                                     encryption. See _encryptMessage().
     *
     * @return object MIME_Part  A MIME_Part object that is signed and
     *                           encrypted according to RFC 2015/3156.
     *                           Returns PEAR_Error on error.
     */
    function signAndEncryptMIMEPart($mime_part, $sign_params = array(),
                                    $encrypt_params = array())
    {
        include_once 'Horde/MIME/Part.php';

        /* RFC 2015 requires that the entire signed message be encrypted. */
        /* We need to explicitly call using Horde_Crypt_pgp:: because we
           don't know whether a subclass has extended these methods. */
        $part = Horde_Crypt_pgp::signMIMEPart($mime_part, $sign_params);
        if (is_a($part, 'PEAR_Error')) {
            return $part;
        }
        $part = Horde_Crypt_pgp::encryptMIMEPart($part, $encrypt_params);
        $part->setContents('This message is in MIME format and has been PGP signed and encrypted.' . "\n");
        $part->setDescription(_("PGP Signed/Encrypted Data"));

        return $part;
    }

    /**
     * Generate a MIME_Part object, in accordance with RFC 2015/3156, that
     * contains a public key.
     *
     * @access public
     *
     * @param string $key  The public key.
     *
     * @return object MIME_Part  A MIME_Part object that contains the public
     *                           key.
     */
    function publicKeyMIMEPart($key)
    {
        include_once 'Horde/MIME/Part.php';

        $part = &new MIME_Part('application/pgp-keys', $key);
        $part->setDescription(_("PGP Public Key"));

        return $part;
    }

    /**
     * Function that handles interfacing with the GnuPG binary.
     *
     * @access private
     *
     * @param array $options            TODO
     * @param string $mode              TODO
     * @param optional array $input     TODO
     * @param optional boolean $output  TODO
     * @param optional boolean $stderr  TODO
     *
     * @return stdClass  TODO
     */
    function _callGpg($options, $mode, $input = array(), $output = false,
                      $stderr = false)
    {
        $cmdline = array_merge($this->_gnupg, $options);
        $data = &new stdClass;
        $data->output = null;
        $data->stderr = null;
        $data->stdout = null;

        /* Create temp files for output. */
        if ($output) {
            $output_file = $this->_createTempFile('horde-pgp', false);
            array_unshift($options, '--output ' . $output_file);

            /* Do we need standard error output? */
            if ($stderr) {
                $stderr_file = $this->_createTempFile('horde-pgp', false);
                $options[] = '> ' . $stderr_file . ' 2>&1';
            }
        }

        /* Build the command line string now. */
        $cmdline = implode(' ', array_merge($this->_gnupg, $options));

        if ($mode == 'w') {
            $fp = popen($cmdline, 'w');
            if (is_array($input)) {
                foreach ($input as $line) {
                    fputs($fp, $line . "\n");
                }
            } else {
                fputs($fp, $input);
            }
        } elseif ($mode == 'r') {
            $fp = popen($cmdline, 'r');
            while (!feof($fp)) {
                $data->stdout .= fgets($fp, 1024);
            }
        }
        pclose($fp);

        if ($output) {
            $fp = @fopen($output_file, 'r');
            $data->output = @fread($fp, filesize($output_file));
            @fclose($fp);
            unlink($output_file);
            if ($stderr) {
                $fp = @fopen($stderr_file, 'r');
                $data->stderr = @fread($fp, filesize($stderr_file));
                @fclose($fp);
                unlink($stderr_file);
            }
        }

        return $data;
    }

}
