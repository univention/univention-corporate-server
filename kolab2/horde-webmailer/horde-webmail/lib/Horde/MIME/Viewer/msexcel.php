<?php
/**
 * The MIME_Viewer_msexcel class renders out Microsoft Excel
 * documents in HTML format by using the xlHtml package.
 *
 * $Horde: framework/MIME/MIME/Viewer/msexcel.php,v 1.20.10.12 2009-01-06 15:23:21 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_msexcel extends MIME_Viewer {

    /**
     * Render out the currently data using xlhtml.
     *
     * @param array $params  Any params this Viewer may need.
     *
     * @return string  The rendered data.
     */
    function render($params = array())
    {
        global $mime_drivers;

        /* Check to make sure the program actually exists. */
        if (!file_exists($mime_drivers['horde']['msexcel']['location'])) {
            return '<pre>' . sprintf(_("The program used to view this data type (%s) was not found on the system."), $mime_drivers['horde']['msexcel']['location']) . '</pre>';
        }

        $data = '';
        $tmp_xls = Horde::getTempFile('horde_msexcel');

        $fh = fopen($tmp_xls, 'w');
        fwrite($fh, $this->mime_part->getContents());
        fclose($fh);

        $fh = popen($mime_drivers['horde']['msexcel']['location'] . " -nh $tmp_xls 2>&1", 'r');
        while (($rc = fgets($fh, 8192))) {
            $data .= $rc;
        }
        pclose($fh);

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
