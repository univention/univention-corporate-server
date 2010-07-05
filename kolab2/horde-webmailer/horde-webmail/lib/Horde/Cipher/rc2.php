<?php
/**
 * The Cipher_rc2:: class implements the Cipher interface encryption data
 * using the RC2 algorithm as described in RFC2268.
 *
 * Based on the notes by Peter Gutmann <pgut01@cs.auckland.ac.nz>
 * http://www.mirrors.wiretapped.net/security/cryptography/
 *   algorithms/rc2/comments/gutman-960211
 *
 * $Horde: framework/Cipher/Cipher/rc2.php,v 1.9.12.11 2009-01-06 15:22:57 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @since   Horde 2.2
 * @package Horde_Cipher
 */
class Horde_Cipher_rc2 extends Horde_Cipher {

    /**
     * Permutations array
     *
     * @var array
     */
    var $_perm = array(
        0xD9, 0x78, 0xF9, 0xC4, 0x19, 0xDD, 0xB5, 0xED,
        0x28, 0xE9, 0xFD, 0x79, 0x4A, 0xA0, 0xD8, 0x9D,
        0xC6, 0x7E, 0x37, 0x83, 0x2B, 0x76, 0x53, 0x8E,
        0x62, 0x4C, 0x64, 0x88, 0x44, 0x8B, 0xFB, 0xA2,
        0x17, 0x9A, 0x59, 0xF5, 0x87, 0xB3, 0x4F, 0x13,
        0x61, 0x45, 0x6D, 0x8D, 0x09, 0x81, 0x7D, 0x32,
        0xBD, 0x8F, 0x40, 0xEB, 0x86, 0xB7, 0x7B, 0x0B,
        0xF0, 0x95, 0x21, 0x22, 0x5C, 0x6B, 0x4E, 0x82,
        0x54, 0xD6, 0x65, 0x93, 0xCE, 0x60, 0xB2, 0x1C,
        0x73, 0x56, 0xC0, 0x14, 0xA7, 0x8C, 0xF1, 0xDC,
        0x12, 0x75, 0xCA, 0x1F, 0x3B, 0xBE, 0xE4, 0xD1,
        0x42, 0x3D, 0xD4, 0x30, 0xA3, 0x3C, 0xB6, 0x26,
        0x6F, 0xBF, 0x0E, 0xDA, 0x46, 0x69, 0x07, 0x57,
        0x27, 0xF2, 0x1D, 0x9B, 0xBC, 0x94, 0x43, 0x03,
        0xF8, 0x11, 0xC7, 0xF6, 0x90, 0xEF, 0x3E, 0xE7,
        0x06, 0xC3, 0xD5, 0x2F, 0xC8, 0x66, 0x1E, 0xD7,
        0x08, 0xE8, 0xEA, 0xDE, 0x80, 0x52, 0xEE, 0xF7,
        0x84, 0xAA, 0x72, 0xAC, 0x35, 0x4D, 0x6A, 0x2A,
        0x96, 0x1A, 0xD2, 0x71, 0x5A, 0x15, 0x49, 0x74,
        0x4B, 0x9F, 0xD0, 0x5E, 0x04, 0x18, 0xA4, 0xEC,
        0xC2, 0xE0, 0x41, 0x6E, 0x0F, 0x51, 0xCB, 0xCC,
        0x24, 0x91, 0xAF, 0x50, 0xA1, 0xF4, 0x70, 0x39,
        0x99, 0x7C, 0x3A, 0x85, 0x23, 0xB8, 0xB4, 0x7A,
        0xFC, 0x02, 0x36, 0x5B, 0x25, 0x55, 0x97, 0x31,
        0x2D, 0x5D, 0xFA, 0x98, 0xE3, 0x8A, 0x92, 0xAE,
        0x05, 0xDF, 0x29, 0x10, 0x67, 0x6C, 0xBA, 0xC9,
        0xD3, 0x00, 0xE6, 0xCF, 0xE1, 0x9E, 0xA8, 0x2C,
        0x63, 0x16, 0x01, 0x3F, 0x58, 0xE2, 0x89, 0xA9,
        0x0D, 0x38, 0x34, 0x1B, 0xAB, 0x33, 0xFF, 0xB0,
        0xBB, 0x48, 0x0C, 0x5F, 0xB9, 0xB1, 0xCD, 0x2E,
        0xC5, 0xF3, 0xDB, 0x47, 0xE5, 0xA5, 0x9C, 0x77,
        0x0A, 0xA6, 0x20, 0x68, 0xFE, 0x7F, 0xC1, 0xAD
    );

    /**
     * Array to hold the key schedule
     *
     * @var array
     */
    var $_keySchedule = array();

    /**
     * Set the key to be used for en/decryption.
     *
     * @param string $key  The key to use.
     */
    function setKey($key)
    {
        $key = array_values(unpack('C*', $key));
        $bits = 1024;

        /* Expand input key to 128 bytes */
        $len = count($key);
        $last = $key[$len - 1];
        for ($i = $len; $i < 128; $i++) {
            $last = $this->_perm[($key[$i - $len] + $last) & 0xFF];
            $key[$i] = $last;
        }

        /* Phase 2 - reduce effective key size to "bits" */
        if ($len != 8) {
            $len = $len * 8;
        }
        $key[128 - $len] = $this->_perm[$key[128 - $len] & 0xFF];
        for ($i = 127 - $len; $i >= 0; $i--) {
            $key[$i] = $this->_perm[$key[$i + $len] ^ $key[$i + 1]];
        }

        /* Phase 3 - convert to 16 bit values */
        for ($i = 63; $i >= 0; $i--) {
            $this->_keySchedule[$i] = ($key[$i * 2 + 1] << 8 | $key[$i * 2]) & 0xFFFF;
        }
    }

