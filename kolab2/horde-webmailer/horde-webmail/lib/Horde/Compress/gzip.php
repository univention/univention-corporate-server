<?php
/**
 * The Horde_Compress_gzip class allows gzip files to be read.
 *
 * $Horde: framework/Compress/Compress/gzip.php,v 1.7.12.13 2009-01-06 15:22:59 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Cochrane <mike@graftonhall.co.nz>
 * @author  Michael Slusarz <slusarz@horde.org>
 * @since   Horde 3.0
 * @package Horde_Compress
 */
class Horde_Compress_gzip extends Horde_Compress {

    /**
     * Gzip file flags.
     *
     * @var array
     */
    var $_flags = array(
        'FTEXT'     =>  0x01,
        'FHCRC'     =>  0x02,
        'FEXTRA'    =>  0x04,
        'FNAME'     =>  0x08,
        'FCOMMENT'  =>  0x10
    );

    /**
     * Decompress a gzip file and get information from it.
     *
     * @param string &$data  The tar file data.
     * @param array $params  The parameter array (Unused).
     *
     * @return string  The uncompressed data.
     */
    function decompress(&$data, $params = array())
    {
        /* If gzip is not compiled into PHP, return now. */
        if (!Util::extensionExists('zlib')) {
            return PEAR::raiseError(_("This server can't uncompress zip and gzip files."));
        }

        /* Gzipped File - decompress it first. */
        $position = 0;
        $info = @unpack('CCM/CFLG/VTime/CXFL/COS', substr($data, $position + 2));
        if (!$info) {
            return PEAR::raiseError(_("Unable to decompress data."));
        }
        $position += 10;

        if ($info['FLG'] & $this->_flags['FEXTRA']) {
            $XLEN = unpack('vLength', substr($data, $position + 0, 2));
            $XLEN = $XLEN['Length'];
            $position += $XLEN + 2;
        }

        if ($info['FLG'] & $this->_flags['FNAME']) {
            $filenamePos = strpos($data, "\x0", $position);
            $filename = substr($data, $position, $filenamePos - $position);
            $position = $filenamePos + 1;
        }

        if ($info['FLG'] & $this->_flags['FCOMMENT']) {
            $commentPos = strpos($data, "\x0", $position);
            $comment = substr($data, $position, $commentPos - $position);
            $position = $commentPos + 1;
        }

        if ($info['FLG'] & $this->_flags['FHCRC']) {
            $hcrc = unpack('vCRC', substr($data, $position + 0, 2));
            $hcrc = $hcrc['CRC'];
            $position += 2;
        }

        $result = @gzinflate(substr($data, $position, strlen($data) - $position));
        if (empty($result)) {
            return PEAR::raiseError(_("Unable to decompress data."));
        }

        return $result;
    }

}
