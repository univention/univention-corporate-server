<?php
/**
 * The Horde_Tree_javascript:: class extends the Horde_Tree class to provide
 * javascript specific rendering functions.
 *
 * Copyright 2003-2004 Marko Djukic <marko@oblo.com>
 *
 * See the enclosed file COPYING for license information (GPL). If you did not
 * receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * $Horde: framework/Tree/Tree/javascript.php,v 1.17 2004/04/07 14:43:14 chuck Exp $
 *
 * @author  Marko Djukic <marko@oblo.com>
 * @version $Revision: 1.1.2.1 $
 * @package Horde_Tree
 * @since   Horde 3.0
 */
class Horde_Tree_javascript extends Horde_Tree {

    /**
     * The name of the source for the tree data.
     *
     * @var string $_source_name
     */
    var $_source_name = null;

    /**
     * The name of the target element to output the javascript tree.
     *
     * @var string $_options_name
     */
    var $_options_name = null;

    /**
     * The name of the target element to output the javascript tree.
     *
     * @var string $_target_name
     */
    var $_target_name = null;

    /**
     * Constructor
     *
     * @access public
     */
    function Horde_Tree_javascript($tree_name, $params = array())
    {
        parent::Horde_Tree($tree_name, $params);

        /* Check for a javascript session state. */
        if ($this->_usesession &&
            isset($_COOKIE[$this->_instance . '_expanded'])) {
            $nodes = explode(',', $_COOKIE[$this->_instance . '_expanded']);

            /* Make sure there are no previous nodes stored in the
               session. */
            $_SESSION['horde_tree'][$this->_instance]['expanded'] = array();

            /* Save nodes to the session. */
            foreach ($nodes as $id) {
                $_SESSION['horde_tree'][$this->_instance]['expanded'][$id] = true;
            }
        }
    }
    
    /**
     * Render the tree.
     *
     * @access public
     */
    function renderTree()
    {
        $this->_source_name = 'n_' . $this->_instance;
        $this->_options_name = 'o_' . $this->_instance;
        $this->_target_name = 't_' . $this->_instance;

        Horde::addScriptFile('tree.js', 'horde');
        echo $this->_getTreeSource();
        echo '<div id="' . $this->_target_name . '"></div>';
        echo $this->_getTreeInit();
    }

    /**
     * Outputs the data for the tree as a javascript array.
     *
     * @access private
     */
    function _getTreeSource()
    {
        $js  = '<script language="JavaScript" type="text/javascript">' . "\n";
        $js .= 'var extraColsLeft = ' . $this->_extra_cols_left . ";\n";
        $js .= 'var extraColsRight = ' . $this->_extra_cols_right . ";\n";
        $js .= 'var ' . $this->_source_name . ' = new Array();' . "\n";

        foreach ($this->_nodes as $node_id => $node) {
            $js .= $this->_getJsArrayElement(sprintf('%s[\'%s\']', $this->_source_name, $node_id), $node);
        }
        $js .= $this->_getJsArrayElement($this->_options_name, $this->_options);
        $js .= '</script>' . "\n";

        return $js;
    }

    /**
     * Outputs the javascript to initialise the tree.
     *
     * @access private
     */
    function _getTreeInit()
    {
        $instance = $this->_instance;
        $js  = '<script language="JavaScript" type="text/javascript">' . "\n";
        $js .= sprintf('%1$s = new Horde_Tree(\'%1$s\');' . "\n",
                        $instance);

        $table_params = sprintf('%s%s%s%s%s',
                                $this->getOption('border', true, 0),
                                $this->getOption('width', true),
                                $this->getOption('class', true),
                                $this->getOption('cellpadding', true, 0),
                                $this->getOption('cellspacing', true, 0));
        $js .= sprintf("%s.setTableStart('%s');\n",
                       $instance,
                       $table_params);

        $js .= sprintf("%s.renderTree('%s');\n</script>\n",
                       $instance,
                       $this->_root_node_id);

        return $js;
    }

    function _getJsArrayElement($js_var, $value)
    {
        if (is_array($value)) {
            $js = $js_var . ' = new Array();' . "\n";
            foreach ($value as $key => $val) {
                if (is_numeric($key)) {
                    $new_js_var = $js_var . '[' . $key . ']';
                } else {
                    $new_js_var = $js_var . '[\'' . $key . '\']';
                }
                $js .= $this->_getJsArrayElement($new_js_var, $val);
            }
            return $js;
        } else {
            require_once 'Horde/Browser.php';
            $browser = &Browser::singleton();
            return $js_var . " = '" . $browser->escapeJSCode(addslashes($value)) . "';\n";
        }
    }

}
