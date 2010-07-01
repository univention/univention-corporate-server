<?php

require_once dirname(__FILE__) . '/Widget.php';

/**
 * The Horde_UI_Tabs:: class manages and renders a tab-like interface.
 *
 * $Horde: framework/UI/UI/Tabs.php,v 1.27.6.14 2009-01-06 15:23:45 jan Exp $
 *
 * Copyright 2001-2003 Robert E. Coyle <robertecoyle@hotmail.com>
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jason M. Felice <jason.m.felice@gmail.com>
 * @since   Horde_UI 0.0.1
 * @package Horde_UI
 */
class Horde_UI_Tabs extends Horde_UI_Widget {

    /**
     * The array of tabs.
     *
     * @var array
     */
    var $_tabs = array();

    /**
     * Adds a tab to the interface.
     *
     * @param string $title  The text which appears on the tab.
     * @param string $link   The target page.
     * @param mixed $params  Either a string value to set the tab variable to,
     *                       or a hash of parameters. If an array, the tab
     *                       variable can be set by the 'tabname' key.
     */
    function addTab($title, $link, $params = array())
    {
        if (!is_array($params)) {
            $params = array('tabname' => $params);
        }
        $this->_tabs[] = array_merge(array('title' => $title,
                                           'link' => $link,
                                           'tabname' => null),
                                     $params);
    }

    /**
     * Returns the title of the tab with the specified name.
     *
     * @param string $tabname  The name of the tab.
     *
     * @return string  The tab's title.
     */
    function getTitleFromAction($tabname)
    {
        foreach ($this->_tabs as $tab) {
            if ($tab['tabname'] == $tabname) {
                return $tab['title'];
            }
        }

        return null;
    }

    /**
     * Renders the tabs.
     *
     * @param string $active_tab  If specified, the name of the active tab. If
     *                            not, the active tab is determined
     *                            automatically.
     */
    function render($active_tab = null)
    {
        $html = "<div class=\"tabset\"><ul>\n";

        $first = true;
        $active = $_SERVER['PHP_SELF'] . $this->_vars->get($this->_name);

        foreach ($this->_tabs as $tab) {
            $link = $this->_addPreserved($tab['link']);
            if (!is_null($this->_name) && !is_null($tab['tabname'])) {
                $link = Util::addParameter($link, $this->_name,
                                           $tab['tabname']);
            }

            $class = '';
            if ((!is_null($active_tab) && $active_tab == $tab['tabname']) ||
                ($active == $tab['link'] . $tab['tabname'])) {
                $class = ' class="activeTab"';
            }

            $id = '';
            if (!empty($tab['id'])) {
                $id = ' id="' . htmlspecialchars($tab['id']) . '"';
            }

            if (!isset($tab['target'])) {
                $tab['target'] = '';
            }

            if (!isset($tab['onclick'])) {
                $tab['onclick'] = '';
            }

            $accesskey = Horde::getAccessKey($tab['title']);

            $html .= '<li' . $class . $id . '>' .
                Horde::link($link, '', '', $tab['target'], $tab['onclick'], null, $accesskey) .
                Horde::highlightAccessKey(str_replace(' ', '&nbsp;', $tab['title']), $accesskey) .
                "</a> </li>\n";
        }

        return $html . "</ul></div><br class=\"clear\" />\n";
    }

}
