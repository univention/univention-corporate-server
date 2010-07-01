<?php
/**
 * Image effect for adding a drop shadow.
 *
 * $Horde: framework/Image/Image/Effect/gd/drop_shadow.php,v 1.4.2.1 2007-12-20 13:49:11 jan Exp $
 *
 * This algorithm is from the phpThumb project available at
 * http://phpthumb.sourceforge.net and all credit for this script should go to
 * James Heinrich <info@silisoftware.com>.  Modifications made to the code
 * to fit it within the Horde framework and to adjust for our coding standards.
 *
 * @author Michael J. Rubinsky <mrubinsk@horde.org>
 * @since  Horde 3.2
 * @package Horde_Image
 */
class Horde_Image_Effect_gd_drop_shadow extends Horde_Image_Effect {

    /**
     * Valid parameters:
     *
     * @TODO
     *
     * @var array
     */
    var $_params = array('distance' => 5,
                         'width' => 2,
                         'hexcolor' => '000000',
                         'angle' => 215,
                         'fade' => 10);

    /**
     * Apply the drop_shadow effect.
     *
     * @return mixed true | PEAR_Error
     */
    function apply()
    {
        $distance = $this->_params['distance'];
        $width = $this->_params['width'];
        $hexcolor = $this->_params['hexcolor'];
        $angle = $this->_params['angle'];
        $fade = $this->_params['fade'];

        $width_shadow  = cos(deg2rad($angle)) * ($distance + $width);
        $height_shadow = sin(deg2rad($angle)) * ($distance + $width);
        $gdimg = $this->_image->_im;
        $imgX = $this->_image->_call('imageSX', array($gdimg));
        $imgY = $this->_image->_call('imageSY', array($gdimg));

        $offset['x'] = cos(deg2rad($angle)) * ($distance + $width - 1);
        $offset['y'] = sin(deg2rad($angle)) * ($distance + $width - 1);

        $tempImageWidth  = $imgX  + abs($offset['x']);
        $tempImageHeight = $imgY + abs($offset['y']);
        $gdimg_dropshadow_temp = $this->_image->_create($tempImageWidth,
                                                        $tempImageHeight);
        if (!is_a($gdimg_dropshadow_temp, 'PEAR_Error')) {
            $this->_image->_call('imageAlphaBlending',
                                 array($gdimg_dropshadow_temp, false));

            $this->_image->_call('imageSaveAlpha',
                                 array($gdimg_dropshadow_temp, true));

            $transparent1 = $this->_image->_allocateColorAlpha($gdimg_dropshadow_temp,
                                                               0, 0, 0, 127);

            if (is_a($transparent1, 'PEAR_Error')) {
                return $transparent1;
            }

            $this->_image->_call('imageFill',
                                 array($gdimg_dropshadow_temp, 0, 0, $transparent1));

            for ($x = 0; $x < $imgX; $x++) {
                for ($y = 0; $y < $imgY; $y++) {
                    $colorat = $this->_image->_call('imageColorAt', array($gdimg, $x, $y));
                    $PixelMap[$x][$y] = $this->_image->_call('imageColorsForIndex',
                                                             array($gdimg, $colorat));
                }
            }

            /* Creates the shadow */
            $r = hexdec(substr($hexcolor, 0, 2));
            $g = hexdec(substr($hexcolor, 2, 2));
            $b = hexdec(substr($hexcolor, 4, 2));

            /* Essentially masks the original image and creates the shadow */
            for ($x = 0; $x < $tempImageWidth; $x++) {
                for ($y = 0; $y < $tempImageHeight; $y++) {
                        if (!isset($PixelMap[$x][$y]['alpha']) ||
                            ($PixelMap[$x][$y]['alpha'] > 0)) {
                            if (isset($PixelMap[$x + $offset['x']][$y + $offset['y']]['alpha']) && ($PixelMap[$x + $offset['x']][$y + $offset['y']]['alpha'] < 127)) {
                                $thisColor = $this->_image->_allocateColorAlpha($gdimg_dropshadow_temp, $r, $g, $b, $PixelMap[$x + $offset['x']][$y + $offset['y']]['alpha']);
                                $this->_image->_call('imageSetPixel',
                                                     array($gdimg_dropshadow_temp, $x, $y, $thisColor));
                            }
                        }
                }
            }
            /* Overlays the original image */
            $this->_image->_call('imageAlphaBlending',
                                 array($gdimg_dropshadow_temp, true));

            for ($x = 0; $x < $imgX; $x++) {
                for ($y = 0; $y < $imgY; $y++) {
                    if ($PixelMap[$x][$y]['alpha'] < 127) {
                        $thisColor = $this->_image->_allocateColorAlpha($gdimg_dropshadow_temp, $PixelMap[$x][$y]['red'], $PixelMap[$x][$y]['green'], $PixelMap[$x][$y]['blue'], $PixelMap[$x][$y]['alpha']);
                        $this->_image->_call('imageSetPixel',
                                             array($gdimg_dropshadow_temp, $x, $y, $thisColor));
                    }
                }
            }

            $this->_image->_call('imageSaveAlpha',
                                 array($gdimg, true));
            $this->_image->_call('imageAlphaBlending',
                                 array($gdimg, false));

            // Why are we flood filling with alpha on the original?/////
            //$transparent2 = $this->_image->_allocateColorAlpha($gdimg, 0, 0, 0, 127);
            //$this->_image->_call('imageFilledRectangle',
                //                 array($gdimg, 0, 0, $imgX, $imgY, $transparent2));

            // Merge the shadow and the original into the original.
            $this->_image->_call('imageCopyResampled',
                                 array($gdimg, $gdimg_dropshadow_temp, 0, 0, 0, 0, $imgX, $imgY, $this->_image->_call('imageSX', array($gdimg_dropshadow_temp)), $this->_image->_call('imageSY', array($gdimg_dropshadow_temp))));

            $this->_image->_call('imageDestroy', array($gdimg_dropshadow_temp));
        }
        return true;
    }

}
