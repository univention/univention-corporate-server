<?php

$block_name = _("Current Time");

/**
 * $Horde: horde/lib/Block/time.php,v 1.16.6.1 2007-12-20 15:01:36 jan Exp $
 *
 * @package Horde_Block
 */
class Horde_Block_Horde_time extends Horde_Block {

    /**
     * Whether this block has changing content.
     */
    var $updateable = true;

    /**
     * @var string
     */
    var $_app = 'horde';

    function _params()
    {
        return array('time' => array('type' => 'enum',
                                     'name' => _("Time format"),
                                     'default' => '24-hour',
                                     'values' => array('24-hour' => _("24 Hour Format"),
                                                       '12-hour' => _("12 Hour Format"))));
    }

    /**
     * The title to go in this block.
     *
     * @return string   The title text.
     */
    function _title()
    {
        return _("Current Time");
    }

    /**
     * The content to go in this block.
     *
     * @return string   The content.
     */
    function _content()
    {
        if (empty($this->_params['time'])) {
            $this->_params['time'] = '24-hour';
        }

        // Set the timezone variable, if available.
        NLS::setTimeZone();

        $html = '<div style="font-size:200%; font-weight:bold; text-align:center">' .
            strftime('%A, %B %d, %Y ');
        if ($this->_params['time'] == '24-hour') {
            $html .= strftime('%H:%M');
        } else {
            $html .= strftime('%I:%M %p');
        }
        return $html . '</div>';
    }

}
