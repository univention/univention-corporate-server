<?php
/**
 * The Horde_Compress_tar class allows tar files to be read.
 *
 * $Horde: framework/Compress/Compress/tar.php,v 1.4.12.13 2009-01-06 15:22:59 jan Exp $
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
class Horde_Compress_tar extends Horde_Compress {

    /**
     * Tar file types.
     *
     * @var array
     */
    var $_types = array(
        0x0   =>  'Unix file',
        0x30  =>  'File',
        0x31  =>  'Link',
        0x32  =>  'Symbolic link',
        0x33  =>  'Character special file',
        0x34  =>  'Block special file',
        0x35  =>  'Directory',
        0x36  =>  'FIFO special file',
        0x37  =>  'Contiguous file'
    );

    /**
     * Tar file flags.
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
     * Decompress a tar file and get information from it.
     *
     * @param string &$data   The tar file data.
     * @param array $params  The parameter array (Unused).
     *
     * @return array  The requested data or PEAR_Error on error.
     * <pre>
     * KEY: Position in the array
     * VALUES: 'attr'  --  File attributes
     *         'data'  --  Raw file contents
     *         'date'  --  File modification time
     *         'name'  --  Filename
     *         'size'  --  Original file size
     *         'type'  --  File type
     * </pre>
     */
    function decompress(&$data, $params = array())
    {
        $position = 0;
        $return_array = array();

        while ($position < strlen($data)) {
            $info = @unpack("a100filename/a8mode/a8uid/a8gid/a12size/a12mtime/a8checksum/Ctypeflag/a100link/a6magic/a2version/a32uname/a32gname/a8devmajor/a8devminor", substr($data, $position));
            if (!$info) {
                return PEAR::raiseError(_("Unable to decompress data."));
            }

            $position += 512;
            $contents = substr($data, $position, octdec($info['size']));
            $position += ceil(octdec($info['size']) / 512) * 512;

            if ($info['filename']) {
                $file = array(
                    'attr' => null,
                    'data' => null,
                    'date' => octdec($info['mtime']),
                    'name' => trim($info['filename']),
                    'size' => octdec($info['size']),
                    'type' => isset($this->_types[$info['typeflag']]) ? $this->_types[$info['typeflag']] : null
                );

                if (($info['typeflag'] == 0) ||
                    ($info['typeflag'] == 0x30) ||
                    ($info['typeflag'] == 0x35)) {
                    /* File or folder. */
                    $file['data'] = $contents;

                    $mode = hexdec(substr($info['mode'], 4, 3));
                    $file['attr'] =
                        (($info['typeflag'] == 0x35) ? 'd' : '-') .
                        (($mode & 0x400) ? 'r' : '-') .
                        (($mode & 0x200) ? 'w' : '-') .
                        (($mode & 0x100) ? 'x' : '-') .
                        (($mode & 0x040) ? 'r' : '-') .
                        (($mode & 0x020) ? 'w' : '-') .
                        (($mode & 0x010) ? 'x' : '-') .
                        (($mode & 0x004) ? 'r' : '-') .
                        (($mode & 0x002) ? 'w' : '-') .
                        (($mode & 0x001) ? 'x' : '-');
                } else {
                    /* Some other type. */
                }

                $return_array[] = $file;
            }
        }

        return $return_array;
    }

}
