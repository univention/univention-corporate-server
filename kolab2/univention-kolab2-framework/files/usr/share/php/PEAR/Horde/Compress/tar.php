<?php
/**
 * The Horde_Compress_tar class allows tar files to be read.
 *
 * $Horde: framework/Compress/Compress/tar.php,v 1.4 2004/01/01 15:14:13 jan Exp $
 *
 * Copyright 2002-2004 Michael Cochrane <mike@graftonhall.co.nz>
 * Copyright 2003-2004 Michael Slusarz <slusarz@bigworm.colorado.edu>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Cochrane <mike@graftonhall.co.nz>
 * @author  Michael Slusarz <slusarz@bigworm.colorado.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Compress
 */
class Horde_Compress_tar extends Horde_Compress {

    /**
     * Tar file types.
     *
     * @var array $_types
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
     * @var array $_flags
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
     * @access public
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
    function &decompress(&$data, $params = array())
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
                $file = array();

                $file['size'] = octdec($info['size']);
                $file['date'] = octdec($info['mtime']);
                $file['name'] = trim($info['filename']);

                if (array_key_exists($info['typeflag'], $this->_types)) {
                   $file['type'] = $this->_types[$info['typeflag']];
                } else {
                   $file['type'] = '';
                }
                $file['data'] = '';
                $file['attr'] = '';

                if (($info['typeflag'] == 0) ||
                    ($info['typeflag'] == 0x30) ||
                    ($info['typeflag'] == 0x35)) {
                    /* File or folder. */
                    $file['data'] = $contents;

                    $file['attr']  = ($info['typeflag'] == 0x35) ? 'd' : '-';
                    $file['attr'] .= (hexdec(substr($info['mode'], 4, 3)) & 0x400) ? 'r' : '-';
                    $file['attr'] .= (hexdec(substr($info['mode'], 4, 3)) & 0x200) ? 'w' : '-';
                    $file['attr'] .= (hexdec(substr($info['mode'], 4, 3)) & 0x100) ? 'x' : '-';
                    $file['attr'] .= (hexdec(substr($info['mode'], 4, 3)) & 0x040) ? 'r' : '-';
                    $file['attr'] .= (hexdec(substr($info['mode'], 4, 3)) & 0x020) ? 'w' : '-';
                    $file['attr'] .= (hexdec(substr($info['mode'], 4, 3)) & 0x010) ? 'x' : '-';
                    $file['attr'] .= (hexdec(substr($info['mode'], 4, 3)) & 0x004) ? 'r' : '-';
                    $file['attr'] .= (hexdec(substr($info['mode'], 4, 3)) & 0x002) ? 'w' : '-';
                    $file['attr'] .= (hexdec(substr($info['mode'], 4, 3)) & 0x001) ? 'x' : '-';
                } else {
                    /* Some other type. */
                }

                $return_array[] = $file;
            }
        }

        return $return_array;
    }

}
