<?php

require_once dirname(__FILE__) . '/../Image.php';

/**
 * This class implements the Horde_Image:: API for the PHP GD
 * extension. It mainly provides some utility functions, such as the
 * ability to make pixels, for now.
 *
 * $Horde: framework/Image/Image/gd.php,v 1.48.10.23 2009-04-14 04:13:20 mrubinsk Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 3.0
 * @package Horde_Image
 */
class Horde_Image_gd extends Horde_Image {

    /**
     * Capabilites of this driver.
     *
     * @var array
     */
    var $_capabilities = array('resize',
                               'crop',
                               'rotate',
                               'flip',
                               'mirror',
                               'grayscale',
                               'sepia',
                               'yellowize',
                               'canvas',
                         );

    /**
     * GD Image resource for the current image data.
     *
     * @var resource
     */
    var $_im;

    /**
     * String identifier of the current image. New image data will not be
     * loaded if the same id is already loaded.
     *
     * @var string
     */
    var $_id = '';

    function Horde_Image_gd($params)
    {
        parent::Horde_Image($params);
        if (!empty($params['type'])) {
            $this->_type = $params['type'];
        }

        if (!empty($params['width'])) {
            $this->_im = &$this->_create($this->_width, $this->_height);
            if (is_a($this->_im, 'PEAR_Error')) {
                return $this->_im;
            }
            if (is_resource($this->_im)) {
                $this->_call('imageFill', array($this->_im, 0, 0, $this->_allocateColor($this->_background)));
            }
        }
    }

    function getContentType()
    {
        return 'image/' . $this->_type;
    }

    /**
     * Display the current image.
     */
    function display()
    {
        $this->headers();
        return $this->_call('image' . $this->_type, array($this->_im));
    }

    /**
     * Returns the raw data for this image.
     *
     * @param boolean $convert  If true, the image data will be returned in the
     *                          target format, independently from any image
     *                          operations.
     *
     * @return string  The raw image data.
     */
    function raw($convert = false)
    {
        if (!is_resource($this->_im)) {
            return '';
        }
        return Util::bufferOutput('image' . $this->_type, $this->_im);
    }

    /**
     * Reset the image data.
     */
    function reset()
    {
        parent::reset();
        if (is_resource($this->_im)) {
            return $this->_call('imageDestroy', array($this->_im));
        }
        return true;
    }

    /**
     * Get the height and width of the current image.
     *
     * @return array  An hash with 'width' containing the width,
     *                'height' containing the height of the image.
     */
    function getDimensions()
    {
        if (is_a($this->_im, 'PEAR_Error')) {
            return $this->_im;
        } elseif (is_resource($this->_im) &&
                  $this->_width == 0 &&
                  $this->_height ==0) {

            $this->_width = $this->_call('imageSX', array($this->_im));
            $this->_height = $this->_call('imageSY', array($this->_im));
            return array('width' => $this->_width,
                         'height' => $this->_height);
        } else {
            return array('width' => $this->_width,
                         'height' => $this->_height);
        }
    }

    /**
     * Creates a color that can be accessed in this object. When a
     * color is set, the integer resource of it is returned.
     *
     * @param string $name  The name of the color.
     *
     * @return integer  The resource of the color that can be passed to GD.
     */
    function _allocateColor($name)
    {
        static $colors = array();

        if (empty($colors[$name])) {
            list($r, $g, $b) = $this->getRGB($name);
            $colors[$name] = $this->_call('imageColorAllocate', array($this->_im, $r, $g, $b));
        }

        return $colors[$name];
    }

    function getFont($font)
    {
        switch ($font) {
        case 'tiny':
            return 1;

        case 'medium':
            return 3;

        case 'large':
            return 4;

        case 'giant':
            return 5;

        case 'small':
        default:
            return 2;
        }
    }

    /**
     * Load the image data from a string.
     *
     * @param string $id          An arbitrary id for the image.
     * @param string $image_data  The data to use for the image.
     */
    function loadString($id, $image_data)
    {
        if ($id != $this->_id) {
            if ($this->_im) {
                if (is_a($result = $this->reset(), 'PEAR_Error')) {
                    return $result;
                }
            }
            $this->_im = &$this->_call('imageCreateFromString', array($image_data));
            $this->_id = $id;
            if (is_a($this->_im, 'PEAR_Error')) {
                return $this->_im;
            }
        }
    }

