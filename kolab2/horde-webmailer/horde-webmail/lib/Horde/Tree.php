<?php

/**
 * Display extra columns to the left of the main tree.
 */
define('HORDE_TREE_EXTRA_LEFT', 0);

/**
 * Display extra columns to the right of the main tree.
 */
define('HORDE_TREE_EXTRA_RIGHT', 1);

/**
 * The preceding text, before the Horde_Tree instance name, used for
 * collapse/expand submissions.
 */
define('HORDE_TREE_TOGGLE', 'ht_toggle_');

/**
 * The Horde_Tree:: class provides a tree view of hierarchical information. It
 * allows for expanding/collapsing of branches and maintains their state. It
 * can work together with the Horde_Tree javascript class to achieve this in
 * DHTML on supported browsers.
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * $Horde: framework/Tree/Tree.php,v 1.46.6.18 2009-01-06 15:23:44 jan Exp $
 *
 * @author  Marko Djukic <marko@oblo.com>
 * @package Horde_Tree
 * @since   Horde 3.0
 */
class Horde_Tree {

    /**
     * The name of this instance.
     *
     * @var string
     */
    var $_instance = null;

    /**
     * Hash with header information.
     *
     * @var array
     */
    var $_header = array();

    /**
     * An array containing all the tree nodes.
     *
     * @var array
     */
    var $_nodes = array();

    /**
     * The top-level nodes in the tree.
     *
     * @var array
     */
    var $_root_nodes = array();

    /**
     * Keep count of how many extra columns there are on the left side
     * of the node.
     *
     * @var integer
     */
    var $_extra_cols_left = 0;

    /**
     * Keep count of how many extra columns there are on the right side
     * of the node.
     *
     * @var integer
     */
    var $_extra_cols_right = 0;

    /**
     * Option values.
     *
     * @var array
     */
    var $_options = array('lines' => true);

    /**
     * Stores the sorting criteria temporarily.
     *
     * @var string
     */
    var $_sortCriteria;

    /**
     * Use session to store cached Tree data?
     *
     * @var boolean
     */
    var $_usesession = true;

    /**
     * Should the tree be rendered statically?
     *
     * @var boolean
     */
    var $_static = false;

    /**
     * Attempts to return a reference to a concrete Horde_Tree
     * instance based on $name and $renderer. It will only create a
     * new instance if no Horde_Tree instance with the same parameters
     * currently exists.
     *
     * This method must be invoked as:
     *   $var = &Horde_Tree::singleton($name[, $renderer]);
     *
     * @static
     *
     * @param mixed  $name      @see Horde_Tree::factory.
     * @param string $renderer  @see Horde_Tree::factory.
     * @param array  $params    @see Horde_Tree::factory.
     *
     * @return Horde_Tree  The concrete Horde_Tree reference, or PEAR_Error on
     *                     error.
     */
    function &singleton($name, $renderer, $params = array())
    {
        static $instances = array();

        $id = $name . ':' . $renderer . ':' . serialize($params);
        if (!isset($instances[$id])) {
            $instances[$id] = &Horde_Tree::factory($name, $renderer, $params);
            if (!$instances[$id]->isSupported()) {
                $renderer = Horde_Tree::fallback($renderer);
                if (is_a($renderer, 'PEAR_Error')) {
                    return $renderer;
                }
                return Horde_Tree::singleton($name, $renderer, $params);
            }
        }

        return $instances[$id];
    }

    /**
     * Attempts to return a concrete Horde_Tree instance.
     *
     * @static
     *
     * @param string $name      The name of this tree instance.
     * @param mixed  $renderer  The type of concrete Horde_Tree subclass to
     *                          return. This is based on the rendering driver
     *                          ($renderer). The code is dynamically included.
     * @param array  $params    Any additional parameters the constructor
     *                          needs.
     *
     * @return Horde_Tree  The newly created concrete Horde_Tree instance, or
     *                     PEAR_Error on error.
     */
    function &factory($name, $renderer, $params = array())
    {
        /* Require the renderer lib. */
        include_once dirname(__FILE__) . '/Tree/' . $renderer . '.php';

        $class = 'Horde_Tree_' . $renderer;
        if (class_exists($class)) {
            $tree = new $class($name, $params);
        } else {
            $tree = PEAR::raiseError(sprintf(_("\"%s\" tree renderer not found."), $renderer));
        }

        return $tree;
    }

    /**
     * Try to fall back to a simpler renderer.
     *
     * @paran string $renderer  The renderer that we can't handle.
     *
     * @return string | PEAR_Error  The next best renderer, or an error
     *                              if we've run out of renderers.
     */
    function fallback($renderer)
    {
        switch ($renderer) {
        case 'javascript':
            return 'html';

        case 'html':
            return PEAR::raiseError('out of renderers');
        }
    }

