<?php
/**
 * The Horde_UI_Language:: class provides a widget for changing the
 * currently selected language.
 *
 * $Horde: framework/UI/UI/Language.php,v 1.5.10.12 2009-01-06 15:23:45 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jason M. Felice <jason.m.felice@gmail.com>
 * @since   Horde_UI 0.0.1
 * @package Horde_UI
 */
class Horde_UI_Language {

    /**
     * Render the language selection.
     *
     * @abstract
     *
     * @param boolean $form  Return the selection box as a complete standalone
     *                       form.
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
                            Horde::url($GLOBALS['registry']->get('webroot', 'horde') . '/services/language.php', false, -1));
            $html .= '<input type="hidden" name="url" value="' . @htmlspecialchars(Horde::selfUrl(false, false, true)) . '" />';
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