    /**
     * Load the image data from a file.
     *
     * @param string $filename  The full path and filename to the file to load
     *                          the image data from. The filename will also be
     *                          used for the image id.
     *
     * @return mixed  PEAR Error if file does not exist or could not be loaded
     *                otherwise NULL if successful or already loaded.
     */
    function loadFile($filename)
    {
        if (is_a($result = $this->reset(), 'PEAR_Error')) {
            return $result;
        }

        if (is_a($info = $this->_call('getimagesize', array($filename)), 'PEAR_Error')) {
            return $info;
        }

        if (is_array($info)) {
            switch ($info[2]) {
            case 1:
                if (function_exists('imagecreatefromgif')) {
                    $this->_im = &$this->_call('imagecreatefromgif', array($filename));
                }
                break;
            case 2:
                $this->_im = &$this->_call('imagecreatefromjpeg', array($filename));
                break;
            case 3:
                $this->_im = &$this->_call('imagecreatefrompng', array($filename));
                break;
            case 15:
                if (function_exists('imagecreatefromgwbmp')) {
                    $this->_im = &$this->_call('imagecreatefromgwbmp', array($filename));
                }
                break;
            case 16:
                $this->_im = &$this->_call('imagecreatefromxbm', array($filename));
                break;
            }
        }

        if (is_a($this->_im, 'PEAR_Error')) {
            return $this->_im;
        }

        if (is_resource($this->_im)) {
            return;
        }

        $result = parent::loadFile($filename);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        return $this->_im = &$this->_call('imageCreateFromString', array($this->_data));
    }

    /**
     * Resize the current image.
     *
     * @param integer $width      The new width.
     * @param integer $height     The new height.
     * @param boolean $ratio      Maintain original aspect ratio.
     *
     * @return PEAR_Error on failure
     */
    function resize($width, $height, $ratio = true)
    {
        /* Abort if we're asked to divide by zero, truncate the image
         * completely in either direction, or there is no image data. */
        if (!$width || !$height || !is_resource($this->_im)) {
            return;
        }

        if ($ratio) {
            if ($width / $height > $this->_call('imageSX', array($this->_im)) / $this->_call('imageSY', array($this->_im))) {
                $width = $height * $this->_call('imageSX', array($this->_im)) / $this->_call('imageSY', array($this->_im));
            } else {
                $height = $width * $this->_call('imageSY', array($this->_im)) / $this->_call('imageSX', array($this->_im));
            }
        }

        $im = $this->_im;
        $this->_im = &$this->_create($width, $height);

        /* Reset geometry since it will change */
        $this->_width = 0;
        $this->_height = 0;

        if (is_a($this->_im, 'PEAR_Error')) {
            return $this->_im;
        }
        if (is_a($result = $this->_call('imageFill', array($this->_im, 0, 0, $this->_call('imageColorAllocate', array($this->_im, 255, 255, 255)))), 'PEAR_Error')) {
            return $result;
        }
        if (is_a($this->_call('imageCopyResampled', array($this->_im, $im, 0, 0, 0, 0, $width, $height, $this->_call('imageSX', array($im)), $this->_call('imageSY', array($im)))), 'PEAR_Error')) {
            return $this->_call('imageCopyResized', array($this->_im, $im, 0, 0, 0, 0, $width, $height, $this->_call('imageSX', array($im)), $this->_call('imageSY', array($im))));
        }
    }

    /**
     * Crop the current image.
     *
     * @param integer $x1  The top left corner of the cropped image.
     * @param integer $y1  The top right corner of the cropped image.
     * @param integer $x2  The bottom left corner of the cropped image.
     * @param integer $y2  The bottom right corner of the cropped image.
     */
    function crop($x1, $y1, $x2, $y2)
    {
        $im = $this->_im;
        $this->_im = &$this->_create($x2 - $x1, $y2 - $y1);
        if (is_a($this->_im, 'PEAR_Error')) {
            return $this->_im;
        }
        $this->_width = 0;
        $this->_height = 0;
        return $this->_call('imageCopy', array($this->_im, $im, 0, 0, $x1, $y1, $x2 - $x1, $y2 - $y1));
    }