    /**
     * Return the size of the blocks that this cipher needs.
     *
     * @return integer  The number of characters per block.
     */
    function getBlockSize()
    {
        return 8;
    }

    /**
     * Encrypt a block of data.
     *
     * @param string $block  The data to encrypt.
     * @param string $key    The key to use.
     *
     * @return string  The encrypted output.
     */
    function encryptBlock($block, $key = null)
    {
        if (!is_null($key)) {
            $this->setKey($key);
        }

        $plain = unpack('v*', $block);

        for ($i = 0; $i < 16; $i++) {
            $plain[1] += ($plain[2] & ~$plain[4]) + ($plain[3] & $plain[4]) + $this->_keySchedule[4 * $i + 0];
            $bin = str_pad(decbin(0xFFFF & $plain[1]), 32, '0', STR_PAD_LEFT);
            $plain[1] = bindec($bin . substr($bin, 16, 1));

            $plain[2] += ($plain[3] & ~$plain[1]) + ($plain[4] & $plain[1]) + $this->_keySchedule[4 * $i + 1];
            $bin = str_pad(decbin(0xFFFF & $plain[2]), 32, '0', STR_PAD_LEFT);
            $plain[2] = bindec($bin . substr($bin, 16, 2));

            $plain[3] += ($plain[4] & ~$plain[2]) + ($plain[1] & $plain[2]) + $this->_keySchedule[4 * $i + 2];
            $bin = str_pad(decbin(0xFFFF & $plain[3]), 16, '0', STR_PAD_LEFT);
            $plain[3] = bindec($bin . substr($bin, 0, 3));

            $plain[4] += ($plain[1] & ~$plain[3]) + ($plain[2] & $plain[3]) + $this->_keySchedule[4 * $i + 3];
            $bin = str_pad(decbin(0xFFFF & $plain[4]), 16, '0', STR_PAD_LEFT);
            $plain[4] = bindec($bin . substr($bin, 0, 5));

            if ($i == 4 || $i == 10) {
                $plain[1] += $this->_keySchedule[$plain[4] & 0x3F];
                $plain[2] += $this->_keySchedule[$plain[1] & 0x3F];
                $plain[3] += $this->_keySchedule[$plain[2] & 0x3F];
                $plain[4] += $this->_keySchedule[$plain[3] & 0x3F];
            }

        }

        $encrypted = pack("v*", $plain[1], $plain[2], $plain[3], $plain[4]);
        return $encrypted;
    }

    /**
     * Decrypt a block of data.
     *
     * @param string $block  The data to decrypt.
     * @param string $key    The key to use.
     *
     * @return string  The decrypted output.
     */
    function decryptBlock($block, $key = null)
    {
        if (!is_null($key)) {
            $this->setKey($key);
        }

        $cipher = unpack('v*', $block);

        for ($i = 15; $i >= 0; $i--) {
            $bin = str_pad(decbin(0xFFFF & $cipher[4]), 16, '0', STR_PAD_LEFT);
            $cipher[4] = bindec(substr($bin, -21, 21) . substr($bin, 0, 11));
            $cipher[4] -= ($cipher[1] & ~$cipher[3]) + ($cipher[2] & $cipher[3]) + $this->_keySchedule[4 * $i + 3];

            $bin = str_pad(decbin(0xFFFF & $cipher[3]), 16, '0', STR_PAD_LEFT);
            $cipher[3] = bindec(substr($bin, -19, 19) . substr($bin, 0, 13));
            $cipher[3] -= ($cipher[4] & ~$cipher[2]) + ($cipher[1] & $cipher[2]) + $this->_keySchedule[4 * $i + 2];

            $bin = str_pad(decbin(0xFFFF & $cipher[2]), 16, '0', STR_PAD_LEFT);
            $cipher[2] = bindec(substr($bin, -18, 18) . substr($bin, 0, 14));
            $cipher[2] -= ($cipher[3] & ~$cipher[1]) + ($cipher[4] & $cipher[1]) + $this->_keySchedule[4 * $i + 1];

            $bin = str_pad(decbin(0xFFFF & $cipher[1]), 16, '0', STR_PAD_LEFT);
            $cipher[1] = bindec(substr($bin, -17, 17) . substr($bin, 0, 15));
            $cipher[1] -= ($cipher[2] & ~$cipher[4]) + ($cipher[3] & $cipher[4]) + $this->_keySchedule[4 * $i + 0];

            if ($i == 5 || $i == 11) {
                $cipher[4] -= $this->_keySchedule[$cipher[3] & 0x3F];
                $cipher[3] -= $this->_keySchedule[$cipher[2] & 0x3F];
                $cipher[2] -= $this->_keySchedule[$cipher[1] & 0x3F];
                $cipher[1] -= $this->_keySchedule[$cipher[4] & 0x3F];
            }
        }

        return pack("v*", $cipher[1], $cipher[2], $cipher[3], $cipher[4]);
    }

}
