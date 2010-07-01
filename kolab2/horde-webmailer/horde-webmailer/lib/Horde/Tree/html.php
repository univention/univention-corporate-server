<?php
/**
 * The Horde_Tree_html:: class extends the Horde_Tree class to provide
 * HTML specific rendering functions.
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * $Horde: framework/Tree/Tree/html.php,v 1.51.2.16 2009-01-06 15:23:44 jan Exp $
 *
 * @author  Marko Djukic <marko@oblo.com>
 * @package Horde_Tree
 * @since   Horde 3.0
 */
class Horde_Tree_html extends Horde_Tree {

    /**
     * Image directory location.
     *
     * @var string
     */
    var $_img_dir = '';

    /**
     * Default tree graphic for a line.
     *
     * @var string
     */
    var $_img_line = 'line.png';

    /**
     * Default tree graphic for a blank.
     *
     * @var string
     */
    var $_img_blank = 'blank.png';

    /**
     * Default tree graphic for a join.
     *
     * @var string
     */
    var $_img_join = 'join.png';

    /**
     * Default tree graphic for a bottom join.
     *
     * @var string
     */
    var $_img_join_bottom = 'joinbottom.png';

    /**
     * Default tree graphic for a plus.
     *
     * @var string
     */
    var $_img_plus = 'plus.png';

    /**
     * Default tree graphic for a bottom plus.
     *
     * @var string
     */
    var $_img_plus_bottom = 'plusbottom.png';

    /**
     * Default tree graphic for a plus only.
     *
     * @var string
     */
    var $_img_plus_only = 'plusonly.png';

    /**
     * Default tree graphic for a minus.
     *
     * @var string
     */
    var $_img_minus = 'minus.png';

    /**
     * Default tree graphic for a bottom minus.
     *
     * @var string
     */
    var $_img_minus_bottom = 'minusbottom.png';

    /**
     * Default tree graphic for a minus only.
     *
     * @var string
     */
    var $_img_minus_only = 'minusonly.png';

    /**
     * Default tree graphic for a null only.
     *
     * @var string
     */
    var $_img_null_only = 'nullonly.png';

    /**
     * Default tree graphic for a folder.
     *
     * @var string
     */
    var $_img_folder = 'folder.png';

    /**
     * Default tree graphic for an open folder.
     *
     * @var string
     */
    var $_img_folder_open = 'folderopen.png';

    /**
     * Default tree graphic for a leaf.
     *
     * @var string
     */
    var $_img_leaf = 'leaf.png';

    /**
     * TODO
     *
     * @var array
     */
    var $_nodes = array();

    /**
     * TODO
     *
     * @var array
     */
    var $_node_pos = array();

    /**
     * TODO
     *
     * @var array
     */
    var $_dropline = array();

    /**
     * Current value of the alt tag count.
     *
     * @var integer
     */
    var $_alt_count = 0;

    /**
     * Constructor
     */
    function Horde_Tree_html($tree_name, $params)
    {
        parent::Horde_Tree($tree_name, $params);

        $this->_img_dir = $GLOBALS['registry']->getImageDir('horde') . '/tree';

        if (!empty($GLOBALS['nls']['rtl'][$GLOBALS['language']])) {
            $this->_img_line = 'rev-line.png';
            $this->_img_join = 'rev-join.png';
            $this->_img_join_bottom = 'rev-joinbottom.png';
            $this->_img_plus = 'rev-plus.png';
            $this->_img_plus_bottom = 'rev-plusbottom.png';
            $this->_img_plus_only = 'rev-plusonly.png';
            $this->_img_minus = 'rev-minus.png';
            $this->_img_minus_bottom = 'rev-minusbottom.png';
            $this->_img_minus_only = 'rev-minusonly.png';
            $this->_img_null_only = 'rev-nullonly.png';
            $this->_img_leaf = 'rev-leaf.png';
        }
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

        $tree = $this->_buildHeader();
        foreach ($this->_root_nodes as $node_id) {
            $tree .= $this->_buildTree($node_id);
        }
        return $tree;
    }

    /**
     * Check the current environment to see if we can render the HTML
     * tree. HTML is always renderable, at least until we add a
     * php-gtk tree backend, in which case this implementation will
     * actually need a body.
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
     * Returns just the JS node definitions as a string. This is a
     * no-op for the HTML renderer.
     */
    function renderNodeDefinitions()
    {
    }

