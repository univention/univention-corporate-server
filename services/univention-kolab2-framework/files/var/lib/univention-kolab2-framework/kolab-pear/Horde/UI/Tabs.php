<?php

require_once dirname(__FILE__) . '/Widget.php';

/**
 * The Horde_UI_Tabs:: class manages and renders a tab-like interface.
 *
 * $Horde: framework/UI/UI/Tabs.php,v 1.13 2004/03/18 16:47:37 chuck Exp $
 *
 * Copyright 2001 Robert E. Coyle <robertecoyle@hotmail.com>
 *
 * See the enclosed file LICENSE for license information (BSD). If you
 * did not receive this file, see http://www.horde.org/licenses/bsdl.php.
 *
 * @version $Revision: 1.1.2.1 $
 * @since   Horde_UI 0.0.1
 * @package Horde_UI
 */
class Horde_UI_Tabs extends Horde_UI_Widget {

    /**
     * The array of tabs.
     * @var array $_tabs
     */
    var $_tabs = array();

    /**
     * Add a tab to the interface.
     *
     * @access public
     *
     * @param string $title    The text which appears on the tab.
     * @param string $link     The target page.
     * @param string $tabname  The value to set the tab variable to.
     */
    function addTab($title, $link, $tabname = null)
    {
        $this->_tabs[] = array('title' => $title, 'link' => $link, 'tabname' => $tabname);
    }

    /**
     * Retreive the title of the tab with the specified name.
     *
     * @access public
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
     * Render the tabs.
     */
    function render()
    {
        $html = '<table width="100%" cellspacing="0" cellpadding="1" border="0" class="tabset"><tr>';

        $width = round(100.0 / count($this->_tabs));
        $first = true;
        $active = $this->_vars->get($this->_name);

        foreach ($this->_tabs as $tab) {
            $class = 'tab';
            $title = $tab['title'];
            $link = $this->_addPreserved($tab['link']);
            $accesskey = Horde::getAccessKey($title);

            if (!is_null($tab['tabname'])) {
                $link = Util::addParameter($link, $this->_name,
                                           $tab['tabname']);

                if ($active == $tab['tabname']) {
                    $class = 'tab-hi';
                }
            }

            $html .= '<td style="padding-left:10px;">&nbsp;</td><td width="' .
                $width . '%" align="center" class="' . $class .
                '" onclick="window.location.href=\'' .
                addslashes(Horde::applicationUrl($link)) . '\'"><b>' .
                Horde::link(Horde::applicationUrl($link), $title, $class,
                            null, null, null, $accesskey) .
                Horde::highlightAccessKey($title, $accesskey) .
                '</a></b></td>';
        }

        $html .= '<td style="padding-left:10px;">&nbsp;</td></tr></table>';
        return $html;
    }

}
