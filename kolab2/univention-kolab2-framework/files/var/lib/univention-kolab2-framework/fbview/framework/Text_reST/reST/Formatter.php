<?php
/**
 * The Text_reST_Formatter:: class is the framework for rendering
 * reStructuredText documents to different media (e.g. HTML).
 *
 * $Horde: framework/Text_reST/reST/Formatter.php,v 1.4 2004/01/01 15:14:35 jan Exp $
 *
 * Copyright 2003-2004 Jason M. Felice <jfelice@cronosys.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you did not
 * receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jason M. Felice <jfelice@cronosys.com>
 * @version $Revision: 1.1.2.1 $
 * @package Text_reST
 */
class Text_reST_Formatter {

    /**
     * Array of driver-specific parameters for formatting.
     *
     * @var array $_args
     */
    var $_args;

    /**
    * Construct a new formatter.
    *
    * @access protected
    *
    * @param optional array $args       Arguments specific to this formatter.
    */
    function Text_reST_Formatter($args = array())
    {
        $this->_args = $args;
    }

    /**
     * Construct a new formatter.
     *
     * @access public
     *
     * @param string $driver            This is the name of the formatting
     *                                  driver to construct.
     * @param optional array $args      This is an array of driver-specific
     *                                  parameters.
     * @return object Text_reST_Formatter the formatter
     */
    function &factory($driver, $args = array())
    {
        if (is_array($driver)) {
            list($path, $driver) = $driver;
        } else {
            $path = dirname(__FILE__) . '/Formatter/';
        }
        $class = 'Text_reST_Formatter_' . $driver;
        require_once $path . $driver . '.php';
        return new $class($args);
    }

    /**
     * Render the document.
     *
     * @abstract
     *
     * @param object Text_reST $document  This is the document
     *                                    we will render.
     * @param string $charset             (optional) The output charset.
     */
    function format(&$document, $charset = null)
    {
    }

}
