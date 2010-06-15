<?php
/**
 * Horde_Mobile_Renderer:: framework for mobile device markup
 * renderers.
 *
 * $Horde: framework/Mobile/Mobile/Renderer.php,v 1.14 2004/01/01 15:16:07 jan Exp $
 *
 * Copyright 2002-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Mobile
 */
class Horde_Mobile_Renderer extends Horde_Mobile {

    var $_browser;

    function Horde_Mobile_Renderer($browser = null)
    {
        if (is_null($browser)) {
            $this->_browser = &new Browser();
        } else {
            $this->_browser = $browser;
        }
    }

    function isBrowser($agent)
    {
        return $this->_browser->isBrowser($agent);
    }

    function hasQuirk($quirk)
    {
        return $this->_browser->hasQuirk($quirk);
    }

    /**
     * Render any Horde_Mobile_element object. Looks for the
     * appropriate rendering function in the renderer; if there isn't
     * one, we ignore this element.
     *
     * @param object Horde_Mobile_element $element  The element to render.
     */
    function renderElement(&$element)
    {
        $func = '_render' . ucfirst(str_replace('horde_mobile_', '', get_class($element)));
        if (method_exists($this, $func)) {
            $this->$func($element);
        }
    }

    function _renderBlock(&$block)
    {
        if (count($block->_elements)) {
            echo '<p>';
            foreach ($block->_elements as $blockElement) {
                $this->renderElement($blockElement);
            }
            echo "</p>\n";
        }
    }

    function _renderForm(&$form)
    {
        foreach ($form->_elements as $formElement) {
            $this->renderElement($formElement);
        }
    }

    function _renderTable(&$table)
    {
        foreach ($table->_rows as $row) {
            $this->_renderRow($row);
        }
    }

    function _renderRow(&$row)
    {
        echo '<tr>';
        foreach ($row->_columns as $column) {
            echo '<td>';
            // Call create function for each cellelement that is a
            // Horde_Mobile object.
            if (!is_null($column)) {
                $this->renderElement($column);
            }
            echo '</td>';
        }
        echo "</tr>\n";
    }

    /**
     * Attempts to return a concrete Horde_Mobile_Renderer instance
     * based on $type.
     *
     * @access public
     *
     * @param string $type             The kind of markup (html, hdml, wml)
     *                                 we want to generate.
     * @param optional object Browser  The Browser object to use.
     * @param optional array $params   A hash containing any
     *                                 options for the renderer.
     *
     * @return object Horde_Mobile_Renderer   The newly created concrete
     *                                        Horde_Mobile_Renderer instance, or
     *                                        a PEAR_Error object on an error.
     */
    function &factory($type, $browser = null, $params = array())
    {
        $type = basename($type);

        if (@file_exists(dirname(__FILE__) . '/Renderer/' . $type . '.php')) {
            include_once dirname(__FILE__) . '/Renderer/' . $type . '.php';
        } else {
            @include_once 'Horde/Mobile/Renderer/' . $type . '.php';
        }
        $class = 'Horde_Mobile_Renderer_' . $type;
        if (class_exists($class)) {
            return $ret = &new $class($browser, $params);
        } else {
            return PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }
    }

    /**
     * Attempts to return a concrete Horde_Mobile_Renderer instance
     * based on $type. It will only create a new instance if no
     * renderer with the same parameters currently exists.
     *
     * @access public
     *
     * @param string $type             The kind of markup (html, hdml, wml)
     *                                 we want to generate.
     * @param optional object Browser  The Browser object to use.
     * @param optional array $params   A hash containing any
     *                                 options for the renderer.
     *
     * @return object Horde_Mobile_Renderer   The newly created concrete
     *                                        Horde_Mobile_Renderer instance, or
     *                                        a PEAR_Error object on an error.
     */
    function &singleton($type, $browser = null, $params = array())
    {
        static $instances;

        if (!isset($instances)) {
            $instances = array();
        }

        $signature = serialize(array($type, $browser, $params));
        if (!array_key_exists($signature, $instances)) {
            $instances[$signature] = &Horde_Mobile_Renderer::factory($type, $browser, $params);
        }

        return $instances[$signature];
    }

}
