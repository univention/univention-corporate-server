<?php
/**
 * The Horde_Tree_html:: class extends the Horde_Tree class to provide HTML
 * specific rendering functions.
 *
 * Copyright 2003-2004 Marko Djukic <marko@oblo.com>
 *
 * See the enclosed file COPYING for license information (GPL). If you did not
 * receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * $Horde: framework/Tree/Tree/html.php,v 1.16 2004/01/05 13:29:30 mdjukic Exp $
 *
 * @author  Marko Djukic <marko@oblo.com>
 * @version $Revision: 1.1.2.1 $
 * @package Horde_Tree
 * @since   Horde 3.0
 */
class Horde_Tree_html extends Horde_Tree {

    /**
     * Image directory location.
     *
     * @var string $_img_dir
     */
    var $_img_dir = '';

    /**
     * Default tree graphics (located in $_img_dir).
     *
     * @var string $_img_line
     * @var string $_img_blank
     * @var string $_img_join
     * @var string $_img_join_bottom
     * @var string $_img_plus
     * @var string $_img_plus_bottom
     * @var string $_img_plus_only
     * @var string $_img_minus
     * @var string $_img_minus_bottom
     * @var string $_img_minus_only
     * @var string $_img_folder
     * @var string $_img_folder_open
     * @var string $_img_leaf
     */
    var $_img_line         = 'line.gif';
    var $_img_blank        = 'blank.gif';
    var $_img_join         = 'join.gif';
    var $_img_join_bottom  = 'joinbottom.gif';
    var $_img_plus         = 'plus.gif';
    var $_img_plus_bottom  = 'plusbottom.gif';
    var $_img_plus_only    = 'plusonly.gif';
    var $_img_minus        = 'minus.gif';
    var $_img_minus_bottom = 'minusbottom.gif';
    var $_img_minus_only   = 'minusonly.gif';
    var $_img_folder       = 'folder.gif';
    var $_img_folder_open  = 'folderopen.gif';
    var $_img_leaf         = 'leaf.gif';

    /**
     * TODO
     *
     * @var array $_nodes
     */
    var $_nodes = array();

    /**
     * TODO
     *
     * @var array $_node_pos
     */
    var $_node_pos = array();

    /**
     * TODO
     *
     * @var array $_dropline
     */
    var $_dropline = array();

    /**
     * Current value of the alt tag count.
     *
     * @var integer $_alt_count
     */
    var $_alt_count = 0;

    /**
     * Constructor
     *
     * @access public
     */
    function Horde_Tree_html($tree_name, $params)
    {
        parent::Horde_Tree($tree_name, $params);

        $this->_img_dir = $GLOBALS['registry']->getParam('graphics', 'horde') . '/tree';
    }
    
    /**
     * Render the tree.
     *
     * @access public
     */
    function renderTree()
    {
        echo $this->_setTableStart();
        echo $this->_buildTree($this->_root_node_id);
        echo '</table>';
    }

    /**
     * Gets the starting html to the table.
     *
     * @access private
     */
    function _setTableStart()
    {
        return sprintf('<table%s%s%s%s%s>',
                       $this->getOption('border', true, '0'),
                       $this->getOption('width', true),
                       $this->getOption('class', true),
                       $this->getOption('cellpadding', true, '0'),
                       $this->getOption('cellspacing', true, '0'));
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
        $output = $this->_buildLine($node_id);

        if (isset($this->_nodes[$node_id]['children']) &&
            $this->_nodes[$node_id]['expanded']) {
            $num_subnodes = count($this->_nodes[$node_id]['children']);
            for ($c = 0; $c < $num_subnodes; $c++) {
                $child_node_id = $this->_nodes[$node_id]['children'][$c];
                $this->_node_pos[$child_node_id] = array();
                $this->_node_pos[$child_node_id]['pos'] = $c . 1;
                $this->_node_pos[$child_node_id]['count'] = $num_subnodes;
                $output .= $this->_buildTree($child_node_id);
            }
        }

        return $output;
    }

    /**
     * Function to create a single line of the tree.
     *
     * @access private
     *
     * @param string $node_id  The Node ID.
     *
     * @return string  The rendered line.
     */
    function _buildLine($node_id)
    {
        $node_class = '';

        if (!empty($this->_nodes[$node_id]['class'])) {
            $node_class = ' class="' . $this->_nodes[$node_id]['class'] . '"';
        }

        $line = '<tr';
        /* If using alternating row shading, work out correct shade. */
        if ($this->getOption('alternate')) {
            $line .= ' class="item' . $this->_alt_count . '"';
            $this->_alt_count = ($this->_alt_count) ? 0 : 1;
        }
        $line .= '>';

        if (isset($this->_nodes[$node_id]['extra'][HORDE_TREE_EXTRA_LEFT])) {
            $extra = $this->_nodes[$node_id]['extra'][HORDE_TREE_EXTRA_LEFT];
            $cMax = count($extra);
            for ($c = 0; $c < $cMax; $c++) {
                $line .= '<td' . $node_class . ' align="center">' . $extra[$c] . '</td>';
            }
        }
        $line .= '<td' . $node_class . '>';

        for ($i = 0; $i < $this->_nodes[$node_id]['indent']; $i++) {
            $line .= '<img src="' . $this->_img_dir . '/';
            $line .= ($this->_dropline[$i]) ? $this->_img_line : $this->_img_blank;
            $line .= '" height="20" width="20" align="middle" border="0" />';
        }
        $line .= $this->_setNodeToggle($node_id) . $this->_setNodeIcon($node_id) . $this->_setLabel($node_id) . '</td>';

        if (isset($this->_nodes[$node_id]['extra'][HORDE_TREE_EXTRA_RIGHT])) {
            $extra = $this->_nodes[$node_id]['extra'][HORDE_TREE_EXTRA_RIGHT];
            $cMax = count($extra);
            for ($c = 0; $c < $cMax; $c++) {
                $line .= '<td' . $node_class . ' align="center">' . $extra[$c] . '</td>';
            }
        }
        $line .= "</tr>\n";

        return $line;
    }

