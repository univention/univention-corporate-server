<?php

require_once 'Horde/Image.php';

/**
 * This class implements the Horde_Image:: API for ImageMagick.
 *
 * $Horde: framework/Image/Image/im.php,v 1.33 2004/05/07 19:16:20 chuck Exp $
 *
 * Copyright 2002-2004 Chuck Hagenbuch <chuck@horde.org>
 * Copyright 2003-2004 Mike Cochrane <mike@graftonhall.co.nz>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Image
 */
class Horde_Image_im extends Horde_Image {

    /**
     * Capabilites of this driver.
     * @var array $_capabilities
     */
    var $_capabilities = array('resize',
                               'crop',
                               'rotate',
                               'grayscale',
                               'flip',
                               'mirror',
                               'sepia',
                               'canvas'
                         );

    /**
     * What kind of images should ImageMagick generate? Defaults to
     * 'png'.
     * @var string $_type
     */
    var $_type = 'png';

    /**
     * Operations to be performed.
     * @var array $_operations
     */
    var $_operations = array();

    /**
     * Current stroke color; cached so we don't issue more -stroke
     * commands than necessary.
     * @var string $_strokeColor
     */
    var $_strokeColor = null;

    /**
     * Current stroke width; cached so we don't issue more -strokewidth
     * commands than necessary.
     * @var string $_strokeWidth
     */
    var $_strokeWidth = null;

    /**
     * Current fill color; cached so we don't issue more -fill
     * commands than necessary.
     * @var string $_fillColor
     */
    var $_fillColor = null;

    /**
     * Constructor.
     */
    function Horde_Image_im($params)
    {
        parent::Horde_Image($params);

        if (!empty($params['type'])) {
            $this->_type = $params['type'];
        }

        // Make sure we start with a white background to be consistent
        // with other drivers.
        if (!empty($params['background'])) {
            $bg = $params['background'];
        } else {
            $bg = 'white';
        }
        $this->rectangle(0, 0, $this->_width, $this->_height, $bg, $bg);
    }

    /**
     * Return the content type for this image.
     *
     * @return string  The content type for this image.
     */
    function getContentType()
    {
        return 'image/' . $this->_type;
    }

    /**
     * Return the raw data for this image.
     *
     * @return string  The raw image data.
     */
    function raw()
    {
        global $conf;

        if (!empty($this->_data)) {
            // If there are no operations, and we already have data,
            // don't bother writing out files, just return the current
            // data.
            if (!count($this->_operations)) {
                return $this->_data;
            }

            $tmpin = $this->toFile($this->_data);
        } else {
            // Create an empty PPM file to load.
            $tmpin = Util::getTempFile('img', false, $this->_tmpdir);
            $fp = fopen($tmpin, 'wb');
            fwrite($fp, sprintf("P3\n%d %d\n255\n ", $this->_width, $this->_height));
            fclose($fp);
        }

        $tmpout = Util::getTempFile('img', false, $this->_tmpdir);

        $command  = $conf['image']['convert'];
        $command .= ' ' . implode(' ', $this->_operations);
        $command .= ' "' . $tmpin . '" +profile "*" ' . $this->_type . ':"' . $tmpout . '" 2>&1';

        exec($command, $output, $retval);

        $fp = fopen($tmpout, 'rb');
        $this->_data = fread($fp, filesize($tmpout));
        fclose($fp);

        @unlink($tmpin);
        @unlink($tmpout);

        return $this->_data;
    }

    /**
     * Reset the image data.
     */
    function reset()
    {
        parent::reset();
        $this->_operations = array();
    }

