<?php
/**
 * The Horde_UI_Widget:: class provides base functionality for other Horde
 * UI elements.
 *
 * $Horde: framework/UI/UI/Widget.php,v 1.7.10.13 2009-01-06 15:23:45 jan Exp $
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
class Horde_UI_Widget {

    /**
     * Any variables that should be preserved in all of the widget's
     * links.
     *
     * @var array
     */
    var $_preserve = array();

    /**
     * The name of this widget.  This is used as the basename for variables
     * we access and manipulate.
     *
     * @var string
     */
    var $_name;

    /**
     * A reference to a Variables:: object this widget will use and
     * manipulate.
     *
     * @var Variables
     */
    var $_vars;

    /**
     * An array of name => value pairs which configure how this widget
     * behaves.
     *
     * @var array
     */
    var $_config;

    /**
     * Holds the name of a callback function to call on any URLS before they
     * are used/returned. If an array, it is taken as an object/method name, if
     * a string, it is taken as a php function.
     *
     * @var callable
     */
    var $_url_callback = array('Horde', 'applicationUrl');

    /**
     * Construct a new UI Widget interface.
     *
     * @param string $name      The name of the variable which will track this
     *                          UI widget's state.
     * @param Variables &$vars  A Variables:: object.
     * @param array $config     The widget's configuration.
     */
    function Horde_UI_Widget($name, &$vars, $config = array())
    {
        $this->_name = $name;
        $this->_vars = &$vars;

        if (array_key_exists('url_callback', $config)) {
            $this->_url_callback = $config['url_callback'];
            unset($config['url_callback']);
        }
        $this->_config = $config;
    }

    /**
     * Instructs Horde_UI_Widget to preserve a variable or a set of variables.
     *
     * @param string|array $var  The name of the variable to preserve, or
     *                           (since Horde 3.2) an array of variables to
     *                           preserve.
     * @param mixed $value       If preserving a single key, the value of the
     *                           variable to preserve.
     */
    function preserve($var, $value = null)
    {
        if (is_array($var)) {
            foreach ($var as $key => $value) {
                $this->_preserve[$key] = $value;
            }
        } else {
            $this->_preserve[$var] = $value;
        }
    }

    /**
     * @access private
     */
    function _addPreserved($link)
    {
        foreach ($this->_preserve as $varName => $varValue) {
            $link = Util::addParameter($link, $varName, $varValue);
        }
        return $link;
    }

    /**
     * Render the widget.
     *
     * @abstract
     *
     * @param mixed $data  The widget's state data.
     */
    function render()
    {}

    /**
     * @protected
     */
    function _link($link)
    {
        if (is_callable($this->_url_callback)) {
            return call_user_func($this->_url_callback, $link);
        }

        return $link;
    }

}