    /**
     * Rotate the current image.
     *
     * @param integer $angle       The angle to rotate the image by,
     *                             in the clockwise direction
     * @param integer $background  The background color to fill any triangles
     */
    function rotate($angle, $background = 'white')
    {
        if (!function_exists('imagerotate')) {
            return;
        }

        $background = $this->_allocateColor($background);
        if (is_a($background, 'PEAR_Error')) {
            return $background;
        }

        $this->_width = 0;
        $this->_height = 0;

        switch ($angle) {
        case '90':
            $x = $this->_call('imageSX', array($this->_im));
            $y = $this->_call('imageSY', array($this->_im));
            $xymax = max($x, $y);

            $im = &$this->_create($xymax, $xymax);
            if (is_a($im, 'PEAR_Error')) {
                return $im;
            }
            if (is_a($result = $this->_call('imageCopy', array($im, $this->_im, 0, 0, 0, 0, $x, $y)), 'PEAR_Error')) {
                return $result;
            }
            $im = &$this->_call('imageRotate', array($im, 270, $background));
            if (is_a($im, 'PEAR_Error')) {
                return $im;
            }
            $this->_im = $im;
            $im = &$this->_create($y, $x);
            if (is_a($im, 'PEAR_Error')) {
                return $im;
            }
            if ($x < $y) {
                if (is_a($result = $this->_call('imageCopy', array($im, $this->_im, 0, 0, 0, 0, $xymax, $xymax)), 'PEAR_Error')) {
                    return $result;
                }
            } elseif ($x > $y) {
                if (is_a($result = $this->_call('imageCopy', array($im, $this->_im, 0, 0, $xymax - $y, $xymax - $x, $xymax, $xymax)), 'PEAR_Error')) {
                    return $result;
                }
            }
            $this->_im = $im;
            break;

        default:
            $this->_im = &$this->_call('imageRotate', array($this->_im, 360 - $angle, $background));
            if (is_a($this->_im, 'PEAR_Error')) {
                return $this->_im;
            }
            break;
        }
    }

    /**
     * Flip the current image.
     */
    function flip()
    {
        $x = $this->_call('imageSX', array($this->_im));
        $y = $this->_call('imageSY', array($this->_im));

        $im = &$this->_create($x, $y);
        if (is_a($im, 'PEAR_Error')) {
            return $im;
        }
        for ($curY = 0; $curY < $y; $curY++) {
            if (is_a($result = $this->_call('imageCopy', array($im, $this->_im, 0, $y - ($curY + 1), 0, $curY, $x, 1)), 'PEAR_Error')) {
                return $result;
            }
        }

        $this->_im = $im;
    }

    /**
     * Mirror the current image.
     */
    function mirror()
    {
        $x = $this->_call('imageSX', array($this->_im));
        $y = $this->_call('imageSY', array($this->_im));

        $im = &$this->_create($x, $y);
        if (is_a($im, 'PEAR_Error')) {
            return $im;
        }
        for ($curX = 0; $curX < $x; $curX++) {
            if (is_a($result = $this->_call('imageCopy', array($im, $this->_im, $x - ($curX + 1), 0, $curX, 0, 1, $y)), 'PEAR_Error')) {
                return $result;
            }
        }

        $this->_im = $im;
    }

    /**
     * Convert the current image to grayscale.
     */
    function grayscale()
    {
        $rateR = .229;
        $rateG = .587;
        $rateB = .114;
        $whiteness = 3;

        if (function_exists('imageistruecolor') && $this->_call('imageIsTrueColor', array($this->_im)) === true) {
            if (is_a($result = $this->_call('imageTrueColorToPalette', array($this->_im, true, 256)), 'PEAR_Error')) {
                return $result;
            }
        }

        $colors = min(256, $this->_call('imageColorsTotal', array($this->_im)));
        for ($x = 0; $x < $colors; $x++) {
            $src = $this->_call('imageColorsForIndex', array($this->_im, $x));
            if (is_a($src, 'PEAR_Error')) {
                return $src;
            }
            $new = min(255, abs($src['red'] * $rateR + $src['green'] * $rateG + $src['blue'] * $rateB) + $whiteness);
            if (is_a($result = $this->_call('imageColorSet', array($this->_im, $x, $new, $new, $new)), 'PEAR_Error')) {
                return $result;
            }
        }
    }

    /**
     * Sepia filter.
     *
     * Basically turns the image to grayscale and then adds some
     * defined tint on it (R += 30, G += 43, B += -23) so it will
     * appear to be a very old picture.
     */
    function sepia()
    {
        $tintR = 80;
        $tintG = 43;
        $tintB = -23;
        $rateR = .229;
        $rateG = .587;
        $rateB = .114;
        $whiteness = 3;

        if ($this->_call('imageIsTrueColor', array($this->_im)) === true) {
            if (is_a($result = $this->_call('imageTrueColorToPalette', array($this->_im, true, 256)), 'PEAR_Error')) {
                return $result;
            }
        }

        $colors = max(256, $this->_call('imageColorsTotal', array($this->_im)));
        for ($x = 0; $x < $colors; $x++) {
            $src = $this->_call('imageColorsForIndex', array($this->_im, $x));
            if (is_a($src, 'PEAR_Error')) {
                return $src;
            }
            $new = min(255, abs($src['red'] * $rateR + $src['green'] * $rateG + $src['blue'] * $rateB) + $whiteness);
            $r = min(255, $new + $tintR);
            $g = min(255, $new + $tintG);
            $b = min(255, $new + $tintB);
            if (is_a($result = $this->_call('imageColorSet', array($this->_im, $x, $r, $g, $b)), 'PEAR_Error')) {
                return $result;
            }
        }
    }

