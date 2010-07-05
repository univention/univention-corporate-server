<?php
/**
 * Simple composite effect for composing multiple images. This effect assumes
 * that all images being passed in are already the desired size.
 *
 * $Horde: framework/Image/Image/Effect/im/composite.php,v 1.2.2.3 2009-05-27 22:42:05 mrubinsk Exp $
 *
 * Copyright 2009 The Horde Project (http://www.horde.org)
 *
 * @author  Michael J. Rubinsky <mrubinsk@horde.org>
 * @package Horde_Image
 */
class Horde_Image_Effect_im_composite extends Horde_Image_Effect {

    /**
     * Valid parameters for border effects:
     *
     * 'images'  - an array of Horde_Image objects to overlay.
     *
     *  ...and ONE of the following. If both are provided, the behaviour is
     *  undefined.
     *
     * 'gravity'    - the ImageMagick gravity constant describing placement
     *                (IM driver only so far, not imagick)
     *
     * 'x' and 'y'  - coordinates for the overlay placement.
     *
     * @var array
     */
    var $_params = array();

    /**
     * Draw the border.
     *
     * This draws the configured border to the provided image. Beware,
     * that every pixel inside the border clipping will be overwritten
     * with the background color.
     */
    function apply()
    {
        if (!is_null($this->_image->_imagick)) {
            foreach ($this->_params['images'] as $image) {
                $topimg = new Horde_Image_ImagickProxy();
                $topimg->clear();
                $topimg->readImageBlob($image->raw());

                /* Calculate center for composite (gravity center)*/
                $geometry = $this->_image->_imagick->getImageGeometry();
                $x = $geometry['width'] / 2;
                $y = $geometry['height'] / 2;

                if (isset($this->_params['x']) && isset($this->_params['y'])) {
                    $x = $this->_params['x'];
                    $y = $this->_params['y'];
                }
                $this->_image->_imagick->compositeImage($topimg, constant('Imagick::COMPOSITE_OVER'), $x, $y);
            }
        } else {
            $ops = $geometry = $gravity = '';
            if (isset($this->_params['gravity'])) {
                $gravity = ' -gravity ' . $this->_params['gravity'];
            }

            if (isset($this->_params['x']) && isset($this->_params['y'])) {
                $geometry = ' -geometry +' . $this->_params['x'] . '+' . $this->_params['y'] . ' ';
            }
            if (isset($this->_params['compose'])) {
                // The -matte ensures that the destination (background) image
                // has an alpha channel - to avoid black holes in the image.
                $compose = ' -compose ' . $this->_params['compose'] . ' -matte';
            }

            foreach($this->_params['images'] as $image) {
                $temp = $image->toFile();
                $this->_image->_toClean[] = $temp;
                $ops .= ' ' . $temp . $gravity . $compose . ' -composite';
            }
            $this->_image->_operations[] = $geometry;
            $this->_image->_postSrcOperations[] = $ops;
        }
        return true;
    }

}



