<?php
/**
 * The Horde_Editor:: package provides an API to generate the code necessary
 * for embedding javascript RTE editors in a web page.
 *
 * $Horde: framework/Editor/Editor.php,v 1.8.10.14 2009-01-06 15:23:03 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Nuno Loureiro <nuno@co.sapo.pt>
 * @since   Horde 3.0
 * @package Horde_Editor
 */
class Horde_Editor {

    /**
     * Javascript code to init the editor.
     *
     * @var string
     */
    var $_js = '';

    /**
     * Attempts to return a concrete Horde_Editor instance based on $driver.
     *
     * @param mixed $driver  The type of concrete Horde_Editor subclass to
     *                       return. If $driver is an array, then we will look
     *                       in $driver[0]/lib/Driver/ for the subclass
     *                       implementation named $driver[1].php.
     * @param array $params  A hash containing any additional configuration or
     *                       connection parameters a subclass might need.
     *
     * @return Horde_Editor  The newly created concrete Horde_Editor instance,
     *                       or false on error.
     */
    function &factory($driver, $params = null)
    {
        if (is_array($driver)) {
            $app = $driver[0];
            $driver = $driver[1];
        }

        $driver = basename($driver);
        if (empty($driver) || ($driver == 'none')) {
            $editor = new Horde_Editor($params);
            return $editor;
        }

        /* Transparent backwards compatible upgrade to Xinha,
         * htmlarea's replacement. */
        if ($driver == 'htmlarea') {
            $driver = 'xinha';
        }

        $class = 'Horde_Editor_' . $driver;
        if (!class_exists($class)) {
            if (!empty($app)) {
                include_once $GLOBALS['registry']->get('fileroot', $app) . '/lib/Editor/' . $driver . '.php';
            } else {
                include_once 'Horde/Editor/' . $driver . '.php';
            }
        }

        if (class_exists($class)) {
            if (is_null($params) && class_exists('Horde')) {
                $params = Horde::getDriverConfig('editor', $driver);
            }
            $editor = new $class($params);
        } else {
            $editor = PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }

        return $editor;
    }

    /**
     * Attempts to return a reference to a concrete Horde_Editor
     * instance based on $driver. It will only create a new instance
     * if no Horde_Editor instance with the same parameters currently
     * exists.
     *
     * This should be used if multiple cache backends (and, thus,
     * multiple Horde_Editor instances) are required.
     *
     * This method must be invoked as:
     *   $var = &Horde_Editor::singleton()
     *
     * @param mixed $driver  The type of concrete Horde_Editor subclass to
     *                       return. If $driver is an array, then we will look
     *                       in $driver[0]/lib/Editor/ for the subclass
     *                       implementation named $driver[1].php.
     * @param array $params  A hash containing any additional configuration or
     *                       connection parameters a subclass might need.
     *
     * @return Horde_Editor  The concrete Horde_Editor reference, or false on
     *                       error.
     */
    function &singleton($driver, $params = null)
    {
        static $instances = array();

        if (is_null($params) && class_exists('Horde')) {
            $params = Horde::getDriverConfig('cache', $driver);
        }

        $signature = serialize(array($driver, $params));
        if (!array_key_exists($signature, $instances)) {
            $instances[$signature] = &Horde_Editor::factory($driver, $params);
        }

        return $instances[$signature];
    }

    /**
     * Returns the JS code needed to instantiate the editor.
     *
     * @since Horde 3.2
     *
     * @return string  Javascript code.
     */
    function getJS()
    {
        return $this->_js;
    }

    /**
     * List the available editors.
     * Can be called statically: Horde_Editor::availableEditors();
     *
     * @since Horde 3.2
     *
     * @return array  List of available editors.
     */
    function availableEditors()
    {
        $eds = array();
        $d = dir(dirname(__FILE__) . '/Editor');
        while (false !== ($entry = $d->read())) {
            if (preg_match('/\.php$/', $entry)) {
                $eds[] = basename($entry, '.php');
            }
        }

        return $eds;
    }

}
