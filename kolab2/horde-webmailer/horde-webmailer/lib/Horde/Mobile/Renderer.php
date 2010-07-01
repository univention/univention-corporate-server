<?php
/**
 * Horde_Mobile_Renderer:: framework for mobile device markup
 * renderers.
 *
 * $Horde: framework/Mobile/Mobile/Renderer.php,v 1.15.10.13 2009-01-06 15:23:25 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 3.0
 * @package Horde_Mobile
 */
class Horde_Mobile_Renderer extends Horde_Mobile {

    var $_browser;

    function Horde_Mobile_Renderer($browser = null)
    {
        if (is_null($browser)) {
            $this->_browser = new Browser();
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
     * @param Horde_Mobile_element $element  The element to render.
     */
    function renderElement(&$element)
    {
        $func = '_render' . ucfirst(str_replace('horde_mobile_', '', strtolower(get_class($element))));
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

    function _renderDl(&$dl)
    {
        foreach ($dl->_dts as $dt) {
            $this->_renderDt($dt);
        }
    }

    function _renderDt(&$dt)
    {
        $i = 0;
        foreach ($dt->_dds as $dd) {
            echo $out = ($i == 0) ? '<dt>' : '<dd>';

            // Call create function for each ddelement that is a
            // Horde_Mobile object.
            if (!is_null($dd)) {
                $this->renderElement($dd);
            }

            echo $out = ($i++ == 0) ? '</dt>' : '</dd>';
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
     * @param string $type      The kind of markup (html, hdml, wml) we want to
     *                          generate.
     * @param Browser $browser  The Browser object to use.
     * @param array $params     A hash containing any options for the renderer.
     *
     * @return Horde_Mobile_Renderer  The newly created concrete
     *                                Horde_Mobile_Renderer instance, or a
     *                                PEAR_Error object on an error.
     */
    function &factory($type, $browser = null, $params = array())
    {
        $type = basename($type);
        $class = 'Horde_Mobile_Renderer_' . $type;
        if (!class_exists($class)) {
            include_once 'Horde/Mobile/Renderer/' . $type . '.php';
        }

        if (class_exists($class)) {
            $renderer = new $class($browser, $params);
        } else {
            $renderer = PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }

        return $renderer;
    }

    /**
     * Attempts to return a concrete Horde_Mobile_Renderer instance
     * based on $type. It will only create a new instance if no
     * renderer with the same parameters currently exists.
     *
     * @param string $type      The kind of markup (html, hdml, wml) we want to
     *                          generate.
     * @param Browser $browser  The Browser object to use.
     * @param array $params     A hash containing any options for the renderer.
     *
     * @return Horde_Mobile_Renderer  The newly created concrete
     *                                Horde_Mobile_Renderer instance, or a
     *                                PEAR_Error object on an error.
     */
    function &singleton($type, $browser = null, $params = array())
    {
        static $instances = array();

        $signature = md5(serialize(array($type, $browser, $params)));
        if (!isset($instances[$signature])) {
            $instances[$signature] = &Horde_Mobile_Renderer::factory($type, $browser, $params);
        }

        return $instances[$signature];
    }

}
