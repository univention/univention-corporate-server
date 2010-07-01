<?php

/* Disable block if not using PHP 5.2+. */
if (version_compare(PHP_VERSION, '5.2', '>=')) {
    $block_name = _("Syndicated Feed");
}

/**
 * $Horde: horde/lib/Block/feed.php,v 1.1.2.1 2008-01-14 20:34:48 chuck Exp $
 *
 * @package Horde_Block
 */
class Horde_Block_Horde_feed extends Horde_Block {

    var $_app = 'horde';

    var $_feed = null;

    function _params()
    {
        return array('uri' => array('type' => 'text',
                                    'name' => _("Feed Address")),
                     'limit' => array('name' => _("Number of articles to display"),
                                      'type' => 'int',
                                      'default' => 10),
                     'interval' => array('name' => _("How many seconds before we check for new articles?"),
                                         'type' => 'int',
                                         'default' => 86400),
                     'details' => array('name' => _("Show extra detail?"),
                                        'type' => 'boolean',
                                        'default' => 20));
    }

    /**
     * The title to go in this block.
     *
     * @return string   The title text.
     */
    function _title()
    {
        $this->_read();
        if (is_a($this->_feed, 'Horde_Feed_Base')) {
            return $this->_feed->title();
        }

        return _("Feed");
    }

    /**
     * The content to go in this block.
     *
     * @return string   The content
     */
    function _content()
    {
        $this->_read();
        if (is_a($this->_feed, 'Horde_Feed_Base')) {
            $html = '';
            $count = 0;
            foreach ($this->_feed as $entry) {
                if ($count++ > $this->_params['limit']) {
                    break;
                }
                $html .= '<a href="' . $entry->link. '"';
                if (empty($this->_params['details'])) {
                    $html .= ' title="' . htmlspecialchars(strip_tags($entry->description())) . '"';
                }
                $html .= '>' . htmlspecialchars($entry->title) . '</a>';
                if (!empty($this->_params['details'])) {
                    $html .= '<br />' .  htmlspecialchars(strip_tags($entry->description())). "<br />\n";
                }
                $html .= '<br />';
            }
            return $html;
        } elseif (is_string($this->_feed)) {
            return $this->_feed;
        } else {
            return '';
        }
    }

    function _read()
    {
        if (empty($this->_params['uri'])) {
            return;
        }

        require_once dirname(__FILE__) . '/feed/reader.php';
        $this->_feed = Horde_Block_Horde_feed_reader::read(
            $this->_params['uri'],
            $this->_params['interval']
        );
    }

}
