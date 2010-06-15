<?php
/**
 * $Horde: horde/lib/Block/iframe.php,v 1.12 2004/05/29 16:21:03 jan Exp $
 *
 * @package Horde_Block
 */
class Horde_Block_iframe extends Horde_Block {

    var $_app = 'horde';

    function getParams()
    {
        return array('iframe' => array('type' => 'text',
                                       'name' => _("URL"),
                                       'default' => 'http://slashdot.org/'),
                     'title'  => array('type' => 'text',
                                       'name' => _("Title")));
    }

    /**
     * The title to go in this block.
     *
     * @return string   The title text.
     */
    function _title()
    {
        global $registry;

        $title = isset($this->_params['title']) ? $this->_params['title'] :$this->_params['iframe'];

        $html  = Horde::link($this->_params['iframe'], $title, 'header') . $title . '</a>';
        $html .= Horde::link($this->_params['iframe'], _("Open in a new window"), 'smallheader', '_new') . Horde::img('webserver.gif', _("Open in a new window"), 'hspace="5"', Horde::url($registry->getParam('graphics'), true, -1)) . _("Open in a new window") . '</a>';

        return $html;
    }

    /**
     * The content to go in this block.
     *
     * @return string   The content
     */
    function _content()
    {
        global $browser;

        if (!$browser->hasFeature('iframes')) {
            $html = _("Your browser does not support this feature.");
        } else {
            if ($browser->isBrowser('msie') || $browser->isBrowser('konqueror')) {
                $height = '';
            } else {
                $height = ' height="100%"';
            }
            $html = '<iframe src="' . htmlspecialchars($this->_params['iframe']) . '" width="100%"' . $height . ' marginheight="0" scrolling="yes" frameborder="0"></iframe>';
        }
        return $html;
    }

}
