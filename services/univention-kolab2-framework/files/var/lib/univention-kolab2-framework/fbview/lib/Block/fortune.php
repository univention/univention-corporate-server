<?php
/**
 * $Horde: horde/lib/Block/fortune.php,v 1.7 2004/05/29 16:21:03 jan Exp $
 *
 * @package Horde_Block
 */
class Horde_Block_fortune extends Horde_Block {

    var $_app = 'horde';

    /**
     * The title to go in this block.
     *
     * @return string   The title text.
     */
    function _title()
    {
        return _("Fortune");
    }

    /**
     * The content to go in this block.
     *
     * @return string   The content
     */
    function _content()
    {
        return nl2br(shell_exec($this->_params['fortune']));
    }

}
