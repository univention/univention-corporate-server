<?php

require_once 'Horde/Array.php';
require_once 'Horde/Block/Layout.php';

/**
 * The Horde_Block_Layout_Manager class allows manipulation of Horde_Block
 * layouts.
 *
 * $Horde: framework/Block/Block/Layout/Manager.php,v 1.4.2.12 2009-01-06 15:22:53 jan Exp $
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
class Horde_Block_Layout_Manager extends Horde_Block_Layout {

    /**
     * Our Horde_Block_Collection instance.
     *
     * @var Horde_Block_Collection
     */
    var $_collection;

    /**
     * The current block layout.
     *
     * @var array
     */
    var $_layout = array();

    /**
     * A cache for the block objects.
     *
     * @var array
     */
    var $_blocks = array();

    /**
     * The maximum number of columns.
     *
     * @var integer
     */
    var $_columns = 0;

    /**
     * Has the layout been updated since it was instantiated.
     *
     * @var boolean
     */
    var $_updated = false;

    /**
     * The current block (array: [row, col]).
     *
     * @var array
     */
    var $_currentBlock = array(null, null);

    /**
     * The new row of the last changed block.
     *
     * @var integer
     */
    var $_changed_row = null;

    /**
     * The new column of the last changed block.
     *
     * @var integer
     */
    var $_changed_col = null;

    /**
     * Constructor.
     *
     * @param Horde_Block_Collection $collection
     * @param array $layout
     */
    function Horde_Block_Layout_Manager(&$collection, $layout = array())
    {
        $this->_collection = &$collection;
        $this->_layout = $layout;
        $this->_editUrl = Horde::selfUrl();

        // Fill the _covered caches and empty rows.
        $rows = count($this->_layout);
        $empty = array();
        for ($row = 0; $row < $rows; $row++) {
            $cols = count($this->_layout[$row]);
            if (!isset($empty[$row])) {
                $empty[$row] = true;
            }
            for ($col = 0; $col < $cols; $col++) {
                if (!isset($this->_layout[$row][$col])) {
                    $this->_blocks[$row][$col] = PEAR::raiseError(_("No block exists at the requested position"), 'horde.error');
                } elseif (is_array($this->_layout[$row][$col])) {
                    $field = $this->_layout[$row][$col];

                    $empty[$row] = false;
                    if (isset($field['width'])) {
                        for ($i = 1; $i < $field['width']; $i++) {
                            $this->_layout[$row][$col + $i] = 'covered';
                        }
                    }
                    if (isset($field['height'])) {
                        if (!isset($field['width'])) {
                            $field['width'] = 1;
                        }
                        for ($i = 1; $i < $field['height']; $i++) {
                            $this->_layout[$row + $i][$col] = 'covered';
                            for ($j = 1; $j < $field['width']; $j++) {
                                $this->_layout[$row + $i][$col + $j] = 'covered';
                            }
                            $empty[$row + $i] = false;
                        }
                    }
                }
            }

            // Strip empty blocks from the end of the rows.
            for ($col = $cols - 1; $col >= 0; $col--) {
                if (!isset($this->_layout[$row][$col]) ||
                    $this->_layout[$row][$col] == 'empty') {
                    unset($this->_layout[$row][$col]);
                } else {
                    break;
                }
            }

            $this->_columns = max($this->_columns, count($this->_layout[$row]));
        }

        // Fill all rows up to the same length.
        $layout = array();
        for ($row = 0; $row < $rows; $row++) {
            $cols = count($this->_layout[$row]);
            if ($cols < $this->_columns) {
                for ($col = $cols; $col < $this->_columns; $col++) {
                    $this->_layout[$row][$col] = 'empty';
                }
            }
            $layout[] = $this->_layout[$row];
        }

        $this->_layout = $layout;
    }

    /**
     * Serialize and return the current block layout.
     */
    function serialize()
    {
        return serialize($this->_layout);
    }

    /**
     * Resets the current layout to the value stored in the preferences.
     */
    function unserialize($data)
    {
        $this->_layout = @unserialize($data);
    }

    /**
     * Returns a single instance of the Horde_Block_Layout_Manager class.
     *
     * @param string $name
     * @param Horde_Block_Collection &$collection
     * @param string $data
     *
     * @static
     *
     * @return Horde_Block_Layout_Manager  The Horde_Block_Layout_Manager instance.
     */
    function &singleton($name, &$collection, $data = '')
    {
        static $instances = array();
        if (!isset($instances[$name])) {
            $instances[$name] = new Horde_Block_Layout_Manager($collection, $data);
        }
        return $instances[$name];
    }

    /**
     * Process a modification to the current layout.
     *
     * @param string $action
     * @param integer $row
     * @param integer $col
     * @param string $url
     */
    function handle($action, $row, $col, $url = null)
    {
        switch ($action) {
        case 'moveUp':
        case 'moveDown':
        case 'moveLeft':
        case 'moveRight':
        case 'expandUp':
        case 'expandDown':
        case 'expandLeft':
        case 'expandRight':
        case 'shrinkLeft':
        case 'shrinkRight':
        case 'shrinkUp':
        case 'shrinkDown':
        case 'removeBlock':
            $result = call_user_func(array(&$this, $action), $row, $col);
            if (is_a($result, 'PEAR_Error')) {
                $GLOBALS['notification']->push($result);
            } else {
                $this->_updated = true;
            }
            break;

        // Save the changes made to a block.
        case 'save':
        // Save the changes made to a block and continue editing.
        case 'save-resume':
            // Get requested block type.
            list($newapp, $newtype) = explode(':', Util::getFormData('app'));

            // Is this a new block?
            $new = false;
            if ($this->isEmpty($row, $col) ||
                !$this->rowExists($row) ||
                !$this->colExists($col)) {
                // Check permissions.
                if (Horde::hasPermission('max_blocks') !== true &&
                    Horde::hasPermission('max_blocks') <= $this->count()) {
                    $message = @htmlspecialchars(sprintf(ngettext("You are not allowed to create more than %d block.", "You are not allowed to create more than %d blocks.", Horde::hasPermission('max_blocks')), Horde::hasPermission('max_blocks')), ENT_COMPAT, NLS::getCharset());
                    if (!empty($conf['hooks']['permsdenied'])) {
                        $message = Horde::callHook('_perms_hook_denied', array('horde:max_blocks'), 'horde', $message);
                    }
                    $GLOBALS['notification']->push($message, 'horde.error', array('content.raw'));
                    break;
                }

                $new = true;
                // Make sure there is somewhere to put it.
                $this->addBlock($row, $col);
            }

            // Or an existing one?
            $exists = false;
            $changed = false;
            if (!$new) {
                // Get target block info.
                $info = $this->getBlockInfo($row, $col);
                $exists = $this->isBlock($row, $col);
                // Has a different block been selected?
                if ($exists &&
                    ($info['app'] != $newapp ||
                     $info['block'] != $newtype)) {
                    $changed = true;
                }
            }

            if ($new || $changed) {
                // Change app or type.
                $info = array();
                $info['app'] = $newapp;
                $info['block'] = $newtype;
                $params = $this->_collection->getParams($newapp, $newtype);
                foreach ($params as $newparam) {
                    $info['params'][$newparam] = $this->_collection->getDefaultValue($newapp, $newtype, $newparam);
                }
                $this->setBlockInfo($row, $col, $info);
            } elseif ($exists) {
                // Change values.
                $this->setBlockInfo($row, $col, array('params' => Util::getFormData('params', array())));
            }
            $this->_updated = true;
            if ($action == 'save') {
                break;
            }

        // Make a block the current block for editing.
        case 'edit':
            $this->_currentBlock = array($row, $col);
            $url = null;
            break;
        }

        if (!empty($url)) {
            header('Location: ' . Util::addParameter($url, 'unique',
                                                     md5(microtime()), false));
        }
    }

    /**
     * Has the layout been changed since it was instantiated?
     *
     * @return boolean
     */
    function updated()
    {
        return $this->_updated;
    }

    /**
     * Get the current block row and column.
     *
     * @return array [row, col]
     */
    function getCurrentBlock()
    {
        return $this->_currentBlock;
    }

    /**
     * Returns the Horde_Block at the specified position.
     *
     * @param integer $row  A layout row.
     * @param integer $col  A layout column.
     *
     * @return Horde_Block  The block from that position or a PEAR_Error
     *                      if something went wrong.
     */
    function &getBlock($row, $col)
    {
        if (!isset($this->_blocks[$row][$col])) {
            $field = $this->_layout[$row][$col];
            $this->_blocks[$row][$col] =
                &Horde_Block_Collection::getBlock($field['app'], $field['params']['type'], $field['params']['params']);
        }

        return $this->_blocks[$row][$col];
    }

    /**
     * Returns the coordinates of the block covering the specified
     * field.
     *
     * @param integer $row  A layout row.
     * @param integer $col  A layout column.
     *
     * @return array  The top-left row-column-coordinate of the block
     *                covering the specified field or null if the field
     *                is empty.
     */
    function getBlockAt($row, $col)
    {
        /* Trivial cases first. */
        if ($this->isEmpty($row, $col)) {
            return null;
        } elseif (!$this->isCovered($row, $col)) {
            return array($row, $col);
        }

        /* This is a covered field. */
        for ($test = $row - 1; $test >= 0; $test--) {
            if (!$this->isCovered($test, $col) &&
                !$this->isEmpty($test, $col) &&
                $test + $this->getHeight($test, $col) - 1 == $row) {
                return array($test, $col);
            }
        }
        for ($test = $col - 1; $test >= 0; $test--) {
            if (!$this->isCovered($row, $test) &&
                !$this->isEmpty($test, $col) &&
                $test + $this->getWidth($row, $test) - 1 == $col) {
                return array($row, $test);
            }
        }
    }

    /**
     * Returns a hash with some useful information about the specified
     * block.
     *
     * Returned hash values:
     * 'app': application name
     * 'block': block name
     * 'params': parameter hash
     *
     * @param integer $row  A layout row.
     * @param integer $col  A layout column.
     *
     * @return array  The information hash.
     */
    function getBlockInfo($row, $col)
    {
        if (!isset($this->_layout[$row][$col]) ||
            $this->isEmpty($row, $col) ||
            $this->isCovered($row, $col)) {
            return PEAR::raiseError(_("No block exists at the requested position"), 'horde.error');
        }

        return array('app' => $this->_layout[$row][$col]['app'],
                     'block' => $this->_layout[$row][$col]['params']['type'],
                     'params' => $this->_layout[$row][$col]['params']['params']);
    }

    /**
     * Sets a batch of information about the specified block.
     *
     * @param integer $row  A layout row.
     * @param integer $col  A layout column.
     * @param array $info   A hash with information values.
     *                      Possible elements are:
     *                      'app': application name
     *                      'block': block name
     *                      'params': parameter hash
     */
    function setBlockInfo($row, $col, $info = array())
    {
        if (!isset($this->_layout[$row][$col])) {
            return PEAR::raiseError(_("No block exists at the requested position"), 'horde.error');
        }

        if (isset($info['app'])) {
            $this->_layout[$row][$col]['app'] = $info['app'];
        }
        if (isset($info['block'])) {
            $this->_layout[$row][$col]['params']['type'] = $info['block'];
        }
        if (isset($info['params'])) {
            $this->_layout[$row][$col]['params']['params'] = $info['params'];
        }

        $this->_changed_row = $row;
        $this->_changed_col = $col;
    }

    /**
     * Returns the number of blocks in the current layout.
     *
     * @since Horde 3.1
     *
     * @return integer  The number of blocks.
     */
    function count()
    {
        $rows = $this->rows();
        $count = 0;

        for ($row = 0; $row < $rows; $row++) {
            $cols = $this->columns($row);
            for ($col = 0; $col < $cols; $col++) {
                if (!$this->isEmpty($row, $col) &&
                    !$this->isCovered($row, $col)) {
                    $count++;
                }
            }
        }

        return $count;
    }

    /**
     * Returns the number of rows in the current layout.
     *
     * @return integer  The number of rows.
     */
    function rows()
    {
        return count($this->_layout);
    }

    /**
     * Returns the number of columns in the specified row of the
     * current layout.
     *
     * @param integer $row  The row to return the number of columns from.
     *
     * @return integer  The number of columns.
     */
    function columns($row)
    {
        if (!isset($this->_layout[$row])) {
            return PEAR::raiseError(sprintf(_("The specified row (%d) does not exist."), $row), 'horde.error');
        }
        return count($this->_layout[$row]);
    }

    /**
     * Checks to see if a given location if being used by a block
     *
     * @param integer $row  A layout row.
     * @param integer $col  A layout column.
     *
     * @return boolean  True if the location is empty
     *                  False is the location is being used.
     */
    function isEmpty($row, $col)
    {
        return !isset($this->_layout[$row][$col]) || $this->_layout[$row][$col] == 'empty';
    }

    /**
     * Returns if the field at the specified position is covered by
     * another block.
     *
     * @param integer $row  A layout row.
     * @param integer $col  A layout column.
     *
     * @return boolean  True if the specified field is covered.
     */
    function isCovered($row, $col)
    {
        return isset($this->_layout[$row][$col]) ? $this->_layout[$row][$col] == 'covered' : false;
    }

    /**
     * Returns if the specified location is the top left field of
     * a block.
     *
     * @param integer $row  A layout row.
     * @param integer $col  A layout column.
     *
     * @return boolean  True if the specified position is a block, false if
     *                  the field doesn't exist, is empty or covered.
     */
    function isBlock($row, $col)
    {
        return $this->rowExists($row) && $this->colExists($col) &&
            !$this->isEmpty($row, $col) && !$this->isCovered($row, $col);
    }

    /**
     * Returns if the specified block has been changed last.
     *
     * @param integer $row  A layout row.
     * @param integer $col  A layout column.
     *
     * @return boolean  True if this block is the last one that was changed.
     */
    function isChanged($row, $col)
    {
        return $this->_changed_row === $row && $this->_changed_col === $col;
    }

    /**
     * Returns a control (linked arrow) for a certain action on the
     * specified block.
     *
     * @param string $type  A control type in the form
     *                      "modification/direction". Possible values for
     *                      modification: expand, shrink, move. Possible values
     *                      for direction: up, down, left, right.
     * @param integer $row  A layout row.
     * @param integer $col  A layout column.
     *
     * @return string  A link containing an arrow representing the requested
     *                 control.
     */
    function getControl($type, $row, $col)
    {
        $type = explode('/', $type);
        $action = $type[0] . ucfirst($type[1]);
        $url = $this->getActionUrl($action, $row, $col);

        switch ($type[0]) {
        case 'expand':
            $title = _("Expand");
            $img = 'large_' . $type[1];
            break;

        case 'shrink':
            $title = _("Shrink");
            $img = 'large_';

            switch ($type[1]) {
            case 'up':
                $img .= 'down';
                break;

            case 'down':
                $img .= 'up';
                break;

            case 'left':
                $img .= 'right';
                break;

            case 'right':
                $img .= 'left';
                break;
            }
            break;

        case 'move':
            switch ($type[1]) {
            case 'up':
                $title = _("Move Up");
                break;

            case 'down':
                $title = _("Move Down");
                break;

            case 'left':
                $title = _("Move Left");
                break;

            case 'right':
                $title = _("Move Right");
                break;
            }

            $img = $type[1];
            break;
        }

        return Horde::link($url, $title) .
            Horde::img('block/' . $img . '.png', $title, '', $GLOBALS['registry']->getImageDir('horde')) . '</a>';
    }

    /**
     * Does a row exist?
     *
     * @param integer $row  The row to look for
     *
     * @return boolean  True if the row exists
     */
    function rowExists($row)
    {
        return $row < count($this->_layout);
    }

    /**
     * Does a column exist?
     *
     * @param integer $col  The column to look for
     *
     * @return boolean  True if the column exists
     */
    function colExists($col)
    {
        return $col < $this->_columns;
    }

    /**
     * Get the width of the block at a given location.
     * This returns the width if there is a block at this
     * location, otherwise returns 1.
     *
     * @param integer $row  A layout row.
     * @param integer $col  A layout column.
     *
     * @return integer  The number of columns this block spans
     */
    function getWidth($row, $col)
    {
        if (!isset($this->_layout[$row][$col]) ||
            !is_array($this->_layout[$row][$col])) {
            return 1;
        }
        if (!isset($this->_layout[$row][$col]['width'])) {
            $this->_layout[$row][$col]['width'] = 1;
        }
        return $this->_layout[$row][$col]['width'];
    }

    /**
     * Get the height of the block at a given location.
     * This returns the height if there is a block at this
     * location, otherwise returns 1.
     *
     * @param integer $row  A layout row.
     * @param integer $col  A layout column.
     *
     * @return integer  The number of rows this block spans
     */
    function getHeight($row, $col)
    {
        if (!isset($this->_layout[$row][$col]) ||
            !is_array($this->_layout[$row][$col])) {
            return 1;
        }
        if (!isset($this->_layout[$row][$col]['height'])) {
            $this->_layout[$row][$col]['height'] = 1;
        }
        return $this->_layout[$row][$col]['height'];
    }

    /**
     * Adds an empty block at the specified position.
     *
     * @param integer $row  A layout row.
     * @param integer $col  A layout column.
     */
    function addBlock($row, $col)
    {
        if (!$this->rowExists($row)) {
            $this->addRow($row);
        }
        if (!$this->colExists($col)) {
            $this->addCol($col);
        }

        $this->_layout[$row][$col] = array('app' => null,
                                           'height' => 1,
                                           'width' => 1,
                                           'params' => array('type' => null,
                                                             'params' => array()));
    }

    /**
     * Adds a new row to the layout.
     *
     * @param integer $row  The number of the row to add
     */
    function addRow($row)
    {
        if ($this->_columns > 0) {
            $this->_layout[$row] = array_fill(0, $this->_columns, 'empty');
        }
    }

    /**
     * Adds a new column to the layout.
     *
     * @param integer $col  The number of the column to add
     */
    function addCol($col)
    {
        foreach ($this->_layout as $id => $val) {
            $this->_layout[$id][$col] = 'empty';
        }
        $this->_columns++;
    }

    /**
     * Removes a block.
     *
     * @param integer $row  A layout row.
     * @param integer $col  A layout column.
     */
    function removeBlock($row, $col)
    {
        $width = $this->getWidth($row, $col);
        $height = $this->getHeight($row, $col);
        for ($i = $height - 1; $i >= 0; $i--) {
            for ($j = $width - 1; $j >= 0; $j--) {
                $this->_layout[$row + $i][$col + $j] = 'empty';
                if (!$this->colExists($col + $j + 1)) {
                    $this->removeColIfEmpty($col + $j);
                }
            }
            if (!$this->rowExists($row + $i + 1) && $this->rowExists($row + $i)) {
                $this->removeRowIfEmpty($row + $i);
            }
        }

        $this->_changed_row = $row;
        $this->_changed_col = $col;

        if (!$this->rowExists($row)) {
            $row--;
            while ($row >= 0 && $this->removeRowIfEmpty($row)) {
                $row--;
            }
        }
        if (!$this->colExists($col)) {
            $col--;
            while ($col >= 0 && $this->removeColIfEmpty($col)) {
                $col--;
            }
        }
    }

    /**
     * Removes a row if it's empty.
     *
     * @param integer $row  The number of the row to to check
     *
     * @return boolean  True if the row is now removed.
     *                  False if the row still exists.
     */
    function removeRowIfEmpty($row)
    {
        if (!$this->rowExists($row)) {
            return true;
        }

        $rows = count($this->_layout[$row]);
        for ($i = 0; $i < $rows; $i++) {
            if (isset($this->_layout[$row][$i]) && $this->_layout[$row][$i] != 'empty') {
                return false;
            }
        }
        unset($this->_layout[$row]);

        return true;
    }

    /**
     * Removes a column if it's empty.
     *
     * @param integer $col  The number of the column to to check
     *
     * @return boolean  True if the column is now removed.
     *                  False if the column still exists.
     */
    function removeColIfEmpty($col)
    {
        if (!$this->colExists($col)) {
            return true;
        }

        $cols = count($this->_layout);
        for ($i = 0; $i < $cols; $i++) {
            if (isset($this->_layout[$i][$col]) && $this->_layout[$i][$col] != 'empty') {
                return false;
            }
        }

        for ($i = 0; $i < $cols; $i++) {
            unset($this->_layout[$i][$col]);
        }

        return true;
    }

    /**
     * Moves a block one row up.
     *
     * @param integer $row  A layout row.
     * @param integer $col  A layout column.
     */
    function moveUp($row, $col)
    {
        if ($this->rowExists($row - 1)) {
            $width = $this->getWidth($row, $col);
            // See if there's room to move into
            for ($i = 0; $i < $width; $i++) {
                if (!$this->isEmpty($row - 1, $col + $i)) {
                    $in_way = $this->getBlockAt($row - 1, $col + $i);
                    if (!is_null($in_way) &&
                        $in_way[1] == $col &&
                        $this->getWidth($in_way[0], $in_way[1]) == $width) {
                        // We need to swap the blocks.
                        $rec1 = Horde_Array::getRectangle($this->_layout, $row, $col,
                                                          $this->getHeight($row, $col), $this->getWidth($row, $col));
                        $rec2 = Horde_Array::getRectangle($this->_layout, $in_way[0], $in_way[1],
                                                          $this->getHeight($in_way[0], $in_way[1]), $this->getWidth($in_way[0], $in_way[1]));
                        for ($j = 0; $j < count($rec1); $j++) {
                            for ($k = 0; $k < count($rec1[$j]); $k++) {
                                $this->_layout[$in_way[0] + $j][$in_way[1] + $k] = $rec1[$j][$k];
                            }
                        }
                        for ($j = 0; $j < count($rec2); $j++) {
                            for ($k = 0; $k < count($rec2[$j]); $k++) {
                                $this->_layout[$in_way[0] + count($rec1) + $j][$in_way[1] + $k] = $rec2[$j][$k];
                            }
                        }
                        $this->_changed_row = $in_way[0];
                        $this->_changed_col = $in_way[1];
                        return;
                    }
                    // Nowhere to go.
                    return PEAR::raiseError(_("Shrink or move neighbouring block(s) out of the way first"), 'horde.warning');
                }
            }

            $lastrow = $row + $this->getHeight($row, $col) - 1;
            for ($i = 0; $i < $width; $i++) {
                $prev = $this->_layout[$row][$col + $i];
                // Move top edge
                $this->_layout[$row - 1][$col + $i] = $prev;
                $this->_layout[$row][$col + $i] = 'covered';
                // Move bottom edge
                $this->_layout[$lastrow][$col + $i] = 'empty';
            }

            if (!$this->rowExists($lastrow + 1)) {
                // Was on the bottom row
                $this->removeRowIfEmpty($lastrow);
            }
        }

        $this->_changed_row = $row - 1;
        $this->_changed_col = $col;
    }

    /**
     * Moves a block one row down.
     *
     * @param integer $row  A layout row.
     * @param integer $col  A layout column.
     */
    function moveDown($row, $col)
    {
        $width = $this->getWidth($row, $col);
        $lastrow = $row + $this->getHeight($row, $col);
        if ($this->rowExists($lastrow)) {
            // See if there's room to move into
            for ($i = 0; $i < $width; $i++) {
                if (!$this->isEmpty($lastrow, $col + $i)) {
                    $in_way = $this->getBlockAt($lastrow, $col + $i);
                    if (!is_null($in_way) &&
                        $in_way[1] == $col &&
                        $this->getWidth($in_way[0], $in_way[1]) == $width) {
                        // We need to swap the blocks.
                        $rec1 = Horde_Array::getRectangle($this->_layout, $row, $col,
                                                          $this->getHeight($row, $col), $this->getWidth($row, $col));
                        $rec2 = Horde_Array::getRectangle($this->_layout, $in_way[0], $in_way[1],
                                                          $this->getHeight($in_way[0], $in_way[1]), $this->getWidth($in_way[0], $in_way[1]));
                        for ($j = 0; $j < count($rec2); $j++) {
                            for ($k = 0; $k < count($rec2[$j]); $k++) {
                                $this->_layout[$row + $j][$col + $k] = $rec2[$j][$k];
                            }
                        }
                        for ($j = 0; $j < count($rec1); $j++) {
                            for ($k = 0; $k < count($rec1[$j]); $k++) {
                                $this->_layout[$row + count($rec2) + $j][$col + $k] = $rec1[$j][$k];
                            }
                        }
                        $this->_changed_row = $in_way[0];
                        $this->_changed_col = $in_way[1];
                        return;
                    }
                    // No where to go
                    return PEAR::raiseError(_("Shrink or move neighbouring block(s) out of the way first"), 'horde.warning');
                }
            }
        } else {
            // Make room to move into
            $this->addRow($lastrow);
        }

        for ($i = 0; $i < $width; $i++) {
            if (!isset($this->_layout[$row][$col + $i])) {
                continue;
            }
            $prev = $this->_layout[$row][$col + $i];
            // Move bottom edge
            $this->_layout[$lastrow][$col + $i] = 'covered';
            // Move top edge
            $this->_layout[$row + 1][$col + $i] = $prev;
            $this->_layout[$row][$col + $i] = 'empty';
        }

        $this->_changed_row = $row + 1;
        $this->_changed_col = $col;
    }

    /**
     * Moves all blocks below a certain row one row down.
     *
     * @param integer $row  A layout row.
     *
     * @return boolean  True if all rows could be moved down.
     */
    function moveDownBelow($row)
    {
        $moved = array();
        for ($y = count($this->_layout) - 1; $y > $row; $y--) {
            for ($x = 0; $x < $this->_columns; $x++) {
                $block = $this->getBlockAt($y, $x);
                if (empty($block)) {
                    continue;
                }
                if (empty($moved[$block[1] . ':' . $block[0]])) {
                    $result = $this->moveDown($block[0], $block[1]);
                    if (is_a($result, 'PEAR_Error')) {
                        return false;
                    }
                    $moved[$block[1] . ':' . ($block[0] + 1)] = true;
                }
            }
        }
        return true;
    }

    /**
     * Moves a block one column left.
     *
     * @param integer $row  A layout row.
     * @param integer $col  A layout column.
     */
    function moveLeft($row, $col)
    {
        if ($this->colExists($col - 1)) {
            $height = $this->getHeight($row, $col);
            // See if there's room to move into.
            for ($i = 0; $i < $height; $i++) {
                if (!$this->isEmpty($row + $i, $col - 1)) {
                    $in_way = $this->getBlockAt($row + $i, $col - 1);
                    if (!is_null($in_way) &&
                        $in_way[0] == $row &&
                        $this->getHeight($in_way[0], $in_way[1]) == $height) {
                        // We need to swap the blocks.
                        $rec1 = Horde_Array::getRectangle($this->_layout, $row, $col,
                                                          $this->getHeight($row, $col), $this->getWidth($row, $col));
                        $rec2 = Horde_Array::getRectangle($this->_layout, $in_way[0], $in_way[1],
                                                          $this->getHeight($in_way[0], $in_way[1]), $this->getWidth($in_way[0], $in_way[1]));
                        for ($j = 0; $j < count($rec1); $j++) {
                            for ($k = 0; $k < count($rec1[$j]); $k++) {
                                $this->_layout[$in_way[0] + $j][$in_way[1] + $k] = $rec1[$j][$k];
                            }
                        }
                        for ($j = 0; $j < count($rec2); $j++) {
                            for ($k = 0; $k < count($rec2[$j]); $k++) {
                                $this->_layout[$in_way[0] + $j][$in_way[1] + count($rec1[$j]) + $k] = $rec2[$j][$k];
                            }
                        }
                        $this->_changed_row = $in_way[0];
                        $this->_changed_col = $in_way[1];
                        return;
                    }
                    // No where to go
                    return PEAR::raiseError(_("Shrink or move neighbouring block(s) out of the way first"), 'horde.warning');
                }
            }

            $lastcol = $col + $this->getWidth($row, $col) - 1;
            for ($i = 0; $i < $height; $i++) {
                if (!isset($this->_layout[$row + $i][$col])) {
                    continue;
                }
                $prev = $this->_layout[$row + $i][$col];
                // Move left hand edge
                $this->_layout[$row + $i][$col - 1] = $prev;
                $this->_layout[$row + $i][$col] = 'covered';
                // Move right hand edge
                $this->_layout[$row + $i][$lastcol] = 'empty';
            }

            if (!$this->colExists($lastcol + 1)) {
                // Was on the right-most column
                $this->removeColIfEmpty($lastcol);
            }

            $this->_changed_row = $row;
            $this->_changed_col = $col - 1;
        }
    }

    /**
     * Moves a block one column right.
     *
     * @param integer $row  A layout row.
     * @param integer $col  A layout column.
     */
    function moveRight($row, $col)
    {
        $height = $this->getHeight($row, $col);
        $lastcol = $col + $this->getWidth($row, $col);
        if ($this->colExists($lastcol)) {
            // See if there's room to move into.
            for ($i = 0; $i < $height; $i++) {
                if (!$this->isEmpty($row + $i, $lastcol)) {
                    $in_way = $this->getBlockAt($row + $i, $lastcol);
                    if (!is_null($in_way) &&
                        $in_way[0] == $row &&
                        $this->getHeight($in_way[0], $in_way[1]) == $height) {
                        // We need to swap the blocks.
                        $rec1 = Horde_Array::getRectangle($this->_layout, $row, $col,
                                                          $this->getHeight($row, $col), $this->getWidth($row, $col));
                        $rec2 = Horde_Array::getRectangle($this->_layout, $in_way[0], $in_way[1],
                                                          $this->getHeight($in_way[0], $in_way[1]), $this->getWidth($in_way[0], $in_way[1]));
                        for ($j = 0; $j < count($rec2); $j++) {
                            for ($k = 0; $k < count($rec2[$j]); $k++) {
                                $this->_layout[$row + $j][$col + $k] = $rec2[$j][$k];
                            }
                        }
                        for ($j = 0; $j < count($rec1); $j++) {
                            for ($k = 0; $k < count($rec1[$j]); $k++) {
                                $this->_layout[$row + $j][$col + count($rec2[$j]) + $k] = $rec1[$j][$k];
                            }
                        }
                        $this->_changed_row = $in_way[0];
                        $this->_changed_col = $in_way[1];
                        return;
                    }
                    // No where to go
                    return PEAR::raiseError(_("Shrink or move neighbouring block(s) out of the way first"), 'horde.warning');
                }
            }
        } else {
            // Make room to move into.
            $this->addCol($lastcol);
        }

        for ($i = 0; $i < $height; $i++) {
            if (!isset($this->_layout[$row + $i][$col])) {
                continue;
            }
            $prev = $this->_layout[$row + $i][$col];
            // Move right hand edge
            $this->_layout[$row + $i][$lastcol] = 'covered';
            // Move left hand edge
            $this->_layout[$row + $i][$col + 1] = $prev;
            $this->_layout[$row + $i][$col] = 'empty';
        }

        $this->_changed_row = $row;
        $this->_changed_col = $col + 1;
    }

    /**
     * Moves all blocks after a certain column one column right.
     *
     * @param integer $col  A layout column.
     *
     * @return boolean  True if all columns could be moved right.
     */
    function moveRightAfter($col)
    {
        $moved = array();
        for ($x = $this->_columns - 1; $x > $col; $x--) {
            for ($y = 0; $y < count($this->_layout); $y++) {
                $block = $this->getBlockAt($y, $x);
                if (empty($block)) {
                    continue;
                }
                if (empty($moved[$block[1] . ':' . $block[0]])) {
                    $result = $this->moveRight($block[0], $block[1]);
                    if (is_a($result, 'PEAR_Error')) {
                        return false;
                    }
                    $moved[($block[1] + 1) . ':' . $block[0]] = true;
                }
            }
        }
        return true;
    }

    /**
     * Makes a block one row taller by moving the top up.
     *
     * @param integer $row  A layout row.
     * @param integer $col  A layout column.
     */
    function expandUp($row, $col)
    {
        if ($this->rowExists($row - 1)) {
            $width = $this->getWidth($row, $col);
            // See if there's room to expand into
            for ($i = 0; $i < $width; $i++) {
                if (!$this->isEmpty($row - 1, $col + $i)) {
                    if (!$this->moveDownBelow($row - 1)) {
                        return PEAR::raiseError(_("Shrink or move neighbouring block(s) out of the way first"), 'horde.warning');
                    } else {
                        $row++;
                    }
                }
            }

            for ($i = 0; $i < $width; $i++) {
                $this->_layout[$row - 1][$col + $i] = $this->_layout[$row][$col + $i];
                $this->_layout[$row][$col + $i] = 'covered';
            }
            $this->_layout[$row - 1][$col]['height'] = $this->getHeight($row - 1, $col) + 1;

            $this->_changed_row = $row - 1;
            $this->_changed_col = $col;
        }
    }

    /**
     * Makes a block one row taller by moving the bottom down.
     *
     * @param integer $row  A layout row.
     * @param integer $col  A layout column.
     */
    function expandDown($row, $col)
    {
        $width = $this->getWidth($row, $col);
        $lastrow = $row + $this->getHeight($row, $col) - 1;
        if (!$this->rowExists($lastrow + 1)) {
            // Add a new row.
            $this->addRow($lastrow + 1);
            for ($i = 0; $i < $width; $i++) {
                $this->_layout[$lastrow + 1][$col + $i] = 'covered';
            }
            $this->_layout[$row][$col]['height'] = $this->getHeight($row, $col) + 1;
        } else {
            // See if there's room to expand into
            for ($i = 0; $i < $width; $i++) {
                if (!$this->isEmpty($lastrow + 1, $col + $i)) {
                    if (!$this->moveDownBelow($lastrow)) {
                        return PEAR::raiseError(_("Shrink or move neighbouring block(s) out of the way first"), 'horde.warning');
                    }
                }
            }

            for ($i = 0; $i < $width; $i++) {
                $this->_layout[$lastrow + 1][$col + $i] = 'covered';
            }
            $this->_layout[$row][$col]['height'] = $this->getHeight($row, $col) + 1;
        }

        $this->_changed_row = $row;
        $this->_changed_col = $col;
    }

    /**
     * Makes a block one column wider by moving the left side out.
     *
     * @param integer $row  A layout row.
     * @param integer $col  A layout column.
     */
    function expandLeft($row, $col)
    {
        if ($this->colExists($col - 1)) {
            $height = $this->getHeight($row, $col);
            // See if there's room to expand into
            for ($i = 0; $i < $height; $i++) {
                if (!$this->isEmpty($row + $i, $col - 1)) {
                    if (!$this->moveRightAfter($col - 1)) {
                        return PEAR::raiseError(_("Shrink or move neighbouring block(s) out of the way first"), 'horde.warning');
                    } else {
                        $col++;
                    }
                }
            }

            for ($i = 0; $i < $height; $i++) {
                $this->_layout[$row + $i][$col - 1] = $this->_layout[$row + $i][$col];
                $this->_layout[$row + $i][$col] = 'covered';
            }
            $this->_layout[$row][$col - 1]['width'] = $this->getWidth($row, $col - 1) + 1;

            $this->_changed_row = $row;
            $this->_changed_col = $col - 1;
        }
    }

    /**
     * Makes a block one column wider by moving the right side out.
     *
     * @param integer $row  A layout row.
     * @param integer $col  A layout column.
     */
    function expandRight($row, $col)
    {
        $height = $this->getHeight($row, $col);
        $lastcol = $col + $this->getWidth($row, $col) - 1;
        if ($this->colExists($lastcol + 1)) {
            // See if there's room to expand into
            for ($i = 0; $i < $height; $i++) {
                if (!$this->isEmpty($row + $i, $lastcol + 1)) {
                    if (!$this->moveRightAfter($lastcol)) {
                        return PEAR::raiseError(_("Shrink or move neighbouring block(s) out of the way first"), 'horde.warning');
                    }
                }
            }

            for ($i = 0; $i < $height; $i++) {
                $this->_layout[$row + $i][$lastcol + 1] = 'covered';
            }
            $this->_layout[$row][$col]['width'] = $this->getWidth($row, $col) + 1;
        } else {
            // Add new column
            $this->addCol($lastcol + 1);
            for ($i = 0; $i < $height; $i++) {
                $this->_layout[$row + $i][$lastcol + 1] = 'covered';
            }
            $this->_layout[$row][$col]['width'] = $this->getWidth($row, $col) + 1;
        }

        $this->_changed_row = $row;
        $this->_changed_col = $col;
    }

    /**
     * Makes a block one row lower by moving the top down.
     *
     * @param integer $row  A layout row.
     * @param integer $col  A layout column.
     */
    function shrinkUp($row, $col)
    {
        if ($this->getHeight($row, $col) > 1) {
            $width = $this->getWidth($row, $col);
            for ($i = 0; $i < $width; $i++) {
                $this->_layout[$row + 1][$col + $i] = $this->_layout[$row][$col + $i];
                $this->_layout[$row][$col + $i] = 'empty';
            }
            $this->_layout[$row + 1][$col]['height'] = $this->getHeight($row + 1, $col) - 1;

            $this->_changed_row = $row + 1;
            $this->_changed_col = $col;
        }
    }

    /**
     * Makes a block one row lower by moving the bottom up.
     *
     * @param integer $row  A layout row.
     * @param integer $col  A layout column.
     */
    function shrinkDown($row, $col)
    {
        if ($this->getHeight($row, $col) > 1) {
            $lastrow = $row + $this->getHeight($row, $col) - 1;
            $width = $this->getWidth($row, $col);
            for ($i = 0; $i < $width; $i++) {
                $this->_layout[$lastrow][$col + $i] = 'empty';
            }
            $this->_layout[$row][$col]['height'] = $this->getHeight($row, $col) - 1;
            if (!$this->rowExists($lastrow + 1)) {
                // Was on the bottom row
                $this->removeRowIfEmpty($lastrow);
            }

            $this->_changed_row = $row;
            $this->_changed_col = $col;
        }
    }

    /**
     * Makes a block one column narrower by moving the left side in.
     *
     * @param integer $row  A layout row.
     * @param integer $col  A layout column.
     */
    function shrinkLeft($row, $col)
    {
        if ($this->getWidth($row, $col) > 1) {
            $height = $this->getHeight($row, $col);
            for ($i = 0; $i < $height; $i++) {
                $this->_layout[$row + $i][$col + 1] = $this->_layout[$row + $i][$col];
                $this->_layout[$row + $i][$col] = 'empty';
            }
            $this->_layout[$row][$col + 1]['width'] = $this->getWidth($row, $col + 1) - 1;

            $this->_changed_row = $row;
            $this->_changed_col = $col + 1;
        }
    }

    /**
     * Makes a block one column narrower by moving the right side in.
     *
     * @param integer $row  A layout row.
     * @param integer $col  A layout column.
     */
    function shrinkRight($row, $col)
    {
        if ($this->getWidth($row, $col) > 1) {
            $lastcol = $col + $this->getWidth($row, $col) - 1;
            $height = $this->getHeight($row, $col);
            for ($i = 0; $i < $height; $i++) {
                $this->_layout[$row + $i][$lastcol] = 'empty';
            }
            $this->_layout[$row][$col]['width'] = $this->getWidth($row, $col) - 1;
            $this->removeColIfEmpty($lastcol);

            $this->_changed_row = $row;
            $this->_changed_col = $col;
        }
    }

}
