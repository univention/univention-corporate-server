<?php
/**
 * The Horde graphing suite.
 *
 * Provides a set of graph backends and methods for creating graphs as
 * HTML tables, SVG images, etc.
 *
 * $Horde: framework/Graph/Graph.php,v 1.25 2004/05/06 20:55:35 chuck Exp $
 *
 * Copyright 2002-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Graph
 */
class Horde_Graph {

    /**
     * The Horde_Image instance that we are drawing the graph to.
     * @protected
     * @var object Horde_Image $img
     */
    var $img;

    var $_graphs = array();

    var $_height;
    var $_width;

    var $_title = '';

    var $_background = 'lightgray';
    var $_titleFont = 'sans-serif';
    var $_labelFont = 'sans-serif';
    var $_axisFont = 'monospace';

    var $_paddingLeft = 60;
    var $_paddingBottom = 40;
    var $_paddingTop = 30;
    var $_paddingRight = 20;

    var $_offsetGridX = 0;

    var $_imgType = 'gd';

    var $_data = array('x' => array(),
                       'y' => array());

    var $_tmpdir;

    var $_plots = array();
    var $_charts = array();

    function Horde_Graph($params)
    {
        if (!empty($params['temp'])) {
            $this->_tmpdir = $params['temp'];
        }

        if (!empty($params['width'])) {
            $this->_width = $params['width'];
            $this->_height = $params['height'];
        }

        if (!empty($params['imgType'])) {
            $this->_imgType = $params['imgType'];
        }
    }

    function &addPlot($plotType, $plotParams)
    {
        if (count($this->_charts)) {
            return PEAR::raiseError('Mixing of Charts and Plots is not allowed.');
        }

        $plotType = basename($plotType);
        @include_once dirname(__FILE__) . '/Graph/Plot/' . $plotType . '.php';

        $class = 'Horde_Graph_Plot_' . $plotType;
        if (class_exists($class)) {
            $plot = &new $class($this, $plotParams);
            $this->_plots[] = &$plot;
            return $plot;
        } else {
            return PEAR::raiseError('Plot type not found');
        }
    }

    function &addChart($chartType, $chartParams)
    {
        if (count($this->_plots)) {
            return PEAR::raiseError('Mixing of Charts and Plots is not allowed.');
        }

        $chartType = basename($chartType);
        @include_once dirname(__FILE__) . '/Graph/Chart/' . $chartType . '.php';

        $class = 'Horde_Graph_Chart_' . $chartType;
        if (class_exists($class)) {
            $chart = &new $class($this, $chartParams);
            $this->_charts[] = &$chart;
            return $chart;
        } else {
            return PEAR::raiseError('Chart type not found');
        }
    }

    function addXData($data)
    {
        $this->_data['x'] = $data;
    }

    function addYData($data, $name = '')
    {
        if (empty($name)) {
            $name = md5(serialize($data));
        }
        $this->_data['y'][$name] = $data;
        return $name;
    }

    function set($param, $value)
    {
        $key = '_' . $param;
        $this->$key = $value;
    }

    /**
     * Cache the image and return a link to view it out of the cache.
     */
    function display()
    {
        global $conf, $registry;
        require_once 'Horde/Cache.php';
        $cache = &Horde_Cache::singleton($conf['cache']['driver'], Horde::getDriverConfig('cache', $conf['cache']['driver']));

        $this->initialize();

        $cid = md5(serialize($this));
        Horde_Cache::setCacheObject($this, 'getCacheable');
        $cache->getData($cid, 'Horde_Cache::getCacheObject()', $conf['cache']['default_lifetime']);

        $url = Horde::url($registry->getParam('webroot', 'horde') . '/services/cacheview.php');
        $url = Util::addParameter($url, 'cid', $cid);

        return $this->img->getLink($url, $this->_title);
    }

    /**
     * Return an array containing all information necessary to
     * retrieve the image, including the data and content-type.
     *
     * @return array
     */
    function getCacheable()
    {
        return serialize(array('data' => $this->draw(false),
                               'ctype' => $this->img->getContentType()));
    }

