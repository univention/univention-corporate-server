<?php
/**
 * The Horde_UI_Language:: class provides a widget for changing the
 * currently selected language.
 *
 * $Horde: framework/UI/UI/Language.php,v 1.4 2004/02/04 17:02:26 chuck Exp $
 *
 * Copyright 2003-2004 Jason M. Felice <jfelice@cronosys.com>
 *
 * See the enclosed file LICENSE for license information (LGPL).
 *
 * @version $Revision: 1.1.2.1 $
 * @since   Horde_UI 0.0.1
 * @package Horde_UI
 */
class Horde_UI_Language {

    /**
     * Render the language selection.
     *
     * @abstract
     *
     * @param optional bool $form  Return the selection box as an complete
     *                             standalone form.
     *
     * @return string  The HTML selection box.
     */
    function render()
    {
        $html = '';
        if (!$GLOBALS['prefs']->isLocked('language')) {
            Horde::addScriptFile('language.js', 'horde');
            $_SESSION['horde_language'] = NLS::select();
            $html = sprintf('<form name="language" action="%s">',
                            Horde::url($GLOBALS['registry']->getParam('webroot', 'horde') . '/services/language.php', false, -1));
            $html .= '<input type="hidden" name="url" value="' . Horde::selfUrl(false, false, true) . '" />';
            $html .= '<select name="new_lang" onchange="document.language.submit()">';
            foreach ($GLOBALS['nls']['languages'] as $key => $val) {
                $sel = ($key == $_SESSION['horde_language']) ? ' selected="selected"' : '';
                $html .= "<option value=\"$key\"$sel>$val</option>";
            }
            $html .= '</select></form>';
        }
        return $html;
    }

}
