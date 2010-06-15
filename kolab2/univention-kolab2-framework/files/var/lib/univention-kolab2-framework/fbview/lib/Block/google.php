<?php
/**
 * $Horde: horde/lib/Block/google.php,v 1.7 2004/05/29 16:21:03 jan Exp $
 *
 * @package Horde_Block
 */
class Horde_Block_google extends Horde_Block {

    var $_app = 'horde';

    /**
     * The title to go in this block.
     *
     * @return string   The title text.
     */
    function _title()
    {
        return _("Google Search");
    }

    /**
     * The content to go in this block.
     *
     * @return string   The content
     */
    function _content()
    {
        $html  = '<form name="google" onsubmit="open_google_win(); return false;">';
        $html .= '<table width="100%" height="100%">';
        $html .= '<tr><script language="JavaScript" type="text/javascript" src="' . $GLOBALS['registry']->getParam('webroot', 'horde') . '/services/javascript.php?file=open_google_win.js&amp;app=horde"></script>';
        $html .= '<td>' . Horde::img('google.png', 'Google') . '</td></tr>';
        $html .= '<tr><td><input maxLength="256" size="40" name="q" width="100%" /></td></tr>';
        $html .= '<tr><td><table width="100%"><tr><td align="center"><input type="radio" name="area" value="web" width="20%" checked="checked" />' . _("Web") . '</td>';
        $html .= '<td align="center"><input type="radio" name="area" value="images" width="20%" />' . _("Images") . '</td>';
        $html .= '<td align="center"><input type="radio" name="area" value="groups" width="20%" />' . _("Groups") . '</td>';
        $html .= '<td align="center"><input type="radio" name="area" value="directory" width="20%" />' . _("Directory") . '</td>';
        $html .= '<td align="center"><input type="radio" name="area" value="news" width="20%" />' . _("News") . '</td></tr></table></td></tr>';
        $html .= '<tr><td><input type="submit" class="button" value="' . _("Google Search") . '" /></td></tr>';
        $html .= '</table>';
        $html .= '</form>';
        return $html;
    }

}
