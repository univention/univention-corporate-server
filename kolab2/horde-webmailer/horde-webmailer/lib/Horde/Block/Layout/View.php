<?php

require_once 'Horde/Browser.php';
require_once 'Horde/Block/Collection.php';
require_once 'Horde/Block/Layout.php';

/**
 * The Horde_Block_Layout_View class represents the user defined portal layout.
 *
 * $Horde: framework/Block/Block/Layout/View.php,v 1.4.2.12 2009-01-06 15:22:53 jan Exp $
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
class Horde_Block_Layout_View extends Horde_Block_Layout {

    /**
     * The current block layout.
     *
     * @var array
     */
    var $_layout = array();

    /**
     * All applications used in this layout.
     *
     * @var array
     */
    var $_applications = array();

    /**
     * CSS link tags pulled out of block content.
     *
     * @var array
     */
    var $_linkTags = array();

    /**
     * Constructor.
     */
    function Horde_Block_Layout_View($layout = array(), $editUrl = '',
                                     $viewUrl = '')
    {
        $this->_layout = $layout;
        $this->_editUrl = $editUrl;
        $this->_viewUrl = $viewUrl;
    }

    /**
     * Render the current layout as HTML.
     *
     * @return string HTML layout.
     */
    function toHtml()
    {
        $browser = &Browser::singleton();
        $tplDir = $GLOBALS['registry']->get('templates', 'horde');
        $interval = $GLOBALS['prefs']->getValue('summary_refresh_time');

        $html = '<table class="nopadding" cellspacing="8" width="100%">';

        $covered = array();
        foreach ($this->_layout as $row_num => $row) {
            $width = floor(100 / count($row));
            $html .= '<tr>';
            foreach ($row as $col_num => $item) {
                if (isset($covered[$row_num]) && isset($covered[$row_num][$col_num])) {
                    continue;
                }
                if (is_array($item)) {
                    $this->_applications[$item['app']] = $item['app'];
                    $block = &Horde_Block_Collection::getBlock($item['app'], $item['params']['type'], $item['params']['params'], $row_num, $col_num);
                    $rowspan = $item['height'];
                    $colspan = $item['width'];
                    for ($i = 0; $i < $item['height']; $i++) {
                        if (!isset($covered[$row_num + $i])) {
                            $covered[$row_num + $i] = array();
                        }
                        for ($j = 0; $j < $item['width']; $j++) {
                            $covered[$row_num + $i][$col_num + $j] = true;
                        }
                    }
                    if (is_a($block, 'PEAR_Error')) {
                        $header = _("Error");
                        $content = $block->getMessage();
                        ob_start();
                        include $tplDir . '/portal/block.inc';
                        $html .= ob_get_clean();
                    } elseif (is_a($block, 'Horde_Block')) {
                        $header = $block->getTitle();
                        $content = $block->getContent();
                        if (is_a($content, 'PEAR_Error')) {
                            $content = $content->getMessage();
                        }
                        if ($browser->hasFeature('xmlhttpreq')) {
                            $refresh_time = isset($item['params']['params']['_refresh_time']) ? $item['params']['params']['_refresh_time'] : $interval;
                        }
                        ob_start();
                        include $tplDir . '/portal/block.inc';
                        $html .= ob_get_clean();
                    } else {
                        $html .= '<td width="' . ($width * $colspan) . '%">&nbsp;</td>';
                    }
                } else {
                    $html .= '<td width="' . ($width) . '%">&nbsp;</td>';
                }
            }
            $html .= '</tr>';
        }
        $html .= '</table>';

        // Strip any CSS <link> tags out of the returned content so
        // they can be handled seperately.
        if (preg_match_all('/<link .*?rel="stylesheet".*?\/>/', $html, $links)) {
            $html = str_replace($links[0], '', $html);
            $this->_linkTags = $links[0];
        }

        return $html;
    }

    /**
     * Get any link tags found in the view.
     */
    function getLinkTags()
    {
        return $this->_linkTags;
    }

    /**
     * Return a list of all the applications used by blocks in this layout.
     *
     * @return array List of applications.
     */
    function getApplications()
    {
        return array_keys($this->_applications);
    }

}