    /**
     * Set the label on the tree line.
     *
     * @access private
     *
     * @param string $node_id  The Node ID.
     *
     * @return string  The label for the tree line.
     */
    function _setLabel($node_id)
    {
        $output = '<span';

        if (!empty($this->_nodes[$node_id]['onclick'])) {
            $output .= ' onclick="' . $this->_nodes[$node_id]['onclick'] . '"';
        }
        $output .= '>';

        $label = $this->_nodes[$node_id]['label'];
        if (!empty($this->_nodes[$node_id]['url'])) {
            $output .= '<a href="' . $this->_nodes[$node_id]['url'] . '">' . $label . '</a>';
        } else {
            $output .= $label;
        }

        return $output . '</span></td>';
    }

    /**
     * Set the node toggle on the tree line.
     *
     * @access private
     *
     * @param string $node_id  The Node ID.
     *
     * @return string  The node toggle for the tree line.
     */
    function _setNodeToggle($node_id)
    {
        $link_start = '';

        if (($node_id == $this->_root_node_id) &&
            isset($this->_nodes[$node_id]['children'])) {
            /* Root, and children. */
            $img = ($this->_nodes[$node_id]['expanded']) ? $this->_img_minus_only : $this->_img_plus_only;
            $this->_dropline[0] = false;
            $url = Util::addParameter(Horde::selfURL(), HORDE_TREE_TOGGLE . $this->_instance, $node_id);
            $link_start = Horde::link($url);
        } elseif (($node_id != $this->_root_node_id) &&
            !isset($this->_nodes[$node_id]['children'])) {
            /* Node no children. */
            if ($this->_node_pos[$node_id]['pos'] < $this->_node_pos[$node_id]['count']) {
                /* Not last node. */
                $img = $this->_img_join;
                $this->_dropline[$this->_nodes[$node_id]['indent']] = true;
            } else {
                /* Last node. */
                $img = $this->_img_join_bottom;
                $this->_dropline[$this->_nodes[$node_id]['indent']] = false;
            }
        } elseif (isset($this->_nodes[$node_id]['children'])) {
            /* Node with children. */
            if ($this->_node_pos[$node_id]['pos'] < $this->_node_pos[$node_id]['count']) {
                /* Not last node. */
                $img = ($this->_nodes[$node_id]['expanded']) ? $this->_img_minus : $this->_img_plus;
                $this->_dropline[$this->_nodes[$node_id]['indent']] = true;
            } else {
                /* Last node. */
                $img = ($this->_nodes[$node_id]['expanded']) ? $this->_img_minus_bottom : $this->_img_plus_bottom;
                $this->_dropline[$this->_nodes[$node_id]['indent']] = false;
            }
            $url = Util::addParameter(Horde::selfURL(), HORDE_TREE_TOGGLE . $this->_instance, $node_id);
            $link_start = Horde::link($url);
        } else {
            /* Root only, no children. */
            $img = $this->_img_minus_only;
            $this->_dropline[0] = false;
        }

        $link_end = ($link_start) ? '</a>' : '';

        return $link_start . '<img src="' . $this->_img_dir . '/' . $img . '" height="20" width="20" align="middle" border="0" />' . $link_end;
    }

    /**
     * Sets the icon for the node.
     *
     * @access private
     *
     * @param string $node_id  The Node ID.
     *
     * @return string  The node icon for the tree line.
     */
    function _setNodeIcon($node_id)
    {
        $img_dir = (!empty($this->_nodes[$node_id]['icondir'])) ? $this->_nodes[$node_id]['icondir'] : $this->_img_dir;

        if (isset($this->_nodes[$node_id]['icon'])) {
            /* Node has a user defined icon. */
            if (isset($this->_nodes[$node_id]['iconopen']) &&
                $this->_nodes[$node_id]['expanded']) {
                $img = $this->_nodes[$node_id]['iconopen'];
            } else {
                $img = $this->_nodes[$node_id]['icon'];
            }
        } else {
            /* Use standard icon set. */
            if (isset($this->_nodes[$node_id]['children'])) {
                /* Node with children. */
                $img = ($this->_nodes[$node_id]['expanded']) ? $this->_img_folder_open : $this->_img_folder;
            } else {
                /* Node no children. */
                $img = $this->_img_leaf;
            }
        }

        $imgtxt = '<img src="' . $img_dir . '/' . $img . '" align="middle" border="0" ';

        /* Does the node have user defined alt text? */
        if (isset($this->_nodes[$node_id]['iconalt'])) {
            $imgtxt .= 'alt="' . $this->_nodes[$node_id]['iconalt'] . '" ';
        }

        return $imgtxt . '/>';
    }

}