    /**
     * Process all of the data sets and set graph properties.
     */
    function initialize()
    {
        // Load a Horde_Image to draw on.
        require_once 'Horde/Image.php';
        $this->img = &Horde_Image::factory($this->_imgType, array('height' => $this->_height, 'width' => $this->_width, 'temp' => $this->_tmpdir));

        // Total image and graph area dimensions.
        $width = $this->_width - 1;
        $height = $this->_height - 1;

        $this->_graphTop = $this->_paddingTop;
        $this->_graphBottom = $this->_height - 1 - ($this->_paddingTop + $this->_paddingBottom);
        $this->_graphLeft = $this->_paddingLeft;
        $this->_graphRight = $this->_width - $this->_paddingRight - 1;
        $this->_graphHeight = $this->_graphBottom - $this->_graphTop;
        $this->_graphWidth = $this->_graphRight - $this->_graphLeft;

        $this->_gridX = min(count($this->_data['x']), round($this->_graphWidth / 40));
        if (!$this->_gridX) {
            require_once 'PEAR.php';
            return PEAR::raiseError('No data.');
        }

        // Find the range of all y values.
        $ydata = array();
        $this->_gridY = 0;
        foreach ($this->_data['y'] as $data) {
            $this->_gridY = max($this->_gridY, count($data));
            $ydata = array_merge($ydata, $data);
        }

        // Calculate the number of Y gridlines (and thus, labels) to
        // show. Try to make sure we don't end up with too dense a
        // grid, but also make sure that we have a few grid lines to
        // break up small datasets.
        $this->_gridY = max(min($this->_gridY, floor($this->_graphHeight / 30)), floor($this->_graphHeight / 60));

        $this->_maxX = count($this->_data['x']);
        list($this->_minY, $this->_maxY) = $this->_findRange($ydata);
        $this->_diffY = $this->_maxY - $this->_minY;

        if (($this->_maxY - $this->_minY) == 0) {
            require_once 'PEAR.php';
            return PEAR::raiseError('No range to graph. Check data.');
        }

        // Format text for labeling the Y axis.
        $deltaLabelsY = ($this->_maxY - $this->_minY) / ($this->_gridY);
        for ($i = 0; $i <= $this->_gridY; $i++) {
            $text = $this->_minY + ($deltaLabelsY * $i);
            $this->_labelsY[$i] = number_format($text, 2);
        }
        if (empty($this->_labelsY)) {
            require_once 'PEAR.php';
            return PEAR::raiseError('No Y axis data.');
        }

        // Calculate the spacing for ticks and grid lines.
        $denominator = $this->_maxX - 1 + (2 * $this->_offsetGridX);
        if ($denominator == 0) {
            $denominator = 1;
        }
        $this->_factorX = $this->_graphWidth / $denominator;
        $this->_factorY = $this->_graphHeight / $this->_maxY;

        $denominator = $this->_gridX - 1 + 2 * $this->_offsetGridX;
        if ($denominator == 0) {
            $denominator = 1;
        }
        $this->_deltaTicksX = ($this->_graphWidth / $denominator) / $this->_factorX;
        $this->_deltaTicksY = ($this->_graphHeight / $this->_gridY) / $this->_factorY;

        return true;
    }

    function draw($display = true)
    {
        $result = $this->initialize();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $plots = count($this->_plots);
        $charts = count($this->_charts);

        if ($plots) {
            $this->drawBackground();
            $this->drawTitle();
            $this->drawGridX();
            $this->drawGridY();
            $this->drawPlotBox();
            $this->drawLabelsX();
            $this->drawLabelsY();

            for ($i = 0; $i < $plots; $i++) {
                $this->_plots[$i]->draw();
            }
        } elseif ($charts) {
            $this->drawTitle();

            for ($i = 0; $i < $charts; $i++) {
                $this->_charts[$i]->draw();
            }
        }

        return $display ? $this->img->display() : $this->img->raw();
    }

    function drawBackground()
    {
        $this->img->rectangle(0, 0, $this->_width - 1, $this->_height - 1, 'black', $this->_background);
        $this->img->rectangle($this->_graphLeft, $this->_graphTop, $this->_graphWidth, $this->_graphHeight, 'black', 'white');
    }

    /**
     * Draw a box around the plot area.
     */
    function drawPlotBox()
    {
        $this->img->rectangle($this->_graphLeft, $this->_graphTop, $this->_graphWidth, $this->_graphHeight, 'black');
    }

    /**
     * Draws grid lines from top to bottom on the image.
     */
    function drawGridX()
    {
        for ($i = 0; $i < $this->_gridX; $i++) {
            $x = $this->translateX($this->_deltaTicksX * $i);
            $this->img->dashedLine($x, $this->_graphTop, $x, $this->_graphBottom, 'gray');
        }
    }

    /**
     * Draws grid lines from left to right on the image.
     */
    function drawGridY()
    {
        for ($i = 0; $i < $this->_gridY; $i++) {
            $y = $this->translateY($this->_deltaTicksY * $i);
            $this->img->dashedLine($this->_graphLeft, $y, $this->_graphRight, $y, 'gray');
        }
    }

