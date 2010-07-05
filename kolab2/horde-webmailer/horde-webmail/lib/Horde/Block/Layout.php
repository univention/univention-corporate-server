<?php
/**
 * The Horde_Block_Layout class provides basic functionality for both managing
 * and displaying blocks through Horde_Block_Layout_Manager and
 * Horde_Block_Layout_View.
 *
 * $Horde: framework/Block/Block/Layout.php,v 1.21.10.13 2009-01-06 15:22:53 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.2
 * @package Horde_Block
 */
class Horde_Block_Layout {

    /**
     * @var string
     */
    var $_editUrl;

    /**
     * @var string
     */
    var $_viewUrl;

    /**
     * Returns whether the specified block may be removed.
     *
     * @param integer $row  A layout row.
     * @param integer $col  A layout column.
     *
     * @return boolean  True if this block may be removed.
     */
    function isRemovable($row, $col)
    {
        global $conf;

        $app = $this->_layout[$row][$col]['app'];
        $type = $this->_layout[$row][$col]['params']['type'];
        $block = $app . ':' . $type;

        /* Check if the block is a fixed block. */
        if (!in_array($block, $conf['portal']['fixed_blocks'])) {
            return true;
        }

        /* Check if we have still another block of the same type. */
        $found = false;
        foreach ($this->_layout as $cur_row) {
            foreach ($cur_row as $cur_col) {
                if (isset($cur_col['app']) &&
                    $cur_col['app'] == $app &&
                    $cur_col['params']['type'] == $type) {
                    if ($found) {
                        return true;
                    } else {
                        $found = true;
                    }
                }
            }
        }

        return false;
    }

    /**
     * Returns an URL triggering an action to a block.
     *
     * @param string $action  An action to trigger.
     * @param integer $row    A layout row.
     * @param integer $col    A layout column.
     *
     * @return string  An URL with all necessary parameters.
     */
    function getActionUrl($action, $row, $col)
    {
        $url = Util::addParameter(
            Horde::url($this->_editUrl),
            array('col' => $col,
                  'row' => $row,
                  'action' => $action,
                  'url' => $this->_viewUrl,
                  'nocache' => base_convert(microtime(), 10, 36)));
        return $url . '#block';
    }

    /**
     * Returns the actions for the block header.
     *
     * @param integer $row   A layout row.
     * @param integer $col   A layout column.
     * @param boolean $edit  Whether to include the edit icon.
     *
     * @return string  HTML code for the block action icons.
     */
    function getHeaderIcons($row, $col, $edit, $url = null)
    {
        $icons = '';
        if ($edit) {
            $icons .= Horde::link($this->getActionUrl('edit', $row, $col),
                                  _("Edit"))
                . Horde::img('edit.png', _("Edit"), '',
                             $GLOBALS['registry']->getImageDir('horde'))
                . '</a>';
        }
        if ($this->isRemovable($row, $col)) {
            $icons .= Horde::link(
                $this->getActionUrl('removeBlock', $row, $col), _("Remove"),
                '', '',
                'return window.confirm(\''
                . addslashes(_("Really delete this block?")) . '\')')
                . Horde::img('delete.png', _("Remove"), '',
                             $GLOBALS['registry']->getImageDir('horde'))
                . '</a>';
        }
        return $icons;
    }

}
