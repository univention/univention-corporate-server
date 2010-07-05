<?php
/**
 * The MIME_Viewer_source class is a class for any viewer that wants
 * to provide line numbers to extend.
 *
 * $Horde: framework/MIME/MIME/Viewer/source.php,v 1.9.10.14 2009-01-06 15:23:22 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_source extends MIME_Viewer {

    /**
     * Add line numbers to a block of code.
     *
     * @param string $code  The code to number.
     */
    function lineNumber($code, $linebreak = "\n")
    {
        $lines = substr_count($code, $linebreak) + 1;
        $html = '<table class="lineNumbered" cellspacing="0"><tr><th>';
        for ($l = 1; $l <= $lines; $l++) {
            $html .= sprintf('<a id="l%s" href="#l%s">%s</a><br />', $l, $l, $l) . "\n";
        }
        return $html . '</th><td><div>' . $code . '</div></td></tr></table>';
    }

    /**
     * Return the MIME content type of the rendered content.
     *
     * @return string  The content type of the output.
     */
    function getType()
    {
        return 'text/html; charset=' . NLS::getCharset();
    }

}
