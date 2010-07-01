<?php

require_once dirname(__FILE__) . '/../Image.php';

/**
 * This class implements the Horde_Image:: API for SWF, using the PHP
 * Ming extension.
 *
 * $Horde: framework/Image/Image/swf.php,v 1.24.10.10 2009-01-06 15:23:12 jan Exp $
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
class Horde_Image_swf extends Horde_Image {

    /**
     * Capabilites of this driver.
     *
     * @var array
     */
    var $_capabilities = array('canvas');

    /**
     * SWF root movie.
     *
     * @var resource
     */
    var $_movie;

    function Horde_Image_swf($params)
    {
        parent::Horde_Image($params);

        $this->_movie = new SWFMovie();
        $this->_movie->setDimension($this->_width, $this->_height);

        // FIXME: honor the 'background' parameter here.
        $this->_movie->setBackground(0xff, 0xff, 0xff);
        $this->_movie->setRate(30);
    }

    function getContentType()
    {
        return 'application/x-shockwave-flash';
    }

    /**
     * Display the movie.
     */
    function display()
    {
        $this->headers();
        $this->_movie->output();
    }

    /**
     * Return the raw data for this image.
     *
     * @return string  The raw image data.
     */
    function raw()
    {
        ob_start();
        $this->_movie->output();
        $data = ob_get_contents();
        ob_end_clean();

        return $data;
    }

    /**
     * Creates a color that can be accessed in this object. When a
     * color is set, the rgba values are returned in an array.
     *
     * @param string $name  The name of the color.
     *
     * @return array  The red, green, blue, alpha values of the color.
     */
    function allocateColor($name)
    {
        list($r, $g, $b) = $this->getRGB($name);
        return array('red' => $r,
                     'green' => $g,
                     'blue' => $b,
                     'alpha' => 255);
    }

    function getFont($font)
    {
        switch ($font) {
        case 'sans-serif':
            return '_sans';

        case 'serif':
            return '_serif';

        case 'monospace':
            return '_typewriter';

        default:
            return $font;
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
        $color = $this->allocateColor($color);

        if (!strncasecmp(PHP_OS, 'WIN', 3)) {
            $text = new SWFTextField(SWFTEXTFIELD_NOEDIT);
        } else {
            $text = new SWFText();
        }
        $text->setColor($color['red'], $color['green'], $color['blue'], $color['alpha']);
        $text->addString($string);
        $text->setFont(new SWFFont($this->getFont($font)));

        $t = $this->_movie->add($text);
        $t->moveTo($x, $y);
        $t->rotate($direction);

        return $t;
    }

    /**
     * Draw a circle.
     *
     * @param integer $x      The x co-ordinate of the centre.
     * @param integer $y      The y co-ordinate of the centre.
     * @param integer $r      The radius of the circle.
     * @param string  $color  The line color of the circle.
     * @param string  $fill   The color to fill the circle.
     */
    function circle($x, $y, $r, $color, $fill = 'none')
    {
        $s = new SWFShape();
        $color = $this->allocateColor($color);
        $s->setLine(1, $color['red'], $color['green'], $color['blue'], $color['alpha']);

        if ($fill != 'none') {
            $fillColor = $this->allocateColor($fill);
            $f = $s->addFill($fillColor['red'], $fillColor['green'], $fillColor['blue'], $fillColor['alpha']);
            $s->setRightFill($f);
        }

        $a = $r * 0.414213562; // = tan(22.5 deg)
        $b = $r * 0.707106781; // = sqrt(2)/2 = sin(45 deg)

        $s->movePenTo($x + $r, $y);

        $s->drawCurveTo($x + $r, $y - $a, $x + $b, $y - $b);
        $s->drawCurveTo($x + $a, $y - $r, $x, $y - $r);
        $s->drawCurveTo($x - $a, $y - $r, $x - $b, $y - $b);
        $s->drawCurveTo($x - $r, $y - $a, $x - $r, $y);
        $s->drawCurveTo($x - $r, $y + $a, $x - $b, $y + $b);
        $s->drawCurveTo($x - $a, $y + $r, $x, $y + $r);
        $s->drawCurveTo($x + $a, $y + $r, $x + $b, $y + $b);
        $s->drawCurveTo($x + $r, $y + $a, $x + $r, $y);

        return $this->_movie->add($s);
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
        $color = $this->allocateColor($color);

        if (is_array($color) && is_array($verts) && (sizeof($verts) > 2)) {
            $shape = new SWFShape();
            $shape->setLine(1, $color['red'], $color['green'], $color['blue'], $color['alpha']);

            if ($fill != 'none') {
                $fillColor = $this->allocateColor($fill);
                $f = $shape->addFill($fillColor['red'], $fillColor['green'], $fillColor['blue'], $fillColor['alpha']);
                $shape->setRightFill($f);
            }

            $first_done = false;
            foreach ($verts as $value) {
                if (!$first_done) {
                    $shape->movePenTo($value['x'], $value['y']);
                    $first_done = true;
                    $first_x = $value['x'];
                    $first_y = $value['y'];
                }
                $shape->drawLineTo($value['x'], $value['y']);
            }
            $shape->drawLineTo($first_x, $first_y);

            return $this->_movie->add($shape);
        } else {
            // If the color is an array and the vertices is a an array
            // of more than 2 points.
            return false;
        }
    }

    /**
     * Draw a rectangle.
     *
     * @param integer $x       The left x-coordinate of the rectangle.
     * @param integer $y       The top y-coordinate of the rectangle.
     * @param integer $width   The width of the rectangle.
     * @param integer $height  The height of the rectangle.
     * @param string  $color   The line color of the rectangle.
     * @param string  $fill    The color to fill the rectangle.
     */
    function rectangle($x, $y, $width, $height, $color, $fill = 'none')
    {
        $verts[0] = array('x' => $x, 'y' => $y);
        $verts[1] = array('x' => $x + $width, 'y' => $y);
        $verts[2] = array('x' => $x + $width, 'y' => $y + $height);
        $verts[3] = array('x' => $x, 'y' => $y + $height);

        return $this->polygon($verts, $color, $fill);
    }

    /**
     * Draw a rectangle.
     *
     * @param integer $x       The left x-coordinate of the rectangle.
     * @param integer $y       The top y-coordinate of the rectangle.
     * @param integer $width   The width of the rectangle.
     * @param integer $height  The height of the rectangle.
     * @param integer $round   The width of the corner rounding.
     * @param string $color    The line color of the rectangle.
     * @param string $fill     The color to fill the rectangle.
     */
    function roundedRectangle($x, $y, $width, $height, $round, $color = 'black', $fill = 'none')
    {
        if ($round <= 0) {
            // Optimize out any calls with no corner rounding.
            return $this->rectangle($x, $y, $width, $height, $color, $fill);
        }

        $s = new SWFShape();
        $color = $this->allocateColor($color);
        $s->setLine(1, $color['red'], $color['green'], $color['blue'], $color['alpha']);

        if ($fill != 'none') {
            $fillColor = $this->allocateColor($fill);
            $f = $s->addFill($fillColor['red'], $fillColor['green'], $fillColor['blue'], $fillColor['alpha']);
            $s->setRightFill($f);
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

        // Start in the upper left.
        $p1 = $this->_arcPoints($round, 180, 225);
        $p2 = $this->_arcPoints($round, 225, 270);

        // Start at the lower left corner of the top left curve.
        $s->movePenTo($x1 + $p1['x1'], $y1 + $p1['y1']);

        // Draw the upper left corner.
        $s->drawCurveTo($x1 + $p1['x3'], $y1 + $p1['y3'], $x1 + $p1['x2'], $y1 + $p1['y2']);
        $s->drawCurveTo($x1 + $p2['x3'], $y1 + $p2['y3'], $x1 + $p2['x2'], $y1 + $p2['y2']);

        // Calculate the upper right points.
        $p3 = $this->_arcPoints($round, 270, 315);
        $p4 = $this->_arcPoints($round, 315, 360);

        // Connect the top left and right curves.
        $s->drawLineTo($x2 + $p3['x1'], $y2 + $p3['y1']);

        // Draw the upper right corner.
        $s->drawCurveTo($x2 + $p3['x3'], $y2 + $p3['y3'], $x2 + $p3['x2'], $y2 + $p3['y2']);
        $s->drawCurveTo($x2 + $p4['x3'], $y2 + $p4['y3'], $x2 + $p4['x2'], $y2 + $p4['y2']);

        // Calculate the lower right points.
        $p5 = $this->_arcPoints($round, 0, 45);
        $p6 = $this->_arcPoints($round, 45, 90);

        // Connect the top right and lower right curves.
        $s->drawLineTo($x3 + $p5['x1'], $y3 + $p5['y1']);

        // Draw the lower right corner.
        $s->drawCurveTo($x3 + $p5['x3'], $y3 + $p5['y3'], $x3 + $p5['x2'], $y3 + $p5['y2']);
        $s->drawCurveTo($x3 + $p6['x3'], $y3 + $p6['y3'], $x3 + $p6['x2'], $y3 + $p6['y2']);

        // Calculate the lower left points.
        $p7 = $this->_arcPoints($round, 90, 135);
        $p8 = $this->_arcPoints($round, 135, 180);

        // Connect the bottom right and bottom left curves.
        $s->drawLineTo($x4 + $p7['x1'], $y4 + $p7['y1']);

        // Draw the lower left corner.
        $s->drawCurveTo($x4 + $p7['x3'], $y4 + $p7['y3'], $x4 + $p7['x2'], $y4 + $p7['y2']);
        $s->drawCurveTo($x4 + $p8['x3'], $y4 + $p8['y3'], $x4 + $p8['x2'], $y4 + $p8['y2']);

        // Close the shape.
        $s->drawLineTo($x1 + $p1['x1'], $y1 + $p1['y1']);

        return $this->_movie->add($s);
    }

    /**
     * Draw a line.
     *
     * @param integer $x0     The x co-ordinate of the start.
     * @param integer $y0     The y co-ordinate of the start.
     * @param integer $x1     The x co-ordinate of the end.
     * @param integer $y1     The y co-ordinate of the end.
     * @param string  $color  The line color.
     * @param string  $width  The width of the line.
     */
    function line($x1, $y1, $x2, $y2, $color = 'black', $width = 1)
    {
        $color = $this->allocateColor($color);

        if (is_array($color)) {
            $shape = new SWFShape();
            $shape->setLine($width, $color['red'], $color['green'], $color['blue'], $color['alpha']);
            $shape->movePenTo($x1, $y1);
            $shape->drawLineTo($x2, $y2);

            return $this->_movie->add($shape);
        } else {
            return false;
        }
    }

    /**
     * Draw a dashed line.
     *
     * @param integer $x0           The x co-ordinate of the start.
     * @param integer $y0           The y co-ordinate of the start.
     * @param integer $x1           The x co-ordinate of the end.
     * @param integer $y1           The y co-ordinate of the end.
     * @param string  $color        The line color.
     * @param string  $width        The width of the line.
     * @param integer $dash_length  The length of a dash on the dashed line
     * @param integer $dash_space   The length of a space in the dashed line
     */
    function dashedLine($x0, $y0, $x1, $y1, $color = 'black', $width = 1, $dash_length = 2, $dash_space = 2)
    {
        // Get the length of the line in pixels.
        $line_length = max(ceil(sqrt(pow(($x1 - $x0), 2) + pow(($y1 - $y0), 2))), 2);

        $cosTheta = ($x1 - $x0) / $line_length;
        $sinTheta = ($y1 - $y0) / $line_length;
        $lastx = $x0;
        $lasty = $y0;

        // Draw the dashed line.
        for ($i = 0; $i < $line_length; $i += ($dash_length + $dash_space)) {
            $x = ($dash_length * $cosTheta) + $lastx;
            $y = ($dash_length * $sinTheta) + $lasty;

            $this->line($lastx, $lasty, $x, $y, $color);

            $lastx = $x + ($dash_space * $cosTheta);
            $lasty = $y + ($dash_space * $sinTheta);
        }
    }

    /**
     * Draw a polyline (a non-closed, non-filled polygon) based on a
     * set of vertices.
     *
     * @param array   $vertices  An array of x and y labeled arrays
     *                           (eg. $vertices[0]['x'], $vertices[0]['y'], ...).
     * @param string  $color     The color you want to draw the line with.
     * @param string  $width     The width of the line.
     */
    function polyline($verts, $color, $width = 1)
    {
        $color = $this->allocateColor($color);

        $shape = new SWFShape();
        $shape->setLine($width, $color['red'], $color['green'], $color['blue'], $color['alpha']);

        $first_done = false;
        foreach ($verts as $value) {
            if (!$first_done) {
                $shape->movePenTo($value['x'], $value['y']);
                $first_done = true;
            }
            $shape->drawLineTo($value['x'], $value['y']);
        }

        return $this->_movie->add($shape);
    }

    /**
     * Draw an arc.
     *
     * @param integer $x      The x co-ordinate of the centre.
     * @param integer $y      The y co-ordinate of the centre.
     * @param integer $r      The radius of the arc.
     * @param integer $start  The start angle of the arc.
     * @param integer $end    The end angle of the arc.
     * @param string $color   The line color of the arc.
     * @param string $fill    The fill color of the arc.
     */
    function arc($x, $y, $r, $start, $end, $color = 'black', $fill = 'none')
    {
        $s = new SWFShape();
        $color = $this->allocateColor($color);
        $s->setLine(1, $color['red'], $color['green'], $color['blue'], $color['alpha']);

        if ($fill != 'none') {
            $fillColor = $this->allocateColor($fill);
            $f = $s->addFill($fillColor['red'], $fillColor['green'], $fillColor['blue'], $fillColor['alpha']);
            $s->setRightFill($f);
        }

        if ($end - $start <= 45) {
            $pts = $this->_arcPoints($r, $start, $end);
            $s->movePenTo($x, $y);
            $s->drawLineTo($pts['x1'] + $x, $pts['y1'] + $y);
            $s->drawCurveTo($pts['x3'] + $x, $pts['y3'] + $y, $pts['x2'] + $x, $pts['y2'] + $y);
            $s->drawLineTo($x, $y);
        } else {
            $sections = ceil(($end - $start) / 45);
            for ($i = 0; $i < $sections; $i++) {
                $pts = $this->_arcPoints($r, $start + ($i * 45), ($start + (($i + 1) * 45) > $end)
                                         ? $end
                                         : ($start + (($i + 1) * 45)));

                // If we are on the first section, move the pen to the
                // centre and draw out to the edge.
                if ($i == 0 && $fill != 'none') {
                    $s->movePenTo($x, $y);
                    $s->drawLineTo($pts['x1'] + $x, $pts['y1'] + $y);
                } else {
                    $s->movePenTo($pts['x1'] + $x, $pts['y1'] + $y);
                }

                // Draw the arc.
                $s->drawCurveTo($pts['x3'] + $x, $pts['y3'] + $y, $pts['x2'] + $x, $pts['y2'] + $y);
            }

            if ($fill != 'none') {
                // Draw a line from the edge back to the centre to close
                // off the segment.
                $s->drawLineTo($x, $y);
            }
        }

        return $this->_movie->add($s);
    }

    /**
     * Draw a rectangle filled with a gradient from $color1 to
     * $color2.
     *
     * @param integer $x       The left x-coordinate of the rectangle.
     * @param integer $y       The top y-coordinate of the rectangle.
     * @param integer $width   The width of the rectangle.
     * @param integer $height  The height of the rectangle.
     * @param string  $color   The outline color of the rectangle.
     * @param string  $fill1   The name of the start color for the gradient.
     * @param string  $fill2   The name of the end color for the gradient.
     */
    function gradientRectangle($x, $y, $width, $height, $color = 'black', $fill1 = 'black', $fill2 = 'white')
    {
        $s = new SWFShape();

        if ($color != 'none') {
            $color = $this->allocateColor($color);
            $s->setLine(1, $color['red'], $color['green'], $color['blue'], $color['alpha']);
        }

        $fill1 = $this->allocateColor($fill1);
        $fill2 = $this->allocateColor($fill2);
        $gradient = new SWFGradient();
        $gradient->addEntry(0.0, $fill1['red'], $fill1['green'], $fill1['blue'], $fill1['alpha']);
        $gradient->addEntry(1.0, $fill2['red'], $fill2['green'], $fill2['blue'], $fill2['alpha']);

        $f = $s->addFill($gradient, SWFFILL_LINEAR_GRADIENT);
        $f->scaleTo($width / $this->_width);
        $f->moveTo($x, $y);
        $s->setRightFill($f);

        $verts[0] = array('x' => $x, 'y' => $y);
        $verts[1] = array('x' => $x + $width, 'y' => $y);
        $verts[2] = array('x' => $x + $width, 'y' => $y + $height);
        $verts[3] = array('x' => $x, 'y' => $y + $height);

        $first_done = false;
        foreach ($verts as $vert) {
            if (!$first_done) {
                $s->movePenTo($vert['x'], $vert['y']);
                $first_done = true;
                $first_x = $vert['x'];
                $first_y = $vert['y'];
            }
            $s->drawLineTo($vert['x'], $vert['y']);
        }
        $s->drawLineTo($first_x, $first_y);

        return $this->_movie->add($s);
    }

}
