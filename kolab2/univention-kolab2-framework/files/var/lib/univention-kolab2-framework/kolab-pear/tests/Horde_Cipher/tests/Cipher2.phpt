--TEST--
DES Cipher:: Tests
--FILE--
<?php

require_once dirname(__FILE__) . "/../Cipher.php";

if (!function_exists('testCipher')) {
    function testCipher($cipher, $key,  $plaintext, $ciphertext)
    {
        $cipher = &Horde_Cipher::factory($cipher);
        $cipher->setKey($key);

        echo "Testing Encryption: ";
        $res = $cipher->encryptBlock($plaintext);
        if ($res == $ciphertext) {
            echo "Pass\n";
        } else {
            echo "Fail\n";
            echo "Returned: ";
            for ($i = 0; $i < strlen($res); $i++) {
                echo str_pad(dechex(ord(substr($res, $i, 1))), 2, '0', STR_PAD_LEFT) . " ";
            } echo "\n";
            echo "Expected: ";
            for ($i = 0; $i < strlen($ciphertext); $i++) {
                echo str_pad(dechex(ord(substr($ciphertext, $i, 1))), 2, '0', STR_PAD_LEFT)  . " ";
            } echo "\n";

        }
        echo "Testing Decryption: ";
        $res = $cipher->decryptBlock($ciphertext);
        if ($res == $plaintext) {
            echo "Pass\n";
        } else {
            echo "Fail\n";
            echo "Returned: ";
            for ($i = 0; $i < strlen($res); $i++) {
                echo str_pad(dechex(ord(substr($res, $i, 1))), 2, '0', STR_PAD_LEFT) . " ";
            } echo "\n";
            echo "Expected: ";
            for ($i = 0; $i < strlen($plaintext); $i++) {
                echo str_pad(dechex(ord(substr($plaintext, $i, 1))), 2, '0', STR_PAD_LEFT)  . " ";
            } echo "\n";
        }
        echo "\n";
        flush();
    }
}  

/* DES Cipher */
echo "DES:\n";
echo "----\n\n";

// 64 Bit key test
$tests = array(
    "\x00\x00\x00\x00\x00\x00\x00\x00", "\x00\x00\x00\x00\x00\x00\x00\x00", "\x8C\xA6\x4D\xE9\xC1\xB1\x23\xA7",
    "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF", "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF", "\x73\x59\xB2\x16\x3E\x4E\xDC\x58",
    "\x30\x00\x00\x00\x00\x00\x00\x00", "\x10\x00\x00\x00\x00\x00\x00\x01", "\x95\x8E\x6E\x62\x7A\x05\x55\x7B",
    "\x01\x23\x45\x67\x89\xAB\xCD\xEF", "\x11\x11\x11\x11\x11\x11\x11\x11", "\x17\x66\x8D\xFC\x72\x92\x53\x2D",
    "\x11\x11\x11\x11\x11\x11\x11\x11", "\x01\x23\x45\x67\x89\xAB\xCD\xEF", "\x8A\x5A\xE1\xF8\x1A\xB8\xF2\xDD",

    // Initial Permutation and Expansion test
    "\x01\x01\x01\x01\x01\x01\x01\x01", "\x95\xF8\xA5\xE5\xDD\x31\xD9\x00", "\x80\x00\x00\x00\x00\x00\x00\x00",

    // Key Permutation test
    "\x80\x01\x01\x01\x01\x01\x01\x01", "\x00\x00\x00\x00\x00\x00\x00\x00", "\x95\xA8\xD7\x28\x13\xDA\xA9\x4D",

    // Data Permutation tests
    "\x10\x46\x91\x34\x89\x98\x01\x31", "\x00\x00\x00\x00\x00\x00\x00\x00", "\x88\xD5\x5E\x54\xF5\x4C\x97\xB4",

    // S-Box test
    "\x7C\xA1\x10\x45\x4A\x1A\x6E\x57", "\x01\xA1\xD6\xD0\x39\x77\x67\x42", "\x69\x0F\x5B\x0D\x9A\x26\x93\x9B",
    "\x01\x31\xD9\x61\x9D\xC1\x37\x6E", "\x5C\xD5\x4C\xA8\x3D\xEF\x57\xDA", "\x7A\x38\x9D\x10\x35\x4B\xD2\x71",
 );

for ($i = 0; $i < count($tests); $i+= 3) {
    echo "64-bit Key\n";
    $key = $tests[$i];
    $plaintext = $tests[$i + 1];
    $ciphertext = $tests[$i + 2];
    testCipher('des', $key, $plaintext, $ciphertext);
}

?>
--EXPECT--
DES:
----

64-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

64-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

64-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

64-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

64-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

64-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

64-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

64-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

64-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

64-bit Key
Testing Encryption: Pass
Testing Decryption: Pass
