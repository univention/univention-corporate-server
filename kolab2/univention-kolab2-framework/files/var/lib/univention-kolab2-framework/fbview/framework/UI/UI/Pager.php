<?php

require_once dirname(__FILE__) . '/Widget.php';

/**
 * The Horde_UI_Pager:: provides links to individual pages.
 *
 * $Horde: framework/UI/UI/Pager.php,v 1.5 2004/02/25 19:12:35 eraserhd Exp $
 *
 * Copyright 2004 Joel Vandal <jvandal@infoteck.qc.ca>
 *
 * See the enclosed file LICENSE for license information (BSD). If you
 * did not receive this file, see http://www.horde.org/licenses/bsdl.php.
 *
 * @author  Ben Chavet <ben@chavet.net>
 * @author  Joel Vandal <jvandal@infoteck.qc.ca>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde_UI 0.0.1
 * @package Horde_UI
 */
class Horde_UI_Pager extends Horde_UI_Widget {

    function Horde_UI_Pager($name, &$vars, $config)
    {
        if (!isset($config['page_limit'])) {
            $config['page_limit'] = 10;
        }
        if (!isset($config['perpage'])) {
            $config['perpage'] = 100;
        }
        parent::Horde_UI_Widget($name, $vars, $config);
    }

    /**
     * Render the pager.
     *
     * @return string  HTML code containing a centered table with the pager
     *      links.
     */
    function render()
    {
        global $prefs, $registry, $conf;

        $num = $this->_config['num'];
        $url = $this->_config['url'];
        $page_limit = $this->_config['page_limit'];
        $perpage = $this->_config['perpage'];

        $current_page = $this->_vars->get($this->_name);

        // Figure out how many pages there will be.
        $pages = ($num / $perpage);
        if (is_integer($pages)) {
            $pages--;
        }
        $pages = (int)$pages;

        // Return nothing if there is only one page.
        if ($pages == 0 || $num == 0) {
            return '';
        }

        $html = '<table cellpadding="2" align="center" border="0" cellspacing="1"><tr>';

        // Create the '<< Prev' link if we are not on the first page.
        $link = Util::addParameter($url, $this->_name, $current_page - 1);
        $link = $this->_addPreserved($link);
        if ($current_page > 0) {
            $html .= '<td>' . Horde::link(Horde::applicationUrl($link),
                                          _("Previous Page"));
            $html .= Horde::img('nav/left.gif', _("Previous Page"),
                                'width="16" height="16" align="middle"',
                                $registry->getParam('graphics', 'horde')) .
                     '</a></td>';
        }

        // Figure out the top & bottom display limits.
        $bottom = $current_page - ($current_page % $page_limit);
        $top = $bottom + $page_limit - 1;

        // Create bottom '[x-y]' link if necessary.
        $link = Util::addParameter($url, $this->_name, $bottom - 1);
        $link = $this->_addPreserved($link);
        if ($bottom > 1) {
            $html .= '<td>' . Horde::link(Horde::applicationUrl($link)) . '[' . ($bottom - $page_limit + 1) . '-' . $bottom . ']</a></td>';
        }

        // Create links to individual pages between limits.
        for ($i = $bottom; $i <= $top && $i <= $pages; $i++) {
            if ($i == $current_page) {
                $html .= '<td><b>(' . ($i + 1) . ')</b></td>';
            } elseif ($i >= 0 && $i <= $pages) {
                $link = Util::addParameter($url, $this->_name, $i);
                $link = $this->_addPreserved($link);
                $html .= '<td>' . Horde::link(Horde::applicationUrl($link)) .
                         ($i + 1) . '</a></td>';
            }
        }

        // Create top '[x-y]' link if necessary.
        if ($top < $pages) {
            $last = $top + $page_limit < $pages ? $top + $page_limit + 1 : $pages + 1;
            $link = Util::addParameter($url, $this->_name, $top + 1);
            $link = $this->_addPreserved($link);
            $html .= '<td>' . Horde::link(Horde::applicationUrl($link)) . '[' .
                     ($top + 2) . '-' . $last . ']</a></td>';
        }

        // Create the 'Next>>' link if we are not on the last page.
        if ($current_page < $pages) {
            $link = Util::addParameter($url, $this->_name, $current_page + 1);
            $link = $this->_addPreserved($link);
            $html .= '<td>' . Horde::link(Horde::applicationUrl($link),
                                          _("Next Page"));
            $html .= Horde::img('nav/right.gif', _("Next Page"),
                                'width="16" height="16" align="middle"',
                                $registry->getParam('graphics', 'horde'))
                     . '</a></td>';
        }

        $html .= '</tr></table>';

        return $html;
    }

}
