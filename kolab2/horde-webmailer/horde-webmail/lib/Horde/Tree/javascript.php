<?php
/**
 * @package Horde_Tree
 */

/**
 * Load the Horde serializer for JSON output.
 */
require_once 'Horde/Serialize.php';

/**
 * The Horde_Tree_javascript:: class extends the Horde_Tree class to provide
 * javascript specific rendering functions.
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * $Horde: framework/Tree/Tree/javascript.php,v 1.34.2.13 2009-01-06 15:23:44 jan Exp $
 *
 * @author  Marko Djukic <marko@oblo.com>
 * @package Horde_Tree
 * @since   Horde 3.0
 */
class Horde_Tree_javascript extends Horde_Tree {

    /**
     * The name of the source for the tree data.
     *
     * @var string
     */
    var $_source_name = null;

    /**
     * The name of the target element to output the javascript tree.
     *
     * @var string
     */
    var $_options_name = null;

    /**
     * The name of the target element to output the javascript tree.
     *
     * @var string
     */
    var $_target_name = null;

    /**
     * Constructor
     */
    function Horde_Tree_javascript($tree_name, $params = array())
    {
        parent::Horde_Tree($tree_name, $params);

        /* Check for a javascript session state. */
        if ($this->_usesession &&
            isset($_COOKIE[$this->_instance . '_expanded'])) {
            /* Remove "exp" prefix from cookie value. */
            $nodes = explode(',', substr($_COOKIE[$this->_instance . '_expanded'], 3));

            /* Make sure there are no previous nodes stored in the
             * session. */
            $_SESSION['horde_tree'][$this->_instance]['expanded'] = array();

            /* Save nodes to the session. */
            foreach ($nodes as $id) {
                $_SESSION['horde_tree'][$this->_instance]['expanded'][$id] = true;
            }
        }

        /* Set variable names. */
        $this->_source_name = 'n_' . $this->_instance;
        $this->_header_name = 'h_' . $this->_instance;
        $this->_options_name = 'o_' . $this->_instance;
        $this->_target_name = 't_' . $this->_instance;

        Horde::addScriptFile('tree.js', 'horde');
    }

    /**
     * Returns the tree.
     *
     * @param boolean $static  If true the tree nodes can't be expanded and
     *                         collapsed and the tree gets rendered expanded.
     *
     * @return string  The HTML code of the rendered tree.
     */
    function getTree($static = false)
    {
        $this->_static = $static;
        $this->_buildIndents($this->_root_nodes);

        return '<div id="' . $this->_target_name . '"></div>' .
            '<script type="text/javascript">//<![CDATA[' . "\n" .
            $this->_getTreeSource() .
            $this->_getTreeInit() .
            "\n//]]></script>\n";
    }

    /**
     * Check the current environment to see if we can render the HTML
     * tree. We check for DOM support in the browser.
     *
     * @static
     *
     * @return boolean  Whether or not this Tree:: backend will function.
     */
    function isSupported()
    {
        require_once 'Horde/Browser.php';
        $browser = &Browser::singleton();
        return $browser->hasFeature('dom');
    }

    /**
     * Returns just the JS node definitions as a string.
     *
     * @return string  The Javascript node array definitions.
     */
    function renderNodeDefinitions()
    {
        $this->_buildIndents($this->_root_nodes);

        return
            $this->_source_name . ' = ' . Horde_Serialize::serialize($this->_nodes, SERIALIZE_JSON, NLS::getCharset()) . ";\n" .
            $this->_instance . '.renderTree(' .
            Horde_Serialize::serialize($this->_root_nodes, SERIALIZE_JSON, NLS::getCharset()) . ', false);';
    }

    /**
     * Outputs the data for the tree as a javascript array.
     *
     * @access private
     */
    function _getTreeSource()
    {
        return
            'var extraColsLeft = ' . $this->_extra_cols_left . ";\n" .
            'var extraColsRight = ' . $this->_extra_cols_right . ";\n" .
            'var ' . $this->_source_name . ' = ' . Horde_Serialize::serialize($this->_nodes, SERIALIZE_JSON, NLS::getCharset()) . ";\n" .
            'var ' . $this->_header_name . ' = ' . Horde_Serialize::serialize($this->_header, SERIALIZE_JSON, NLS::getCharset()) . ";\n" .
            'var ' . $this->_options_name . ' = ' . Horde_Serialize::serialize($this->_options, SERIALIZE_JSON, NLS::getCharset()) . ";\n";
    }

    /**
     * Outputs the javascript to initialise the tree.
     *
     * @access private
     */
    function _getTreeInit()
    {
        return
            sprintf('%1$s = new Horde_Tree(\'%1$s\');' . "\n" . '%1$s' . '.renderTree(',
                    $this->_instance) .
            Horde_Serialize::serialize($this->_root_nodes, SERIALIZE_JSON, NLS::getCharset()) . ', ' .
            ($this->_static ? 'true' : 'false') . ');';
    }

}
