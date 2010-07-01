<?php
/**
 * The MIME_Viewer_rar class renders out the contents of .rar archives in HTML
 * format.
 *
 * $Horde: framework/MIME/MIME/Viewer/rar.php,v 1.18.10.15 2009-01-06 15:23:21 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @author  Michael Cochrane <mike@graftonhall.co.nz>
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_rar extends MIME_Viewer {

    /**
     * Rar compression methods.
     *
     * @var array
     */
    var $_methods = array(
        0x30  =>  'Store',
        0x31  =>  'Fastest',
        0x32  =>  'Fast',
        0x33  =>  'Normal',
        0x34  =>  'Good',
        0x35  =>  'Best'
    );

    /**
     * Render out the currently set contents using rar.
     *
     * @param array $params  Any parameters the Viewer may need.
     *
     * @return string  The rendered contents.
     */
    function render($params = array())
    {
        $contents = $this->mime_part->getContents();

        /* Make sure this is a valid rar file. */
        if ($this->checkRarData($contents) === false) {
            return '<pre>' . _("This does not appear to be a valid rar archive.") . '</pre>';
        }

        require_once 'Horde/Text.php';

        $rarData = $this->getRarData($contents);
        $fileCount = count($rarData);

        $text  = '<strong>' . htmlspecialchars(sprintf(_("Contents of \"%s\""), $this->mime_part->getName())) . ':</strong>' . "\n";
        $text .= '<table><tr><td align="left"><tt><span class="fixed">';
        $text .= Text::htmlAllSpaces(_("Archive Name") . ':  ' . $this->mime_part->getName()) . "\n";
        $text .= Text::htmlAllSpaces(_("Archive File Size") . ': ' . strlen($contents) . ' bytes') . "\n";
        $text .= Text::htmlAllSpaces(sprintf(ngettext("File Count: %d file", "File Count: %d files", $fileCount), $fileCount));
        $text .= "\n\n";
        $text .= Text::htmlAllSpaces(
                     String::pad(_("File Name"),     50, ' ', STR_PAD_RIGHT) .
                     String::pad(_("Attributes"),    10, ' ', STR_PAD_LEFT) .
                     String::pad(_("Size"),          10, ' ', STR_PAD_LEFT) .
                     String::pad(_("Modified Date"), 19, ' ', STR_PAD_LEFT) .
                     String::pad(_("Method"),        10, ' ', STR_PAD_LEFT) .
                     String::pad(_("Ratio"),         10, ' ', STR_PAD_LEFT)
                 ) . "\n";

        $text .= str_repeat('-', 109) . "\n";

        foreach ($rarData as $val) {
            $ratio = (empty($val['size'])) ? 0 : 100 * ($val['csize'] / $val['size']);
            $text .= Text::htmlAllSpaces(
                         String::pad($val['name'], 50, ' ', STR_PAD_RIGHT) .
                         String::pad($val['attr'], 10, ' ', STR_PAD_LEFT) .
                         String::pad($val['size'], 10, ' ', STR_PAD_LEFT) .
                         String::pad(strftime("%d-%b-%Y %H:%M", $val['date']), 19, ' ', STR_PAD_LEFT) .
                         String::pad($val['method'], 10, ' ', STR_PAD_LEFT) .
                         String::pad(sprintf("%1.1f%%", $ratio), 10, ' ', STR_PAD_LEFT)
                     ) . "\n";
        }

        $text .= str_repeat('-', 106) . "\n";
        $text .= '</span></tt></td></tr></table>';

        return nl2br($text);
    }

    /**
     * Returns the MIME type of this part.
     *
     * @return string  The MIME type of this part.
     */
    function getType()
    {
        return 'text/html; charset=' . NLS::getCharset();
    }

    /**
     * Checks to see if the data is a valid Rar archive.
     *
     * @param string &$data  The rar archive data.
     *
     * @return boolean  True if valid, false if invalid.
     */
    function checkRarData(&$data)
    {
        $fileHeader = "\x52\x61\x72\x21\x1a\x07\x00";
        if (strpos($data, $fileHeader) === false) {
            return false;
        } else {
            return true;
        }
    }

    /**
     * Get the list of files/data from the rar archive.
     *
     * @param string &$data  The rar archive data.
     *
     * @return array  KEY: Position in RAR archive
     *                VALUES: 'attr'    --  File attributes
     *                        'date'    --  File modification time
     *                        'csize'   --  Compressed file size
     *                        'method'  --  Compression method
     *                        'name'    --  Filename
     *                        'size'    --  Original file size
     */
    function getRarData(&$data)
    {
        $return_array = array();

        $blockStart = strpos($data, "\x52\x61\x72\x21\x1a\x07\x00");
        $position = $blockStart + 7;

        while ($position < strlen($data)) {
            $head_crc   = substr($data, $position + 0, 2);
            $head_type  = ord(substr($data, $position + 2, 1));
            $head_flags = unpack('vFlags', substr($data, $position + 3, 2));
            $head_flags = $head_flags['Flags'];
            $head_size  = unpack('vSize', substr($data, $position + 5, 2));
            $head_size  = $head_size['Size'];

            $position += 7;
            $head_size -= 7;

            switch ($head_type) {

            case 0x73:
                /* Archive header */
                $position += $head_size;

                break;

            case 0x74:
                $file = array();

                /* File Header */
                $info = unpack('VPacked/VUnpacked/COS/VCRC32/VTime/CVersion/CMethod/vLength/vAttrib', substr($data, $position));

                $file['name'] = substr($data, $position + 25, $info['Length']);
                $file['size'] = $info['Unpacked'];
                $file['csize'] = $info['Packed'];

                $file['date'] = mktime((($info['Time'] >> 11) & 0x1f),
                                       (($info['Time'] >> 5) & 0x3f),
                                       (($info['Time'] << 1) & 0x3e),
                                       (($info['Time'] >> 21) & 0x07),
                                       (($info['Time'] >> 16) & 0x1f),
                                       ((($info['Time'] >> 25) & 0x7f) + 80));

                $file['method'] = $this->_methods[$info['Method']];

                $file['attr']  = '';
                $file['attr'] .= ($info['Attrib'] & 0x10) ? 'D' : '-';
                $file['attr'] .= ($info['Attrib'] & 0x20) ? 'A' : '-';
                $file['attr'] .= ($info['Attrib'] & 0x03) ? 'S' : '-';
                $file['attr'] .= ($info['Attrib'] & 0x02) ? 'H' : '-';
                $file['attr'] .= ($info['Attrib'] & 0x01) ? 'R' : '-';

                $return_array[] = $file;

                $position += $head_size;
                $position += $info['Packed'];
                break;

            default:
                $position += $head_size;
                if (isset($add_size)) {
                    $position += $add_size;
                }
                break;

            }
        }

        return $return_array;
    }

}
