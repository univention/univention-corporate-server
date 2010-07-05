<?php
/**
 * The Cipher_des:: class implements the Cipher interface encryption data
 * using the Data Encryption Standard (DES) algorithm as define in FIPS46-3.
 *
 * $Horde: framework/Cipher/Cipher/des.php,v 1.4.12.11 2009-01-06 15:22:57 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @since   Horde 3.0
 * @package Horde_Cipher
 */
class Horde_Cipher_des extends Horde_Cipher {

    /**
     * Initial Permutation
     *
     * @var array
     */
    var $ip = array(
        58, 50, 42, 34, 26, 18, 10,  2,
        60, 52, 44, 36, 28, 20, 12,  4,
        62, 54, 46, 38, 30, 22, 14,  6,
        64, 56, 48, 40, 32, 24, 16,  8,
        57, 49, 41, 33, 25, 17,  9,  1,
        59, 51, 43, 35, 27, 19, 11,  3,
        61, 53, 45, 37, 29, 21, 13,  5,
        63, 55, 47, 39, 31, 23, 15,  7
    );

    /**
     * Final Permutation IP^-1
     *
     * @var array
     */
    var $fp = array(
        40,  8, 48, 16, 56, 24, 64, 32,
        39,  7, 47, 15, 55, 23, 63, 31,
        38,  6, 46, 14, 54, 22, 62, 30,
        37,  5, 45, 13, 53, 21, 61, 29,
        36,  4, 44, 12, 52, 20, 60, 28,
        35,  3, 43, 11, 51, 19, 59, 27,
        34,  2, 42, 10, 50, 18, 58, 26,
        33,  1, 41,  9, 49, 17, 57, 25
    );

    /**
     * E Bit Selection Table
     *
     * @var array
     */
    var $e = array(
        32,  1,  2,  3,  4,  5,
         4,  5,  6,  7,  8,  9,
         8,  9, 10, 11, 12, 13,
        12, 13, 14, 15, 16, 17,
        16, 17, 18, 19, 20, 21,
        20, 21, 22, 23, 24, 25,
        24, 25, 26, 27, 28, 29,
        28, 29, 30, 31, 32,  1
    );

    /**
     * S boxes
     *
     * @var array
     */
    var $_s = array(
        /* S1 */
        1 => array(
           14,  4, 13,  1,  2, 15, 11,  8,  3, 10,  6, 12,  5,  9,  0,  7,
            0, 15,  7,  4, 14,  2, 13,  1, 10,  6, 12, 11,  9,  5,  3,  8,
            4,  1, 14,  8, 13,  6,  2, 11, 15, 12,  9,  7,  3, 10,  5,  0,
           15, 12,  8,  2,  4,  9,  1,  7,  5, 11,  3, 14, 10,  0,  6, 13
        ),

        /* S2 */
        2 => array(
           15,  1,  8, 14,  6, 11,  3,  4,  9,  7,  2, 13, 12,  0,  5, 10,
            3, 13,  4,  7, 15,  2,  8, 14, 12,  0,  1, 10,  6,  9, 11,  5,
            0, 14,  7, 11, 10,  4, 13,  1,  5,  8, 12,  6,  9,  3,  2, 15,
           13,  8, 10,  1,  3, 15,  4,  2, 11,  6,  7, 12,  0,  5, 14,  9,
        ),

        /* S3 */
        3 => array(
           10,  0,  9, 14,  6,  3, 15,  5,  1, 13, 12,  7, 11,  4,  2,  8,
           13,  7,  0,  9,  3,  4,  6, 10,  2,  8,  5, 14, 12, 11, 15,  1,
           13,  6,  4,  9,  8, 15,  3,  0, 11,  1,  2, 12,  5, 10, 14,  7,
            1, 10, 13,  0,  6,  9,  8,  7,  4, 15, 14,  3, 11,  5,  2, 12,
        ),

        /* S4 */
        4 => array(
            7, 13, 14,  3,  0,  6,  9, 10,  1,  2,  8,  5, 11, 12,  4, 15,
           13,  8, 11,  5,  6, 15,  0,  3,  4,  7,  2, 12,  1, 10, 14,  9,
           10,  6,  9,  0, 12, 11,  7, 13, 15,  1,  3, 14,  5,  2,  8,  4,
            3, 15,  0,  6, 10,  1, 13,  8,  9,  4,  5, 11, 12,  7,  2, 14,
        ),

        /* S5 */
        5 => array(
            2, 12,  4,  1,  7, 10, 11,  6,  8,  5,  3, 15, 13,  0, 14,  9,
           14, 11,  2, 12,  4,  7, 13,  1,  5,  0, 15, 10,  3,  9,  8,  6,
            4,  2,  1, 11, 10, 13,  7,  8, 15,  9, 12,  5,  6,  3,  0, 14,
           11,  8, 12,  7,  1, 14,  2, 13,  6, 15,  0,  9, 10,  4,  5,  3,
        ),

        /* S6 */
        6 => array(
           12,  1, 10, 15,  9,  2,  6,  8,  0, 13,  3,  4, 14,  7,  5, 11,
           10, 15,  4,  2,  7, 12,  9,  5,  6,  1, 13, 14,  0, 11,  3,  8,
            9, 14, 15,  5,  2,  8, 12,  3,  7,  0,  4, 10,  1, 13, 11,  6,
            4,  3,  2, 12,  9,  5, 15, 10, 11, 14,  1,  7,  6,  0,  8, 13,
        ),

        /* S7 */
        7 => array(
            4, 11,  2, 14, 15,  0,  8, 13,  3, 12,  9,  7,  5, 10,  6,  1,
           13,  0, 11,  7,  4,  9,  1, 10, 14,  3,  5, 12,  2, 15,  8,  6,
            1,  4, 11, 13, 12,  3,  7, 14, 10, 15,  6,  8,  0,  5,  9,  2,
            6, 11, 13,  8,  1,  4, 10,  7,  9,  5,  0, 15, 14,  2,  3, 12,
        ),

        /* S8 */
        8 => array(
            13,  2,  8,  4,  6, 15, 11,  1, 10,  9,  3, 14,  5,  0, 12,  7,
             1, 15, 13,  8, 10,  3,  7,  4, 12,  5,  6, 11,  0, 14,  9,  2,
             7, 11,  4,  1,  9, 12, 14,  2,  0,  6, 10, 13, 15,  3,  5,  8,
             2,  1, 14,  7,  4, 10,  8, 13, 15, 12,  9,  0,  3,  5,  6, 11
        )
    );

