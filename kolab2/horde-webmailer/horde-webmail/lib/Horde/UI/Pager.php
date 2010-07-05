<?php

require_once dirname(__FILE__) . '/Widget.php';

/**
 * The Horde_UI_Pager:: provides links to individual pages.
 *
 * $Horde: framework/UI/UI/Pager.php,v 1.7.10.16 2009-01-06 15:23:45 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Ben Chavet <ben@chavet.net>
 * @author  Joel Vandal <joel@scopserv.com>
 * @author  Chuck Hagenbuch <chuck@horde.org>
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

        $html = '<div class="pager">';

        if ($current_page > 0) {
            // Create the '<< Prev' link if we are not on the first page.
            $link = Util::addParameter($url, $this->_name, $current_page - 1);
            $link = $this->_addPreserved($link);
            $link = $this->_link($link);
            if (isset($this->_config['previousHTML'])) {
                $html .= Horde::link($link, '', 'prev') . $this->_config['previousHTML'] . '</a>';
            } else {
                $html .= Horde::link($link, '', 'prev') . htmlspecialchars(_("<Previous")) . '</a>';
            }
        }

        // Figure out the top & bottom display limits.
        $bottom = max(0, $current_page - ($page_limit / 2) + 1);
        $top = $bottom + $page_limit - 1;
        if ($top - 1 > $pages) {
            $bottom -= ($top - 1) - $pages;
            $top = $pages + 1;
        }

        // Create bottom '[x-y]' link if necessary.
        $link = $this->_addPreserved(Util::addParameter($url, $this->_name, $bottom - 1));
        $link = $this->_link($link);

        if ($bottom > 0) {
            $html .= ' ' . Horde::link($link, '', 'prevRange') . '[' . ($bottom == 1 ? $bottom : '1-' . $bottom) . ']</a>';
        }

        // Create links to individual pages between limits.
        for ($i = $bottom; $i <= $top && $i <= $pages; ++$i) {
            if ($i == $current_page) {
                $html .= ' <strong>(' . ($i + 1) . ')</strong>';
            } elseif ($i >= 0 && $i <= $pages) {
                $link = $this->_addPreserved(Util::addParameter($url, $this->_name, $i));
                $link = $this->_link($link);
                $html .= ' ' . Horde::link($link) . ($i + 1) . '</a>';
            }
        }

        // Create top '[x-y]' link if necessary.
        if ($top < $pages) {
            $link = $this->_addPreserved(Util::addParameter($url, $this->_name, $top + 1));
            $link = $this->_link($link);

            $html .= ' ' . Horde::link($link, '', 'nextRange') . '[' .
                ($top + 2 == $pages + 1 ? $pages + 1 : ($top + 2) . '-' . ($pages + 1)) . ']</a>';
        }

        // Create the 'Next>>' link if we are not on the last page.
        if ($current_page < $pages) {
            $link = $this->_addPreserved(Util::addParameter($url, $this->_name, $current_page + 1));
            $link = $this->_link($link);
            if (isset($this->_config['nextHTML'])) {
                $html .= Horde::link($link, '', 'next') . $this->_config['nextHTML'] . '</a>';
            } else {
                $html .= ' ' . Horde::link($link, '', 'next') . htmlspecialchars(_("Next>")) . '</a>';
            }
        }

        return $html . '</div>';
    }

}
