<?php
/**
 * The Horde_Tree_select:: class extends the Horde_Tree class to provide
 * <option> tag rendering.
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * $Horde: framework/Tree/Tree/select.php,v 1.2.2.11 2009-01-06 15:23:44 jan Exp $
 *
 * @author  Ben Chavet <ben@horde.org>
 * @package Horde_Tree
 * @since   Horde 3.1
 */
class Horde_Tree_select extends Horde_Tree {

    /**
     * TODO
     *
     * @var array
     */
    var $_nodes = array();

    /**
     * Constructor.
     */
    function Horde_Tree_select($tree_name, $params)
    {
        parent::Horde_Tree($tree_name, $params);
        $this->_static = true;
    }

    /**
     * Returns the tree.
     *
     * @return string  The HTML code of the rendered tree.
     */
    function getTree()
    {
        $this->_buildIndents($this->_root_nodes);

        $tree = '';
        foreach ($this->_root_nodes as $node_id) {
            $tree .= $this->_buildTree($node_id);
        }
        return $tree;
    }

    /**
     * Checks the current environment to see if we can render the HTML tree.
     * HTML is always renderable, at least until we add a php-gtk tree
     * backend, in which case this implementation will actually need a body.
     *
     * @static
     *
     * @return boolean  Whether or not this Tree:: backend will function.
     */
    function isSupported()
    {
        return true;
    }

    /**
     * Returns just the JS node definitions as a string. This is a no-op for
     * the select renderer.
     */
    function renderNodeDefinitions()
    {
    }

    /**
     * Adds additional parameters to a node.
     *
     * @param string $id     The unique node id.
     * @param array $params  Any other parameters to set.
     * <pre>
     * selected --  Whether this node is selected
     * </pre>
     */
    function addNodeParams($id, $params = array())
    {
        if (!is_array($params)) {
            $params = array($params);
        }

        $allowed = array('selected');

        foreach ($params as $param_id => $param_val) {
            /* Set only allowed and non-null params. */
            if (in_array($param_id, $allowed) && !is_null($param_val)) {
                $this->_nodes[$id][$param_id] = $param_val;
            }
        }
    }

    /**
     * Recursive function to walk through the tree array and build the output.
     *
     * @access private
     *
     * @param string $node_id  The Node ID.
     *
     * @return string  The tree rendering.
     */
    function _buildTree($node_id)
    {
        $selected = $this->_nodes[$node_id]['selected'] ? ' selected="selected"' : '';

        $output = '<option value="' . htmlspecialchars($node_id) . '"' . $selected . '>' .
            str_repeat('&nbsp;&nbsp;', (int)$this->_nodes[$node_id]['indent']) . htmlspecialchars($this->_nodes[$node_id]['label']) .
            '</option>';

        if (isset($this->_nodes[$node_id]['children']) &&
            $this->_nodes[$node_id]['expanded']) {
            $num_subnodes = count($this->_nodes[$node_id]['children']);
            for ($c = 0; $c < $num_subnodes; $c++) {
                $child_node_id = $this->_nodes[$node_id]['children'][$c];
                $output .= $this->_buildTree($child_node_id);
            }
        }

        return $output;
    }

}
