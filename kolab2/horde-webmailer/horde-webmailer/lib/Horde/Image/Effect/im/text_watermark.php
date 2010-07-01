<?php
/**
 * Image effect for watermarking images with text for the im driver..
 *
 * $Horde: framework/Image/Image/Effect/im/text_watermark.php,v 1.3.2.1 2007-12-20 13:49:11 jan Exp $
 *
 * @author  Michael J. Rubinsky <mrubinsk@horde.org>
 * @since   Horde 3.2
 * @package Horde_Image
 */
class Horde_Image_Effect_im_text_watermark extends Horde_Image_Effect {

    /**
     * Valid parameters for watermark effects:
     *
     *   text (required)  - The text of the watermark.
     *   halign           - The horizontal placement
     *   valign           - The vertical placement
     *   font             - The font name or family to use
     *   fontsize         - The size of the font to use
     *                      (small, medium, large, giant)
     *
     * @var array
     */
    var $_params = array('halign' => 'right',
                         'valign' => 'bottom',
                         'font' => 'courier',
                         'fontsize' => 'small');

    /**
     * Add the watermark
     *
     */
    function apply()
    {
        /* Determine placement on image */
        switch ($this->_params['valign']) {
        case 'bottom':
            $v = 'south';
            break;
        case 'center':
            $v = 'center';
            break;
        default:
            $v = 'north';
        }

        switch ($this->_params['halign']) {
        case 'right':
            $h = 'east';
            break;
        case 'center':
            $h = 'center';
            break;
        default:
            $h = 'west';

        }
        if (($v == 'center' && $h != 'center') ||
            ($v == 'center' && $h == 'center')) {
            $gravity = $h;
        } elseif ($h == 'center' && $v != 'center') {
            $gravity = $v;
        } else {
            $gravity = $v . $h;
        }
        /* Determine font point size */
        $point = $this->_image->_getFontSize($this->_params['fontsize']);
        $this->_image->raw();
        $this->_image->_postSrcOperations[] = ' -font ' . $this->_params['font'] . ' -pointsize ' . $point . ' \( +clone -resize 1x1 -fx 1-intensity -threshold 50% -scale 32x32 -write mpr:color +delete \) -tile mpr:color -gravity ' . $gravity . ' -annotate +20+10 "' . $this->_params['text'] . '"';
        $this->_image->raw();
    }

}
