<?php
/**
 * Proxy class for using PHP5 Imagick code in PHP4 compliant code.
 * Mostly used to be able to deal with any exceptions that are thrown
 * from Imagick.
 *
 * All methods not explicitly set below are passed through as-is to the imagick
 * object.
 *
 * $Horde: framework/Image/Image/imagick.php,v 1.8.2.4 2009-03-23 18:15:47 mrubinsk Exp $
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael J. Rubinsky <mrubinsk@horde.org>
 * @since   Horde 3.2
 * @package Horde_Image
 */
class Horde_Image_ImagickProxy {

    /**
     * Instance variable for our Imagick object.
     *
     * @var Imagick object
     */
    protected $_imagick = null;

    /**
     * Constructor. Instantiate our imagick object and set some defaults.
     */
    public function __construct($width = 1, $height = 1, $bg = 'white', $format = 'png')
    {
        $this->_imagick = new Imagick();
        $this->_imagick->newImage($width, $height, new ImagickPixel($bg));
        $this->_imagick->setImageFormat($format);
    }

    /**
     * Clears the current imagick object and reloads it
     * with the passed in binary data.
     *
     * @param string $image_data  The data representing an image.
     *
     * @return mixed true || PEAR_Error
     */
    public function loadString($image_data)
    {
        try {
            if (!$this->_imagick->clear()) {
                return PEAR::raiseError('Unable to clear the Imagick object');
            }
            if (!$this->_imagick->readImageBlob($image_data)) {
                return PEAR::raiseError(sprintf("Call to Imagick::readImageBlob failed on line %s of %s", __LINE__, __FILE__));
            }
            return true;
        } catch (ImagickException $e) {
                return PEAR::raiseError($e->getMessage());
        }
    }

    /**
     * Rotates image as described.  Don't pass through since we are not passing
     * a ImagickPixel object from PHP4 code.
     *
     * @param string  $bg     Background color
     * @param integer $angle  Angle to rotate
     *
      * @return mixed true || PEAR_Error
     */
    public function rotateImage($bg, $angle)
    {
        try {
            if (!$this->_imagick->rotateImage(new ImagickPixel($bg), $angle)) {
                return PEAR::raiseError(sprintf("Call to Imagick::rotateImage failed on line %s of %s", __LINE__, __FILE__));
            }
            return true;
        } catch (ImagickException $e) {
            return PEAR::raiseError($e->getMessage());
        }
    }

   /**
     * Change image to a grayscale image.
     *
     * @return mixed  true || PEAR_Error
     */
    function grayscale()
    {
        try {
            if (!$this->_imagick->setImageColorSpace(Imagick::COLORSPACE_GRAY)) {
                return PEAR::raiseError(sprintf("Call to Imagick::setImageColorSpace failed on line %s of %s", __LINE__, __FILE__));
            }
            return true;
        } catch (ImagickException $e) {
            return PEAR::raiseError($e->getMessage());
        }
    }

    /**
     * Places a string of text on this image with the specified properties
     *
     * @TODO
     *
     * @return mixed  true || PEAR_Error
     */
    function text($string, $x, $y, $font = 'ariel', $color = 'black', $direction = 0, $fontsize = 'small')
    {
        try {
            $pixel = new ImagickPixel($color);
            $draw = new ImagickDraw();
            $draw->setFillColor($pixel);
            if (!empty($font)) {
                $draw->setFont($font);
            }
            $draw->setFontSize($fontsize);
            $draw->setGravity(Imagick::GRAVITY_NORTHWEST);
            $res = $this->_imagick->annotateImage($draw, $x, $y, $direction, $string);
            $draw->destroy();
            if (!$res) {
                return PEAR::raiseError(sprintf("Call to Imagick::annotateImage failed on line %s of %s", __LINE__, __FILE__));
            }
            return true;
        } catch (ImagickException $e) {
            return PEAR::raiseError($e->getMessage());
        }
    }

    /**
     * @TODO
     *
     * @return mixed true || PEAR_Error
     */
    function circle($x, $y, $r, $color, $fill)
    {
        try {
            $draw = new ImagickDraw();
            $draw->setFillColor(new ImagickPixel($fill));
            $draw->setStrokeColor(new ImagickPixel($color));
            $draw->circle($x, $y, $r + $x, $y);
            $res = $this->_imagick->drawImage($draw);
            $draw->destroy();
            if (!$res) {
                return PEAR::raiseError(sprintf("Call to Imagick::drawImage failed on line %s of %s", __LINE__, __FILE__));
            }
            return true;
        } catch (ImagickException $e) {
            return PEAR::raiseError($e->getMessage());
        }
    }