    /**
     * Primitive function
     *
     * @var array
     */
    var $p = array(
        16,  7, 20, 21,
        29, 12, 28, 17,
         1, 15, 23, 26,
         5, 18, 31, 10,
         2,  8, 24, 14,
        32, 27,  3,  9,
        19, 13, 30,  6,
        22, 11,  4, 25
    );

    /**
     * Permuted Choice Table
     *
     * @var array
     */
    var $pc1 = array(
        57, 49, 41, 33, 25, 17,  9,
         1, 58, 50, 42, 34, 26, 18,
        10,  2, 59, 51, 43, 35, 27,
        19, 11,  3, 60, 52, 44, 36,

        63, 55, 47, 39, 31, 23, 15,
         7, 62, 54, 46, 38, 30, 22,
        14,  6, 61, 53, 45, 37, 29,
        21, 13,  5, 28, 20, 12,  4
    );

    /**
     * Number left rotations of pc1
     *
     * @var array
     */
    var $shifts = array(
        1, 1, 2, 2, 2, 2, 2, 2,
        1, 2, 2, 2, 2, 2, 2, 1
    );

    /**
     * Permuted Choice Table 2
     *
     * @var array
     */
    var $pc2 = array(
        14, 17, 11, 24,  1,  5,
         3, 28, 15,  6, 21, 10,
        23, 19, 12,  4, 26,  8,
        16,  7, 27, 20, 13,  2,
        41, 52, 31, 37, 47, 55,
        30, 40, 51, 45, 33, 48,
        44, 49, 39, 56, 34, 53,
        46, 42, 50, 36, 29, 32
    );

    /**
     * Key Schedule
     *
     * @var array
     */
    var $_Ks = array();

    /**
     * Set the key to be used for en/decryption.
     *
     * @param string $key  The key to use.
     */
    function setKey($key)
    {
        if (!is_null($key)) {
            $this->_Ks = $this->_keySchedule($key);
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
            $this->_Ks = $this->_keySchedule($key);
        }

        $block = $this->_initialPerm($block);

        $L = substr($block, 0, 4);
        $R = substr($block, 4, 4);

        for ($i = 1; $i <= 16; $i++ ) {
            $R_prev = $R;
            $L_prev = $L;

            $L = $R;
            $R = $L_prev ^ $this->_f($R_prev, $i);
        }

        $block = $R . $L;
        $block = $this->_finalPerm($block);

        return $block;
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
        $block = $this->_initialPerm($block);

        if (!is_null($key)) {
            $this->_Ks = $this->_keySchedule($key);
        }

        $L = substr($block, 0, 4);
        $R = substr($block, 4, 4);

        for ($i = 16; $i >= 1; $i-- ) {
            $R_prev = $R;
            $L_prev = $L;

            $L = $R_prev;
            $R = $L_prev ^ $this->_f($R_prev, $i);
        }

        $block = $R . $L;
        $block = $this->_finalPerm($block);

        return $block;
    }

