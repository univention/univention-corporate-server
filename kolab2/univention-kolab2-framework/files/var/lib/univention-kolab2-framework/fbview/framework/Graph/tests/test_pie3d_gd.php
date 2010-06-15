<?php
/**
 * $Horde: framework/Graph/tests/test_pie3d_gd.php,v 1.1 2004/05/06 20:57:39 chuck Exp $
 *
 * @package Horde_Graph
 */

$image = imagecreate(100, 100);

$white = imagecolorallocate($image, 0xFF, 0xFF, 0xFF);
$gray = imagecolorallocate($image, 0xC0, 0xC0, 0xC0);
$darkgray = imagecolorallocate($image, 0x90, 0x90, 0x90);
$navy = imagecolorallocate($image, 0x00, 0x00, 0x80);
$darknavy = imagecolorallocate($image, 0x00, 0x00, 0x50);
$red = imagecolorallocate($image, 0xFF, 0x00, 0x00);
$darkred = imagecolorallocate($image, 0x90, 0x00, 0x00);


$angle = 50;
$thickness = 10;

for ($i = $angle + $thickness; $i > $angle; $i--) {
    imagefilledarc($image, 50, $i, 100, $angle, 0, 45, $darknavy, IMG_ARC_PIE);
    imagefilledarc($image, 50, $i, 100, $angle, 45, 75 , $darkgray, IMG_ARC_PIE);
    imagefilledarc($image, 50, $i, 100, $angle, 75, 360 , $darkred, IMG_ARC_PIE);
}

imagefilledarc($image, 50, 50, 100, $angle, 0, 45, $navy, IMG_ARC_PIE);
imagefilledarc($image, 50, 50, 100, $angle, 45, 75 , $gray, IMG_ARC_PIE);
imagefilledarc($image, 50, 50, 100, $angle, 75, 360 , $red, IMG_ARC_PIE);

header('Content-type: image/png');
imagepng($image);