    /**
     * Resize the current image.
     *
     * @param integer $width   The new width.
     * @param integer $height  The new height.
     * @param boolean $ratio   Maintain original aspect ratio.
     */
    function resize($width, $height, $ratio = true)
    {
        if ($ratio) {
            $this->_operations[] = "-resize {$width}x{$height}";
        } else {
            $this->_operations[] = "-resize {$width}x{$height}!";
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
        $line = ($x2 - $x1) . 'x' . ($y2 - $y1) . '+' . $x1 . '+' . $y2;
        $this->_operations[] = '-crop ' . $line;
    }

    /**
     * Rotate the current image.
     *
     * @param integer $angle       The angle to rotate the image by,
     *                             in the clockwise direction.
     * @param integer $background  The background color to fill any triangles.
     */
    function rotate($angle, $background = 'white')
    {
        $this->_operations[] = "-rotate {$angle} -background $background";
    }

    /**
     * Flip the current image.
     */
    function flip()
    {
        $this->_operations[] = '-flip';
    }

    /**
     * Mirror the current image.
     */
    function mirror()
    {
        $this->_operations[] = '-flop';
    }

    /**
     * Convert the current image to grayscale.
     */
    function grayscale()
    {
        $this->_operations[] = '-colorspace GRAY -colors 256';
    }

    /**
     * Sepia filter.
     */
    function sepia()
    {
        $this->_operations[] = '-modulate 110 -colorspace GRAY -colors 256 -gamma 1.25/1/0.66';
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
    function text($string, $x, $y, $font = '_sans', $color = 'black', $direction = 0)
    {
        $this->setStrokeColor($color);
        $this->setStrokeWidth(1);

        $string = addslashes('"' . $string . '"');
        $y = $y + 12;
        $this->_operations[] = "-draw \"text $x,$y $string\"";
    }

    /**
     * Draw a circle.
     *
     * @param integer $x      The x coordinate of the centre.
     * @param integer $y      The y coordinate of the centre.
     * @param integer $r      The radius of the circle.
     * @param string  $color  The line color of the circle.
     * @param string  $fill   (optional) The color to fill the circle.
     */
    function circle($x, $y, $r, $color, $fill = 'none')
    {
        $this->setStrokeColor($color);
        $this->setFillColor($fill);

        $xMax = $x + $r;
        $this->_operations[] = "-draw \"circle $x,$y $xMax,$y\"";
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
        $this->setStrokeColor($color);
        $this->setFillColor($fill);

        $command = '';
        foreach ($verts as $vert) {
            $command .= sprintf(' %d,%d', $vert['x'], $vert['y']);
        }
        $this->_operations[] = "-draw \"polygon $command\"";
    }

    /**
     * Draw a rectangle.
     *
     * @param integer $x       The left x-coordinate of the rectangle.
     * @param integer $y       The top y-coordinate of the rectangle.
     * @param integer $width   The width of the rectangle.
     * @param integer $height  The height of the rectangle.
     * @param string  $color   The line color of the rectangle.
     * @param string  $fill    (optional) The color to fill the rectangle.
     */
    function rectangle($x, $y, $width, $height, $color, $fill = 'none')
    {
        $this->setStrokeColor($color);
        $this->setFillColor($fill);

        $xMax = $x + $width;
        $yMax = $y + $height;
        $this->_operations[] = "-draw \"rectangle $x,$y $xMax,$yMax\"";
    }

    /**
     * Draw a rounded rectangle.
     *
     * @param integer $x       The left x-coordinate of the rectangle.
     * @param integer $y       The top y-coordinate of the rectangle.
     * @param integer $width   The width of the rectangle.
     * @param integer $height  The height of the rectangle.
     * @param integer $round   The width of the corner rounding.
     * @param string  $color   The line color of the rectangle.
     * @param string  $fill    The color to fill the rounded rectangle with.
     */
    function roundedRectangle($x, $y, $width, $height, $round, $color, $fill)
    {
        $this->setStrokeColor($color);
        $this->setFillColor($fill);

        $x1 = $x + $width;
        $y1 = $y + $height;
        $this->_operations[] = "-draw \"roundRectangle $x,$y $x1,$y1, $round,$round\"";
    }

    /**
     * Draw a line.
     *
     * @param integer $x0     The x coordinate of the start.
     * @param integer $y0     The y coordinate of the start.
     * @param integer $x1     The x coordinate of the end.
     * @param integer $y1     The y coordinate of the end.
     * @param string  $color  (optional) The line color.
     * @param string  $width  (optional) The width of the line.
     */
    function line($x0, $y0, $x1, $y1, $color = 'black', $width = 1)
    {
        $this->setStrokeColor($color);
        $this->setStrokeWidth($width);
        $this->_operations[] = "-draw \"line $x0,$y0 $x1,$y1\"";
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
        $this->setStrokeColor($color);
        $this->setStrokeWidth($width);
        $this->setFillColor('none');

        $command = '';
        foreach ($verts as $vert) {
            $command .= sprintf(' %d,%d', $vert['x'], $vert['y']);
        }
        $this->_operations[] = "-draw \"polyline $command\"";
    }

    /**
     * Draw an arc.
     *
     * @param integer $x      The x coordinate of the centre.
     * @param integer $y      The y coordinate of the centre.
     * @param integer $r      The radius of the arc.
     * @param integer $start  The start angle of the arc.
     * @param integer $end    The end angle of the arc.
     * @param string  $color  The line color of the arc.
     * @param string  $fill   The fill color of the arc (defaults to none).
     */
    function arc($x, $y, $r, $start, $end, $color = 'black', $fill = 'none')
    {
        $this->setStrokeColor($color);
        $this->setFillColor($fill);

        // Split up arcs greater than 180 degrees into two pieces.
        $mid = round(($start + $end) / 2);
        if ($mid > 90) {
            $this->_operations[] = "-draw \"ellipse $x,$y $r,$r $start,$mid\"";
            $this->_operations[] = "-draw \"ellipse $x,$y $r,$r $mid,$end\"";
        } else {
            $this->_operations[] = "-draw \"ellipse $x,$y $r,$r $start,$end\"";
        }

        // If filled, draw the outline.
        if (!empty($fill)) {
            list($x1, $y1) = $this->_circlePoint($start, $r * 2);
            list($x2, $y2) = $this->_circlePoint($mid, $r * 2);
            list($x3, $y3) = $this->_circlePoint($end, $r * 2);

            // This seems to result in slightly better placement of
            // pie slices.
            $x++;
            $y++;

            $verts = array(array('x' => $x + $x3, 'y' => $y + $y3),
                           array('x' => $x, 'y' => $y),
                           array('x' => $x + $x1, 'y' => $y + $y1));

            if ($mid > 90) {
                $verts1 = array(array('x' => $x + $x2, 'y' => $y + $y2),
                                array('x' => $x, 'y' => $y),
                                array('x' => $x + $x1, 'y' => $y + $y1));
                $verts2 = array(array('x' => $x + $x3, 'y' => $y + $y3),
                                array('x' => $x, 'y' => $y),
                                array('x' => $x + $x2, 'y' => $y + $y2));

                $this->polygon($verts1, $fill, $fill);
                $this->polygon($verts2, $fill, $fill);
            } else {
                $this->polygon($verts, $fill, $fill);
            }

            $this->polyline($verts, $color);
        }
    }

    /**
     * Change the current stroke color. Will only affect the command
     * string if $stroke is different from the previous stroke color
     * (stored in $this->_strokeColor).
     *
     * @access private
     * @see $_strokeColor
     *
     * @param string $color  The new stroke color.
     */
    function setStrokeColor($color)
    {
        if ($color != $this->_strokeColor) {
            $this->_operations[] = "-stroke $color";
            $this->_strokeColor = $color;
        }
    }

    /**
     * Change the current stroke width. Will only affect the command
     * string if $width is different from the previous stroke width
     * (stored in $this->_strokeWidth).
     *
     * @access private
     * @see $_stroke
     *
     * @param string $width  The new stroke width.
     */
    function setStrokeWidth($width)
    {
        if ($width != $this->_strokeWidth) {
            $this->_operations[] = "-strokewidth $width";
            $this->_strokeWidth = $width;
        }
    }

    /**
     * Change the current fill color. Will only affect the command
     * string if $color is different from the previous fill color
     * (stored in $this->_fillColor).
     *
     * @access private
     * @see $_fill
     *
     * @param string $color  The new fill color.
     */
    function setFillColor($color)
    {
        if ($color != $this->_fillColor) {
            $this->_operations[] = "-fill $color";
            $this->_fillColor = $color;
        }
    }

}
