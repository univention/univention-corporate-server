<?php

require_once 'Horde/Util.php';

/**
 * This class defines the Horde_Image:: API, and also provides some
 * utility functions, such as generating highlights of a color.
 *
 * $Horde: framework/Image/Image.php,v 1.37 2004/05/18 14:53:56 mdjukic Exp $
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
class Horde_Image {

    /**
     * Current color.
     *
     * @var string $_rgb
     */
    var $_rgb = 'ff0000';

    /**
     * Background color.
     *
     * @var string $_background
     */
    var $_background = 'white';

    /**
     * Observers.
     *
     * @var array $_observers
     */
    var $_observers = array();

    /**
     * Capabilites of this driver.
     *
     * @var array $_capabilities
     */
    var $_capabilities = array();

    /**
     * The current image data.
     *
     * @var string $_data
     */
    var $_data = '';

    /**
     * The current image id.
     *
     * @var string $_id
     */
    var $_id = '';

    /**
     * The current height/width of the image data.
     *
     * @var integer $_height
     * @var integer $_width
     */
    var $_width = 0;
    var $_height = 0;

    /**
     * A directory for temporary files.
     *
     * @var string $_tmpdir
     */
    var $_tmpdir;

    /**
     * Constructor.
     *
     * @access public
     *
     * @param string $rgb  The base color for generated pixels/images.
     */
    function Horde_Image($params)
    {
        $this->_tmpdir = $params['temp'];
        if (isset($params['width'])) {
            $this->_width = $params['width'];
        }
        if (isset($params['height'])) {
            $this->_height = $params['height'];
        }
        if (!empty($params['rgb'])) {
            $this->_rgb = $params['rgb'];
        }
        $this->_background = isset($params['background']) ? $params['background'] : 'white';
    }

    function getCapabilites()
    {
        return $this->_capabilities;
    }

    function hasCapability($capability)
    {
        return in_array($capability, $this->_capabilities);
    }

    function getLink($url, $title = '')
    {
        return Horde::img($url, $title, '', '');
    }

    /**
     * Generate image headers.
     */
    function headers()
    {
        header('Content-type: ' . $this->getContentType());
    }

    /**
     * Calculate a lighter (or darker) version of a color.
     *
     * @static
     *
     * @access public
     *
     * @param string $color            An HTML color, e.g.: #ffffcc.
     * @param optional string $factor  TODO
     *
     * @return string  A modified HTML color.
     */
    function modifyColor($color, $factor = 0x11)
    {
        $r = hexdec(substr($color, 1, 2)) + $factor;
        $g = hexdec(substr($color, 3, 2)) + $factor;
        $b = hexdec(substr($color, 5, 2)) + $factor;

        $r = min(max($r, 0), 255);
        $g = min(max($g, 0), 255);
        $b = min(max($b, 0), 255);

        return '#' . str_pad(dechex($r), 2, '0', STR_PAD_LEFT) . str_pad(dechex($g), 2, '0', STR_PAD_LEFT) . str_pad(dechex($b), 2, '0', STR_PAD_LEFT);
    }

    /**
     * Calculate a more intense version of a color.
     *
     * @static
     *
     * @param string $color            An HTML color, e.g.: #ffffcc.
     * @param optional string $factor  TODO
     *
     * @return string  A more intense HTML color.
     */
    function moreIntenseColor($color, $factor = 0x11)
    {
        $r = hexdec(substr($color, 1, 2));
        $g = hexdec(substr($color, 3, 2));
        $b = hexdec(substr($color, 5, 2));

        if ($r >= $g && $r >= $b) {
            $g = $g / $r;
            $b = $b / $r;

            $r += $factor;
            $g = floor($g * $r);
            $b = floor($b * $r);
        } elseif ($g >= $r && $g >= $b) {
            $r = $r / $g;
            $b = $b / $g;

            $g += $factor;
            $r = floor($r * $g);
            $b = floor($b * $g);
        } else {
            $r = $r / $b;
            $g = $g / $b;

            $b += $factor;
            $r = floor($r * $b);
            $g = floor($g * $b);
        }

        $r = min(max($r, 0), 255);
        $g = min(max($g, 0), 255);
        $b = min(max($b, 0), 255);

        return '#' . str_pad(dechex($r), 2, '0', STR_PAD_LEFT) . str_pad(dechex($g), 2, '0', STR_PAD_LEFT) . str_pad(dechex($b), 2, '0', STR_PAD_LEFT);
    }

    function getRGB($colorname)
    {
        require_once dirname(__FILE__) . '/Image/rgb.php';
        return isset($GLOBALS['horde_image_rgb_colors'][$colorname]) ?
            $GLOBALS['horde_image_rgb_colors'][$colorname] :
            array(0, 0, 0);
    }

    function getHexColor($colorname)
    {
        require_once dirname(__FILE__) . '/Image/rgb.php';
        if (isset($GLOBALS['horde_image_rgb_colors'][$colorname])) {
            list($r, $g, $b) = $GLOBALS['horde_image_rgb_colors'][$colorname];
            return '#' . str_pad(dechex(min($r, 255)), 2, '0', STR_PAD_LEFT) . str_pad(dechex(min($g, 255)), 2, '0', STR_PAD_LEFT) . str_pad(dechex(min($b, 255)), 2, '0', STR_PAD_LEFT);
        } else {
            return 'black';
        }
    }

    /**
     * Draw a shaped point at the specified (x,y) point. Useful for
     * scatter diagrams, debug points, etc. Draws squares, circles,
     * diamonds, and triangles.
     *
     * @param integer $x              The x coordinate of the point to brush.
     * @param integer $y              The y coordinate of the point to brush.
     * @param optional string $color  The color to brush the point with.
     * @param optional string $shape  What brush to use? Defaults to a square.
     */
    function brush($x, $y, $color = 'black', $shape = 'square')
    {
        switch ($shape) {
        case 'triangle':
            $verts[0] = array('x' => $x + 3, 'y' => $y + 3);
            $verts[1] = array('x' => $x, 'y' => $y - 3);
            $verts[2] = array('x' => $x - 3, 'y' => $y + 3);
            $this->polygon($verts, $color, $color);
            break;

        case 'circle':
            $this->circle($x, $y, 3, $color, $color);
            break;

        case 'diamond':
            $verts[0] = array('x' => $x - 3, 'y' => $y);
            $verts[1] = array('x' => $x, 'y' => $y + 3);
            $verts[2] = array('x' => $x + 3, 'y' => $y);
            $verts[3] = array('x' => $x, 'y' => $y - 3);
            $this->polygon($verts, $color, $color);
            break;

        case 'square':
        default:
            $this->rectangle($x - 2, $y - 2, 4, 4, $color, $color);
            break;
        }
    }

    /**
     * Add an observer to this image. The observer will be notified
     * when the image's changes.
     */
    function addObserver($method, &$object)
    {
        $this->_observers[] = array($method, &$object);
    }

    /**
     * Let observers know that something happened worth acting on.
     */
    function notifyObservers()
    {
        for ($i = 0; $i < count($this->_observers); ++$i) {
            $obj = &$this->_observers[$i][1];
            $method = $this->_observers[$i][0];
            $obj->$method($this);
        }
    }

    /**
     * Reset the image data.
     */
    function reset()
    {
        $this->_data = '';
        $this->_id = '';
        $this->_width = null;
        $this->_height = null;
        $this->_background = 'white';
    }

    /**
     * Get the height and width of the current image data.
     *
     * @return array  An hash with 'width' containing the width,
     *                'height' containing the height of the image.
     */
    function getDimensions()
    {
        $tmp = $this->toFile();
        $details = @getimagesize($tmp);
        unlink($tmp);

        return array('width' => $details[0],
                     'height' => $details[1]);
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
            $this->reset();
            $this->_data = $image_data;
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
        if ($filename != $this->_id) {
            $this->reset();
            if (!file_exists($filename)) {
                return PEAR::raiseError('The image file ' . $image . ' does not exist.');
            }
            if ($this->_data = file_get_contents($filename)) {
                $this->_id = $filename;
            } else {
                return PEAR::raiseError('Could not load the image file ' . $image);
            }
        }
    }

    function toFile($data = false)
    {
        $tmp = Util::getTempFile('img', false, $this->_tmpdir);
        $fp = @fopen($tmp, 'wb');
        fwrite($fp, $data ? $data : $this->raw());
        fclose($fp);
        return $tmp;
    }

    /**
     * Display the current image.
     */
    function display()
    {
        $this->headers();
        echo $this->raw();
    }

    /**
     * Return the raw data for this image.
     *
     * @return string  The raw image data.
     */
    function raw()
    {
        return $this->_data;
    }

    /**
     * Get an x,y pair on circle, assuming center is 0,0.
     *
     * @access private
     *
     * @param double $degrees   The degrees of arc to get the point for.
     * @param int    $diameter  The diameter of the circle.
     *
     * @return array  (x coordinate, y coordinate) of the point.
     */
    function _circlePoint($degrees, $diameter)
    {
        // Avoid problems with doubles.
        $degrees += 0.0001;

        return array(cos(deg2rad($degrees)) * ($diameter / 2),
                     sin(deg2rad($degrees)) * ($diameter / 2));
    }

    /**
     * Get point coordinates at the limits of an arc. Only valid for
     * angles ($end - $start) <= 45 degrees.
     *
     * @access private
     *
     * @param integer $r      The radius of the arc.
     * @param integer $start  The starting angle.
     * @param integer $end    The ending angle.
     *
     * @return array  The start point, end point, and anchor point.
     */
    function _arcPoints($r, $start, $end)
    {
        // Start point.
        $pts['x1'] = $r * cos(deg2rad($start));
        $pts['y1'] = $r * sin(deg2rad($start));

        // End point.
        $pts['x2'] = $r * cos(deg2rad($end));
        $pts['y2'] = $r * sin(deg2rad($end));

        // Anchor point.
        $a3 = ($start + $end) / 2;
        $r3 = $r / cos(deg2rad(($end - $start) / 2));
        $pts['x3'] = $r3 * cos(deg2rad($a3));
        $pts['y3'] = $r3 * sin(deg2rad($a3));

        return $pts;
    }

    /**
     * Attempts to return a concrete Horde_Image instance based on
     * $driver.
     *
     * @param mixed $driver  The type of concrete Horde_Image subclass to return.
     *                       This is based on the storage driver ($driver). The
     *                       code is dynamically included. If $driver is an array,
     *                       then we will look in $driver[0]/lib/Image/ for
     *                       the subclass implementation named $driver[1].php.
     * @param array $params  (optional) A hash containing any additional
     *                       configuration or connection parameters a subclass
     *                       might need.
     *
     * @return object Horde_Image  The newly created concrete Horde_Image instance,
     *                             or false on an error.
     */
    function &factory($driver, $params = array())
    {
        if (is_array($driver)) {
            list($app, $driver) = $driver;
        }

        if (!empty($app)) {
            require_once $GLOBALS['registry']->getParam('fileroot', $app) . '/lib/Image/' . $driver . '.php';
        } elseif (@file_exists(dirname(__FILE__) . '/Image/' . $driver . '.php')) {
            require_once dirname(__FILE__) . '/Image/' . $driver . '.php';
        } else {
            @include_once 'Horde/Image/' . $driver . '.php';
        }
        $class = 'Horde_Image_' . $driver;
        if (class_exists($class)) {
            return $ret = &new $class($params);
        } else {
            return PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }
    }

    /**
     * Attempts to return a reference to a concrete Horde_Image
     * instance based on $driver. It will only create a new instance
     * if no Horde_Image instance with the same parameters currently
     * exists.
     *
     * This should be used if multiple types of image renderers (and,
     * thus, multiple Horde_Image instances) are required.
     *
     * This method must be invoked as: $var = &Horde_Image::singleton()
     *
     * @param mixed $driver  The type of concrete Horde_Image subclass to return.
     *                       This is based on the storage driver ($driver). The
     *                       code is dynamically included. If $driver is an array,
     *                       then we will look in $driver[0]/lib/Image/ for
     *                       the subclass implementation named $driver[1].php.
     * @param array $params  (optional) A hash containing any additional
     *                       configuration or connection parameters a subclass
     *                       might need.
     *
     * @return object Horde_Image  The concrete Horde_Image reference, or false
     *                             on an error.
     */
    function &singleton($driver, $params = array())
    {
        static $instances;
        if (!isset($instances)) {
            $instances = array();
        }

        $signature = serialize(array($driver, $params));
        if (!isset($instances[$signature])) {
            $instances[$signature] = &Horde_Image::factory($driver, $params);
        }

        return $instances[$signature];
    }

}
