<?php
/**
 * Image effect for adding a drop shadow.
 *
 * $Horde: framework/Image/Image/Effect/im/drop_shadow.php,v 1.11.2.2 2009-03-23 18:15:48 mrubinsk Exp $
 *
 * @author  Michael J. Rubinsky <mrubinsk@horde.org>
 * @since   Horde 3.2
 * @package Horde_Image
 */
class Horde_Image_Effect_im_drop_shadow extends Horde_Image_Effect {

    /**
     * Valid parameters: Most are currently ignored for the im version
     * of this effect.
     *
     * @TODO
     *
     * @var array
     */
    var $_params = array('distance' => 5, // This is used as the x and y offset
                         'width' => 2,
                         'hexcolor' => '000000',
                         'angle' => 215,
                         'fade' => 3, // Sigma value
                         'padding' => 0,
                         'background' => 'none');

    /**
     * Apply the effect.
     *
     * @return mixed true | PEAR_Error
     */
    function apply()
    {
        if (!is_null($this->_image->_imagick)) {
            // $shadow is_a ImagickProxy object
            $shadow = $this->_image->_imagick->cloneIM();
            $shadow->setImageBackgroundColor('black');
            $shadow->shadowImage(80, $this->_params['fade'],
                                 $this->_params['distance'],
                                 $this->_params['distance']);


            // If we have an actual background color, we need to explicitly
            // create a new background image with that color to be sure there
            // *is* a background color.
            if ($this->_params['background'] != 'none') {
                $size = $shadow->getImageGeometry();
                $new = new Horde_Image_ImagickProxy($size['width'],
                                                    $size['height'],
                                                    $this->_params['background'],
                                                    $this->_image->_type);

                $new->compositeImage($shadow,
                                     constant('Imagick::COMPOSITE_OVER'), 0, 0);
                $shadow->clear();
                $shadow->addImage($new);
                $new->destroy();
            }

            if ($this->_params['padding']) {
                $shadow->borderImage($this->_params['background'],
                                     $this->_params['padding'],
                                     $this->_params['padding']);
            }
            $shadow->compositeImage($this->_image->_imagick,
                                    constant('Imagick::COMPOSITE_OVER'),
                                    0, 0);
            $this->_image->_imagick->clear();
            $this->_image->_imagick->addImage($shadow);
            $shadow->destroy();
        } else {
            $size = $this->_image->getDimensions();
            $this->_image->_postSrcoperations[] = "-size {$size['width']}x{$size['height']} xc:{$this->_params['background']} "
                . "-fill {$this->_params['background']} -draw \"matte 0,0 reset\" -tile";
            $this->_image->_postSrcOperations[] = '\( +clone -background black -shadow 80x' . $this->_params['fade'] . '+' . $this->_params['distance'] . '+' . $this->_params['distance'] . ' \) +swap -background none -flatten +repage -bordercolor ' . $this->_params['background'] . ' -border ' . $this->_params['padding'] ;
        }
        $this->_image->_width = 0;
        $this->_image->_height = 0;

        return true;
    }

}