    /**
     * Returns the HTML code for a header row, if necessary.
     *
     * @access private
     *
     * @return string  The HTML code of the header row or an empty string.
     */
    function _buildHeader()
    {
        if (!count($this->_header)) {
            return '';
        }

        $html = '<div';
        /* If using alternating row shading, work out correct
         * shade. */
        if ($this->getOption('alternate')) {
            $html .= ' class="item' . $this->_alt_count . '"';
            $this->_alt_count = 1 - $this->_alt_count;
        }
        $html .= '>';

        foreach ($this->_header as $header) {
            $html .= '<div class="leftFloat';
            if (!empty($header['class'])) {
                $html .= ' ' . $header['class'];
            }
            $html .= '"';

            $style = '';
            if (!empty($header['width'])) {
                $style .= 'width:' . $header['width'] . ';';
            }
            if (!empty($header['align'])) {
                $style .= 'text-align:' . $header['align'] . ';';
            }
            if (!empty($style)) {
                $html .= ' style="' . $style . '"';
            }
            $html .= '>';
            $html .= empty($header['html']) ? '&nbsp;' : $header['html'];
            $html .= '</div>';
        }

        return $html . '</div>';
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
                $this->_node_pos[$child_node_id]['pos'] = $c + 1;
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
        $className = 'treeRow';
        if (!empty($this->_nodes[$node_id]['class'])) {
            $className .= ' ' . $this->_nodes[$node_id]['class'];
        }
        /* If using alternating row shading, work out correct
         * shade. */
        if ($this->getOption('alternate')) {
            $className .= ' item' . $this->_alt_count;
            $this->_alt_count = 1 - $this->_alt_count;
        }

        $line = '<div class="' . $className . '">';

        /* If we have headers, track which logical "column" we're in
         * for any given cell of content. */
        $column = 0;

        if (isset($this->_nodes[$node_id]['extra'][HORDE_TREE_EXTRA_LEFT])) {
            $extra = $this->_nodes[$node_id]['extra'][HORDE_TREE_EXTRA_LEFT];
            $cMax = count($extra);
            for ($c = 0; $c < $cMax; $c++) {
                $style = '';
                if (isset($this->_header[$column]['width'])) {
                    $style .= 'width:' . $this->_header[$column]['width'] . ';';
                }

                $line .= '<div class="leftFloat"';
                if (!empty($style)) {
                    $line .= ' style="' . $style . '"';
                }
                $line .= '>' . $extra[$c] . '</div>';

                $column++;
            }
        }

        $style = '';
        if (isset($this->_header[$column]['width'])) {
            $style .= 'width:' . $this->_header[$column]['width'] . ';';
        }
        $line .= '<div class="leftFloat"';
        if (!empty($style)) {
            $line .= ' style="' . $style . '"';
        }
        $line .= '>';

        if ($this->getOption('multiline')) {
            $line .= '<table cellspacing="0"><tr><td>';
        }

        for ($i = $this->_static ? 1 : 0; $i < $this->_nodes[$node_id]['indent']; $i++) {
            $line .= '<img src="' . $this->_img_dir . '/';
            if ($this->_dropline[$i] && $this->getOption('lines', false, true)) {
                $line .= $this->_img_line . '" '
                    . 'alt="|&nbsp;&nbsp;&nbsp;" ';
            } else {
                $line .= $this->_img_blank . '" '
                    . 'alt="&nbsp;&nbsp;&nbsp;" ';
            }
            $line .= 'height="20" width="20" style="vertical-align:middle" />';
        }
        $line .= $this->_setNodeToggle($node_id) . $this->_setNodeIcon($node_id);
        if ($this->getOption('multiline')) {
            $line .= '</td><td>';
        }
        $line .= $this->_setLabel($node_id);

        if ($this->getOption('multiline')) {
            $line .= '</td></tr></table>';
        }

        $line .= '</div>';
        $column++;

        if (isset($this->_nodes[$node_id]['extra'][HORDE_TREE_EXTRA_RIGHT])) {
            $extra = $this->_nodes[$node_id]['extra'][HORDE_TREE_EXTRA_RIGHT];
            $cMax = count($extra);
            for ($c = 0; $c < $cMax; $c++) {
                $style = '';
                if (isset($this->_header[$column]['width'])) {
                    $style .= 'width:' . $this->_header[$column]['width'] . ';';
                }

                $line .= '<div class="leftFloat"';
                if (!empty($style)) {
                    $line .= ' style="' . $style . '"';
                }
                $line .= '>' . $extra[$c] . '</div>';

                $column++;
            }
        }

        return $line . "</div>\n";
    }

    /**
     * Sets the label on the tree line.
     *
     * @access private
     *
     * @param string $node_id  The Node ID.
     *
     * @return string  The label for the tree line.
     */
    function _setLabel($node_id)
    {
        $n = $this->_nodes[$node_id];

        $output = '<span';
        if (!empty($n['onclick'])) {
            $output .= ' onclick="' . $n['onclick'] . '"';
        }
        $output .= '>';

        $label = $n['label'];
        if (!empty($n['url'])) {
            $target = '';
            if (!empty($n['target'])) {
                $target = ' target="' . $n['target'] . '"';
            } elseif ($target = $this->getOption('target')) {
                $target = ' target="' . $target . '"';
            }
            $output .= '<a' . (!empty($n['urlclass']) ? ' class="' . $n['urlclass'] . '"' : '') . ' href="' . $n['url'] . '"' . $target . '>' . $label . '</a>';
        } else {
            $output .= $label;
        }

        return $output . '</span>';
    }

