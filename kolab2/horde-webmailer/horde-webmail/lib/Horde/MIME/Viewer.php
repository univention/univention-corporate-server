<?php
/**
 * The MIME_Viewer:: class provides an abstracted interface to
 * render out MIME types into HTML format.  It depends on a
 * set of MIME_Viewer_* drivers which handle the actual rendering,
 * and also a configuration file to map MIME types to drivers.
 *
 * $Horde: framework/MIME/MIME/Viewer.php,v 1.64.10.15 2009-01-06 15:23:20 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer {

    /**
     * The MIME_Part object to render.
     *
     * @var MIME_Part
     */
    var $mime_part;

    /**
     * Configuration parameters.
     *
     * @var array
     */
    var $_conf = array();

    /**
     * getDriver cache.
     *
     * @var array
     */
    var $_driverCache = array();

    /**
     * Force viewing of a part inline, regardless of the Content-Disposition
     * of the MIME Part.
     *
     * @var boolean
     */
    var $_forceinline = false;

    /**
     * Attempts to return a concrete MIME_Viewer_* object based on the
     * type of MIME_Part passed onto it.
     *
     * @param MIME_Part &$mime_part  Reference to a MIME_Part object with the
     *                               information to be rendered.
     * @param string $mime_type      Use this MIME type instead of the type
     *                               stored in the $mime_part.
     *
     * @return MIME_Viewer  The MIME_Viewer object, or false on error.
     */
    function &factory(&$mime_part, $mime_type = null)
    {
        $viewer = false;

        /* Check that we have a valid MIME_Part object */
        if (!is_a($mime_part, 'MIME_Part')) {
            return $viewer;
        }

        /* Determine driver type from the MIME type */
        if (empty($mime_type)) {
            $mime_type = $mime_part->getType();
            if (empty($mime_type)) {
                return $viewer;
            }
        }

        /* Spawn the relevant driver, and return it (or false on failure) */
        if (($ob = MIME_Viewer::includeDriver($mime_type))) {
            $class = (($ob->module == 'horde') ? '' : $ob->module . '_') . 'MIME_Viewer_' . $ob->driver;
            if (class_exists($class)) {
                $viewer = &new $class($mime_part, $GLOBALS['mime_drivers'][$ob->module][$ob->driver]);
            }
        }

        return $viewer;
    }

    /**
     * Include the code for the relevant driver.
     *
     * @param string $mime_type  The Content-type of the part to be rendered.
     *
     * @return stdClass  See MIME_Driver::getDriver().
     */
    function includeDriver($mime_type)
    {
        // TODO: BC - switch to require_once for Horde 4.0; don't need $config;
        //       don't need to make sure the 2 variables are unset.
        static $config = false;
        global $registry;

        $app = $registry->getApp();

        if (!$config) {
            $GLOBALS['mime_drivers'] = $GLOBALS['mime_drivers_map'] = array();
            $result = Horde::loadConfiguration('mime_drivers.php', array('mime_drivers', 'mime_drivers_map'), 'horde');
            if (!is_a($result, 'PEAR_Error')) {
                extract($result);
            }
            if ($app != 'horde') {
                $result = Horde::loadConfiguration('mime_drivers.php', array('mime_drivers', 'mime_drivers_map'), $app);
                if (!is_a($result, 'PEAR_Error')) {
                    require_once 'Horde/Array.php';
                    if (isset($result['mime_drivers'])) {
                        $mime_drivers = Horde_Array::array_merge_recursive_overwrite($mime_drivers, $result['mime_drivers']);
                    }
                    if (isset($result['mime_drivers_map'])) {
                        $mime_drivers_map = Horde_Array::array_merge_recursive_overwrite($mime_drivers_map, $result['mime_drivers_map']);
                    }
                }
            }
            $GLOBALS['mime_drivers'] = $mime_drivers;
            $GLOBALS['mime_drivers_map'] = $mime_drivers_map;
            $config = true;
        }

        /* Figure the correct driver for this MIME type. If there is no
           application-specific module, a general Horde one will attempt to
           be used. */
        if (($ob = MIME_Viewer::getDriver($mime_type, $app))) {
            /* Include the class. */
            require_once MIME_Viewer::resolveDriver($ob->driver, $ob->module);
        }

        return $ob;
    }

    /**
     * Constructor for MIME_Viewer
     *
     * @param MIME_Part &$mime_part  Reference to a MIME_Part object with the
     *                               information to be rendered.
     */
    function MIME_Viewer(&$mime_part, $conf = array())
    {
        $this->mime_part = &$mime_part;
        $this->_conf = $conf;
    }

    /**
     * Sets the MIME_Part object for the class.
     *
     * @param MIME_Part &$mime_part  Reference to a MIME_Part object with the
     *                               information to be rendered.
     */
    function setMIMEPart(&$mime_part)
    {
        $this->mime_part = &$mime_part;
    }

    /**
     * Return the MIME type of the rendered content.  This can be
     * overridden by the individual drivers, depending on what format
     * they output in. By default, it passes through the MIME type of
     * the object, or replaces custom extension types with
     * 'text/plain' to let the browser do a best-guess render.
     *
     * @return string  MIME-type of the output content.
     */
    function getType()
    {
        if ($this->mime_part->getPrimaryType() == 'x-extension') {
            return 'text/plain';
        } else {
            return $this->mime_part->getType(true);
        }
    }

    /**
     * Return the rendered version of the object.
     *
     * Should be overridden by individual drivers to perform custom tasks.
     * The $mime_part class variable has the information to render,
     * encapsulated in a MIME_Part object.
     *
     * @param mixed $params  Any optional parameters this driver needs at
     *                       runtime.
     *
     * @return string  Rendered version of the object.
     */
    function render($params = null)
    {
        return $this->mime_part->getContents();
    }

    /**
     * Return text/html output used as alternative output when the fully
     * rendered object cannot (or should not) be displayed.  For example,
     * this function should be used for MIME attachments that cannot be
     * viewed inline, where the user may be given options on how to view
     * the attachment.
     * Should be overridden by individual drivers to perform custom tasks.
     * The $mime_part class variable has the information to render,
     * encapsulated in a MIME_Part object.
     *
     * @param mixed $params  Any optional parameters this driver needs at
     *                       runtime.
     *
     * @return string  Text/html rendered information.
     */
    function renderAttachmentInfo()
    {
    }

    /**
     * Can this driver render the the data inline?
     *
     * @return boolean  True if the driver can display inline.
     */
    function canDisplayInline()
    {
        if ($this->getConfigParam('inline')) {
            return true;
        } else {
            return false;
        }
    }

    /**
     * Given a driver and an application, this returns the fully
     * qualified filesystem path to the driver source file.
     *
     * @param string $driver  Driver name.
     * @param string $app     Application name.
     *
     * @return string  Filesystem path of the driver/application queried.
     */
    function resolveDriver($driver = 'default', $app = 'horde')
    {
        if ($app == 'horde') {
            return dirname(__FILE__) . '/Viewer/' . $driver . '.php';
        } else {
            return $GLOBALS['registry']->applications[$app]['fileroot'] . '/lib/MIME/Viewer/' . $driver . '.php';
        }
    }

    /**
     * Given an input MIME type and a module name, this function
     * resolves it into a specific output driver which can handle it.
     *
     * @param string $mimeType  MIME type to resolve.
     * @param string $module    Module in which to search for the driver.
     *
     * @return stdClass  Object with the following items:
     * <pre>
     * 'driver'  --  Name of driver (e.g. 'enscript')
     * 'exact'   --  Was the driver and exact match? (true/false)
     * 'module'  --  The module containing driver (e.g. 'horde')
     * </pre>
     * Returns false if driver could not be found.
     */
    function getDriver($mimeType, $module = 'horde')
    {
        global $mime_drivers, $mime_drivers_map;

        $cacheName = $mimeType . '|' . $module;
        if (isset($this) && isset($this->_driverCache[$cacheName])) {
            return $this->_driverCache[$cacheName];
        }

        $driver = '';
        $exactDriver = false;

        list($primary_type, ) = explode('/', $mimeType, 2);
        $allSub = $primary_type . '/*';

        /* If the module doesn't exist in $mime_drivers_map, check for
           Horde viewers. */
        if (!isset($mime_drivers_map[$module]) && $module != 'horde') {
            return MIME_Viewer::getDriver($mimeType, 'horde');
        }

        $dr = &$mime_drivers[$module];
        $map = &$mime_drivers_map[$module];

        /* If an override exists for this MIME type, then use that */
        if (isset($map['overrides'][$mimeType])) {
            $driver = $map['overrides'][$mimeType];
            $exactDriver = true;
        } elseif (isset($map['overrides'][$allSub])) {
            $driver = $map['overrides'][$allSub];
            $exactDriver = true;
        } elseif (isset($map['registered'])) {
            /* Iterate through the list of registered drivers, and see if
               this MIME type exists in the MIME types that they claim to
               handle. If the driver handles it, then assign it as the
               rendering driver. If we find a generic handler, keep iterating
               to see if we can find a specific handler. */
            foreach ($map['registered'] as $val) {
                if (in_array($mimeType, $dr[$val]['handles'])) {
                    $driver = $val;
                    $exactDriver = true;
                    break;
                } elseif (in_array($allSub, $dr[$val]['handles'])) {
                    $driver = $val;
                }
            }
        }

        /* If this is an application specific module, and an exact match was
           not found, search for a Horde-wide specific driver. Only use the
           Horde-specific driver if it is NOT the 'default' driver AND the
           Horde driver is an exact match. */
        if (!$exactDriver && $module != 'horde') {
            $ob = MIME_Viewer::getDriver($mimeType, 'horde');
            if (empty($driver) ||
                (($ob->driver != 'default') && $ob->exact)) {
                $driver = $ob->driver;
                $module = 'horde';
            }
        }

        /* If the 'default' driver exists in this module, fall back to that. */
        if (empty($driver) &&
            @is_file(MIME_Viewer::resolveDriver('default', $module))) {
            $driver = 'default';
        }

        if (empty($driver)) {
            $this->_driverCache[$cacheName] = false;
            return false;
        } else {
            $ob = new stdClass;
            $ob->driver = $driver;
            $ob->exact  = $exactDriver;
            $ob->module = $module;
            if (isset($this)) {
                $this->_driverCache[$cacheName] = $ob;
            }
            return $ob;
        }
    }

    /**
     * Given a MIME type, this function will return an appropriate
     * icon.
     *
     * @param string $mimeType  The MIME type that we need an icon for.
     *
     * @return string  The URL to the appropriate icon.
     */
    function getIcon($mimeType)
    {
        $app = $GLOBALS['registry']->getApp();
        $ob = MIME_Viewer::_getIcon($mimeType, $app);

        if ($ob === null) {
            if ($app != 'horde') {
                $obHorde = MIME_Viewer::_getIcon($mimeType, 'horde');
                return ($obHorde === null) ? null : $obHorde->url;
            } else {
                return null;
            }
        } elseif (($ob->match !== 0) && ($app != 'horde')) {
            $obHorde = MIME_Viewer::_getIcon($mimeType, 'horde');
            if ($ob->match !== null && $ob->match <= $obHorde->match) {
                return $ob->url;
            } else {
                return $obHorde->url;
            }
        } else {
            return $ob->url;
        }
    }

    /**
     * Given an input MIME type and module, this function returns the
     * URL of an icon that can be associated with it
     *
     * @access private
     *
     * @param string $mimeType  MIME type to get the icon for.
     *
     * @return stdClass  url:   URL to an icon, or null if none
     *                          could be found.
     *                   exact: How exact the match is.
     *                          0 => 'exact', 1 => 'primary',
     *                          2 => 'driver', 3 => 'default'
     *                          or null.
     */
    function _getIcon($mimeType, $module = 'horde')
    {
        global $mime_drivers;

        $ob = MIME_Viewer::getDriver($mimeType, $module);
        if (!is_object($ob)) {
            return array(false, null);
        }
        $driver = $ob->driver;

        list($primary_type,) = explode('/', $mimeType, 2);
        $allSub = $primary_type . '/*';
        $retOb = &new stdClass();
        $retOb->match = null;
        $retOb->url = null;

        /* If the module doesn't exist in $mime_drivers, return now. */
        if (!isset($mime_drivers[$module])) {
            return null;
        }
        $dr = &$mime_drivers[$module];

        /* If a specific icon for this driver and mimetype is defined,
           then use that. */
        if (isset($dr[$driver]['icons'])) {
            $icondr = &$mime_drivers[$module][$driver]['icons'];
            $iconList = array($mimeType => 0, $allSub => 1, 'default' => 2);
            foreach ($iconList as $key => $val) {
                if (isset($icondr[$key])) {
                    $retOb->url = $icondr[$key];
                    $retOb->match = $val;
                    break;
                }
            }
        }

        /* Try to use a default icon if none already obtained. */
        if (is_null($retOb->url) && isset($dr['default'])) {
            $dr = &$mime_drivers[$module]['default'];
            if (isset($dr['icons']['default'])) {
                $retOb->url = $dr['default']['icons']['default'];
                $retOb->match = 3;
            }
        }

        if (!is_null($retOb->url)) {
            $retOb->url = $GLOBALS['registry']->getImageDir($module) . '/mime/' . $retOb->url;
        }

        return $retOb;
    }

    /**
     * Returns the character set used for the Viewer.
     * Should be overridden by individual drivers to perform custom tasks.
     *
     * @return string  The character set used by this Viewer.
     */
    function getCharset()
    {
        return $this->mime_part->getCharset();
    }

    /**
     * Return a configuration parameter for the current viewer.
     *
     * @param string $param  The parameter name.
     *
     * @return mixed  The value of the parameter; returns null if the parameter
     *                doesn't exist.
     */
    function getConfigParam($param)
    {
        return (isset($this->_conf[$param])) ? $this->_conf[$param] : null;
    }

    /**
     * Should we force viewing of this MIME Part inline, regardless of the
     * Content-Disposition of the MIME Part?
     *
     * @return boolean  Force viewing inline?
     */
    function forceInlineView()
    {
        return $this->_forceinline;
    }

}