    /**
     * Draw the title.
     */
    function drawTitle()
    {
        if (!empty($this->_title)) {
            $this->img->text($this->_title, $this->_graphLeft + ($this->_graphWidth / 2) - ((strlen($this->_title) / 2) * 7), $this->_graphTop - 20, $this->_titleFont);
        }
    }

    /**
     * Draws the axis tag text outside the plotting area on the x
     * axis.
     */
    function drawLabelsX()
    {
        // Draw X axis label.
        if (!empty($this->_xlabel)) {
            $x = $this->_graphLeft + ($this->_graphWidth / 2) - (strlen($this->_xlabel) * 3);
            $y = $this->_graphBottom + 50;
            $this->img->text($this->_xlabel, $x, $y, $this->_labelFont);
        }

        $lastX = 0;
        $minDiff = 20;
        foreach ($this->_data['x'] as $i => $text) {
            $x = $this->translateX($i);
            if ($x - $lastX >= $minDiff) {
                $lastX = $x;
                $this->img->text($text, $x - 5, $this->_graphBottom + (strlen($text) * 7), $this->_axisFont, 'black', -90);
                $this->img->line($x, $this->_graphBottom + 2, $x, $this->_graphBottom - 2);
            }
        }
    }

    /**
     * Draws the axis tag text outside the plotting area on the y
     * axis.
     */
    function drawLabelsY()
    {
        // Draw Y axis label.
        if (!empty($this->_ylabel)) {
            $y = $this->_graphTop + ($this->_graphHeight / 2) + ((strlen($this->_ylabel) / 2) * 5);
            $this->img->text($this->_ylabel, 5, $y, $this->_labelFont, 'black', -90);
        }

        foreach ($this->_labelsY as $i => $label) {
            $y = $this->translateY($i * $this->_deltaTicksY);
            $this->img->text($label, $this->_graphLeft - (strlen($label) * 7), $y - 5, $this->_axisFont);
            $this->img->line($this->_graphLeft - 2, $y, $this->_graphLeft + 2, $y);
        }
    }

    /**
     * Take a pair of (x,y) graph coordinates and return the
     * screen-pixel coordinates for them.
     *
     * @param float &$x     The x position in world coordinates.
     * @param float &$y     The y position in world coordinates.
     */
    function translate(&$x, &$y)
    {
        $x = $this->translateX($x);
        $y = $this->translateY($y);
    }

    /**
     * Translate the x coordinate of a point on the plot to screen
     * coordinates.
     *
     * @param float $x  The x world (plot) coordinate.
     */
    function translateX($x)
    {
        return (($x + $this->_offsetGridX) * $this->_factorX) + $this->_graphLeft;
    }

    /**
     * Translate the y coordinate of a point on the plot to screen
     * coordinates.
     *
     * @param float $y  The y world (plot) coordinate.
     */
    function translateY($y)
    {
        if ($y) {
            return $this->_graphBottom - ($y * $this->_factorY);
        } else {
            return $this->_graphBottom;
        }
    }

    /**
     * Find the minimum and maximum values for a set of data.
     *
     * The $resolution variable is used for rounding maximum and
     * minimum values. If maximum value is 8645 then:
     *
     * If $resolution is 0, then maximum value becomes 9000.
     * If $resolution is 1, then maximum value becomes 8700.
     * If $resolution is 2, then maximum value becomes 8650.
     * If $resolution is 3, then maximum value becomes 8645.
     *
     * @param array   $data        The Dataset to find the range for.
     * @param integer $min         (optional) Minimum value to start at. The lowest number
     *                             in the dataset is used if it's lower.
     * @param integer $max         (optional) Maximum value to start at. The highest number
     *                             in the dataset is used if it's higher.
     * @param integer $resolution  (optional) The resolution to use for the range.
     *
     * @return array  The minimum and maximum values for the range.
     * @private
     */
    function _findRange($data, $min = 0, $max = 0, $resolution = 0)
    {
        if (!count($data)) {
            return array('min' => 0, 'max' => 0);
        }

        $data[] = $max;
        $data[] = $min;
        $max = max($data);
        $min = min($data);

        if ($max == 0) {
            $factor = 1;
        } else {
            if ($max < 0) {
                $factor = -pow(10, (floor(log10(abs($max))) + $resolution));
            } else {
                $factor = pow(10, (floor(log10(abs($max))) - $resolution));
            }
        }

        $max = $factor * @ceil($max / $factor);
        $min = $factor * @floor($min / $factor);

        return array($min, $max);
    }

}
