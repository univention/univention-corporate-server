--TEST--
RC2 Cipher:: Tests
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

/* RC2 Cipher */
echo "RC2:\n";
echo "----\n\n";

// 8 Bit key test
echo "8-bit Key\n";
$key = "\x88";
$plaintext = "\x00\x00\x00\x00\x00\x00\x00\x00";
$ciphertext = "\x61\xa8\xa2\x44\xad\xac\xcc\xf0";
testCipher('rc2', $key, $plaintext, $ciphertext);

// 64 Bit key test
echo "64-bit Key\n";
$key = "\x00\x00\x00\x00\x00\x00\x00\x00";
$plaintext = "\x00\x00\x00\x00\x00\x00\x00\x00";
$ciphertext = "\xeb\xb7\x73\xf9\x93\x27\x8e\xff";
testCipher('rc2', $key, $plaintext, $ciphertext);

// 128 Bit key test
echo "128-bit Key\n";
$key = "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F";
$plaintext = "\x00\x00\x00\x00\x00\x00\x00\x00";
$ciphertext = "\x50\xDC\x01\x62\xBD\x75\x7F\x31";
testCipher('rc2', $key, $plaintext, $ciphertext);

// 64 Bit key test
echo "64-bit Key\n";
$key = "\xff\xff\xff\xff\xff\xff\xff\xff";
$plaintext = "\xff\xff\xff\xff\xff\xff\xff\xff";
$ciphertext = "\x27\x8b\x27\xe4\x2e\x2f\x0d\x49";
testCipher('rc2', $key, $plaintext, $ciphertext);

?>
--EXPECT--
RC2:
----

8-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

64-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

128-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

64-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