    /**
     * Yellowize filter.
     *
     * Adds a layer of yellow that can be transparent or solid. If
     * $intensityA is 255 the image will be 0% transparent (solid).
     *
     * @param integer $intensityY  How strong should the yellow (red and green) be? (0-255)
     * @param integer $intensityB  How weak should the blue be? (>= 2, in the positive limit it will be make BLUE 0)
     */
    function yellowize($intensityY = 50, $intensityB = 3)
    {
        if ($this->_call('imageIsTrueColor', array($this->_im)) === true) {
            if (is_a($result = $this->_call('imageTrueColorToPalette', array($this->_im, true, 256)), 'PEAR_Error')) {
                return $result;
            }
        }

        $colors = max(256, $this->_call('imageColorsTotal', array($this->_im)));
        for ($x = 0; $x < $colors; $x++) {
            $src = $this->_call('imageColorsForIndex', array($this->_im, $x));
            if (is_a($src, 'PEAR_Error')) {
                return $src;
            }
            $r = min($src['red'] + $intensityY, 255);
            $g = min($src['green'] + $intensityY, 255);
            $b = max(($r + $g) / max($intensityB, 2), 0);
            if (is_a($result = $this->_call('imageColorSet', array($this->_im, $x, $r, $g, $b)), 'PEAR_Error')) {
                return $result;
            }
        }
    }

    /**
     * Draws a text string on the image in a specified location, with
     * the specified style information.
     *
     * @param string  $text       The text to draw.
     * @param integer $x          The left x coordinate of the start of the
     *                            text string.
     * @param integer $y          The top y coordinate of the start of the text
     *                            string.
     * @param string  $font       The font identifier you want to use for the
     *                            text.
     * @param string  $color      The color that you want the text displayed in.
     * @param integer $direction  An integer that specifies the orientation of
     *                            the text.
     */
    function text($string, $x, $y, $font = 'monospace', $color = 'black', $direction = 0, $fontsize = 'small')
    {
        $c = $this->_allocateColor($color);
        if (is_a($c, 'PEAR_Error')) {
            return $c;
        }
        $f = $this->getFont($font);
        switch ($direction) {
        case -90:
        case 270:
            $result = $this->_call('imageStringUp', array($this->_im, $f, $x, $y, $string, $c));
            break;

        case 0:
        default:
            $result = $this->_call('imageString', array($this->_im, $f, $x, $y, $string, $c));
        }

        return $result;
    }

    /**
     * Draw a circle.
     *
     * @param integer $x     The x co-ordinate of the centre.
     * @param integer $y     The y co-ordinate of the centre.
     * @param integer $r     The radius of the circle.
     * @param string $color  The line color of the circle.
     * @param string $fill   The color to fill the circle.
     */
    function circle($x, $y, $r, $color, $fill = null)
    {
        $c = $this->_allocateColor($color);
        if (is_a($c, 'PEAR_Error')) {
            return $c;
        }
        if (is_null($fill)) {
            $result = $this->_call('imageEllipse', array($this->_im, $x, $y, $r * 2, $r * 2, $c));
        } else {
            if ($fill !== $color) {
                $fillColor = $this->_allocateColor($fill);
                if (is_a($fillColor, 'PEAR_Error')) {
                    return $fillColor;
                }
                if (is_a($result = $this->_call('imageFilledEllipse', array($this->_im, $x, $y, $r * 2, $r * 2, $fillColor)), 'PEAR_Error')) {
                    return $result;
                }
                $result = $this->_call('imageEllipse', array($this->_im, $x, $y, $r * 2, $r * 2, $c));
            } else {
                $result = $this->_call('imageFilledEllipse', array($this->_im, $x, $y, $r * 2, $r * 2, $c));
            }
        }
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
    }

