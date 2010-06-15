<?php
/**
 * The Horde_UI_VarRenderer:: class provides base functionality for
 * other Horde UI elements.
 *
 * $Horde: framework/UI/UI/VarRenderer.php,v 1.10 2004/03/20 22:13:14 eraserhd Exp $
 *
 * Copyright 2003-2004 Jason M. Felice <jfelice@cronosys.com>
 *
 * See the enclosed file LICENSE for license information (LGPL).
 *
 * @version $Revision: 1.1.2.1 $
 * @since   Horde_UI 0.0.1
 * @package Horde_UI
 */
class Horde_UI_VarRenderer {

    /**
     * Parameters which change this renderer's behavior.
     * @var array $_params
     */
    var $_params;

    /**
     * Construct a new renderer.
     *
     * @access public
     *
     * @param array $params    The name of the variable which will track this
     *                         UI widget's state.
     */
    function Horde_UI_VarRenderer($params = array())
    {
        $this->_params = $params;
    }

    /**
     * Construct a new Horde_UI_VarRenderer:: instance.
     *
     * @param mixed $driver             This is the renderer subclass we
     *                                  will instantiate.  If an array is
     *                                  passed, the first element is the
     *                                  library path and the second element
     *                                  is the driver name.
     * @param optional array $params    parameters specific to the subclass
     * @return object a Horde_UI_VarRenderer:: subclass instance.
     */
    function &factory($driver, $params = array())
    {
        if (is_array($driver)) {
            $app = $driver[0];
            $driver = $driver[1];
        }

        $driver = basename($driver);

        if (!empty($app)) {
            require_once $GLOBALS['registry']->getParam('fileroot', $app) . '/lib/UI/VarRenderer/' . $driver . '.php';
        } elseif (@file_exists(dirname(__FILE__) . '/VarRenderer/' . $driver . '.php')) {
            require_once dirname(__FILE__) . '/VarRenderer/' . $driver . '.php';
        } else {
            @include_once 'Horde/UI/VarRenderer/' . $driver . '.php';
        }

        $class = 'Horde_UI_VarRenderer_' . $driver;
        if (class_exists($class)) {
            return $ret = &new $class($params);
        } else {
            return PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }
    }

    /**
     * Return a Horde_UI_VarRenderer:: instance, constructing one with
     * the specified parameters if necessary.
     *
     * @param string $driver            This is the renderer subclass we
     *                                  will instantiate.
     * @param optional array $params    parameters specific to the subclass
     * @return object a Horde_UI_VarRenderer:: subclass instance.
     */
    function &singleton($driver, $params = array())
    {
        static $cache;

        if (is_null($driver)) {
            $class = 'Horde_UI_VarRenderer';
        }
        $key = serialize(array ($driver, $params));
        if (!isset($cache[$key])) {
            $cache[$key] = &Horde_UI_VarRenderer::factory($driver, $params);
        }
        return $cache[$key];
    }

    /**
     * Render a variable.
     *
     * @param object &$form             Reference to a Horde_Form:: instance,
     *                                  or null if none is available.
     * @param object &$var              Reference to a Horde_Form_Var::
     * @param object &$vars             A Variables::
     * @param bool $isInput             Whether this is an input field.
     */
    function render(&$form, &$var, &$vars, $isInput = false)
    {
        if ($isInput) {
            $state = 'Input';
        } else {
            $state = 'Display';
        }
        $method = "_renderVar${state}_" . $var->type->getTypeName();
        if (!@method_exists($this, $method)) {
            $method = "_renderVar${state}Default";
        }
        return $this->$method($form, $var, $vars);
    }

    /**
     * Finish rendering after all fields are output.
     */
    function renderEnd()
    {
        return "";
    }

}