    /**
     * Put an input string through an initial permutation
     *
     * @param string $input  Input string.
     *
     * @return string  Permutated string.
     */
    function _initialPerm($input)
    {
        // TODO: Some stylie bitwise thing instead.

        $input_bin = '';
        for ($i = 0; $i < 8; $i++) {
            $input_bin .= str_pad(decbin(ord($input[$i])), 8, '0', STR_PAD_LEFT);
        }

        $output_bin = '';
        foreach ($this->ip as $offset) {
            $output_bin .= $input_bin[$offset - 1];
        }

        $output = '';
        for ($i = 0; $i < 8; $i++) {
            $output .= chr(bindec(substr($output_bin, 8 * $i, 8)));
        }

        return $output;
    }

    /**
     * Put an input string through a final permutation.
     *
     * @param string $input  Input string.
     *
     * @return string  Permutated string.
     */
    function _finalPerm($input)
    {
        // TODO: Some stylie bitwise thing instead.
        $input_bin = '';
        for ($i = 0; $i < 8; $i++) {
            $input_bin .= str_pad(decbin(ord($input[$i])), 8, '0', STR_PAD_LEFT);
        }

        $output_bin = '';
        foreach ($this->fp as $offset) {
            $output_bin .= $input_bin[$offset - 1];
        }

        $output = '';
        for ($i = 0; $i < 8; $i++) {
            $output .= chr(bindec(substr($output_bin, 8 * $i, 8)));
        }

        return $output;
    }


    /**
     * f() The permutation function.
     *
     * @param string $input  Input string.
     * @param integer $round  The round.
     *
     * @return string  The output string.
     */
    function _f($input, $round)
    {
        // TODO: Some stylie bitwise thing instead.
        $key = $this->_Ks[$round];

        $input_bin = '';
        for ($i = 0; $i < 4; $i++) {
            $input_bin .= str_pad(decbin(ord($input[$i])), 8, '0', STR_PAD_LEFT);
        }

        $expanded_bin = '';
        foreach ($this->e as $offset) {
            $expanded_bin .= $input_bin[$offset - 1];
        }

        $expanded = array();
        for ($i = 0; $i < 8; $i++) {
            $expanded[$i] = bindec('00' . substr($expanded_bin, $i * 6, 6)) ^ $key[$i];
        }

        $combined_bin = '';
        for ($i = 0; $i < 8; $i++) {
            $s_index = (($expanded[$i] & 0x20) >> 4) | ($expanded[$i] & 0x01);
            $s_index = 16 * $s_index + (($expanded[$i] & 0x1E) >> 1);
            $val = $this->_s[$i + 1][$s_index];
            $combined_bin .= str_pad(decbin($val), 4, '0', STR_PAD_LEFT);
        }

        $output_bin = '';
        foreach ($this->p as $offset) {
            $output_bin .= $combined_bin[$offset - 1];
        }

        $output = '';
        for ($i = 0; $i < 4; $i++) {
            $output .= chr(bindec(substr($output_bin, $i * 8, 8)));
        }

        return $output;
    }

    /**
     * Create the complete key shedule.
     *
     * @param string $key  The key to use.
     *
     * @return array Key schedule.
     */
    function _keySchedule($key)
    {
        $key = str_pad($key, 8, "\0");
        $ks = array();

        $key_bin = '';
        for ($i = 0; $i < 8; $i++) {
            $key_bin .= str_pad(decbin(ord($key[$i])), 8, '0', STR_PAD_LEFT);
        }

        $c = '';
        $d = '';
        for ($i = 0; $i < 28; $i++) {
            $c .= $key_bin[$this->pc1[$i] - 1];
            $d .= $key_bin[$this->pc1[28 + $i] - 1];
        }

        for ($i = 0; $i < 16; $i++) {
            $c = substr($c, $this->shifts[$i]) . substr($c, 0, $this->shifts[$i]);
            $d = substr($d, $this->shifts[$i]) . substr($d, 0, $this->shifts[$i]);

            $cd = $c . $d;

            $permutated_bin = '';
            foreach ($this->pc2 as $offset) {
                $permutated_bin .= $cd[$offset - 1];
            }

            for ($j = 0; $j < 8; $j++) {
                $ks[$i + 1][] = bindec('00' . substr($permutated_bin, $j * 6, 6));
            }
        }

        return $ks;
    }

}