    /**
     * Draw a polygon based on a set of vertices.
     *
     * @param array $vertices  An array of x and y labeled arrays
     *                         (eg. $vertices[0]['x'], $vertices[0]['y'], ...).
     * @param string $color    The color you want to draw the polygon with.
     * @param string $fill     The color to fill the polygon.
     */
    function polygon($verts, $color, $fill = 'none')
    {
        $vertices = array();
        foreach ($verts as $vert) {
            $vertices[] = $vert['x'];
            $vertices[] = $vert['y'];
        }

        if ($fill != 'none') {
            $f = $this->_allocateColor($fill);
            if (is_a($f, 'PEAR_Error')) {
                return $f;
            }
            if (is_a($result = $this->_call('imageFilledPolygon', array($this->_im, $vertices, count($verts), $f)), 'PEAR_Error')) {
                return $result;
            }
        }

        if ($fill == 'none' || $fill != $color) {
            $c = $this->_allocateColor($color);
            if (is_a($c, 'PEAR_Error')) {
                return $c;
            }
            if (is_a($result = $this->_call('imagePolygon', array($this->_im, $vertices, count($verts), $c)), 'PEAR_Error')) {
                return $result;
            }
        }
    }

    /**
     * Draw a rectangle.
     *
     * @param integer $x       The left x-coordinate of the rectangle.
     * @param integer $y       The top y-coordinate of the rectangle.
     * @param integer $width   The width of the rectangle.
     * @param integer $height  The height of the rectangle.
     * @param string $color    The line color of the rectangle.
     * @param string $fill     The color to fill the rectangle with.
     */
    function rectangle($x, $y, $width, $height, $color = 'black', $fill = 'none')
    {
        if ($fill != 'none') {
            $f = $this->_allocateColor($fill);
            if (is_a($f, 'PEAR_Error')) {
                return $f;
            }
            if (is_a($result = $this->_call('imageFilledRectangle', array($this->_im, $x, $y, $x + $width, $y + $height, $f)), 'PEAR_Error')) {
                return $result;
            }
        }

        if ($fill == 'none' || $fill != $color) {
            $c = $this->_allocateColor($color);
            if (is_a($c, 'PEAR_Error')) {
                return $c;
            }
            if (is_a($result = $this->_call('imageRectangle', array($this->_im, $x, $y, $x + $width, $y + $height, $c)), 'PEAR_Error')) {
                return $result;
            }
        }
    }

    /**
     * Draw a rounded rectangle.
     *
     * @param integer $x       The left x-coordinate of the rectangle.
     * @param integer $y       The top y-coordinate of the rectangle.
     * @param integer $width   The width of the rectangle.
     * @param integer $height  The height of the rectangle.
     * @param integer $round   The width of the corner rounding.
     * @param string $color    The line color of the rectangle.
     * @param string $fill     The color to fill the rounded rectangle with.
     */
    function roundedRectangle($x, $y, $width, $height, $round, $color = 'black', $fill = 'none')
    {
        if ($round <= 0) {
            // Optimize out any calls with no corner rounding.
            return $this->rectangle($x, $y, $width, $height, $color, $fill);
        }

        $c = $this->_allocateColor($color);
        if (is_a($c, 'PEAR_Error')) {
            return $c;
        }

        // Set corner points to avoid lots of redundant math.
        $x1 = $x + $round;
        $y1 = $y + $round;

        $x2 = $x + $width - $round;
        $y2 = $y + $round;

        $x3 = $x + $width - $round;
        $y3 = $y + $height - $round;

        $x4 = $x + $round;
        $y4 = $y + $height - $round;

        $r = $round * 2;

        // Calculate the upper left arc.
        $p1 = $this->_arcPoints($round, 180, 225);
        $p2 = $this->_arcPoints($round, 225, 270);

        // Calculate the upper right arc.
        $p3 = $this->_arcPoints($round, 270, 315);
        $p4 = $this->_arcPoints($round, 315, 360);

        // Calculate the lower right arc.
        $p5 = $this->_arcPoints($round, 0, 45);
        $p6 = $this->_arcPoints($round, 45, 90);

        // Calculate the lower left arc.
        $p7 = $this->_arcPoints($round, 90, 135);
        $p8 = $this->_arcPoints($round, 135, 180);

        // Draw the corners - upper left, upper right, lower right,
        // lower left.
        if (is_a($result = $this->_call('imageArc', array($this->_im, $x1, $y1, $r, $r, 180, 270, $c)), 'PEAR_Error')) {
            return $result;
        }
        if (is_a($result = $this->_call('imageArc', array($this->_im, $x2, $y2, $r, $r, 270, 360, $c)), 'PEAR_Error')) {
            return $result;
        }
        if (is_a($result = $this->_call('imageArc', array($this->_im, $x3, $y3, $r, $r, 0, 90, $c)), 'PEAR_Error')) {
            return $result;
        }
        if (is_a($result = $this->_call('imageArc', array($this->_im, $x4, $y4, $r, $r, 90, 180, $c)), 'PEAR_Error')) {
            return $result;
        }

        // Draw the connecting sides - top, right, bottom, left.
        if (is_a($result = $this->_call('imageLine', array($this->_im, $x1 + $p2['x2'], $y1 + $p2['y2'], $x2 + $p3['x1'], $y2 + $p3['y1'], $c)), 'PEAR_Error')) {
            return $result;
        }
        if (is_a($result = $this->_call('imageLine', array($this->_im, $x2 + $p4['x2'], $y2 + $p4['y2'], $x3 + $p5['x1'], $y3 + $p5['y1'], $c)), 'PEAR_Error')) {
            return $result;
        }
        if (is_a($result = $this->_call('imageLine', array($this->_im, $x3 + $p6['x2'], $y3 + $p6['y2'], $x4 + $p7['x1'], $y4 + $p7['y1'], $c)), 'PEAR_Error')) {
            return $result;
        }
        if (is_a($result = $this->_call('imageLine', array($this->_im, $x4 + $p8['x2'], $y4 + $p8['y2'], $x1 + $p1['x1'], $y1 + $p1['y1'], $c)), 'PEAR_Error')) {
            return $result;
        }

        if ($fill != 'none') {
            $f = $this->_allocateColor($fill);
            if (is_a($f, 'PEAR_Error')) {
                return $f;
            }
            if (is_a($result = $this->_call('imageFillToBorder', array($this->_im, $x + ($width / 2), $y + ($height / 2), $c, $f)), 'PEAR_Error')) {
                return $result;
            }
        }
    }

