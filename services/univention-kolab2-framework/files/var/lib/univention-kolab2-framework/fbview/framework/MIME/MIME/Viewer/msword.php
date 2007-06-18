<?php
/**
 * The MIME_Viewer_msword class renders out Microsoft Word
 * documents in HTML format by using the wvWare package.
 *
 * $Horde: framework/MIME/MIME/Viewer/msword.php,v 1.25 2004/05/04 22:07:18 jan Exp $
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
class MIME_Viewer_msword extends MIME_Viewer {

    /**
     * Render out the current data using wvWare.
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
        if (!file_exists($mime_drivers['horde']['msword']['location'])) {
            return '<pre>' . sprintf(_("The program used to view this data type (%s) was not found on the system."), $mime_drivers['horde']['msword']['location']) . '</pre>';
        }

        $data = '';
        $tmp_word   = Horde::getTempFile('msword');
        $tmp_output = Horde::getTempFile('msword');
        $tmp_dir    = Horde::getTempDir();
        $tmp_file   = str_replace($tmp_dir . '/', '', $tmp_output);

        if (OS_WINDOWS) {
            $args = ' -x ' . dirname($mime_drivers['horde']['msword']['location']) . "\\wvHtml.xml -d $tmp_dir -1 $tmp_word > $tmp_output";
        } else {
            $version = exec($mime_drivers['horde']['msword']['location'] . ' --version');
            if (version_compare($version, '0.7.0') >= 0) {
                $args = " --targetdir=$tmp_dir $tmp_word $tmp_file";
            } else {
                $args = " $tmp_word $tmp_output";
            }
        }

        $fh = fopen($tmp_word, 'w');
        fwrite($fh, $this->mime_part->getContents());
        fclose($fh);

        exec($mime_drivers['horde']['msword']['location'] . $args);

        if (!file_exists($tmp_output)) {
            return _("Unable to translate this Word document");
        }

        $fh = fopen($tmp_output, 'r');
        while (($rc = fgets($fh, 8192))) {
            $data .= $rc;
        }
        fclose($fh);
        
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