    /**
     * @TODO
     *
     * @return mixed  true || PEAR_Error
     */
    function polygon($verts, $color, $fill)
    {
        try {
            $draw = new ImagickDraw();
            $draw->setFillColor(new ImagickPixel($fill));
            $draw->setStrokeColor(new ImagickPixel($color));
            $draw->polygon($verts);
            $res = $this->_imagick->drawImage($draw);
            $draw->destroy();
            if (!$res) {
                return PEAR::raiseError(sprintf("Call to Imagick::drawImage failed on line %s of %s", __LINE__, __FILE__));
            }
            return true;
        } catch (ImagickException $e) {
            return PEAR::raiseError($e->getMessage());
        }
    }

    /**
     * @TODO
     *
     * @return mixed  true || Pear_Error
     */
    function rectangle($x, $y, $width, $height, $color, $fill = 'none')
    {
        try {
            $draw = new ImagickDraw();
            $draw->setStrokeColor(new ImagickPixel($color));
            $draw->setFillColor(new ImagickPixel($fill));
            $draw->rectangle($x, $y, $x + $width, $y + $height);
            $res = $this->_imagick->drawImage($draw);
            $draw->destroy();
            if (!$res) {
                return PEAR::raiseError(sprintf("Call to Imagick::drawImage failed on line %s of %s", __LINE__, __FILE__));
            }
            return true;
        } catch (ImagickException $e) {
            return PEAR::raiseError($e->getMessage());
        }
    }

    /**
     * Rounded Rectangle
     *
     *
     */
    function roundedRectangle($x, $y, $width, $height, $round, $color, $fill)
    {
        $draw = new ImagickDraw();
        $draw->setStrokeColor(new ImagickPixel($color));
        $draw->setFillColor(new ImagickPixel($fill));
        $draw->roundRectangle($x, $y, $x + $width, $y + $height, $round, $round);
        $res = $this->_imagick->drawImage($draw);


    }

    /**
     * @TODO
     *
     * @return mixed  true || PEAR_Error
     */
    function line($x0, $y0, $x1, $y1, $color, $width)
    {
        try {
            $draw = new ImagickDraw();
            $draw->setStrokeColor(new ImagickPixel($color));
            $draw->setStrokeWidth($width);
            $draw->line($x0, $y0, $x1, $y1);
            $res = $this->_imagick->drawImage($draw);
            $draw->destroy();
            if (!$res) {
                return PEAR::raiseError(sprintf("Call to Imagick::drawImage failed on line %s of %s", __LINE__, __FILE__));
            }
            return true;
        } catch (ImagickException $e) {
            return PEAR::raiseError($e->getMessage());
        }
    }

    /**
     * @TODO
     *
     * @return mixed  true || PEAR_Error
     */
    function dashedLine($x0, $y0, $x1, $y1, $color, $width, $dash_length, $dash_space)
    {
        try {
            $draw = new ImagickDraw();
            $draw->setStrokeColor(new ImagickPixel($color));
            $draw->setStrokeWidth($width);
            $draw->setStrokeDashArray(array($dash_length, $dash_space));
            $draw->line($x0, $y0, $x1, $y1);
            $res = $this->_imagick->drawImage($draw);
            $draw->destroy();
            if (!$res) {
                return PEAR::raiseError(sprintf("Call to Imagick::drawImage failed on line %s of %s", __LINE__, __FILE__));
            }
            return true;
        } catch (ImagickException $e) {
            return PEAR::raiseError($e->getMessage());
        }
    }

    /**
     * @TODO
     *
     * @return mixed  true || PEAR_Error
     */
    function polyline($verts, $color, $width)
    {
        try {
            $draw = new ImagickDraw();
            $draw->setStrokeColor(new ImagickPixel($color));
            $draw->setStrokeWidth($width);
            $draw->setFillColor(new ImagickPixel('none'));
            $draw->polyline($verts);
            $res = $this->_imagick->drawImage($draw);
            $draw->destroy();
            if (!$res) {
                return PEAR::raiseError(sprintf("Call to Imagick::drawImage failed on line %s of %s", __LINE__, __FILE__));
            }
            return true;
        } catch (ImagickException $e) {
            return PEAR::raiseError($e->getMessage());
        }
    }

