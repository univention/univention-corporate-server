<?php
/**
 * The MIME_Viewer_source class is a class for any viewer that wants
 * to provide line numbers to extend.
 *
 * $Horde: framework/MIME/MIME/Viewer/source.php,v 1.8 2004/05/22 03:06:23 chuck Exp $
 *
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
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
        $html  = '<table style="border: 1px solid black" cellspacing="0" cellpadding="0" width="100%">';
        $html .= '<tr><td valign="top" style="background-color:#e9e9e9; padding-left:10px; padding-right:10px; text-align:right;">';
        for ($l = 1; $l <= $lines; $l++) {
            $html .= sprintf('<a style="font-family:monospace; font-size:12px;" name="%s" href="#%s">%s</a><br />', $l, $l, $l) . "\n";
        }
        $html .= '</td><td width="100%" valign="top" nowrap="nowrap" style="background-color:white; padding-left:10px; font-family:monospace; font-size:12px; white-space:pre;">' . $code . '</td>';
        return $html . '</tr></table>';
    }

}
