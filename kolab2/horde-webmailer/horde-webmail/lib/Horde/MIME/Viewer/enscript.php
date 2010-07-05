<?php

require_once dirname(__FILE__) . '/source.php';

/**
 * The MIME_Viewer_enscript class renders out various content
 * in HTML format by using GNU Enscript.
 *
 * $Horde: framework/MIME/MIME/Viewer/enscript.php,v 1.39.10.13 2009-01-06 15:23:21 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_enscript extends MIME_Viewer_source {

    /**
     * Render out the data using Enscript.
     *
     * @param array $params  Any parameters the Viewer may need.
     *
     * @return string  The rendered data.
     */
    function render($params = array())
    {
        global $mime_drivers;

        /* Check to make sure the program actually exists. */
        if (!file_exists($mime_drivers['horde']['enscript']['location'])) {
            return '<pre>' . sprintf(_("The program used to view this data type (%s) was not found on the system."), $mime_drivers['horde']['enscript']['location']) . '</pre>';
        }

        /* Create temporary files for input to Enscript. Note that we
           cannot use a pipe, since enscript must have access to the
           whole file to determine its type for coloured syntax
           highlighting. */
        $tmpin = Horde::getTempFile('EnscriptIn');

        /* Write the contents of our buffer to the temporary input file. */
        $contents = $this->mime_part->getContents();
        $fh = fopen($tmpin, 'wb');
        fwrite($fh, $contents, strlen($contents));
        fclose($fh);

        /* Execute the enscript command. */
        $lang = escapeshellarg($this->_typeToLang($this->mime_part->getType()));
        $results = shell_exec($mime_drivers['horde']['enscript']['location'] . " -E$lang --language=html --color --output=- < $tmpin");

        /* Strip out the extraneous HTML from Enscript, and output it. */
        $res_arr = preg_split('/\<\/?pre\>/i', $results);
        if (count($res_arr) == 3) {
            $results = trim($res_arr[1]);
        }

        /* Educated Guess at whether we are inline or not. */
        if (headers_sent() || ob_get_length()) {
            return $this->lineNumber($results);
        } else {
            return Util::bufferOutput('require', $GLOBALS['registry']->get('templates', 'horde') . '/common-header.inc') .
                $this->lineNumber($results) .
                Util::bufferOutput('require', $GLOBALS['registry']->get('templates', 'horde') . '/common-footer.inc');
        }
    }

    /**
     * Attempts to determine what language to use for the enscript program
     * from a MIME type.
     *
     * @access private
     *
     * @param string $type  The MIME type.
     *
     * @return string  The enscript 'language' parameter string.
     */
    function _typeToLang($type)
    {
        include_once dirname(__FILE__) . '/../Magic.php';

        $ext = MIME_Magic::MIMEToExt($type);

        switch ($ext) {
        case 'cs':
            return 'java';

        case 'el':
            return 'elisp';

        case 'h':
            return 'c';

        case 'C':
        case 'H':
        case 'cc':
        case 'hh':
        case 'c++':
        case 'cxx':
        case 'cpp':
            return 'cpp';

        case 'htm':
        case 'shtml':
        case 'xml':
            return 'html';

        case 'js':
            return 'javascript';

        case 'pas':
            return 'pascal';

        case 'al':
        case 'cgi':
        case 'pl':
        case 'pm':
            return 'perl';

        case 'ps':
            return 'postscript';

        case 'vb':
            return 'vba';

        case 'vhd':
            return 'vhdl';

        case 'patch':
        case 'diff':
            return 'diffu';

        default:
            return $ext;
        }
    }

}
