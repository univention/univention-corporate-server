<?php
/**
 * Image border decorator for the Horde_Image package.
 *
 * $Horde: framework/Image/Image/Effect/border.php,v 1.1.2.1 2007-12-20 13:49:11 jan Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @package Horde_Image
 */
class Horde_Image_Effect_border extends Horde_Image_Effect {

    /**
     * Valid parameters for border decorators:
     *
     *   padding         - Pixels from the image edge that the border will start.
     *   borderColor     - Border color. Defaults to black.
     *   fillColor       - Color to fill the border with. Defaults to white.
     *   lineWidth       - Border thickness, defaults to 1 pixel.
     *   roundWidth      - Width of the corner rounding. Defaults to none.
     *
     * @var array
     */
    var $_params = array('padding' => 0,
                         'borderColor' => 'black',
                         'fillColor' => 'white',
                         'lineWidth' => 1,
                         'roundWidth' => 0);

    /**
     * Draw the border.
     *
     * This draws the configured border to the provided image. Beware,
     * that every pixel inside the border clipping will be overwritten
     * with the background color.
     */
    function apply()
    {
        $o = $this->_params;

        $d = $this->_image->getDimensions();
        $x = $o['padding'];
        $y = $o['padding'];
        $width = $d['width'] - (2 * $o['padding']);
        $height = $d['height'] - (2 * $o['padding']);

        if ($o['roundWidth'] > 0) {
            $this->_image->roundedRectangle($x, $y, $width, $height, $o['roundWidth'], $o['borderColor'], $o['fillColor']);
        } else {
            $this->_image->rectangle($x, $y, $width, $height, $o['borderColor'], $o['fillColor']);
        }
    }

}
