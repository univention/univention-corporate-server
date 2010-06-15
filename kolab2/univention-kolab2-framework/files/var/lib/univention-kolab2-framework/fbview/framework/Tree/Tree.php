<?php

/** @const HORDE_TREE_EXTRA_LEFT Display extra columns to left of tree. */
define('HORDE_TREE_EXTRA_LEFT', 0);

/** @const HORDE_TREE_EXTRA_RIGHT Display extra columns to right of tree. */
define('HORDE_TREE_EXTRA_RIGHT', 1);

/** @const HORDE_TREE_TOGGLE The preceding text, before the Horde_Tree instance name, used for collapse/expand submissions. */
define('HORDE_TREE_TOGGLE', 'ht_toggle_');

/**
 * The Horde_Tree:: class provides a tree view of hierarchical information. It
 * allows for expanding/collapsing of branches and maintains their state. It
 * can work together with the Horde_Tree javascript class to achieve this in
 * DHTML on supported browsers.
 *
 * Copyright 2003-2004 Marko Djukic <marko@oblo.com>
 *
 * See the enclosed file COPYING for license information (GPL). If you did not
 * receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * $Horde: framework/Tree/Tree.php,v 1.32 2004/01/12 20:58:18 slusarz Exp $
 *
 * @author  Marko Djukic <marko@oblo.com>
 * @version $Revision: 1.1.2.1 $
 * @package Horde_Tree
 * @since   Horde 3.0
 */
class Horde_Tree {

    /**
     * The name of this instance.
     *
     * @var string $_instance
     */
    var $_instance = null;

    /**
     * An array containing all the tree nodes.
     *
     * @var array $_nodes
     */
    var $_nodes = array();

    /**
     * The root node of this tree.
     *
     * @var integer $_root_node_id
     */
    var $_root_node_id = null;

    /**
     * Keep count of how many extra columns there are on either side of the
     * node.
     *
     * @var integer $_extra_cols_left
     * @var integer $_extra_cols_right
     */
    var $_extra_cols_left = 0;
    var $_extra_cols_right = 0;

    /**
     * Option values.
     *
     * @var array $_options
     */
    var $_options = array();

    /**
     * Use session to store cached Tree data?
     *
     * @var boolean $_usesession
     */
    var $_usesession = true;

    /**
     * Attempts to return a reference to a concrete Horde_Tree instance
     * based on $tree_name and $renderer.
     * It will only create a new instance if no Horde_Tree instance with
     * the same parameters currently exists.
     *
     * This method must be invoked as:
     *   $var = &Horde_Tree::singleton($tree_name[, $renderer]);
     *
     * @access public
     *
     * @param mixed $tree_name           See Horde_Tree::factory().
     * @param optional string $renderer  See Horde_Tree::factory().
     * @param optional array $params     See Horde_Tree::factory().
     *
     * @return object Horde_Tree  The concrete Horde_Tree reference, or
     *                            PEAR_Error on error.
     */
    function &singleton($tree_name, $renderer = 'javascript',
                        $params = array())
    {
        static $instance = array();

        $id = $tree_name . ':' . $renderer . ':' . serialize($params);

        if (!isset($instance[$id])) {
            $instance[$id] = &Horde_Tree::factory($tree_name, $renderer, $params);
        }

        return $instance[$id];
    }

    /**
     * Attempts to return a concrete Horde_Tree instance.
     *
     * @access public
     *
     * @param string $tree_name         The name of this tree instance.
     * @param optional mixed $renderer  The type of concrete Horde_Tree
     *                                  subclass to return. This is based on
     *                                  the rendering driver ($renderer). The
     *                                  code is dynamically included. If
     *                                  $renderer an array, then we will look
     *                                  in $renderer[0]/lib/Tree/ for the
     *                                  subclass implementation named
     *                                  $renderer[1].php.
     * @param optional array $params    Any additional parameters the
     *                                  constructor needs.
     *
     * @return object Horde_Tree  The newly created concrete Horde_Tree
     *                            instance, or PEAR_Error on error.
     */
    function &factory($tree_name, $renderer = 'javascript', $params = array())
    {
        if (!$GLOBALS['browser']->hasFeature('javascript')) {
            /* If no javascript available default to HTML driver. */
            $renderer = 'html';
        } elseif (!@file_exists(dirname(__FILE__) . '/Tree/' . $renderer . '.php')) {
            /* If driver does not exist default to javascript renderer. */
            $renderer = 'javascript';
        }

        /* Require the renderer lib. */
        include_once dirname(__FILE__) . '/Tree/' . $renderer . '.php';

        $class = 'Horde_Tree_' . $renderer;
        if (class_exists($class)) {
            return $ret = &new $class($tree_name, $params);
        } else {
            return PEAR::raiseError(sprintf(_("'%s' tree renderer not found."), $renderer));
        }
    }

