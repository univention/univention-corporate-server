<?php
/**
 * The abstract Horde_Block:: class represents a single block within
 * the Blocks framework.
 *
 * $Horde: framework/Block/Block.php,v 1.33.10.11 2009-06-20 23:16:42 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.0
 * @package Horde_Block
 */
class Horde_Block {

    /**
     * Whether this block has changing content.
     */
    var $updateable = false;

    /**
     * Block specific parameters.
     *
     * @var array
     */
    var $_params = array();

    /**
     * The Block row.
     *
     * @since Horde 3.2
     * @var integer
     */
    var $_row;

    /**
     * The Block column.
     *
     * @since Horde 3.2
     * @var integer
     */
    var $_col;

    /**
     * Application that this block originated from.
     *
     * @var string
     */
    var $_app;

    /**
     * Constructor.
     *
     * @param array|boolean $params  Any parameters the block needs. If false,
     *                               the default parameter will be used.
     * @param integer $row           The block row. @since Horde 3.2.
     * @param integer $col           The block column. @since Horde 3.2.
     */
    function Horde_Block($params = array(), $row = null, $col = null)
    {
        // @todo: we can't simply merge the default values and stored values
        // because empty parameter values are not stored at all, so they would
        // always be overwritten by the defaults.
        if ($params === false) {
            $params = $this->getParams();
            foreach ($params as $name => $param) {
                $this->_params[$name] = $param['default'];
            }
        } else {
            $this->_params = $params;
        }
        $this->_row = $row;
        $this->_col = $col;
    }

    /**
     * Returns the application that this block belongs to.
     *
     * @return string  The application name.
     */
    function getApp()
    {
        return $this->_app;
    }

    /**
     * Returns any settable parameters for this block. This is a
     * static method. It does *not* reference $this->_params; that is
     * for runtime parameters (the choices made from these options).
     *
     * @static
     *
     * @return array  The block's configurable parameters.
     */
    function getParams()
    {
        global $registry;

        /* Switch application contexts, if necessary. Return an error
         * immediately if pushApp() fails. */
        $app_pushed = $registry->pushApp($this->_app);
        if (is_a($app_pushed, 'PEAR_Error')) {
            return $app_pushed->getMessage();
        }

        $params = $this->_params();

        /* If we changed application context in the course of this
         * call, undo that change now. */
        if ($app_pushed === true) {
            $registry->popApp();
        }

        return $params;
    }

    /**
     * Returns the text to go in the title of this block.
     *
     * This function handles the changing of current application as
     * needed so code is executed in the scope of the application the
     * block originated from.
     *
     * @return string  The block's title.
     */
    function getTitle()
    {
        global $registry;

        /* Switch application contexts, if necessary. Return an error
         * immediately if pushApp() fails. */
        $app_pushed = $registry->pushApp($this->_app);
        if (is_a($app_pushed, 'PEAR_Error')) {
            return $app_pushed->getMessage();
        }

        $title = $this->_title();

        /* If we changed application context in the course of this
         * call, undo that change now. */
        if ($app_pushed === true) {
            $registry->popApp();
        }

        return $title;
    }

    /**
     * Returns the content for this block.
     *
     * This function handles the changing of current application as
     * needed so code is executed in the scope of the application the
     * block originated from.
     *
     * @return string  The block's content.
     */
    function getContent()
    {
        global $registry;

        /* Switch application contexts, if necessary. Return an error
         * immediately if pushApp() fails. */
        $app_pushed = $registry->pushApp($this->_app);
        if (is_a($app_pushed, 'PEAR_Error')) {
            return $app_pushed->getMessage();
        }

        $content = $this->_content();

        /* If we changed application context in the course of this
         * call, undo that change now. */
        if ($app_pushed === true) {
            $registry->popApp();
        }

        return $content;
    }

    function buildTree(&$tree, $indent = 0, $parent = null)
    {
        global $registry;

        /* Switch application contexts, if necessary. Return an error
         * immediately if pushApp() fails. */
        $app_pushed = $registry->pushApp($this->_app);
        if (is_a($app_pushed, 'PEAR_Error')) {
            return $app_pushed->getMessage();
        }

        $this->_buildTree($tree, $indent, $parent);

        /* If we changed application context in the course of this
         * call, undo that change now. */
        if ($app_pushed === true) {
            $registry->popApp();
        }
    }

    /**
     * Returns the title to go in this block.
     *
     * @abstract
     *
     * @return string  The block title.
     */
    function _title()
    {
        return '';
    }

    /**
     * Returns the parameters needed by block.
     *
     * @abstract
     *
     * @return array  The block's parameters.
     */
    function _params()
    {
        return array();
    }

    /**
     * Returns this block's content.
     *
     * @abstract
     *
     * @return string  The block's content.
     */
    function _content()
    {
        return '';
    }

    /**
     * Returns this block's content.
     *
     * @abstract
     */
    function _buildTree(&$tree, $indent = 0, $parent = null)
    {
    }

}
