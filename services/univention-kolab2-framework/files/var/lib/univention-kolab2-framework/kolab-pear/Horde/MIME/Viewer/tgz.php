<?php
/**
 * The MIME_Viewer_tgz class renders out plain or gzipped tarballs in HTML.
 *
 * $Horde: framework/MIME/MIME/Viewer/tgz.php,v 1.36 2004/04/07 14:43:10 chuck Exp $
 *
 * Copyright 1999-2004 Anil Madhavapeddy <anil@recoil.org>
 * Copyright 2002-2004 Michael Cochrane <mike@graftonhall.co.nz>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @author  Michael Cochrane <mike@graftonhall.co.nz>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_tgz extends MIME_Viewer {

    /**
     * Render out the currently set tar file contents.
     *
     * @access public
     *
     * @param optional array $params  Any parameters the Viewer may need.
     *
     * @return string  The rendered contents.
     */
    function render($params = array())
    {
        require_once 'Horde/Compress.php';

        $contents = $this->mime_part->getContents();

        /* Only decompress gzipped files. */
        $subtype = $this->mime_part->getSubType();
        if (($subtype == 'x-gzip-compressed') ||
            ($subtype == 'tgz') ||
            ($subtype == 'x-tgz') ||
            ($subtype == 'x-gzip') ||
            ($subtype == 'x-gtar')) {
            $gzip = &Horde_Compress::singleton('gzip');
            $contents = $gzip->decompress($contents);
            if (empty($contents)) {
                return '<pre>' . _("Unable to open compressed archive.") . '</pre>';
            } elseif (is_a($contents, 'PEAR_Error')) {
                return '<pre>' . $contents->getMessage() . '</pre>';
            }
        }

        /* Obtain the list of files/data in the tar file. */
        $tar = &Horde_Compress::singleton('tar');

        $tarData = &$tar->decompress($contents);
        if (is_a($tarData, 'PEAR_Error')) {
            return '<pre>' . $tarData->getMessage() . '</pre>';
        }

        $fileCount = count($tarData);

        include_once 'Horde/Text.php';

        $text  = '<b>' . htmlspecialchars(sprintf(_("Contents of '%s'"), $this->mime_part->getName())) . ':</b>' . "\n";
        $text .= '<table><tr><td align="left"><tt><span class="fixed">';
        $text .= Text::htmlAllSpaces(_("Archive Name") . ':  ' . $this->mime_part->getName()) . "\n";
        $text .= Text::htmlAllSpaces(_("Archive File Size") . ': ' . strlen($contents) . ' bytes') . "\n";
        $text .= Text::htmlAllSpaces(($fileCount != 1) ? sprintf(_("File Count: %s files"), $fileCount) : sprintf(_("File Count: %s file"), $fileCount));
        $text .= "\n\n";
        $text .= Text::htmlAllSpaces(
                     str_pad(_("File Name"),     62, ' ', STR_PAD_RIGHT) .
                     str_pad(_("Attributes"),    15, ' ', STR_PAD_LEFT) .
                     str_pad(_("Size"),          10, ' ', STR_PAD_LEFT) .
                     str_pad(_("Modified Date"), 19, ' ', STR_PAD_LEFT)
                 ) . "\n";

        $text .= str_repeat('-', 106) . "\n";

        foreach ($tarData as $val) {
           $text .= Text::htmlAllSpaces(
                        str_pad($val['name'], 62, ' ', STR_PAD_RIGHT) .
                        str_pad($val['attr'], 15, ' ', STR_PAD_LEFT) .
                        str_pad($val['size'], 10, ' ', STR_PAD_LEFT) .
                        str_pad(strftime("%d-%b-%Y %H:%M", $val['date']), 19, ' ', STR_PAD_LEFT)
                    ) . "\n";
        }

        $text .= str_repeat('-', 106) . "\n";
        $text .= '</span></tt></td></tr></table>';

        return nl2br($text);
    }

    function getType()
    {
        return 'text/html';
    }

}
