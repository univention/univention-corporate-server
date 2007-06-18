<?php
/**
 * The Horde_UI_Widget:: class provides base functionality for other Horde
 * UI elements.
 *
 * $Horde: framework/UI/UI/Widget.php,v 1.6 2004/02/25 19:12:35 eraserhd Exp $
 *
 * Copyright 2003-2004 Jason M. Felice <jfelice@cronosys.com>
 *
 * See the enclosed file LICENSE for license information (LGPL).
 *
 * @version $Revision: 1.1.2.1 $
 * @since   Horde_UI 0.0.1
 * @package Horde_UI
 */
class Horde_UI_Widget {

    /**
     * Any variables that should be preserved in all of the widget's
     * links.
     * @var array $_preserve
     */
    var $_preserve = array();

    /**
     * The name of this widget.  This is used as the basename for variables
     * we access and manipulate.
     * @var string $_name
     */
    var $_name;

    /**
     * A reference to a Variables:: object this widget will use and
     * manipulate.
     * @var object Variables $_vars
     */
    var $_vars;

    /**
     * An array of name => value pairs which configure how this widget
     * behaves.
     */
    var $_config;

    /**
     * Construct a new UI Widget interface.
     *
     * @access public
     *
     * @param string $name                   The name of the variable which
     *                                       will track this UI widget's state.
     * @param object Variables &$vars  A Variables:: object.
     * @param optional array $config         The widget's configuration.
     */
    function Horde_UI_Widget($name, &$vars, $config = array())
    {
        $this->_name = $name;
        $this->_vars = &$vars;
        $this->_config = $config;
    }

    /**
     * Instruct Horde_UI_Widget:: to preserve a variable.
     *
     * @access public
     *
     * @param string $var    The name of the variable to preserve.
     * @param mixed  $value  The value of the variable to preserve.
     */
    function preserve($var, $value)
    {
        $this->_preserve[$var] = $value;
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
     * @param optional mixed $data  The widget's state data.
     */
    function render() {}

}
