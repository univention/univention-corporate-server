<?php

require_once dirname(__FILE__) . '/../Image.php';

/**
 * This class implements the Horde_Image:: API for the PHP GD
 * extension. It mainly provides some utility functions, such as the
 * ability to make pixels, for now.
 *
 * $Horde: framework/Image/Image/gd.php,v 1.45 2004/05/26 12:45:41 jan Exp $
 *
 * Copyright 2002-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Image
 */
class Horde_Image_gd extends Horde_Image {

    /**
     * Capabilites of this driver.
     * @var array $_capabilities
     */
    var $_capabilities = array('resize',
                               'crop',
                               'rotate',
                               'flip',
                               'mirror',
                               'grayscale',
                               'sepia',
                               'yellowize',
                               'watermark',
                               'canvas',
                         );

    /**
     * What kind of images should GD generate? Defaults to 'png'.
     * @var string $_type
     */
    var $_type = 'png';

    /**
     * GD Image resource for the current image data.
     * @var resource $_im
     */
    var $_im;

    /**
     * String identifier of the current image. New image data will not
     * be loaded if the same id is already loaded.
     * @var string $_id
     */
    var $_id = '';

    function Horde_Image_gd($params)
    {
        parent::Horde_Image($params);
        if (!empty($params['type'])) {
            $this->_type = $params['type'];
        }

        if (!empty($params['width'])) {
            $this->_im = @imageCreateTrueColor($this->_width, $this->_height);
            if (!is_resource($this->_im)) {
                $this->_im = imageCreate($this->_width, $this->_height);
            }

            imageFill($this->_im, 0, 0, $this->allocateColor($this->_background));
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
        $function = 'image' . $this->_type;
        $function($this->_im);
    }

    /**
     * Return the raw data for this image.
     *
     * @return string  The raw image data.
     */
    function raw()
    {
        return Util::bufferOutput('image' . $this->_type, $this->_im);
    }

    /**
     * Reset the image data.
     */
    function reset()
    {
        parent::reset();
        @imageDestroy($this->_im);
    }

    /**
     * Get the height and width of the current image.
     *
     * @return array  An hash with 'width' containing the width,
     *                'height' containing the height of the image.
     */
    function getDimensions()
    {
        if ($this->_im) {
            return array('width' => imageSX($this->_im),
                         'height' => imageSY($this->_im));
        } else {
            return array('width' => 0, 'height' => 0);
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
    function allocateColor($name)
    {
        static $colors = array();

        if (empty($colors[$name])) {
            list($r, $g, $b) = $this->getRGB($name);
            $colors[$name] = imageColorAllocate($this->_im, $r, $g, $b);
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
     * @access public
     *
     * @params string $id          An arbitrary id for the image.
     * @params string $image_data  The data to use for the image.
     */
    function loadString($id, $image_data)
    {
        if ($id != $this->_id) {
            if ($this->_im) {
                $this->reset();
            }
            $this->_im = @imageCreateFromString($image_data);
            $this->_id = $id;
        }
    }

    /**
     * Load the image data from a file.
     *
     * @access public
     *
     * @params string $filename  The full path and filename to the file to load
     *                           the image data from. The filename will also be
     *                           used for the image id.
     *
     * @return mixed  PEAR Error if file does not exist or could not be loaded
     *                otherwise NULL if successful or already loaded.
     */
    function loadFile($filename)
    {
        $this->reset();

        $info = getimagesize($filename);
        if (is_array($info)) {
            switch ($info[2]) {
            case 1:
                if (function_exists('imagecreatefromgif')) {
                    $this->_im = @imagecreatefromgif($filename);
                }
                break;
            case 2:
                $this->_im = @imagecreatefromjpeg($filename);
                break;
            case 3:
                $this->_im = @imagecreatefrompng($filename);
                break;
            case 15:
                if (function_exists('imagecreatefromgwbmp')) {
                    $this->_im = @imagecreatefromgwbmp($filename);
                }
                break;
            case 16:
                $this->_im = @imagecreatefromxbm($filename);
                break;
            }
        }

        if (is_resource($this->_im)) {
            return;
        }

        $result = parent::loadFile($filename);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        $this->_im = @imageCreateFromString($this->_data);
    }

    /**
     * Resize the current image.
     *
     * @param integer $width      The new width.
     * @param integer $height     The new height.
     * @param boolean $ratio      Maintain original aspect ratio.
     */
    function resize($width, $height, $ratio = true)
    {
        /* Abort if we're asked to divide by zero, or truncate the
         * image completely in either direction. */
        if (!$width || !$height) {
            return;
        }

        if ($ratio) {
            if ($width / $height > imageSX($this->_im) / imageSY($this->_im)) {
                $width = $height * imageSX($this->_im) / imageSY($this->_im);
            } else {
                $height = $width * imageSY($this->_im) / imageSX($this->_im);
            }
        }

        $im = $this->_im;
        $this->_im = @imageCreateTrueColor($width, $height);
        if (!is_resource($this->_im)) {
            $this->_im = imageCreate($width, $height);
        }
        imageFill($this->_im, 0, 0, imageColorAllocate($this->_im, 255, 255, 255));
        if (!@imageCopyResampled($this->_im, $im, 0, 0, 0, 0, $width, $height, imageSX($im), imageSY($im))) {
            imageCopyResized($this->_im, $im, 0, 0, 0, 0, $width, $height, imageSX($im), imageSY($im));
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
        $this->_im = @imageCreateTrueColor($x2 - $x1, $y2 - $y1);
        if (!is_resource($this->_im)) {
            $this->_im = imageCreate($x2 - $x1, $y2 - $y1);
        }
        imageCopy($this->_im, $im, 0, 0, $x1, $y1, $x2 - $x1, $y2 - $y1);
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

        $background = $this->allocateColor($background);

        switch ($angle) {
        case '90':
            $x = imageSX($this->_im);
            $y = imageSY($this->_im);
            $xymax = max($x, $y);

            $im = @imageCreateTrueColor($xymax, $xymax);
            if (!is_resource($im)) {
                $im = imageCreate($xymax, $xymax);
            }
            imageCopy($im, $this->_im, 0, 0, 0, 0, $x, $y);
            $im = imageRotate($im, 270, $background);
            $this->_im = $im;
            $im = @imageCreateTrueColor($y, $x);
            if (!is_resource($im)) {
                $im = imageCreate($y, $x);
            }
            if ($x < $y) {
                imageCopy($im, $this->_im, 0, 0, 0, 0, $xymax, $xymax);
            } elseif ($x > $y) {
                imageCopy($im, $this->_im, 0, 0, $xymax - $y, $xymax - $x, $xymax, $xymax);
            }
            $this->_im = $im;
            break;

        default:
            $this->_im = imageRotate($this->_im, 360 - $angle, $background);
            break;
        }
    }

    /**
     * Flip the current image.
     */
    function flip()
    {
        $x = imageSX($this->_im);
        $y = imageSY($this->_im);

        $im = @imageCreateTrueColor($x, $y);
        if (!is_resource($im)) {
            $im = imageCreate($x, $y);
        }
        for ($curY = 0; $curY < $y; $curY++) {
            imageCopy($im, $this->_im, 0, $y - ($curY + 1), 0, $curY, $x, 1);
        }

        $this->_im = $im;
    }

    /**
     * Mirror the current image.
     */
    function mirror()
    {
        $x = imageSX($this->_im);
        $y = imageSY($this->_im);

        $im = @imageCreateTrueColor($x, $y);
        if (!is_resource($im)) {
            $im = imageCreate($x, $y);
        }
        for ($curX = 0; $curX < $x; $curX++) {
            imageCopy($im, $this->_im, $x - ($curX + 1), 0, $curX, 0, 1, $y);
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

        if (function_exists('imageistruecolor') && imageIsTrueColor($this->_im)) {
            @imageTrueColorToPalette($this->_im, true, 256);
        }

        $colors = min(256, imageColorsTotal($this->_im));
        for ($x = 0; $x < $colors; $x++) {
            $src = imageColorsForIndex($this->_im, $x);
            $new = min(255, abs($src['red'] * $rateR + $src['green'] * $rateG + $src['blue'] * $rateB) + $whiteness);
            imageColorSet($this->_im, $x, $new, $new, $new);
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

        if (imageIsTrueColor($this->_im)) {
            imageTrueColorToPalette($this->_im, true, 256);
        }

        $colors = max(256, imageColorsTotal($this->_im));
        for ($x = 0; $x < $colors; $x++) {
            $src = imageColorsForIndex($this->_im, $x);
            $new = min(255, abs($src['red'] * $rateR + $src['green'] * $rateG + $src['blue'] * $rateB) + $whiteness);
            $r = min(255, $new + $tintR);
            $g = min(255, $new + $tintG);
            $b = min(255, $new + $tintB);
            imageColorSet($this->_im, $x, $r, $g, $b);
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
        if (imageIsTrueColor($this->_im)) {
            imageTrueColorToPalette($this->_im, true, 256);
        }

        $colors = max(256, imageColorsTotal($this->_im));
        for ($x = 0; $x < $colors; $x++) {
            $src = imageColorsForIndex($this->_im, $x);
            $r = min($src['red'] + $intensityY, 255);
            $g = min($src['green'] + $intensityY, 255);
            $b = max(($r + $g) / max($intensityB, 2), 0);
            imageColorSet($this->_im, $x, $r, $g, $b);
        }
    }

    function watermark($text, $halign = 'right', $valign = 'bottom', $font = 'small')
    {
        $color = imageColorClosest($this->_im, 255, 255, 255);
        $shadow = imageColorClosest($this->_im, 0, 0, 0);

        // Shadow offset in pixels.
        $drop = 1;

        // Maximum text width.
        $maxwidth = 200;

        // Amount of space to leave between the text and the image
        // border.
        $padding = 10;

        $f = $this->getFont($font);
        $fontwidth = imageFontWidth($f);
        $fontheight = imageFontHeight($f);

        // So that shadow is not off the image with right align and
        // bottom valign.
        $margin = floor($padding + $drop) / 2;

        if ($maxwidth) {
            $maxcharsperline = floor(($maxwidth - ($margin * 2)) / $fontwidth);
            $text = wordwrap($text, $maxcharsperline, "\n", 1);
        }

        // Split $text into individual lines.
        $lines = explode("\n", $text);

        switch ($valign){
        case 'center':
            $y = (imageSY($this->_im) - ($fontheight * count($lines))) / 2;
            break;

        case 'bottom':
            $y = imageSY($this->_im) - (($fontheight * count($lines)) + $margin);
            break;

        default:
            $y = $margin;
            break;
        }

        switch ($halign) {
        case 'right':
            foreach ($lines as $line) {
                imageString($this->_im, $f, (imageSX($this->_im) - $fontwidth * strlen($line)) - $margin + $drop, ($y + $drop), $line, $shadow);
                imageString($this->_im, $f, (imageSX($this->_im) - $fontwidth * strlen($line)) - $margin, $y, $line, $color);
                $y += $fontheight;
            }
            break;

        case 'center':
            foreach ($lines as $line) {
                imageString($this->_im, $f, floor((imageSX($this->_im) - $fontwidth * strlen($line)) / 2) + $drop, ($y + $drop), $line, $shadow);
                imageString($this->_im, $f, floor((imageSX($this->_im) - $fontwidth * strlen($line)) / 2), $y, $line, $color);
                $y += $fontheight;
            }
            break;

        default:
            foreach ($lines as $line) {
                imageString($this->_im, $f, $margin + $drop, ($y + $drop), $line, $shadow);
                imageString($this->_im, $f, $margin, $y, $line, $color);
                $y += $fontheight;
            }
            break;
        }
    }

    /**
     * Draws a text string on the image in a specified location, with
     * the specified style information.
     *
     * @param string  $text       The text to draw.
     * @param integer $x          The left x coordinate of the start of the text string.
     * @param integer $y          The top y coordinate of the start of the text string.
     * @param string  $font       The font identifier you want to use for the text.
     * @param string  $color      The color that you want the text displayed in.
     * @param integer $direction  An integer that specifies the orientation of the text.
     */
    function text($string, $x, $y, $font = 'monospace', $color = 'black', $direction = 0)
    {
        $c = $this->allocateColor($color);
        $f = $this->getFont($font);
        switch ($direction) {
        case -90:
        case 270:
            imageStringUp($this->_im, $f, $x, $y, $string, $c);
            break;

        case 0:
        default:
            imageString($this->_im, $f, $x, $y, $string, $c);
        }
    }

    /**
     * Draw a circle.
     *
     * @param integer $x      The x co-ordinate of the centre.
     * @param integer $y      The y co-ordinate of the centre.
     * @param integer $r      The radius of the circle.
     * @param string  $color  The line color of the circle.
     * @param string  $fill   (optional) The color to fill the circle.
     */
    function circle($x, $y, $r, $color, $fill = null)
    {
        $c = $this->allocateColor($color);
        if (is_null($fill)) {
            imageEllipse($this->_im, $x, $y, $r * 2, $r * 2, $c);
        } else {
            if ($fill !== $color) {
                $fillColor = $this->allocateColor($fill);
                imageFilledEllipse($this->_im, $x, $y, $r * 2, $r * 2, $fillColor);
                imageEllipse($this->_im, $x, $y, $r * 2, $r * 2, $c);
            } else {
                imageFilledEllipse($this->_im, $x, $y, $r * 2, $r * 2, $c);
            }
        }
    }

    /**
     * Draw a polygon based on a set of vertices.
     *
     * @param array   $vertices  An array of x and y labeled arrays
     *                           (eg. $vertices[0]['x'], $vertices[0]['y'], ...).
     * @param string  $color     The color you want to draw the polygon with.
     * @param string  $fill      (optional) The color to fill the polygon.
     */
    function polygon($verts, $color, $fill = 'none')
    {
        $vertices = array();
        foreach ($verts as $vert) {
            $vertices[] = $vert['x'];
            $vertices[] = $vert['y'];
        }

        if ($fill != 'none') {
            $f = $this->allocateColor($fill);
            imageFilledPolygon($this->_im, $vertices, count($verts), $f);
        }

        if ($fill == 'none' || $fill != $color) {
            $c = $this->allocateColor($color);
            imagePolygon($this->_im, $vertices, count($verts), $c);
        }
    }

    /**
     * Draw a rectangle.
     *
     * @param integer $x       The left x-coordinate of the rectangle.
     * @param integer $y       The top y-coordinate of the rectangle.
     * @param integer $width   The width of the rectangle.
     * @param integer $height  The height of the rectangle.
     * @param string  $color   (optional) The line color of the rectangle. Defaults to black.
     * @param string  $fill    (optional) The color to fill the rectangle with. Defaults to none.
     */
    function rectangle($x, $y, $width, $height, $color = 'black', $fill = 'none')
    {
        if ($fill != 'none') {
            $f = $this->allocateColor($fill);
            imageFilledRectangle($this->_im, $x, $y, $x + $width, $y + $height, $f);
        }

        if ($fill == 'none' || $fill != $color) {
            $c = $this->allocateColor($color);
            imageRectangle($this->_im, $x, $y, $x + $width, $y + $height, $c);
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
     * @param string  $color   (optional) The line color of the rectangle. Defaults to black.
     * @param string  $fill    (optional) The color to fill the rounded rectangle with. Defaults to none.
     */
    function roundedRectangle($x, $y, $width, $height, $round, $color = 'black', $fill = 'none')
    {
        if ($round <= 0) {
            // Optimize out any calls with no corner rounding.
            return $this->rectangle($x, $y, $width, $height, $color, $fill);
        }

        $c = $this->allocateColor($color);

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
        imageArc($this->_im, $x1, $y1, $r, $r, 180, 270, $c);
        imageArc($this->_im, $x2, $y2, $r, $r, 270, 360, $c);
        imageArc($this->_im, $x3, $y3, $r, $r, 0, 90, $c);
        imageArc($this->_im, $x4, $y4, $r, $r, 90, 180, $c);

        // Draw the connecting sides - top, right, bottom, left.
        imageLine($this->_im, $x1 + $p2['x2'], $y1 + $p2['y2'], $x2 + $p3['x1'], $y2 + $p3['y1'], $c);
        imageLine($this->_im, $x2 + $p4['x2'], $y2 + $p4['y2'], $x3 + $p5['x1'], $y3 + $p5['y1'], $c);
        imageLine($this->_im, $x3 + $p6['x2'], $y3 + $p6['y2'], $x4 + $p7['x1'], $y4 + $p7['y1'], $c);
        imageLine($this->_im, $x4 + $p8['x2'], $y4 + $p8['y2'], $x1 + $p1['x1'], $y1 + $p1['y1'], $c);

        if ($fill != 'none') {
            $f = $this->allocateColor($fill);
            imageFillToBorder($this->_im, $x + ($width / 2), $y + ($height / 2), $c, $f);
        }
    }

    /**
     * Draw a line.
     *
     * @param integer $x0     The x co-ordinate of the start.
     * @param integer $y0     The y co-ordinate of the start.
     * @param integer $x1     The x co-ordinate of the end.
     * @param integer $y1     The y co-ordinate of the end.
     * @param string  $color  (optional) The line color.
     * @param string  $width  (optional) The width of the line.
     */
    function line($x1, $y1, $x2, $y2, $color = 'black', $width = 1)
    {
        $c = $this->allocateColor($color);

        // Don't need to do anything special for single-width lines.
        if ($width == 1) {
            imageLine($this->_im, $x1, $y1, $x2, $y2, $c);
        } elseif ($x1 == $x2) {
            // For vertical lines, we can just draw a vertical
            // rectangle.
            $left = $x1 - floor(($width - 1) / 2);
            $right = $x1 + floor($width / 2);
            imageFilledRectangle($this->_im, $left, $y1, $right, $y2, $c);
        } elseif ($y1 == $y2) {
            // For horizontal lines, we can just draw a horizontal
            // filled rectangle.
            $top = $y1 - floor($width / 2);
            $bottom = $y1 + floor(($width - 1) / 2);
            imageFilledRectangle($this->_im, $x1, $top, $x2, $bottom, $c);
        } else {
            // Angled lines.

            // Make sure that the end points of the line are
            // perpendicular to the line itself.
            $a = atan2($y1 - $y2, $x2 - $x1);
            $dx = (sin($a) * $width / 2);
            $dy = (cos($a) * $width / 2);

            $verts = array($x2 + $dx, $y2 + $dy, $x2 - $dx, $y2 - $dy, $x1 - $dx, $y1 - $dy, $x1 + $dx, $y1 + $dy);
            imageFilledPolygon($this->_im, $verts, count($verts) / 2, $c);
        }
    }

    /**
     * Draw a dashed line.
     *
     * @param integer $x0           The x co-ordinate of the start.
     * @param integer $y0           The y co-ordinate of the start.
     * @param integer $x1           The x co-ordinate of the end.
     * @param integer $y1           The y co-ordinate of the end.
     * @param string  $color        (optional) The line color.
     * @param string  $width        (optional) The width of the line.
     * @param integer $dash_length  The length of a dash on the dashed line
     * @param integer $dash_space   The length of a space in the dashed line
     */
    function dashedLine($x1, $y1, $x2, $y2, $color = 'black', $width = 1, $dash_length = 2, $dash_space = 2)
    {
        $c = $this->allocateColor($color);
        $w = $this->allocateColor('white');

        // Set up the style array according to the $dash_* parameters.
        $style = array();
        for ($i = 0; $i < $dash_length; $i++) {
            $style[] = $c;
        }
        for ($i = 0; $i < $dash_space; $i++) {
            $style[] = $w;
        }

        imageSetStyle($this->_im, $style);
        imageSetThickness($this->_im, $width);
        imageLine($this->_im, $x1, $y1, $x2, $y2, IMG_COLOR_STYLED);
    }

    /**
     * Draw a polyline (a non-closed, non-filled polygon) based on a
     * set of vertices.
     *
     * @param array   $vertices  An array of x and y labeled arrays
     *                           (eg. $vertices[0]['x'], $vertices[0]['y'], ...).
     * @param string  $color     The color you want to draw the line with.
     * @param string  $width     (optional) The width of the line.
     */
    function polyline($verts, $color, $width = 1)
    {
        $first = true;
        foreach ($verts as $vert) {
            if (!$first) {
                $this->line($lastX, $lastY, $vert['x'], $vert['y'], $color, $width);
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
        $c = $this->allocateColor($color);
        if (is_null($fill)) {
            imageArc($this->_im, $x, $y, $r * 2, $r * 2, $start, $end, $c);
        } else {
            if ($fill !== $color) {
                $f = $this->allocateColor($fill);
                imageFilledArc($this->_im, $x, $y, $r * 2, $r * 2, $start, $end, $f, IMG_ARC_PIE);
                imageFilledArc($this->_im, $x, $y, $r * 2, $r * 2, $start, $end, $c, IMG_ARC_EDGED | IMG_ARC_NOFILL);
            } else {
                imageFilledArc($this->_im, $x, $y, $r * 2, $r * 2, $start, $end, $c, IMG_ARC_PIE);
            }
        }
    }

}
