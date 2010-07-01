<?php
/**
 * The MIME_Viewer_tnef class allows MS-TNEF attachments to be displayed.
 *
 * $Horde: framework/MIME/MIME/Viewer/tnef.php,v 1.13.10.14 2009-01-06 15:23:22 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_tnef extends MIME_Viewer {

    /**
     * Render out the current tnef data.
     *
     * @param array $params  Any parameters the viewer may need.
     *
     * @return string  The rendered contents.
     */
    function render($params = array())
    {
        require_once 'Horde/Compress.php';

        $tnef = &Horde_Compress::singleton('tnef');

        $data = '<table border="1">';
        $info = $tnef->decompress($this->mime_part->getContents());
        if (empty($info) || is_a($info, 'PEAR_Error')) {
            $data .= '<tr><td>' . _("MS-TNEF Attachment contained no data.") . '</td></tr>';
        } else {
            $data .= '<tr><td>' . _("Name") . '</td><td>' . _("Mime Type") . '</td></tr>';
            foreach ($info as $part) {
                $data .= '<tr><td>' . $part['name'] . '</td><td>' . $part['type'] . '/' . $part['subtype'] . '</td></tr>';
            }
        }
        $data .= '</table>';

        return $data;
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
