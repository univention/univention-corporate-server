<?php
/**
 * Image border decorator for the Horde_Image package.
 *
 * $Horde: framework/Image/Image/Decorator/border.php,v 1.1 2004/05/04 21:36:10 chuck Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @package Horde_Image
 */
class Horde_Image_Decorator_border {

    /**
     * Valid parameters for border decorators:
     *
     *   padding         - Pixels from the image edge that the border will start.
     *   borderColor     - Border color. Defaults to black.
     *   fillColor       - Color to fill the border with. Defaults to white.
     *   lineWidth       - Border thickness, defaults to 1 pixel.
     *   roundWidth      - Width of the corner rounding. Defaults to none.
     *
     * @var array $_params
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
     *
     * @access public
     */
    function draw(&$image)
    {
        $o = $this->_params;

        $d = $image->getDimensions();
        $x = $o['padding'];
        $y = $o['padding'];
        $width = $d['width'] - (2 * $o['padding']);
        $height = $d['height'] - (2 * $o['padding']);

        if ($o['roundWidth'] > 0) {
            $image->roundedRectangle($x, $y, $width, $height, $o['roundWidth'], $o['borderColor'], $o['fillColor']);
        } else {
            $image->rectangle($x, $y, $width, $height, $o['borderColor'], $o['fillColor']);
        }
    }

}
