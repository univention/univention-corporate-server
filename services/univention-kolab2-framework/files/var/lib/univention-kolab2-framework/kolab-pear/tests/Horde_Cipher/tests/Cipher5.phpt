--TEST--
Blowfish Cipher:: Tests
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

/* Blowfish */
// selection of tests from: http://www.counterpane.com/vectors.txt
echo "Blowfish:\n";
echo "---------\n\n";

// 64 Bit key text
echo "64-bit Key\n";
$key = "\x49\xE9\x5D\x6D\x4C\xA2\x29\xBF";
$plaintext = "\x02\xFE\x55\x77\x81\x17\xF1\x2A";
$ciphertext = "\xCF\x9C\x5D\x7A\x49\x86\xAD\xB5";
testCipher('blowfish', $key, $plaintext, $ciphertext);

$plaintext = "\xFE\xDC\xBA\x98\x76\x54\x32\x10";
$c[ 1] = "\xF9\xAD\x59\x7C\x49\xDB\x00\x5E"; $k[ 1] = "\xF0";
$c[ 2] = "\xE9\x1D\x21\xC1\xD9\x61\xA6\xD6"; $k[ 2] = "\xF0\xE1";
$c[ 3] = "\xE9\xC2\xB7\x0A\x1B\xC6\x5C\xF3"; $k[ 3] = "\xF0\xE1\xD2";
$c[ 4] = "\xBE\x1E\x63\x94\x08\x64\x0F\x05"; $k[ 4] = "\xF0\xE1\xD2\xC3";
$c[ 5] = "\xB3\x9E\x44\x48\x1B\xDB\x1E\x6E"; $k[ 5] = "\xF0\xE1\xD2\xC3\xB4";
$c[ 6] = "\x94\x57\xAA\x83\xB1\x92\x8C\x0D"; $k[ 6] = "\xF0\xE1\xD2\xC3\xB4\xA5";
$c[ 7] = "\x8B\xB7\x70\x32\xF9\x60\x62\x9D"; $k[ 7] = "\xF0\xE1\xD2\xC3\xB4\xA5\x96";
$c[ 8] = "\xE8\x7A\x24\x4E\x2C\xC8\x5E\x82"; $k[ 8] = "\xF0\xE1\xD2\xC3\xB4\xA5\x96\x87";
$c[ 9] = "\x15\x75\x0E\x7A\x4F\x4E\xC5\x77"; $k[ 9] = "\xF0\xE1\xD2\xC3\xB4\xA5\x96\x87\x78";
$c[10] = "\x12\x2B\xA7\x0B\x3A\xB6\x4A\xE0"; $k[10] = "\xF0\xE1\xD2\xC3\xB4\xA5\x96\x87\x78\x69";
$c[11] = "\x3A\x83\x3C\x9A\xFF\xC5\x37\xF6"; $k[11] = "\xF0\xE1\xD2\xC3\xB4\xA5\x96\x87\x78\x69\x5A";
$c[12] = "\x94\x09\xDA\x87\xA9\x0F\x6B\xF2"; $k[12] = "\xF0\xE1\xD2\xC3\xB4\xA5\x96\x87\x78\x69\x5A\x4B";
$c[13] = "\x88\x4F\x80\x62\x50\x60\xB8\xB4"; $k[13] = "\xF0\xE1\xD2\xC3\xB4\xA5\x96\x87\x78\x69\x5A\x4B\x3C";
$c[14] = "\x1F\x85\x03\x1C\x19\xE1\x19\x68"; $k[14] = "\xF0\xE1\xD2\xC3\xB4\xA5\x96\x87\x78\x69\x5A\x4B\x3C\x2D";
$c[15] = "\x79\xD9\x37\x3A\x71\x4C\xA3\x4F"; $k[15] = "\xF0\xE1\xD2\xC3\xB4\xA5\x96\x87\x78\x69\x5A\x4B\x3C\x2D\x1E";
$c[16] = "\x93\x14\x28\x87\xEE\x3B\xE1\x5C"; $k[16] = "\xF0\xE1\xD2\xC3\xB4\xA5\x96\x87\x78\x69\x5A\x4B\x3C\x2D\x1E\x0F";
$c[17] = "\x03\x42\x9E\x83\x8C\xE2\xD1\x4B"; $k[17] = "\xF0\xE1\xD2\xC3\xB4\xA5\x96\x87\x78\x69\x5A\x4B\x3C\x2D\x1E\x0F\x00";
$c[18] = "\xA4\x29\x9E\x27\x46\x9F\xF6\x7B"; $k[18] = "\xF0\xE1\xD2\xC3\xB4\xA5\x96\x87\x78\x69\x5A\x4B\x3C\x2D\x1E\x0F\x00\x11";
$c[19] = "\xAF\xD5\xAE\xD1\xC1\xBC\x96\xA8"; $k[19] = "\xF0\xE1\xD2\xC3\xB4\xA5\x96\x87\x78\x69\x5A\x4B\x3C\x2D\x1E\x0F\x00\x11\x22";
$c[20] = "\x10\x85\x1C\x0E\x38\x58\xDA\x9F"; $k[20] = "\xF0\xE1\xD2\xC3\xB4\xA5\x96\x87\x78\x69\x5A\x4B\x3C\x2D\x1E\x0F\x00\x11\x22\x33";
$c[21] = "\xE6\xF5\x1E\xD7\x9B\x9D\xB2\x1F"; $k[21] = "\xF0\xE1\xD2\xC3\xB4\xA5\x96\x87\x78\x69\x5A\x4B\x3C\x2D\x1E\x0F\x00\x11\x22\x33\x44";
$c[22] = "\x64\xA6\xE1\x4A\xFD\x36\xB4\x6F"; $k[22] = "\xF0\xE1\xD2\xC3\xB4\xA5\x96\x87\x78\x69\x5A\x4B\x3C\x2D\x1E\x0F\x00\x11\x22\x33\x44\x55";
$c[23] = "\x80\xC7\xD7\xD4\x5A\x54\x79\xAD"; $k[23] = "\xF0\xE1\xD2\xC3\xB4\xA5\x96\x87\x78\x69\x5A\x4B\x3C\x2D\x1E\x0F\x00\x11\x22\x33\x44\x55\x66";
$c[24] = "\x05\x04\x4B\x62\xFA\x52\xD0\x80"; $k[24] = "\xF0\xE1\xD2\xC3\xB4\xA5\x96\x87\x78\x69\x5A\x4B\x3C\x2D\x1E\x0F\x00\x11\x22\x33\x44\x55\x66\x77";
foreach ($k as $id => $key) {
    echo (strlen($key) * 8) . "-bit Key\n";
    testCipher('blowfish', $key, $plaintext, $c[$id]);
}

?>
--EXPECT--
Blowfish:
---------

64-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

8-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

16-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

24-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

32-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

40-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

48-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

56-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

64-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

72-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

80-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

88-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

96-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

104-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

112-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

120-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

128-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

136-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

144-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

152-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

160-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

168-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

176-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

184-bit Key
Testing Encryption: Pass
Testing Decryption: Pass

192-bit Key
Testing Encryption: Pass
Testing Decryption: Pass
