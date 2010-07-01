<?php
/**
 * The Text:: class provides common methods for manipulating text.
 *
 * $Horde: framework/Horde/Horde/Text.php,v 1.2.10.9 2009-01-06 15:23:10 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jon Parise <jon@horde.org>
 * @since   Horde 1.3
 * @package Horde_Text
 */
class Text {

    /**
     * Convert a line of text to display properly in HTML.
     *
     * @param string $text  The string of text to convert.
     *
     * @return string  The HTML-compliant converted text.
     */
    function htmlSpaces($text = '')
    {
        static $charset;
        if (!isset($charset)) {
            $charset = NLS::getCharset();
        }

        $text = @htmlspecialchars($text, ENT_COMPAT, $charset);
        $text = str_replace("\t", '&nbsp; &nbsp; &nbsp; &nbsp; ', $text);
        $text = str_replace('  ', '&nbsp; ', $text);
        $text = str_replace('  ', ' &nbsp;', $text);

        return $text;
    }

    /**
     * Same as htmlSpaces() but converts all spaces to &nbsp;
     *
     * @see htmlSpaces()
     *
     * @param string $text  The string of text to convert.
     *
     * @return string  The HTML-compliant converted text.
     */
    function htmlAllSpaces($text = '')
    {
        $text = Text::htmlSpaces($text);
        $text = str_replace(' ', '&nbsp;', $text);

        return $text;
    }

}
