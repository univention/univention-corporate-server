<?php
/**
 * $Horde: horde/util/barcode.php,v 1.10.10.7 2009-01-06 15:28:05 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

@define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/core.php';
require_once 'Horde/Image.php';

// Get text, uppercase, add start/stop characters.
$text = Util::getFormData('barcode', 'test');
$text = String::upper($text, true);
$text = "*$text*";
$textlen = strlen($text);

$height = Util::getFormData('h', 40);
$thinwidth = Util::getFormData('w', 2);
$thickwidth = $thinwidth * 3;
$width = $textlen * (7 * $thinwidth + 3 * $thickwidth) - $thinwidth;

$codingmap = array('0' => '000110100', '1' => '100100001',
                   '2' => '001100001', '3' => '101100000', '4' => '000110001',
                   '5' => '100110000', '6' => '001110000', '7' => '000100101',
                   '8' => '100100100', '9' => '001100100', 'A' => '100001001',
                   'B' => '001001001', 'C' => '101001000', 'D' => '000011001',
                   'E' => '100011000', 'F' => '001011000', 'G' => '000001101',
                   'H' => '100001100', 'I' => '001001100', 'J' => '000011100',
                   'K' => '100000011', 'L' => '001000011', 'M' => '101000010',
                   'N' => '000010011', 'O' => '100010010', 'P' => '001010010',
                   'Q' => '000000111', 'R' => '100000110', 'S' => '001000110',
                   'T' => '000010110', 'U' => '110000001', 'V' => '011000001',
                   'W' => '111000000', 'X' => '010010001', 'Y' => '110010000',
                   'Z' => '011010000', ' ' => '011000100', '$' => '010101000',
                   '%' => '000101010', '*' => '010010100', '+' => '010001010',
                   '-' => '010000101', '.' => '110000100', '/' => '010100010');

$image = &Horde_Image::factory(Util::getFormData('type', 'png'),
                               array('temp' => Horde::getTempDir(),
                                     'width' => $width,
                                     'height' => $height,
                                     'background' => 'white'));

$xpos = 0;
for ($idx = 0; $idx < $textlen; $idx++) {
    $char = substr($text, $idx, 1);
    // Make unknown chars a '-'.
    if (!isset($codingmap[$char])) {
        $char = '-';
    }
    for ($bar = 0; $bar <= 8; $bar++) {
        $elementwidth = $codingmap[$char]{$bar} ? $thickwidth : $thinwidth;
        if (($bar + 1) % 2) {
            $image->rectangle($xpos, 0, $elementwidth - 1, $height, 'black', 'black');
        }
        $xpos += $elementwidth;
    }
    $xpos += $thinwidth;
}

header('Pragma: public');
$image->display();
