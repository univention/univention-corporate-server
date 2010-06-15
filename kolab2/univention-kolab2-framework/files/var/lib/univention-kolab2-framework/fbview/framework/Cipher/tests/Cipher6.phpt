--TEST--
Blockmode Cipher:: Tests
--FILE--
<?php

require_once dirname(__FILE__) . "/../Cipher.php";

if (!function_exists('testBlockCipher')) {
    function testBlockCipher(&$cipher, $plaintext, $ciphertext)
    {
        echo "Testing Encryption: ";
        if ($cipher->encrypt($plaintext) == $ciphertext) {
            echo "Pass\n";
        } else {
            echo "Fail\n";
        }
        echo "Testing Decryption: ";
        if ($cipher->decrypt($ciphertext) == $plaintext) {
            echo "Pass\n";
        } else {
            echo "Fail\n";
        }
        echo "\n";
        flush();
    }
}  

/* Block Mode Tests */
echo "Block Mode Tests:\n";
echo "-----------------\n";
echo "(using Blowfish test vectors)\n\n";

$key = "\x01\x23\x45\x67\x89\xAB\xCD\xEF\xF0\xE1\xD2\xC3\xB4\xA5\x96\x87";
$iv = "\xFE\xDC\xBA\x98\x76\x54\x32\x10";
$plaintext = "7654321 Now is the time for ";

echo "Cipher Block Chaining (CBC) Test\n";
$ciphertext = "\x6B\x77\xB4\xD6\x30\x06\xDE\xE6\x05\xB1\x56\xE2\x74\x03\x97\x93\x58\xDE\xB9\xE7\x15\x46\x16\xD9\x59\xF1\x65\x2B\xD5\xFF\x92\xCC";
$cipher = &Horde_Cipher::factory('blowfish');
$cipher->setBlockMode("cbc");
$cipher->setKey($key);
$cipher->setIV($iv);
testBlockCipher($cipher, $plaintext, $ciphertext);


echo "Electronic Code Book (ECB) Test\n";
$ciphertext = "\x2a\xfd\x7d\xaa\x60\x62\x6b\xa3\x86\x16\x46\x8c\xc2\x9c\xf6\xe1\x29\x1e\x81\x7c\xc7\x40\x98\x2d\x6f\x87\xac\x5f\x17\x1a\xab\xea";
$cipher = &Horde_Cipher::factory('blowfish');
$cipher->setBlockMode("ecb");
$cipher->setKey($key);
$cipher->setIV($iv);
testBlockCipher($cipher, $plaintext, $ciphertext);

echo "64 Bit Cipher Feedback (CFB64) Test\n";
$ciphertext = "\xE7\x32\x14\xA2\x82\x21\x39\xCA\xF2\x6E\xCF\x6D\x2E\xB9\xE7\x6E\x3D\xA3\xDE\x04\xD1\x51\x72\x00\x51\x9D\x57\xA6";
$cipher = &Horde_Cipher::factory('blowfish');
$cipher->setBlockMode("cfb64");
$cipher->setKey($key);
$cipher->setIV($iv);
testBlockCipher($cipher, $plaintext, $ciphertext);

echo "64 Bit Output Feedback (OFB64) Test\n";
$ciphertext = "\xE7\x32\x14\xA2\x82\x21\x39\xCA\x62\xB3\x43\xCC\x5B\x65\x58\x73\x10\xDD\x90\x8D\x0C\x24\x1B\x22\x63\xC2\xCF\x80";
$cipher = &Horde_Cipher::factory('blowfish');
$cipher->setBlockMode("ofb64");
$cipher->setKey($key);
$cipher->setIV($iv);
testBlockCipher($cipher, $plaintext, $ciphertext);

?>
--EXPECT--
Block Mode Tests:
-----------------
(using Blowfish test vectors)

Cipher Block Chaining (CBC) Test
Testing Encryption: Pass
Testing Decryption: Pass

Electronic Code Book (ECB) Test
Testing Encryption: Pass
Testing Decryption: Pass

64 Bit Cipher Feedback (CFB64) Test
Testing Encryption: Pass
Testing Decryption: Pass

64 Bit Output Feedback (OFB64) Test
Testing Encryption: Pass
Testing Decryption: Pass