    /**
     * Draw a line.
     *
     * @param integer $x0    The x co-ordinate of the start.
     * @param integer $y0    The y co-ordinate of the start.
     * @param integer $x1    The x co-ordinate of the end.
     * @param integer $y1    The y co-ordinate of the end.
     * @param string $color  The line color.
     * @param string $width  The width of the line.
     */
    function line($x1, $y1, $x2, $y2, $color = 'black', $width = 1)
    {
        $c = $this->_allocateColor($color);
        if (is_a($c, 'PEAR_Error')) {
            return $c;
        }

        // Don't need to do anything special for single-width lines.
        if ($width == 1) {
            $result = $this->_call('imageLine', array($this->_im, $x1, $y1, $x2, $y2, $c));
        } elseif ($x1 == $x2) {
            // For vertical lines, we can just draw a vertical
            // rectangle.
            $left = $x1 - floor(($width - 1) / 2);
            $right = $x1 + floor($width / 2);
            $result = $this->_call('imageFilledRectangle', array($this->_im, $left, $y1, $right, $y2, $c));
        } elseif ($y1 == $y2) {
            // For horizontal lines, we can just draw a horizontal
            // filled rectangle.
            $top = $y1 - floor($width / 2);
            $bottom = $y1 + floor(($width - 1) / 2);
            $result = $this->_call('imageFilledRectangle', array($this->_im, $x1, $top, $x2, $bottom, $c));
        } else {
            // Angled lines.

            // Make sure that the end points of the line are
            // perpendicular to the line itself.
            $a = atan2($y1 - $y2, $x2 - $x1);
            $dx = (sin($a) * $width / 2);
            $dy = (cos($a) * $width / 2);

            $verts = array($x2 + $dx, $y2 + $dy, $x2 - $dx, $y2 - $dy, $x1 - $dx, $y1 - $dy, $x1 + $dx, $y1 + $dy);
            $result = $this->_call('imageFilledPolygon', array($this->_im, $verts, count($verts) / 2, $c));
        }

        return $result;
    }

    /**
     * Draw a dashed line.
     *
     * @param integer $x0           The x co-ordinate of the start.
     * @param integer $y0           The y co-ordinate of the start.
     * @param integer $x1           The x co-ordinate of the end.
     * @param integer $y1           The y co-ordinate of the end.
     * @param string $color         The line color.
     * @param string $width         The width of the line.
     * @param integer $dash_length  The length of a dash on the dashed line
     * @param integer $dash_space   The length of a space in the dashed line
     */
    function dashedLine($x0, $y0, $x1, $y1, $color = 'black', $width = 1, $dash_length = 2, $dash_space = 2)
    {
        $c = $this->_allocateColor($color);
        if (is_a($c, 'PEAR_Error')) {
            return $c;
        }
        $w = $this->_allocateColor('white');
        if (is_a($w, 'PEAR_Error')) {
            return $w;
        }

        // Set up the style array according to the $dash_* parameters.
        $style = array();
        for ($i = 0; $i < $dash_length; $i++) {
            $style[] = $c;
        }
        for ($i = 0; $i < $dash_space; $i++) {
            $style[] = $w;
        }

        if (is_a($result = $this->_call('imageSetStyle', array($this->_im, $style)), 'PEAR_Error')) {
            return $result;
        }
        if (is_a($result = $this->_call('imageSetThickness', array($this->_im, $width)), 'PEAR_Error')) {
            return $result;
        }
        return $this->_call('imageLine', array($this->_im, $x0, $y0, $x1, $y1, IMG_COLOR_STYLED));
    }

