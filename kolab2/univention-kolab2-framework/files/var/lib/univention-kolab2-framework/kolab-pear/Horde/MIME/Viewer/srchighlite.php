<?php

require_once dirname(__FILE__) . '/source.php';

/**
 * The MIME_Viewer_srchighlite class renders out various content
 * in HTML format by using Source-highlight.
 *
 * Web C Plus plus: http://www.gnu.org/software/src-highlite/
 *
 * $Horde: framework/MIME/MIME/Viewer/srchighlite.php,v 1.12 2004/05/22 03:06:24 chuck Exp $
 *
 * Copyright 2003-2004 Mike Cochrane <mike@graftonhall.co.nz>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_srchighlite extends MIME_Viewer_source {

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
        global $mime_drivers, $registry;

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

        // Educated Guess at whether we are inline or not
        $inline = headers_sent();
        $html = '';

        if (!$inline) {
            $html .= Util::bufferOutput('require', $registry->getParam('templates', 'horde') . '/common-header.inc');
            $html .= "<div style='background-color:white'>";
        }

        /* Execute Source-Highlite. */
        exec($mime_drivers['horde']['srchighlite']['location'] . " --src-lang $lang --out-format xhtml --input $tmpin --output $tmpout");
        $fp = @fopen($tmpout, 'r');
        $data = @fread($fp, filesize($tmpout));
        @fclose($fp);
        unlink($tmpout);

        $html .= $this->lineNumber($this->lineNumber($data));

        if (!$inline) {
            $html .= '</div>';
            $html .= Util::bufferOutput('require', $registry->getParam('templates', 'horde') . '/common-footer.inc');
        }

        return $html;
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
