<?php

require_once dirname(__FILE__) . '/../Image.php';
require_once 'XML/SVG.php';

/**
 * This class implements the Horde_Image:: API for SVG.
 *
 * $Horde: framework/Image/Image/svg.php,v 1.31.10.10 2009-01-06 15:23:12 jan Exp $
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
class Horde_Image_svg extends Horde_Image {

    var $_svg;

    /**
     * Capabilites of this driver.
     *
     * @var array
     */
    var $_capabilities = array('canvas');

    function Horde_Image_svg($params)
    {
        parent::Horde_Image($params);
        $this->_svg = new XML_SVG_Document(array('width' => $this->_width,
                                                 'height' => $this->_height));
    }

    function getContentType()
    {
        return 'image/svg+xml';
    }

    function getLink($url, $title = '')
    {
    }

    function display()
    {
        $this->_svg->printElement();
    }

    /**
     * Return the raw data for this image.
     *
     * @return string  The raw image data.
     */
    function raw()
    {
        return $this->_svg->bufferObject();
    }

    function getFont($font)
    {
        return $font;
    }

    function _createSymbol($s, $id)
    {
        $s->setParam('id', $id);
        $defs = new XML_SVG_Defs();
        $defs->addChild($s);
        $this->_svg->addChild($defs);
    }

    function _createDropShadow($id = 'dropShadow')
    {
        $defs = new XML_SVG_Defs();
        $filter = new XML_SVG_Filter(array('id' => $id));
        $filter->addPrimitive('GaussianBlur', array('in' => 'SourceAlpha',
                                                    'stdDeviation' => 2,
                                                    'result' => 'blur'));
        $filter->addPrimitive('Offset', array('in' => 'blur',
                                              'dx' => 4,
                                              'dy' => 4,
                                              'result' => 'offsetBlur'));
        $merge = new XML_SVG_FilterPrimitive('Merge');
        $merge->addMergeNode('offsetBlur');
        $merge->addMergeNode('SourceGraphic');

        $filter->addChild($merge);
        $defs->addChild($filter);
        $this->_svg->addChild($defs);
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
        $height = 12;
        $style = 'font-family:' . $font . ';font-height:' . $height . 'px;fill:' . $this->getHexColor($color) . ';text-anchor:start;';
        $transform = 'rotate(' . $direction . ',' . $x . ',' . $y . ')';
        $this->_svg->addChild(new XML_SVG_Text(array('text' => $string,
                                                     'x' => (int)$x,
                                                     'y' => (int)$y + $height,
                                                     'transform' => $transform,
                                                     'style' => $style)));
    }

    /**
     * Draw a circle.
     *
     * @param integer $x      The x coordinate of the centre.
     * @param integer $y      The y coordinate of the centre.
     * @param integer $r      The radius of the circle.
     * @param string  $color  The line color of the circle.
     * @param string  $fill   The color to fill the circle.
     */
    function circle($x, $y, $r, $color, $fill = null)
    {
        if (!empty($fill)) {
            $style = 'fill:' . $this->getHexColor($fill) . '; ';
        } else {
            $style = 'fill:none;';
        }
        $style .= 'stroke:' . $this->getHexColor($color) . '; stroke-width:1';

        $this->_svg->addChild(new XML_SVG_Circle(array('cx' => $x,
                                                       'cy' => $y,
                                                       'r' => $r,
                                                       'style' => $style)));
    }

    /**
     * Draw a polygon based on a set of vertices.
     *
     * @param array $vertices  An array of x and y labeled arrays
     *                         (eg. $vertices[0]['x'], $vertices[0]['y'], ...).
     * @param string $color    The color you want to draw the polygon with.
     * @param string $fill     The color to fill the polygon.
     */
    function polygon($verts, $color, $fill = null)
    {
        if (!empty($fill)) {
            $style = 'fill:' . $this->getHexColor($fill) . '; ';
        } else {
            $style = 'fill:none;';
        }
        $style .= 'stroke:' . $this->getHexColor($color) . '; stroke-width:1';

        $points = '';
        foreach ($verts as $v) {
            $points .= $v['x'] . ',' . $v['y'] . ' ';
        }
        $points = trim($points);

        $this->_svg->addChild(new XML_SVG_Polygon(array('points' => $points,
                                                        'style' => $style)));
    }

    /**
     * Draw a rectangle.
     *
     * @param integer $x       The left x-coordinate of the rectangle.
     * @param integer $y       The top y-coordinate of the rectangle.
     * @param integer $width   The width of the rectangle.
     * @param integer $height  The height of the rectangle.
     * @param string $color    The line color of the rectangle.
     * @param string $fill     The color to fill the rectangle.
     */
    function rectangle($x, $y, $width, $height, $color, $fill = null)
    {
        if (!empty($fill)) {
            $style = 'fill:' . $this->getHexColor($fill) . '; ';
        } else {
            $style = 'fill:none;';
        }
        $style .= 'stroke:' . $this->getHexColor($color) . '; stroke-width:1';

        $this->_svg->addChild(new XML_SVG_Rect(array('x' => $x,
                                                     'y' => $y,
                                                     'width' => $width,
                                                     'height' => $height,
                                                     'style' => $style)));
    }

    /**
     * Draw a rectangle.
     *
     * @param integer $x       The left x-coordinate of the rectangle.
     * @param integer $y       The top y-coordinate of the rectangle.
     * @param integer $width   The width of the rectangle.
     * @param integer $height  The height of the rectangle.
     * @param integer $round   The width of the corner rounding.
     * @param string  $color   The line color of the rectangle.
     * @param string  $fill    The color to fill the rectangle.
     */
    function roundedRectangle($x, $y, $width, $height, $round, $color, $fill)
    {
        if (!empty($fill)) {
            $style = 'fill:' . $this->getHexColor($fill) . '; ';
        } else {
            $style = 'fill:none;';
        }
        $style .= 'stroke:' . $this->getHexColor($color) . '; stroke-width:1';

        $this->_svg->addChild(new XML_SVG_Rect(array('x' => $x,
                                                     'y' => $y,
                                                     'rx' => $round,
                                                     'ry' => $round,
                                                     'width' => $width,
                                                     'height' => $height,
                                                     'style' => $style)));
    }

    /**
     * Draw a line.
     *
     * @param integer $x0     The x coordinate of the start.
     * @param integer $y0     The y coordinate of the start.
     * @param integer $x1     The x coordinate of the end.
     * @param integer $y1     The y coordinate of the end.
     * @param string $color   The line color.
     * @param string $width   The width of the line.
     */
    function line($x1, $y1, $x2, $y2, $color = 'black', $width = 1)
    {
        $style = 'stroke:' . $this->getHexColor($color) . '; stroke-width:' . (int)$width;
        $this->_svg->addChild(new XML_SVG_Line(array('x1' => $x1,
                                                     'y1' => $y1,
                                                     'x2' => $x2,
                                                     'y2' => $y2,
                                                     'style' => $style)));
    }

    /**
     * Draw a dashed line.
     *
     * @param integer $x0           The x coordinate of the start.
     * @param integer $y0           The y coordinate of the start.
     * @param integer $x1           The x coordinate of the end.
     * @param integer $y1           The y coordinate of the end.
     * @param string  $color        The line color.
     * @param string  $width        The width of the line.
     * @param integer $dash_length  The length of a dash on the dashed line
     * @param integer $dash_space   The length of a space in the dashed line
     */
    function dashedLine($x1, $y1, $x2, $y2, $color = 'black', $width = 1, $dash_length = 2, $dash_space = 2)
    {
        $style = 'stroke:' . $this->getHexColor($color) . '; stroke-width:' . (int)$width . '; stroke-dasharray:' . $dash_length . ',' . $dash_space . ';';
        $this->_svg->addChild(new XML_SVG_Line(array('x1' => $x1,
                                                     'y1' => $y1,
                                                     'x2' => $x2,
                                                     'y2' => $y2,
                                                     'style' => $style)));
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
        $style = 'stroke:' . $this->getHexColor($color) . '; stroke-width:' . $width . ';fill:none;';

        // Calculate the path entry.
        $path = '';

        $first = true;
        foreach ($verts as $vert) {
            if ($first) {
                $first = false;
                $path .= 'M ' . $vert['x'] . ',' . $vert['y'];
            } else {
                $path .= ' L ' . $vert['x'] . ',' . $vert['y'];
            }
        }

        $this->_svg->addChild(new XML_SVG_Path(array('d' => $path,
                                                     'style' => $style)));
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
    function arc($x, $y, $r, $start, $end, $color = 'black', $fill = null)
    {
        if (!empty($fill)) {
            $style = 'fill:' . $this->getHexColor($fill) . '; ';
        } else {
            $style = 'fill:none;';
        }
        $style .= 'stroke:' . $this->getHexColor($color) . '; stroke-width:1';

        $mid = round(($start + $end) / 2);

        // Calculate the path entry.
        $path = '';

        // If filled, draw the outline.
        if (!empty($fill)) {
            // Start at the center of the ellipse the arc is on.
            $path .= "M $x,$y ";

            // Draw out to ellipse edge.
            list($arcX, $arcY) = $this->_circlePoint($start, $r * 2);
            $path .= 'L ' . round($x + $arcX) . ',' .
                round($y + $arcY) . ' ';
        }

        // Draw arcs.
        list($arcX, $arcY) = $this->_circlePoint($mid, $r * 2);
        $path .= "A $r,$r 0 0 1 " .
            round($x + $arcX) . ',' .
            round($y + $arcY) . ' ';

        list($arcX, $arcY) = $this->_circlePoint($end, $r * 2);
        $path .= "A $r,$r 0 0 1 " .
            round($x + $arcX) . ',' .
            round($y + $arcY) . ' ';

        // If filled, close the outline.
        if (!empty($fill)) {
            $path .= 'Z';
        }

        $path = trim($path);

        $this->_svg->addChild(new XML_SVG_Path(array('d' => $path,
                                                     'style' => $style)));
    }

}
