<?php
/**
 * The MIME_Viewer_rpm class renders out lists of files in RPM
 * packages by using the rpm tool to query the package.
 *
 * $Horde: framework/MIME/MIME/Viewer/rpm.php,v 1.12 2004/04/16 17:21:45 jan Exp $
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
class MIME_Viewer_rpm extends MIME_Viewer {

    /**
     * Render out the RPM contents.
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
        if (!file_exists($mime_drivers['horde']['rpm']['location'])) {
            return '<pre>' . sprintf(_("The program used to view this data type (%s) was not found on the system."), $mime_drivers['horde']['rpm']['location']) . '</pre>';
        }

        $data = '';
        $tmp_rpm = Horde::getTempFile('horde_rpm');

        $fh = fopen($tmp_rpm, 'w');
        fwrite($fh, $this->mime_part->getContents());
        fclose($fh);

        $fh = popen($mime_drivers['horde']['rpm']['location'] . " -qip $tmp_rpm 2>&1", 'r');
        while (($rc = fgets($fh, 8192))) {
            $data .= $rc;
        }
        pclose($fh);

        return '<pre>' . htmlentities($data) . '</pre>';
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