    /**
     * Constructor.
     *
     * @access public
     *
     * @param string $tree_name       The name of this tree instance.
     * @param optional array $params  Additional parameters.
     * <pre>
     * 'nosession'  --  (boolean) If true, do not store tree data in session.
     * </pre>
     *
     * @return object Horde_Tree  The new Horde_Tree object.
     */
    function Horde_Tree($tree_name, $params = array())
    {
        $this->_instance = $tree_name;
        $this->_usesession = empty($params['nosession']);

        /* Set up the session for later to save tree states. */
        if ($this->_usesession &&
            !isset($_SESSION['horde_tree'][$this->_instance])) {
            $_SESSION['horde_tree'][$this->_instance] = array();
        }
    }

    /**
     * Set an option.
     * Available options:
     *   alternate    --  Alternate shading in the table? (boolean)
     *   border       --  The border size around the tree table. (integer)
     *   cellpadding  --  The cellpadding to use for the table. (integer)
     *   cellspacing  --  The cellspacing to use for the table. (integer)
     *   class        --  The class to use for the table. (string)
     *   width        --  The width of the tree table. (string)
     *
     * @access public
     *
     * @param mixed $option        The option name -or- an array of option
     *                             name/value pairs.
     * @param optional mixed $val  The option's value.
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
     * Get an option's value.
     *
     * @access public
     *
     * @param string $option            The name of the option to fetch.
     * @param optional bool $html       True or false whether to format the
     *                                  return value in html. Defaults to
     *                                  false.
     * @param optional string $default  A default value to use in case none
     *                                  is set for the requested option.
     *
     * @return mixed  The option's value.
     */
    function getOption($option, $html = false, $default = null)
    {
        $value = null;

        if (!isset($this->_options[$option]) && !is_null($default)) {
            /* Requested option has not been but there is a default. */
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
     * @access public
     *
     * @param string $id                  The unique node id.
     * @param string $parent              The parent's unique node id.
     * @param string $label               The text label for the node.
     * @param string $indent              The level of indentation.
     * @param optional boolean $expanded  Is this level expanded or not.
     * @param optional array $params      Any other parameters to set (see
     *                                    addNodeParams() for full details).
     * @param optional array $extra_right Any other columns to display to the
     *                                    right of the tree.
     * @param optional array $extra_left  Any other columns to display to the
     *                                    left of the tree.
     */
    function addNode($id, $parent, $label, $indent, $expanded = true,
                     $params = array(), $extra_right = array(),
                     $extra_left = array())
    {
        $this->_nodes[$id]['label'] = $label;
        $this->_nodes[$id]['indent'] = $indent;

        if ($this->_usesession) {
            $session_state = $_SESSION['horde_tree'][$this->_instance];
            $toggle_id = Util::getFormData(HORDE_TREE_TOGGLE . $this->_instance);
            if ($id == $toggle_id) {
                /* We have a url toggle request for this node. */
                if (isset($session_state['expanded'][$id])) {
                    /* Use session state if it is set. */
                    $expanded = (!$session_state['expanded'][$id]);
                } else {
                    /* Otherwise use what was passed through the function. */
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
            $this->_root_node_id = $id;
        } else {
            $this->_nodes[$parent]['children'][] = $id;
        }
    }

    /**
     * Adds additional parameters to a node.
     *
     * @access public
     *
     * @param string $id              The unique node id.
     * @param optional array $params  Any other parameters to set.
     * <pre>
     * class     --  CSS class to use with this node
     * icon      --  Icon to display next node
     * iconalt   --  Alt text to use for the icon
     * icondir   --  Icon directory
     * iconopen  --  Icon to indicate this node as expanded
     * onclick   --  Onclick event attached to this node
     * url       --  URL to link the node to
     * </pre>
     */
    function addNodeParams($id, $params = array())
    {
        if (!is_array($params)) {
            $params = array($params);
        }

        $allowed = array(
            'class', 'icon', 'iconalt', 'icondir', 'iconopen', 'onclick',
            'url'
        );

        foreach ($params as $param_id => $param_val) {
            /* Set only allowed params, and only if not empty. */
            if (!empty($param_val) && in_array($param_id, $allowed)) {
                $this->_nodes[$id][$param_id] = $param_val;
            }
        }
    }

    /**
     * Adds extra columns to be displayed to the side of the node.
     *
     * @access public
     *
     * @param mixed $id      The unique node id.
     * @param integer $side  Which side to place the extra columns on.
     * @param array $extra   Extra columns to display.
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

}
