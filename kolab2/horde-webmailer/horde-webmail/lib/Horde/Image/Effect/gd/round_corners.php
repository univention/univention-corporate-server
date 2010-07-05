<?php
/**
 * Image effect for round image corners.
 *
 * $Horde: framework/Image/Image/Effect/gd/round_corners.php,v 1.6.2.1 2007-12-20 13:49:11 jan Exp $
 *
 * This algorithm is from the phpThumb project available at
 * http://phpthumb.sourceforge.net and all credit for this script should go to
 * James Heinrich <info@silisoftware.com>.  Modifications made to the code
 * to fit it within the Horde framework and to adjust for our coding standards.
 *
 * @author  Michael J. Rubinsky <mrubinsk@horde.org>
 * @since   Horde 3.2
 * @package Horde_Image
 */
class Horde_Image_Effect_gd_round_corners extends Horde_Image_Effect {

    /**
     * Valid parameters:
     *
     * radius - Radius of rounded corners.
     *
     * @var array
     */
    var $_params = array('radius' => 10);

    /**
     * Apply the round_corners effect.
     *
     * @return mixed true | PEAR_Error
     */
    function apply()
    {
        // Original comments from phpThumb projet:
        // generate mask at twice desired resolution and downsample afterwards
        // for easy antialiasing mask is generated as a white double-size
        // elipse on a triple-size black background and copy-paste-resampled
        // onto a correct-size mask image as 4 corners due to errors when the
        // entire mask is resampled at once (gray edges)
        $radius_x = $radius_y = $this->_params['radius'];
        $gdimg = $this->_image->_im;
        $imgX = round($this->_image->_call('imageSX', array($gdimg)));
        $imgY = round($this->_image->_call('imageSY', array($gdimg)));

        $gdimg_cornermask_triple = $this->_image->_create(round($radius_x * 6),
                                                          round($radius_y * 6));
        if (!is_a($gdimg_cornermask_triple, 'PEAR_Error')) {

            $gdimg_cornermask = $this->_image->_create($imgX, $imgY);
            if (!is_a($gdimg_cornermask, 'PEAR_Error')) {
                $color_transparent = $this->_image->_call('imageColorAllocate',
                                                          array($gdimg_cornermask_triple,
                                                                255,
                                                                255,
                                                                255));

                $this->_image->_call('imageFilledEllipse',
                                     array($gdimg_cornermask_triple,
                                           $radius_x * 3,
                                           $radius_y * 3,
                                           $radius_x * 4,
                                           $radius_y * 4,
                                           $color_transparent));

                $this->_image->_call('imageFilledRectangle',
                                     array($gdimg_cornermask,
                                           0,
                                           0,
                                           $imgX,
                                           $imgY,
                                           $color_transparent));

                $this->_image->_call('imageCopyResampled',
                                     array($gdimg_cornermask,
                                           $gdimg_cornermask_triple,
                                           0,
                                           0,
                                           $radius_x,
                                           $radius_y,
                                           $radius_x,
                                           $radius_y,
                                           $radius_x * 2,
                                           $radius_y * 2));

                $this->_image->_call('imageCopyResampled',
                                     array($gdimg_cornermask,
                                           $gdimg_cornermask_triple,
                                           0,
                                           $imgY - $radius_y,
                                           $radius_x,
                                           $radius_y * 3,
                                           $radius_x,
                                           $radius_y,
                                           $radius_x * 2,
                                           $radius_y * 2));

                $this->_image->_call('imageCopyResampled',
                                     array($gdimg_cornermask,
                                           $gdimg_cornermask_triple,
                                           $imgX - $radius_x,
                                           $imgY - $radius_y,
                                           $radius_x * 3,
                                           $radius_y * 3,
                                           $radius_x,
                                           $radius_y,
                                           $radius_x * 2,
                                           $radius_y * 2));

                $this->_image->_call('imageCopyResampled',
                                     array($gdimg_cornermask,
                                           $gdimg_cornermask_triple,
                                           $imgX - $radius_x,
                                           0,
                                           $radius_x * 3,
                                           $radius_y,
                                           $radius_x,
                                           $radius_y,
                                           $radius_x * 2,
                                           $radius_y * 2));

                $result = $this->_image->_applyMask($gdimg_cornermask);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }
                $this->_image->_call('imageDestroy', array($gdimg_cornermask));
                return true;
            } else {
                return $gdimg_cornermas; // PEAR_Error
            }
            $this->_image->_call('imageDestroy',
                                 array($gdimg_cornermask_triple));
        } else {
            return $gdimg_cornermas_triple; // PEAR_Error
        }
    }

}
