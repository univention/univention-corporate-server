<?php

require_once dirname(__FILE__) . '/source.php';

/**
 * The MIME_Viewer_srchighlite class renders out various content in HTML
 * format by using Source-highlight.
 *
 * Source-highlight: http://www.gnu.org/software/src-highlite/
 *
 * $Horde: framework/MIME/MIME/Viewer/srchighlite.php,v 1.14.10.13 2009-01-06 15:23:22 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_srchighlite extends MIME_Viewer_source {

    /**
     * Render out the currently set contents using Source-highlight
     *
     * @param array $params  Any parameters the viewer may need.
     *
     * @return string  The rendered contents.
     */
    function render($params = array())
    {
        global $mime_drivers;

        /* Check to make sure the program actually exists. */
        if (!file_exists($mime_drivers['horde']['srchighlite']['location'])) {
            return '<pre>' . sprintf(_("The program used to view this data type (%s) was not found on the system."), $mime_drivers['horde']['srchighlite']['location']) . '</pre>';
        }

        /* Create temporary files for Webcpp. */
        $tmpin  = Horde::getTempFile('SrcIn');
        $tmpout = Horde::getTempFile('SrcOut', false);

        /* Write the contents of our buffer to the temporary input file. */
        $contents = $this->mime_part->getContents();
        $fh = fopen($tmpin, 'wb');
        fwrite($fh, $contents, strlen($contents));
        fclose($fh);

        /* Determine the language from the mime type. */
        $lang = '';
        switch ($this->mime_part->getType()) {
        case 'text/x-java':
            $lang = 'java';
            break;

        case 'text/x-csrc':
        case 'text/x-c++src':
        case 'text/cpp':
            $lang = 'cpp';
            break;

        case 'application/x-perl':
            $lang = 'perl';
            break;

        case 'application/x-php':
        case 'x-extension/phps':
        case 'x-extension/php3s':
        case 'application/x-httpd-php':
        case 'application/x-httpd-php3':
        case 'application/x-httpd-phps':
            $lang = 'php3';
            break;

        case 'application/x-python':
            $lang = 'python';
            break;

            // $lang = 'prolog';
            // break;

            // $lang = 'flex';
            // break;

            // $lang = 'changelog';
            // break;

            // $lang = 'ruby';
            // break;
        }

        /* Execute Source-Highlite. */
        exec($mime_drivers['horde']['srchighlite']['location'] . " --src-lang $lang --out-format xhtml --input $tmpin --output $tmpout");
        $results = file_get_contents($tmpout);
        unlink($tmpout);

        /* Educated Guess at whether we are inline or not. */
        if (headers_sent() || ob_get_length()) {
            return $this->lineNumber($results);
        } else {
            return Util::bufferOutput('require', $GLOBALS['registry']->get('templates', 'horde') . '/common-header.inc') .
                $this->lineNumber($results) .
                Util::bufferOutput('require', $GLOBALS['registry']->get('templates', 'horde') . '/common-footer.inc');
        }
    }

}
