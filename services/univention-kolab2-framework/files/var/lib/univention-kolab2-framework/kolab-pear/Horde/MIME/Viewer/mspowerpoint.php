<?php
/**
 * The MIME_Viewer_mspowerpoint class renders out Microsoft Powerpoint
 * documents in HTML format by using the xlHtml package.
 *
 * $Horde: framework/MIME/MIME/Viewer/mspowerpoint.php,v 1.13 2004/04/16 17:21:45 jan Exp $
 *
 * Copyright 1999-2004 Anil Madhavapeddy <anil@recoil.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_mspowerpoint extends MIME_Viewer {

    /**
     * Render out the current data using ppthtml.
     *
     * @access public
     *
     * @param optional array $params  Any parameters the Viewer may need.
     *
     * @return string  The rendered contents.
     */
    function render($params = array())
    {
        global $mime_drivers;

        /* Check to make sure the program actually exists. */
        if (!file_exists($mime_drivers['horde']['mspowerpoint']['location'])) {
            return '<pre>' . sprintf(_("The program used to view this data type (%s) was not found on the system."), $mime_drivers['horde']['mspowerpoint']['location']) . '</pre>';
        }

        $data = '';
        $tmp_ppt = Horde::getTempFile('horde_mspowerpoint');

        $fh = fopen($tmp_ppt, 'w');
        fwrite($fh, $this->mime_part->getContents());
        fclose($fh);

        $fh = popen($mime_drivers['horde']['mspowerpoint']['location'] . " $tmp_ppt 2>&1", 'r');
        while (($rc = fgets($fh, 8192))) {
            $data .= $rc;
        }
        pclose($fh);

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
