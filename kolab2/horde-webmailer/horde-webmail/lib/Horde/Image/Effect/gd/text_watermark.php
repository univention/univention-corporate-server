<?php
/**
 * Image effect for watermarking images with text for the im driver..
 *
 * $Horde: framework/Image/Image/Effect/gd/text_watermark.php,v 1.2.2.1 2007-12-20 13:49:11 jan Exp $
 *
 * @author  Michael J. Rubinsky <mrubinsk@horde.org>
 * @package Horde_Image
 */
class Horde_Image_Effect_gd_text_watermark extends Horde_Image_Effect {

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
     */
    function apply()
    {
        $color = $this->_image->_call('imageColorClosest',
                                      array($this->_image->_im, 255, 255, 255));
        if (is_a($color, 'PEAR_Error')) {
            return $color;
        }
        $shadow = $this->_image->_call('imageColorClosest',
                                       array($this->_image->_im, 0, 0, 0));
        if (is_a($shadow, 'PEAR_Error')) {
            return $shadow;
        }

        // Shadow offset in pixels.
        $drop = 1;

        // Maximum text width.
        $maxwidth = 200;

        // Amount of space to leave between the text and the image
        // border.
        $padding = 10;

        $f = $this->_image->getFont($this->_params['fontsize']);
        $fontwidth = $this->_image->_call('imageFontWidth', array($f));
        if (is_a($fontwidth, 'PEAR_Error')) {
            return $fontwidth;
        }
        $fontheight = $this->_image->_call('imageFontHeight', array($f));
        if (is_a($fontheight, 'PEAR_Error')) {
            return $fontheight;
        }

        // So that shadow is not off the image with right align and
        // bottom valign.
        $margin = floor($padding + $drop) / 2;

        if ($maxwidth) {
            $maxcharsperline = floor(($maxwidth - ($margin * 2)) / $fontwidth);
            $text = wordwrap($this->_params['text'], $maxcharsperline, "\n", 1);
        }

        // Split $text into individual lines.
        $lines = explode("\n", $text);

        switch ($this->_params['valign']) {
        case 'center':
            $y = ($this->_image->_call('imageSY', array($this->_image->_im)) - ($fontheight * count($lines))) / 2;
            break;

        case 'bottom':
            $y = $this->_image->_call('imageSY', array($this->_image->_im)) - (($fontheight * count($lines)) + $margin);
            break;

        default:
            $y = $margin;
            break;
        }

        switch ($this->_params['halign']) {
        case 'right':
            foreach ($lines as $line) {
                if (is_a($result = $this->_image->_call('imageString', array($this->_image->_im, $f, ($this->_image->_call('imageSX', array($this->_image->_im)) - $fontwidth * strlen($line)) - $margin + $drop, ($y + $drop), $line, $shadow)), 'PEAR_Error')) {
                    return $result;
                }
                $result = $this->_image->_call('imageString', array($this->_image->_im, $f, ($this->_image->_call('imageSX', array($this->_image->_im)) - $fontwidth * strlen($line)) - $margin, $y, $line, $color));
                $y += $fontheight;
            }
            break;

        case 'center':
            foreach ($lines as $line) {
                if (is_a($result = $this->_image->_call('imageString', array($this->_image->_im, $f, floor(($this->_image->_call('imageSX', array($this->_image->_im)) - $fontwidth * strlen($line)) / 2) + $drop, ($y + $drop), $line, $shadow)), 'PEAR_Error')) {
                    return $result;
                }
                $result = $this->_image->_call('imageString', array($this->_image->_im, $f, floor(($this->_image->_call('imageSX', array($this->_image->_im)) - $fontwidth * strlen($line)) / 2), $y, $line, $color));
                $y += $fontheight;
            }
            break;

        default:
            foreach ($lines as $line) {
                if (is_a($result = $this->_image->_call('imageString', array($this->_image->_im, $f, $margin + $drop, ($y + $drop), $line, $shadow)), 'PEAR_Error')) {
                    return $result;
                }
                $result = $this->_image->_call('imageString', array($this->_image->_im, $f, $margin, $y, $line, $color));
                $y += $fontheight;
            }
            break;
        }

        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
    }

}