    /**
     * Draw a polyline (a non-closed, non-filled polygon) based on a
     * set of vertices.
     *
     * @param array $vertices  An array of x and y labeled arrays
     *                         (eg. $vertices[0]['x'], $vertices[0]['y'], ...).
     * @param string $color    The color you want to draw the line with.
     * @param string $width    The width of the line.
     */
    function polyline($verts, $color, $width = 1)
    {
        $first = true;
        foreach ($verts as $vert) {
            if (!$first) {
                if (is_a($result = $this->line($lastX, $lastY, $vert['x'], $vert['y'], $color, $width), 'PEAR_Error')) {
                    return $result;
                }
            } else {
                $first = false;
            }
            $lastX = $vert['x'];
            $lastY = $vert['y'];
        }
    }

    /**
     * Draw an arc.
     *
     * @param integer $x      The x co-ordinate of the centre.
     * @param integer $y      The y co-ordinate of the centre.
     * @param integer $r      The radius of the arc.
     * @param integer $start  The start angle of the arc.
     * @param integer $end    The end angle of the arc.
     * @param string  $color  The line color of the arc.
     * @param string  $fill   The fill color of the arc (defaults to none).
     */
    function arc($x, $y, $r, $start, $end, $color = 'black', $fill = null)
    {
        $c = $this->_allocateColor($color);
        if (is_a($c, 'PEAR_Error')) {
            return $c;
        }
        if (is_null($fill)) {
            $result = $this->_call('imageArc', array($this->_im, $x, $y, $r * 2, $r * 2, $start, $end, $c));
        } else {
            if ($fill !== $color) {
                $f = $this->_allocateColor($fill);
                if (is_a($f, 'PEAR_Error')) {
                    return $f;
                }
                if (is_a($result = $this->_call('imageFilledArc', array($this->_im, $x, $y, $r * 2, $r * 2, $start, $end, $f, IMG_ARC_PIE)), 'PEAR_Error')) {
                    return $result;
                }
                $result = $this->_call('imageFilledArc', array($this->_im, $x, $y, $r * 2, $r * 2, $start, $end, $c, IMG_ARC_EDGED | IMG_ARC_NOFILL));
            } else {
                $result = $this->_call('imageFilledArc', array($this->_im, $x, $y, $r * 2, $r * 2, $start, $end, $c, IMG_ARC_PIE));
            }
        }
        return $result;
    }