    /**
     * Sets the node toggle on the tree line.
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

        if (($this->_nodes[$node_id]['indent'] == 0) &&
            isset($this->_nodes[$node_id]['children'])) {
            /* Top level node with children. */
            $this->_dropline[0] = false;
            if ($this->_static) {
                return '';
            } elseif (!$this->getOption('lines', false, true)) {
                $img = $this->_img_blank;
                $alt = '&nbsp;&nbsp;&nbsp;';
            } elseif ($this->_nodes[$node_id]['expanded']) {
                $img = $this->_img_minus_only;
                $alt = '-';
            } else {
                $img = $this->_img_plus_only;
                $alt = '+';
            }
            if (!$this->_static) {
                $url = Util::addParameter(Horde::selfUrl(), HORDE_TREE_TOGGLE . $this->_instance, $node_id);
                $link_start = Horde::link($url);
            }
        } elseif (($this->_nodes[$node_id]['indent'] != 0) &&
            !isset($this->_nodes[$node_id]['children'])) {
            /* Node without children. */
            if ($this->_node_pos[$node_id]['pos'] < $this->_node_pos[$node_id]['count']) {
                /* Not last node. */
                if ($this->getOption('lines', false, true)) {
                    $img = $this->_img_join;
                    $alt = '|-';
                } else {
                    $img = $this->_img_blank;
                    $alt = '&nbsp;&nbsp;&nbsp;';
                }
                $this->_dropline[$this->_nodes[$node_id]['indent']] = true;
            } else {
                /* Last node. */
                if ($this->getOption('lines', false, true)) {
                    $img = $this->_img_join_bottom;
                    $alt = '`-';
                } else {
                    $img = $this->_img_blank;
                    $alt = '&nbsp;&nbsp;&nbsp;';
                }
                $this->_dropline[$this->_nodes[$node_id]['indent']] = false;
            }
        } elseif (isset($this->_nodes[$node_id]['children'])) {
            /* Node with children. */
            if ($this->_node_pos[$node_id]['pos'] < $this->_node_pos[$node_id]['count']) {
                /* Not last node. */
                if (!$this->getOption('lines', false, true)) {
                    $img = $this->_img_blank;
                    $alt = '&nbsp;&nbsp;&nbsp;';
                } elseif ($this->_static) {
                    $img = $this->_img_join;
                    $alt = '|-';
                } elseif ($this->_nodes[$node_id]['expanded']) {
                    $img = $this->_img_minus;
                    $alt = '-';
                } else {
                    $img = $this->_img_plus;
                    $alt = '+';
                }
                $this->_dropline[$this->_nodes[$node_id]['indent']] = true;
            } else {
                /* Last node. */
                if (!$this->getOption('lines', false, true)) {
                    $img = $this->_img_blank;
                    $alt = '&nbsp;&nbsp;&nbsp;';
                } elseif ($this->_static) {
                    $img = $this->_img_join_bottom;
                    $alt = '`-';
                } elseif ($this->_nodes[$node_id]['expanded']) {
                    $img = $this->_img_minus_bottom;
                    $alt = '-';
                } else {
                    $img = $this->_img_plus_bottom;
                    $alt = '+';
                }
                $this->_dropline[$this->_nodes[$node_id]['indent']] = false;
            }
            if (!$this->_static) {
                $url = Util::addParameter(Horde::selfUrl(), HORDE_TREE_TOGGLE . $this->_instance, $node_id);
                $link_start = Horde::link($url);
            }
        } else {
            /* Top level node with no children. */
            if ($this->_static) {
                return '';
            }
            if ($this->getOption('lines', false, true)) {
                $img = $this->_img_null_only;
                $alt = '&nbsp;&nbsp;';
            } else {
                $img = $this->_img_blank;
                $alt = '&nbsp;&nbsp;&nbsp;';
            }
            $this->_dropline[0] = false;
        }

        $link_end = ($link_start) ? '</a>' : '';

        $img = $link_start . '<img src="' . $this->_img_dir . '/' . $img . '"'
            . (isset($alt) ? ' alt="' . $alt . '"' : '')
            . ' height="20" width="20" style="vertical-align:middle" border="0" />'
            . $link_end;

        return $img;
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
        $img_dir = isset($this->_nodes[$node_id]['icondir']) ? $this->_nodes[$node_id]['icondir'] : $this->_img_dir;
        if ($img_dir) {
            $img_dir .= '/';
        }

        if (isset($this->_nodes[$node_id]['icon'])) {
            if (empty($this->_nodes[$node_id]['icon'])) {
                return '';
            }
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
                /* Leaf node (no children). */
                $img = $this->_img_leaf;
            }
        }

        $imgtxt = '<img src="' . $img_dir . $img . '"';

        /* Does the node have user defined alt text? */
        if (isset($this->_nodes[$node_id]['iconalt'])) {
            $imgtxt .= ' alt="' . htmlspecialchars($this->_nodes[$node_id]['iconalt']) . '"';
        }

        return $imgtxt . ' />';
    }

}
