<?php
/**
 * Effect for creating a polaroid looking image.
 *
 * $Horde: framework/Image/Image/Effect/im/polaroid_image.php,v 1.7.2.2 2009-03-23 18:15:48 mrubinsk Exp $
 *
 * @author  Michael J. Rubinsky <mrubinsk@horde.org>
 * @since   Horde 3.2
 * @package Horde_Image
 */
class Horde_Image_Effect_im_polaroid_image extends Horde_Image_Effect {

    /**
     * Valid parameters for the polaroid effect
     *
     * resize_height    -    The height that each individual thumbnail
     *                       should be resized to before composing on the image.
     *
     * background       -    The color of the image background.
     *
     * angle            -    Angle to rotate the image.
     *
     * shadowcolor      -    The color of the image shadow.
     */

    /**
     * @var array
     */
    var $_params = array('background' => 'none',
                         'angle' => 0,
                         'shadowcolor' => 'black'
                         );

    /**
     * Create the effect
     *
     */
    function apply()
    {
        if (!is_null($this->_image->_imagick) &&
            $this->_image->_imagick->methodExists('polaroidImage') &&
            $this->_image->_imagick->methodExists('trimImage')) {

           // This determines the color of the underlying shadow.
           $this->_image->_imagick->setImageBackgroundColor($this->_params['shadowcolor']);

            $result = $this->_image->_imagick->polaroidImage($this->_params['angle']);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            // We need to create a new image to composite the polaroid over.
            // (yes, even if it's a transparent background evidently)
            $size = $this->_image->getDimensions();
            $imk = new Horde_Image_ImagickProxy($size['width'],
                                                $size['height'],
                                                $this->_params['background'],
                                                $this->_image->_type);

            $result = $imk->compositeImage($this->_image->_imagick,
                                       constant('Imagick::COMPOSITE_OVER'),
                                       0, 0);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
            $this->_image->_imagick->clear();
            $this->_image->_imagick->addImage($imk);
            $imk->destroy();


        } else {
            // Check for im version > 6.3.2
            $this->_image->_imagick = null;
            $ver = $this->_image->_getIMVersion();
            if (is_array($ver) && version_compare($ver[0], '6.3.2') >= 0) {
                $this->_image->_postSrcOperations[] = sprintf("-bordercolor \"#eee\" -background none -polaroid %s \( +clone -fill %s -draw 'color 0,0 reset' \) +swap +flatten",
                                                              $this->_params['angle'], $this->_params['background']);
            } else {
                $size = $this->_image->getDimensions();
                $this->_image->_postSrcOperations[] = sprintf("-bordercolor \"#eee\" -border 8 bordercolor grey90 -border 1 -bordercolor none -background none -rotate %s \( +clone -shadow 60x1.5+1+1 -rotate 90 -wave 1x%s -rotate 90 \) +swap -rotate 90 -wave 1x%s -rotate -90 -flatten \( +clone -fill %s -draw 'color 0,0 reset ' \) +swap -flatten",
                                                               $this->_params['angle'], $size['height'] * 2, $size['height'] * 2, $this->_params['background']);
            }
            return true;
        }
    }

}
