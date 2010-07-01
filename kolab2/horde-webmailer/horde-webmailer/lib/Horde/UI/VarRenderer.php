<?php

include_once 'Horde/NLS.php';

/**
 * The Horde_UI_VarRenderer:: class provides base functionality for
 * other Horde UI elements.
 *
 * $Horde: framework/UI/UI/VarRenderer.php,v 1.12.10.14 2009-01-06 15:23:45 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jason M. Felice <jason.m.felice@gmail.com>
 * @since   Horde_UI 0.0.1
 * @package Horde_UI
 */
class Horde_UI_VarRenderer {

    /**
     * Parameters which change this renderer's behavior.
     *
     * @var array
     */
    var $_params;

    /**
     * Charset to use for output.
     *
     * @var string
     */
    var $_charset;

    /**
     * Constructs a new renderer.
     *
     * @param array $params  The name of the variable which will track this UI
     *                       widget's state.
     */
    function Horde_UI_VarRenderer($params = array())
    {
        $this->_params = $params;
        $this->_charset = NLS::getCharset();
    }

    /**
     * Constructs a new Horde_UI_VarRenderer:: instance.
     *
     * @param mixed $driver  This is the renderer subclass we will instantiate.
     *                       If an array is passed, the first element is the
     *                       library path and the second element is the driver
     *                       name.
     * @param array $params  Parameters specific to the subclass.
     *
     * @return Horde_UI_VarRenderer  A Horde_UI_VarRenderer:: subclass
     *                               instance.
     */
    function &factory($driver, $params = array())
    {
        if (is_array($driver)) {
            $app = $driver[0];
            $driver = $driver[1];
        }

        $driver = basename($driver);
        $class = 'Horde_UI_VarRenderer_' . $driver;
        if (!class_exists($class)) {
            if (!empty($app)) {
                include $GLOBALS['registry']->get('fileroot', $app) . '/lib/UI/VarRenderer/' . $driver . '.php';
            } else {
                include 'Horde/UI/VarRenderer/' . $driver . '.php';
            }
        }

        if (class_exists($class)) {
            $vr = new $class($params);
        } else {
            $vr = PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }

        return $vr;
    }

    /**
     * Renders a variable.
     *
     * @param Horde_Form $form            A Horde_Form instance,
     *                                    or null if none is available.
     * @param Horde_Form_Variable &$var   Reference to a Horde_Form_Variable.
     * @param Variables &$vars            A Variables instance.
     * @param boolean $isInput            Whether this is an input field.
     */
    function render($form, &$var, &$vars, $isInput = false)
    {
        if ($isInput) {
            $state = 'Input';
        } else {
            $state = 'Display';
        }
        $method = "_renderVar${state}_" . $var->type->getTypeName();
        if (!method_exists($this, $method)) {
            $method = "_renderVar${state}Default";
        }
        return $this->$method($form, $var, $vars);
    }

    /**
     * Finishes rendering after all fields are output.
     */
    function renderEnd()
    {
        return '';
    }

}