    /**
     * Constructor.
     *
     * @param string $name    The name of this tree instance.
     * @param array  $params  Additional parameters.
     * <pre>
     * 'nosession'  --  (boolean) If true, do not store tree data in session.
     * </pre>
     */
    function Horde_Tree($name, $params = array())
    {
        $this->_instance = $name;
        $this->_usesession = empty($params['nosession']);
        unset($params['nosession']);
        $this->setOption($params);

        /* Set up the session for later to save tree states. */
        if ($this->_usesession &&
            !isset($_SESSION['horde_tree'][$this->_instance])) {
            $_SESSION['horde_tree'][$this->_instance] = array();
        }
    }

    /**
     * Renders the tree.
     *
     * @param boolean $static  If true the tree nodes can't be expanded and
     *                         collapsed and the tree gets rendered expanded.
     */
    function renderTree($static = false)
    {
        echo $this->getTree($static);
    }

    /**
     * Sets an option.
     * Available options:
     * <pre>
     *   alternate    --  Alternate shading in the table? (boolean)
     *   hideHeaders  --  Don't render any HTML for the header row, just use the widths.
     *   class        --  The class to use for the table. (string)
     *   lines        --  Show tree lines? (boolean)
     *   multiline    --  Do the node labels contain linebreaks? (boolean)
     * </pre>
     *
     * @param mixed $option  The option name -or- an array of option name/value
     *                       pairs.
     * @param mixed $val     The option's value.
     */
    function setOption($options, $value = null)
    {
        if (!is_array($options)) {
            $options = array($options => $value);
        }

        foreach ($options as $option => $value) {
            $this->_options[$option] = $value;
        }
    }

    /**
     * Gets an option's value.
     *
     * @param string $option   The name of the option to fetch.
     * @param boolean $html    True or false whether to format the return value
     *                         in html. Defaults to false.
     * @param string $default  A default value to use in case none is set for
     *                         the requested option.
     *
     * @return mixed  The option's value.
     */
    function getOption($option, $html = false, $default = null)
    {
        $value = null;

        if (!isset($this->_options[$option]) && !is_null($default)) {
            /* Requested option has not been but there is a
             * default. */
            $value = $default;
        } elseif (isset($this->_options[$option])) {
            /* Requested option has been set, get its value. */
            $value = $this->_options[$option];
        }

        if ($html && !is_null($value)) {
            /* Format value for html output. */
            $value = sprintf(' %s="%s"', $option, $value);
        }

        return $value;
    }

    /**
     * Adds a node to the node tree array.
     *
     * @param string  $id           The unique node id.
     * @param string  $parent       The parent's unique node id.
     * @param string  $label        The text label for the node.
     * @param string  $indent       Deprecated, this is calculated automatically
     *                              based on the parent node.
     * @param boolean $expanded     Is this level expanded or not.
     * @param array   $params       Any other parameters to set (@see
     *                              addNodeParams() for full details).
     * @param array   $extra_right  Any other columns to display to the right of
     *                              the tree.
     * @param array   $extra_left   Any other columns to display to the left of
     *                              the tree.
     */
    function addNode($id, $parent, $label, $indent = null, $expanded = true,
                     $params = array(), $extra_right = array(),
                     $extra_left = array())
    {
        $this->_nodes[$id]['label'] = $label;

        if ($this->_usesession) {
            $session_state = $_SESSION['horde_tree'][$this->_instance];
            $toggle_id = Util::getFormData(HORDE_TREE_TOGGLE . $this->_instance);
            if ($id == $toggle_id) {
                /* We have a url toggle request for this node. */
                if (isset($session_state['expanded'][$id])) {
                    /* Use session state if it is set. */
                    $expanded = (!$session_state['expanded'][$id]);
                } else {
                    /* Otherwise use what was passed through the
                     * function. */
                    $expanded = (!$expanded);
                }

                /* Save this state to session. */
                $_SESSION['horde_tree'][$this->_instance]['expanded'][$id] = $expanded;
            } elseif (isset($session_state['expanded'][$id])) {
                /* If we have a saved session state use it. */
                $expanded = $session_state['expanded'][$id];
            }
        }

        $this->_nodes[$id]['expanded'] = $expanded;

        /* If any params included here add them now. */
        if (!empty($params)) {
            $this->addNodeParams($id, $params);
        }

        /* If any extra columns included here add them now. */
        if (!empty($extra_right)) {
            $this->addNodeExtra($id, HORDE_TREE_EXTRA_RIGHT, $extra_right);
        }
        if (!empty($extra_left)) {
            $this->addNodeExtra($id, HORDE_TREE_EXTRA_LEFT, $extra_left);
        }

        if (is_null($parent)) {
            if (!in_array($id, $this->_root_nodes)) {
                $this->_root_nodes[] = $id;
            }
        } else {
            if (empty($this->_nodes[$parent]['children'])) {
                $this->_nodes[$parent]['children'] = array();
            }
            if (!in_array($id, $this->_nodes[$parent]['children'])) {
                $this->_nodes[$parent]['children'][] = $id;
            }
        }
    }

