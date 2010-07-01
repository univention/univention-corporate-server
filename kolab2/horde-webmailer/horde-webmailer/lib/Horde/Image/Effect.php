<?php
/**
 * The Horde_Image_Effect parent class defines a general API for
 * ways to apply effects to Horde_Image objects.
 *
 * $Horde: framework/Image/Image/Effect.php,v 1.5.2.1 2007-12-20 13:49:10 jan Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Michael J. Rubinsky <mrubinsk@horde.org>
 * @since   Horde 3.2
 * @package Horde_Image
 */
class Horde_Image_Effect {

    /**
     * Effect parameters.
     *
     * @var array
     */
    var $_params = array();

    var $_image = null;

    /**
     * Effect constructor.
     *
     * @param array $params  Any parameters for the effect. Parameters are
     *                       documented in each subclass.
     */
    function Horde_Image_Effect($params = array())
    {
        foreach ($params as $key => $val) {
            $this->_params[$key] = $val;
        }
    }

    function _setImageObject(&$image)
    {
        $this->_image = &$image;
    }

    function factory($type, $driver, $params)
    {
        if (is_array($type)) {
            list($app, $type) = $type;
        }

        // First check for a driver specific effect, if we can't find one,
        // assume there is a vanilla effect object around.
        $class = 'Horde_Image_Effect_' . $driver . '_' . $type;
        $vclass = 'Horde_Image_Effect_' . $type;
        if (!class_exists($class) && !class_exists($vclass)) {
            if (!empty($app)) {
                $path = $GLOBALS['registry']->get('fileroot', $app) . '/lib/Image/Effect/' . $driver . '/' . $type . '.php';
            } else {
                $path = 'Horde/Image/Effect/' . $driver . '/' . $type . '.php';
            }
            @include_once $path;
            if (!class_exists($class)) {
                 if (!empty($app)) {
                    $path = $GLOBALS['registry']->get('fileroot', $app) . '/lib/Image/Effect/' . $type . '.php';
                } else {
                    $path = 'Horde/Image/Effect/' . $type . '.php';
                }
                $class = $vclass;
                include_once $path;
            }
        }
        if (class_exists($class)) {
            $effect = new $class($params);
        } else {
            $effect = PEAR::raiseError(sprintf("Horde_Image_Effect %s for %s driver not found.", $type, $driver));
        }

        return $effect;
    }


}
