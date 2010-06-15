<?php
/**
 * The Horde_Cipher_BlockMode_ofb64:: This class implements the
 * Horde_Cipher_BlockMode using a 64 bit output feedback. This can
 * used to encypt any length string and the encrypted version will be
 * the same length.
 *
 * $Horde: framework/Cipher/Cipher/BlockMode/ofb64.php,v 1.7 2004/01/01 15:14:11 jan Exp $
 *
 * Copyright 2002-2004 Mike Cochrane <mike@graftonhall.co.nz>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.2
 * @package Horde_Cipher
 */
class Horde_Cipher_BlockMode_ofb64 extends Horde_Cipher_BlockMode {

    function encrypt(&$cipher, $plaintext)
    {
        $encrypted = '';

        $n = 0;
        $jMax = strlen($plaintext);
        for ($j = 0; $j < $jMax; $j++) {
            if ($n == 0) {
                $this->_iv = $cipher->encryptBlock($this->_iv);
            }

            $c = $plaintext[$j] ^ $this->_iv[$n];
            $encrypted .= $c;

            $n = (++$n) & 0x07;
        }

        return $encrypted;
    }

    function decrypt(&$cipher, $ciphertext)
    {
        $decrypted = '';

        $n = 0;
        $jMax = strlen($ciphertext);
        for ($j = 0; $j < $jMax; $j++) {
            if ($n == 0) {
                $this->_iv = $cipher->encryptBlock($this->_iv);
            }

            $c = $ciphertext[$j] ^ $this->_iv[$n];
            $decrypted .= $c;

            $n = (++$n) & 0x07;
        }

        return $decrypted;
    }

}
