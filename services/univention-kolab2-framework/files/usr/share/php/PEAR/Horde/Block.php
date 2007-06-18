<?php
/**
 * The abstract Horde_Block:: class represents a single block within
 * the Blocks framework.
 *
 * $Horde: framework/Block/Block.php,v 1.29 2004/05/29 16:31:51 jan Exp $
 *
 * Copyright 2003-2004 Mike Cochrane <mike@graftonhall.co.nz>
 * Copyright 2003-2004 Jan Schneider <jan@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @author  Jan Schneider <jan@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Block
 */
class Horde_Block {

    /**
     * Block specific parameters.
     *
     * @var array $_params
     */
    var $_params = array();

    /**
     * Application that this block originated from.
     *
     * @var string $_app
     */
    var $_app;

    /**
     * Constructor.
     *
     * @param array $params  Any parameters the block needs.
     */
    function Horde_Block($params = array()) 
    {
        $this->_params = $params;
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
        return array();
    }

    /**
     * Returns the text to go in the title of this block.
     *
     * This function handles the changing of current application as needed
     * so code is executed in the scope of the application the block
     * originated from.
     *
     * @return string  The title text
     */
    function getTitle()
    {
        global $registry;

        /* Switch application contexts, if necessary. Return an
         * error immediately if pushApp() fails. */
        $pushed = $registry->pushApp($this->_app);
        if (is_a($pushed, 'PEAR_Error')) {
            return $pushed->getMessage();
        }

        $title = $this->_title();

        /* If we changed application context in the course of this
         * call, undo that change now. */
        if ($pushed === true) {
            $registry->popApp();
        }

        return $title;
    }

    /**
     * Returns the content for this block.
     *
     * This function handles the changing of current application as needed
     * so code is executed in the scope of the application the block
     * originated from.
     *
     * @return string  The content
     */
    function getContent()
    {
        global $registry;

        /* Switch application contexts, if necessary. Return an error
         * immediately if pushApp() fails. */
        $pushed = $registry->pushApp($this->_app);
        if (is_a($pushed, 'PEAR_Error')) {
            return $pushed->getMessage();
        }

        $content = $this->_content();

        /* If we changed application context in the course of this
         * call, undo that change now. */
        if ($pushed === true) {
            $registry->popApp();
        }

        return $content;
    }

    /**
     * The title to go in this block.
     * This function should be defined in all subclasses of this class.
     *
     * @abstract
     * @return string   The title text.
     */
    function _title()
    {
        return 'No title';
    }

    /**
     * The content to go in this block.
     * This function should be defined in all subclasses of this class.
     *
     * @abstract
     * @return string   The content
     */
    function _content()
    {
        return 'No content';
    }

}
