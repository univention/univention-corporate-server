<?php
/**
 * The MIME_Viewer_tnef class allows MS-TNEF attachments to be displayed.
 *
 * $Horde: framework/MIME/MIME/Viewer/tnef.php,v 1.13 2004/04/07 14:43:10 chuck Exp $
 *
 * Copyright 2002-2004 Jan Schneider <jan@horde.org>
 * Copyright 2002-2004 Michael Slusarz <slusarz@bigworm.colorado.edu>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @author  Michael Slusarz <slusarz@bigworm.colorado.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_tnef extends MIME_Viewer {

    /**
     * Render out the current tnef data.
     *
     * @access public
     *
     * @param optional array $params  Any parameters the viewer may need.
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
     * @access public
     *
     * @return string  The content type of the output. 
     */
    function getType()
    {
        return 'text/html';
    }

}
