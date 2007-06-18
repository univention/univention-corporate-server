<?php
/**
 * The MIME_Viewer_webcpp class renders out various content
 * in HTML format by using Web C Plus Plus.
 *
 * Web C Plus plus: http://webcpp.sourceforge.net/
 *
 * $Horde: framework/MIME/MIME/Viewer/webcpp.php,v 1.10 2004/04/16 17:21:45 jan Exp $
 *
 * Copyright 2002-2004 Mike Cochrane <mike@graftonhall.co.nz>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_webcpp extends MIME_Viewer {

    /**
     * Render out the currently set contents using Web C Plus Plus.
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
        exec($mime_drivers['horde']['webcpp']['location'] . " --pipe --pipe -x=$ext < $tmpin > $tmpout");
        $results = file($tmpout);

        /* Extract the style sheet, removing any global body formatting
         * if we're displaying inline.
         */
        $res = preg_split('/(\<\/style\>)|(\<style type\=\"text\/css\"\>)/', implode('', $results));
        $style = $res[1];
        if ($this->canDisplayInline()) {
            $style = preg_replace('/\nbody\s+?{.*?}/s', '', $style);
        }

        /* Extract the content. */
        $res = preg_split('/\<\/?pre\>/', implode('', $results));
        $body = $res[1];
         
        return '<style>' . $style . '</style><pre><div class="webcpp">' . $body. '</div></pre>';
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