    /**
     * @TODO
     *
     * @return mixed  true || PEAR_Error
     */
    function setImageBackgroundColor($color)
    {
        try {
            $res = $this->_imagick->setImageBackgroundColor(new ImagickPixel($color));
            if (!$res) {
                return PEAR::raiseError(sprintf("Call to Imagick::setImageBackgroundColor failed on line %s of %s", __LINE__, __FILE__));
            }
            return true;
        } catch (ImagickException $e) {
            return PEAR::raiseError($e->getMessage());
        }
    }

    /**
     * @TODO
     *
     * @return mixed  true || PEAR_Error
     */
    function compositeImage(&$imagickProxy, $constant, $x, $y, $channel = null)
    {
        try {
            $res = $this->_imagick->compositeImage($imagickProxy->getIMObject(),
                                                   $constant,
                                                   $x,
                                                   $y, $channel);
            if (!$res) {
                return PEAR::raiseError(sprintf("Call to Imagick::compositeImage failed on line %s of %s", __LINE__, __FILE__));
            }
            return true;
        } catch (ImagickException $e) {
            return PEAR::raiseError($e->getMessage());
        }
    }

    /**
     * @TODO
     *
     * @return mixed  true || PEAR_Error
     */
    function addImage(&$imagickProxy)
    {
        try {
            $res = $this->_imagick->addImage($imagickProxy->getIMObject());
            if (!$res) {
                return PEAR::raiseError(sprintf("Call to Imagick::drawImage failed on line %s of %s", __LINE__, __FILE__));
            }
            return true;
        } catch (ImagickException $e) {
            return PEAR::raiseError($e->getMessage());
        }
    }

    /**
     * Add a border to this image.
     *
     * @param string $color    The color of the border.
     * @param integer $width   The border width
     * @param integer $height  The border height
     *
     * @return mixed  true || PEAR_Error
     *
     */
     function borderImage($color, $width, $height)
     {
         try {
             // Jump through all there hoops to preserve any transparency.
             $border = $this->_imagick->clone();
             $border->borderImage(new ImagickPixel($color),
                                  $width, $height);
             $border->compositeImage($this->_imagick,
                                    constant('Imagick::COMPOSITE_COPY'),
                                    $width, $height);
            $this->_imagick->clear();
            $this->_imagick->addImage($border);
            $border->destroy();
            return true;
         } catch (ImagickException $e) {
             return PEAR::raiseError($e->getMessage());
         }
     }

    /**
     * Return the raw Imagick object
     *
     * @return Imagick  The Imagick object for this proxy.
     */
    function &getIMObject()
    {
        return $this->_imagick;
    }

    /**
     * Produces a clone of this ImagickProxy object.
     *
     * @return mixed  Horde_Image_ImagickProxy object || PEAR_Error
     *
     */
    function &cloneIM()
    {
        try {
            $new = new Horde_Image_ImagickProxy();
            $new->clear();
            if (!$new->readImageBlob($this->getImageBlob())) {
                return PEAR::raiseError(sprintf("Call to Imagick::readImageBlob failed on line %s of %s", __LINE__, __FILE__));
            }
            return $new;
        } catch (ImagickException $e) {
            return PEAR::raiseError($e->getMessage());
        }
    }

    /**
     *
     */
    function polaroidImage($angle = 0)
    {
        try {
            $bg = new ImagickDraw();
            return $this->_imagick->polaroidImage($bg, $angle);
        } catch (ImagickException $e) {
            return PEAR::raiseError($e->getMessage());
        }

    }

    /**
     * Check if a particular method exists in the installed version of Imagick
     *
     * @param string $methodName  The name of the method to check for.
     *
     * @return boolean
     */
    function methodExists($methodName)
    {
        if (method_exists($this->_imagick, $methodName)) {
            return true;
        } else {
            return false;
        }
    }

    /**
     * Pass through any methods not explicitly handled above.
     * Note that any methods that take any Imagick* object as a parameter
     * should be called through it's own method as above so we can avoid
     * having objects that might throw exceptions running in PHP4 code.
     */
    function __call($method, $params)
    {
        try {
            if (method_exists($this->_imagick, $method)) {
                $result = call_user_func_array(array($this->_imagick, $method), $params);
            } else {
                return PEAR::raiseError(sprintf("Unable to execute %s.  Your ImageMagick version may not support this feature.", $method));
            }
        } catch (ImagickException $e) {
            return PEAR::raiseError($e->getMessage());
        }
        return $result;
    }

}
