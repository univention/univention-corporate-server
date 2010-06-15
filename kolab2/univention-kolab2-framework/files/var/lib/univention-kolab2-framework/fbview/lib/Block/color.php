<?php
/**
 * $Horde: horde/lib/Block/color.php,v 1.9 2004/05/29 16:21:03 jan Exp $
 *
 * @package Horde_Block
 */
class Horde_Block_color extends Horde_Block {

    var $_app = 'horde';

    function getParams()
    {
        return array('type' => 'text',
                     'name' => _("Color"),
                     'default' => '#ff0000');
    }

    /**
     * The title to go in this block.
     *
     * @return string   The title text.
     */
    function _title()
    {
        return _("Color");
    }

    /**
     * The content to go in this block.
     *
     * @return string   The content
     */
    function _content()
    {
        $html  = '<table width="100" height="100" bgcolor="%s">';
        $html .= '<tr><td>&nbsp;</td></tr>';
        $html .= '</table>';

        return sprintf($html, $this->_params['color']);
    }

}