    /**
     * Adds additional parameters to a node.
     *
     * @param string $id     The unique node id.
     * @param array $params  Any other parameters to set.
     * <pre>
     * class     --  CSS class to use with this node
     * icon      --  Icon to display next node
     * iconalt   --  Alt text to use for the icon
     * icondir   --  Icon directory
     * iconopen  --  Icon to indicate this node as expanded
     * onclick   --  Onclick event attached to this node
     * url       --  URL to link the node to
     * urlclass  --  CSS class for the node's URL
     * title     --  Link tooltip title
     * target    --  Target for the 'url' link
     * </pre>
     */
    function addNodeParams($id, $params = array())
    {
        if (!is_array($params)) {
            $params = array($params);
        }

        $allowed = array(
            'class', 'icon', 'iconalt', 'icondir', 'iconopen',
            'onclick', 'url', 'urlclass', 'title', 'target',
        );

        foreach ($params as $param_id => $param_val) {
            /* Set only allowed and non-null params. */
            if (in_array($param_id, $allowed) && !is_null($param_val)) {
                $this->_nodes[$id][$param_id] = $param_val;
            }
        }
    }

    /**
     * Adds extra columns to be displayed to the side of the node.
     *
     * @param mixed   $id     The unique node id.
     * @param integer $side   Which side to place the extra columns on.
     * @param array   $extra  Extra columns to display.
     */
    function addNodeExtra($id, $side, $extra)
    {
        if (!is_array($extra)) {
            $extra = array($extra);
        }

        $col_count = count($extra);

        switch ($side) {
        case HORDE_TREE_EXTRA_LEFT:
            $this->_nodes[$id]['extra'][HORDE_TREE_EXTRA_LEFT] = $extra;
            if ($col_count > $this->_extra_cols_left) {
                $this->_extra_cols_left = $col_count;
            }
            break;

        case HORDE_TREE_EXTRA_RIGHT:
            $this->_nodes[$id]['extra'][HORDE_TREE_EXTRA_RIGHT] = $extra;
            if ($col_count > $this->_extra_cols_right) {
                $this->_extra_cols_right = $col_count;
            }
            break;
        }
    }

    /**
     * Sorts the tree by the specified node property.
     *
     * @param string $criteria  The node property to sort by.
     * @param integer $id       Used internally for recursion.
     */
    function sort($criteria, $id = -1)
    {
        if (!isset($this->_nodes[$id]['children'])) {
            return;
        }

        if ($criteria == 'key') {
            ksort($this->_nodes[$id]['children']);
        } else {
            $this->_sortCriteria = $criteria;
            usort($this->_nodes[$id]['children'], array($this, '_sort'));
        }

        foreach ($this->_nodes[$id]['children'] as $child) {
            $this->sort($criteria, $child);
        }
    }

    /**
     * Helper method for sort() to compare two tree elements.
     *
     * @access private
     */
    function _sort($a, $b)
    {
        if (!isset($this->_nodes[$a][$this->_sortCriteria])) {
            return 1;
        }
        if (!isset($this->_nodes[$b][$this->_sortCriteria])) {
            return -1;
        }
        return strcoll($this->_nodes[$a][$this->_sortCriteria],
                       $this->_nodes[$b][$this->_sortCriteria]);
    }

    /**
     * Returns whether the specified node is currently expanded.
     *
     * @param mixed $id  The unique node id.
     *
     * @return boolean  True if the specified node is expanded.
     */
    function isExpanded($id)
    {
        if (isset($this->_nodes[$id])) {
            return $this->_nodes[$id]['expanded'];
        }
        return false;
    }

    /**
     * Adds column headers to the tree table.
     *
     * @param array $header  An array containing hashes with header
     *                       information. The following keys are allowed:
     * <pre>
     * html  -- The HTML content of the header cell
     * width -- The width of the header cell
     * align -- The alignment inside the header cell
     * class -- The CSS class of the header cell
     * </pre>
     */
    function setHeader($header)
    {
        $this->_header = $header;
    }

    /**
     * Set the indent level for each node in the tree.
     */
    function _buildIndents($nodes, $indent = 0)
    {
        foreach ($nodes as $id) {
            $this->_nodes[$id]['indent'] = $indent;
            if (!empty($this->_nodes[$id]['children'])) {
                $this->_buildIndents($this->_nodes[$id]['children'], $indent + 1);
            }
        }
    }

}
