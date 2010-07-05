<?php
/**
 * Image effect for rounding image corners.
 *
 * $Horde: framework/Image/Image/Effect/im/round_corners.php,v 1.13.2.2 2009-03-23 18:15:48 mrubinsk Exp $
 *
 * @author  Michael J. Rubinsky <mrubinsk@horde.org>
 * @since   Horde 3.2
 * @package Horde_Image
 */
class Horde_Image_Effect_im_round_corners extends Horde_Image_Effect {

    /**
     * Valid parameters:
     *
     *  radius - Radius of rounded corners.
     *
     * @var array
     */
    var $_params = array('radius' => 10,
                         'background' => 'none',
                         'border' => 0,
                         'bordercolor' => 'none');

    function apply()
    {
        /* Use imagick extension if available */
        $round = $this->_params['radius'];
        // Apparently roundCorners() requires imagick to be compiled against
        // IM > 6.2.8.
        if (!is_null($this->_image->_imagick) &&
            $this->_image->_imagick->methodExists('roundCorners')) {
            $result = $this->_image->_imagick->roundCorners($round, $round);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            // Using a border?
            if ($this->_params['bordercolor'] != 'none' &&
                $this->_params['border'] > 0) {

                $size = $this->_image->getDimensions();

                $new = new Horde_Image_ImagickProxy($size['width'] + $this->_params['border'],
                                                    $size['height'] + $this->_params['border'],
                                                    $this->_params['bordercolor'],
                                                    $this->_image->_type);

                $result = $new->roundCorners($round, $round);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }
                $new->compositeImage($this->_image->_imagick,
                                     constant('Imagick::COMPOSITE_OVER'), 1, 1);
                $this->_image->_imagick->clear();
                $this->_image->_imagick->addImage($new);
                $new->destroy();
            }

            // If we have a background other than 'none' we need to
            // compose two images together to make sure we *have* a background.
            if ($this->_params['background'] != 'none') {
                $size = $this->_image->getDimensions();
                $new = new Horde_Image_ImagickProxy($size['width'],
                                                    $size['height'],
                                                    $this->_params['background'],
                                                    $this->_image->_type);



                $new->compositeImage($this->_image->_imagick,
                                     constant('Imagick::COMPOSITE_OVER'), 0, 0);
                $this->_image->_imagick->clear();
                $this->_image->_imagick->addImage($new);
                $new->destroy();
            }
        } else {
            // Get image dimensions
            $dimensions = $this->_image->getDimensions();
            $height = $dimensions['height'];
            $width = $dimensions['width'];

            // Make sure we don't attempt to use Imagick for any other effects
            // to make sure we do them in the proper order.
            $this->_image->_imagick = null;

            $this->_image->_operations[] = "-size {$width}x{$height} xc:{$this->_params['background']} "
                . "-fill {$this->_params['background']} -draw \"matte 0,0 reset\" -tile";

            $this->_image->roundedRectangle(round($round / 2),
                                    round($round / 2),
                                    $width - round($round / 2) - 2,
                                    $height - round($round / 2) - 2,
                                    $round + 2,
                                    'none',
                                    'white');
        }

        // Reset width/height since these might have changed
        $this->_image->_width = 0;
        $this->_image->_height = 0;
        return true;
    }
}
