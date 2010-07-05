<?php
/**
 * Unsharp mask Image effect.
 *
 * $Horde: framework/Image/Image/Effect/gd/unsharp_mask.php,v 1.1.2.1 2007-12-20 13:49:11 jan Exp $
 *
 * Unsharp mask algorithm by Torstein Hønsi 2003 <thoensi_at_netcom_dot_no>
 * From: http://www.vikjavev.com/hovudsida/umtestside.php
 *
 * @package Horde_Image
 */
class Horde_Image_Effect_gd_unsharp_mask extends Horde_Image_Effect {

    /**
     * Valid parameters:
     *
     * @TODO
     *
     * @var array
     */
    var $_params = array('amount' => 0,
                         'radius' => 0,
                         'threshold' => 0);

    /**
     * Apply the unsharp_mask effect.
     *
     * @return mixed true | PEAR_Error
     */
    function apply()
    {
        $amount = $this->_params['amount'];
        $radius = $this->_params['radius'];
        $threshold = $this->_params['threshold'];

        // Attempt to calibrate the parameters to Photoshop:
        $amount = min($amount, 500);
        $amount = $amount * 0.016;
        if ($amount == 0) {
            return true;
        }

        $radius = min($radius, 50);
        $radius = $radius * 2;

        $threshold = min($threshold, 255);

        $radius = abs(round($radius));  // Only integers make sense.
        if ($radius == 0) {
            return true;
        }

        $img = $this->_image->_im;
        $w = ImageSX($img);
        $h = ImageSY($img);
        $imgCanvas  = ImageCreateTrueColor($w, $h);
        $imgCanvas2 = ImageCreateTrueColor($w, $h);
        $imgBlur    = ImageCreateTrueColor($w, $h);
        $imgBlur2   = ImageCreateTrueColor($w, $h);
        ImageCopy($imgCanvas,  $img, 0, 0, 0, 0, $w, $h);
        ImageCopy($imgCanvas2, $img, 0, 0, 0, 0, $w, $h);

        // Gaussian blur matrix:
        //
        //  1   2   1
        //  2   4   2
        //  1   2   1
        //
        //////////////////////////////////////////////////

        // Move copies of the image around one pixel at the time and merge them with weight
        // according to the matrix. The same matrix is simply repeated for higher radii.
        for ($i = 0; $i < $radius; $i++)    {
            ImageCopy     ($imgBlur, $imgCanvas, 0, 0, 1, 1, $w - 1, $h - 1);            // up left
            ImageCopyMerge($imgBlur, $imgCanvas, 1, 1, 0, 0, $w,     $h,     50);        // down right
            ImageCopyMerge($imgBlur, $imgCanvas, 0, 1, 1, 0, $w - 1, $h,     33.33333);  // down left
            ImageCopyMerge($imgBlur, $imgCanvas, 1, 0, 0, 1, $w,     $h - 1, 25);        // up right
            ImageCopyMerge($imgBlur, $imgCanvas, 0, 0, 1, 0, $w - 1, $h,     33.33333);  // left
            ImageCopyMerge($imgBlur, $imgCanvas, 1, 0, 0, 0, $w,     $h,     25);        // right
            ImageCopyMerge($imgBlur, $imgCanvas, 0, 0, 0, 1, $w,     $h - 1, 20 );       // up
            ImageCopyMerge($imgBlur, $imgCanvas, 0, 1, 0, 0, $w,     $h,     16.666667); // down
            ImageCopyMerge($imgBlur, $imgCanvas, 0, 0, 0, 0, $w,     $h,     50);        // center
            ImageCopy     ($imgCanvas, $imgBlur, 0, 0, 0, 0, $w,     $h);

            // During the loop above the blurred copy darkens, possibly due to a roundoff
            // error. Therefore the sharp picture has to go through the same loop to
            // produce a similar image for comparison. This is not a good thing, as processing
            // time increases heavily.
            ImageCopy     ($imgBlur2, $imgCanvas2, 0, 0, 0, 0, $w, $h);
            ImageCopyMerge($imgBlur2, $imgCanvas2, 0, 0, 0, 0, $w, $h, 50);
            ImageCopyMerge($imgBlur2, $imgCanvas2, 0, 0, 0, 0, $w, $h, 33.33333);
            ImageCopyMerge($imgBlur2, $imgCanvas2, 0, 0, 0, 0, $w, $h, 25);
            ImageCopyMerge($imgBlur2, $imgCanvas2, 0, 0, 0, 0, $w, $h, 33.33333);
            ImageCopyMerge($imgBlur2, $imgCanvas2, 0, 0, 0, 0, $w, $h, 25);
            ImageCopyMerge($imgBlur2, $imgCanvas2, 0, 0, 0, 0, $w, $h, 20 );
            ImageCopyMerge($imgBlur2, $imgCanvas2, 0, 0, 0, 0, $w, $h, 16.666667);
            ImageCopyMerge($imgBlur2, $imgCanvas2, 0, 0, 0, 0, $w, $h, 50);
            ImageCopy     ($imgCanvas2, $imgBlur2, 0, 0, 0, 0, $w, $h);
        }

        // Calculate the difference between the blurred pixels and the original
        // and set the pixels
        for ($x = 0; $x < $w; $x++) { // each row
            for ($y = 0; $y < $h; $y++) { // each pixel

                $rgbOrig = ImageColorAt($imgCanvas2, $x, $y);
                $rOrig = (($rgbOrig >> 16) & 0xFF);
                $gOrig = (($rgbOrig >>  8) & 0xFF);
                $bOrig =  ($rgbOrig        & 0xFF);

                $rgbBlur = ImageColorAt($imgCanvas, $x, $y);
                $rBlur = (($rgbBlur >> 16) & 0xFF);
                $gBlur = (($rgbBlur >>  8) & 0xFF);
                $bBlur =  ($rgbBlur        & 0xFF);

                // When the masked pixels differ less from the original
                // than the threshold specifies, they are set to their original value.
                $rNew = (abs($rOrig - $rBlur) >= $threshold) ? max(0, min(255, ($amount * ($rOrig - $rBlur)) + $rOrig)) : $rOrig;
                $gNew = (abs($gOrig - $gBlur) >= $threshold) ? max(0, min(255, ($amount * ($gOrig - $gBlur)) + $gOrig)) : $gOrig;
                $bNew = (abs($bOrig - $bBlur) >= $threshold) ? max(0, min(255, ($amount * ($bOrig - $bBlur)) + $bOrig)) : $bOrig;

                if (($rOrig != $rNew) || ($gOrig != $gNew) || ($bOrig != $bNew)) {
                    $pixCol = ImageColorAllocate($img, $rNew, $gNew, $bNew);
                    ImageSetPixel($img, $x, $y, $pixCol);
                }
            }
        }
        ImageDestroy($imgCanvas);
        ImageDestroy($imgCanvas2);
        ImageDestroy($imgBlur);
        ImageDestroy($imgBlur2);

        return true;
    }

}
