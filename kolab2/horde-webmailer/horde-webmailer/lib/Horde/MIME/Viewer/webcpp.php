<?php
/**
 * The MIME_Viewer_webcpp class renders out various content
 * in HTML format by using Web C Plus Plus.
 *
 * Web C Plus plus: http://webcpp.sourceforge.net/
 *
 * $Horde: framework/MIME/MIME/Viewer/webcpp.php,v 1.11.10.13 2009-01-06 15:23:22 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_webcpp extends MIME_Viewer {

    /**
     * Render out the currently set contents using Web C Plus Plus.
     *
     * @param array $params  Any parameters the Viewer may need.
     *
     * @return string  The rendered contents.
     */
    function render($params = array())
    {
        global $mime_drivers;

        require_once 'Horde/MIME/Contents.php';
        $attachment = MIME_Contents::viewAsAttachment();

        /* Check to make sure the program actually exists. */
        if (!file_exists($mime_drivers['horde']['webcpp']['location'])) {
            return '<pre>' . sprintf(_("The program used to view this data type (%s) was not found on the system."), $mime_drivers['horde']['webcpp']['location']) . '</pre>';
        }

        /* Create temporary files for Webcpp. */
        $tmpin  = Horde::getTempFile('WebcppIn');
        $tmpout = Horde::getTempFile('WebcppOut');

        /* Write the contents of our buffer to the temporary input file. */
        $contents = $this->mime_part->getContents();
        $fh = fopen($tmpin, 'wb');
        fwrite($fh, $contents, strlen($contents));
        fclose($fh);

        /* Get the extension for the mime type. */
        include_once 'Horde/MIME/Magic.php';
        $ext = MIME_Magic::MIMEToExt($this->mime_part->getType());

        /* Execute Web C Plus Plus. Specifying the in and out files didn't
           work for me but pipes did. */
        exec($mime_drivers['horde']['webcpp']['location'] . " --pipe --pipe -x=$ext -l -a -t < $tmpin > $tmpout");
        $results = file_get_contents($tmpout);

        /* If we are not displaying inline, all the formatting is already
         * done for us. */
        if ($attachment) {
            /* The first 2 lines are the Content-Type line and a blank line
             * so we should remove them before outputting. */
            return preg_replace("/.*\n.*\n/", '', $results, 1);
        }

        /* Extract the style sheet, removing any global body formatting
         * if we're displaying inline. */
        $res = preg_split(';(</style>)|(<style type="text/css">);', $results);
        $style = $res[1];
        $style = preg_replace('/\nbody\s+?{.*?}/s', '', $style);

        /* Extract the content. */
        $res = preg_split('/\<\/?pre\>/', $results);
        $body = $res[1];

        return '<style>' . $style . '</style><div class="webcpp" style="white-space:pre;font-family:Lucida Console,Courier,monospace;">' . $body . '</div>';
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