    /**
     * Applies the specified mask to the image.
     *
     * @param resource $gdimg_mask  The gd image resource representing the mask
     *
     * @return mixed  true | PEAR_Error
     */
    function _applyMask($gdimg_mask) {
        $imgX = round($this->_call('imageSX', array($this->_im)));
        $imgY = round($this->_call('imageSY', array($this->_im)));

        $gdimg_mask_resized = $this->_create($imgX, $imgY);
        if (!is_a($gdimg_mask_resized, 'PEAR_Error')) {
            $result = $this->_call('imageCopyResampled',
                                   array($gdimg_mask_resized,
                                         $gdimg_mask,
                                         0, 0, 0, 0,
                                         $imgX,
                                         $imgY,
                                         $this->_call('imageSX', array($gdimg_mask)),
                                         $this->_call('imageSY', array($gdimg_mask))));
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            $gdimg_mask_blendtemp = $this->_create($imgX, $imgY);
            if (is_a($gdimg_mask_blendtemp, 'PEAR_Error')) {
                return $gdimg_mask_blendtemp;
            }
            $mbtX = $this->_call('imageSX', array($gdimg_mask_blendtemp));
            $mbtY = $this->_call('imageSY', array($gdimg_mask_blendtemp));

            if (!is_a($gdimg_mask_blendtemp, 'PEAR_Error')) {
                $color_background = $this->_call('imageColorAllocate',
                                                 array($gdimg_mask_blendtemp, 0, 0, 0));

                $this->_call('imageFilledRectangle', array($gdimg_mask_blendtemp,
                                                           0,
                                                           0,
                                                           $mbtX,
                                                           $mbtY,
                                                           $color_background));

                $this->_call('imageAlphaBlending',
                             array($gdimg_mask_blendtemp, false));

                $this->_call('imageSaveAlpha',
                             array($gdimg_mask_blendtemp, true));

                for ($x = 0; $x < $imgX; $x++) {
                    for ($y = 0; $y < $imgY; $y++) {
                        $colorat = $this->_call('imageColorAt',
                                                 array($this->_im, $x, $y));

                        if (is_a($colorat, 'PEAR_Error')) {
                            return $colorat;
                        }

                        $realPixel = $this->_call('imageColorsForIndex',
                                                  array($this->_im, $colorat));

                        $colorat = $this->_call('imageColorAt',
                                                array($gdimg_mask_resized, $x, $y));

                        if (is_a($colorat, 'PEAR_Error')) {
                            return $colorat;
                        }

                        $maskPixel = $this->_grayscalePixel($this->_call('imageColorsForIndex',
                                                                         array($gdimg_mask_resized, $colorat)));

                        $maskAlpha = 127 - (floor($maskPixel['red'] / 2) * (1 - ($realPixel['alpha'] / 127)));
                        $newcolor = $this->_allocateColorAlpha($gdimg_mask_blendtemp,
                                                               $realPixel['red'],
                                                               $realPixel['green'],
                                                               $realPixel['blue'],
                                                               intval($maskAlpha));
                        $this->_call('imageSetPixel',
                                     array($gdimg_mask_blendtemp, $x, $y, $newcolor));
                    }
                }
                $this->_call('imageAlphaBlending', array($this->_im, false));
                $this->_call('imageSaveAlpha', array($this->_im, true));
                $this->_call('imageCopy', array($this->_im,
                                                $gdimg_mask_blendtemp,
                                                0, 0, 0, 0,
                                                $mbtX,
                                                $mbtY));

                $this->_call('imageDestroy', array($gdimg_mask_blendtemp));

            } else {
                return $gdimg_mask_blendtemp; // PEAR_Error
            }
            $this->_call('imageDestroy', array($gdimg_mask_resized));
        } else {
            return $gdimg_mask_resized; // PEAR_Error
        }
        return true;
    }

    /**
     * @TODO
     */
    function _grayscaleValue($r, $g, $b) {
        return round(($r * 0.30) + ($g * 0.59) + ($b * 0.11));
    }

    /**
     * @TODO
     */
    function _grayscalePixel($OriginalPixel) {
        $gray = $this->_grayscaleValue($OriginalPixel['red'], $OriginalPixel['green'], $OriginalPixel['blue']);
        return array('red'=>$gray, 'green'=>$gray, 'blue'=>$gray);
    }

    /**
     * Creates an image of the given size.
     * If possible the function returns a true color image.
     *
     * @param integer $width   The image width.
     * @param integer $height  The image height.
     *
     * @return resource|object PEAR Error  The image handler or a PEAR_Error
     *                                     on error.
     */
    function &_create($width, $height)
    {
        $result = &$this->_call('imageCreateTrueColor', array($width, $height));
        if (!is_resource($result)) {
            $result = &$this->_call('imageCreate', array($width, $height));
        }
        return $result;
    }

    function _allocateColorAlpha($gdimg_hexcolorallocate, $r, $g, $b , $alpha = false) {
        $result = $this->_call('imageColorAllocateAlpha',
                                array($gdimg_hexcolorallocate, $r, $g, $b, intval($alpha)));
        if (is_a($result, 'PEAR_Error')) {
            $result = $this->_call('imageColorAllocate',
                                   array($gdimg_hexcolorallocate, $r, $g, $b));
        }
        return $result;
    }


    /**
     * Wraps a call to a function of the gd extension.
     * If the call produces an error, a PEAR_Error is returned, the function
     * result otherwise.
     *
     * @param string $function  The name of the function to wrap.
     * @param array $params     An array with all parameters for that function.
     *
     * @return mixed  Either the function result or a PEAR_Error if an error
     *                occured when executing the function.
     */
    function &_call($function, $params = null)
    {
        unset($php_errormsg);
        $track = ini_set('track_errors', 1);
        $error_mask = E_ALL & ~E_WARNING & ~E_NOTICE;
        if (defined('E_STRICT')) {
            $error_mask &= ~E_STRICT;
        }
        error_reporting($error_mask);
        $result = call_user_func_array($function, $params);
        if ($track !== false) {
            ini_set('track_errors', $track);
        }
        error_reporting($GLOBALS['conf']['debug_level']);
        if (!empty($php_errormsg)) {
            $error_msg = $php_errormsg;
            require_once 'PEAR.php';
            $result = PEAR::raiseError($function . ': ' . $error_msg);
        }
        return $result;
    }

}
