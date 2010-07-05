<?php

/**
 * Strategy for writing file to temporary directory, then copying to VFS.
 *
 * $Horde: framework/VFS_ISOWriter/ISOWriter/RealOutputStrategy/copy.php,v 1.1.8.8 2009-01-06 15:23:49 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jason M. Felice <jason.m.felice@gmail.com>
 * @package VFS_ISO
 * @since   Horde 3.0
 */
class VFS_ISOWriter_RealOutputStrategy_copy extends VFS_ISOWriter_RealOutputStrategy {

    var $_tempFilename = null;

    /**
     * Get a real filename to which we can write.
     *
     * In this implementation, we create and store a temporary filename.
     */
    function getRealFilename()
    {
        if (is_null($this->_tempFilename)) {

            $tmp_locations = array('/tmp', '/var/tmp', 'c:\WUTemp', 'c:\temp',
                                   'c:\windows\temp', 'c:\winnt\temp');

            /* First, try PHP's upload_tmp_dir directive. */
            $tmp = ini_get('upload_tmp_dir');

            /* Otherwise, try to determine the TMPDIR environment
             * variable. */
            if (empty($tmp)) {
                $tmp = getenv('TMPDIR');
            }

            /* If we still cannot determine a value, then cycle through a
             * list of preset possibilities. */
            while (empty($tmp) && count($tmp_locations)) {
                $tmp_check = array_shift($tmp_locations);
                if (@is_dir($tmp_check)) {
                    $tmp = $tmp_check;
                }
            }

            if (empty($tmp)) {
                return PEAR::raiseError(_("Cannot find a temporary directory."));
            }

            $this->_tempFilename = tempnam($tmp, 'iso');
        }

        return $this->_tempFilename;
    }

    function finished()
    {
        if (empty($this->_tempFilename)) {
            return;
        }
        if (!file_exists($this->_tempFilename)) {
            return;
        }

        if (preg_match('!^(.*)/([^/]*)$!', $this->_targetFile, $matches)) {
            $dir = $matches[1];
            $file = $matches[2];
        } else {
            $dir = '';
            $file = $this->_targetFile;
        }

        $res = $this->_targetVfs->write($dir, $file, $this->_tempFilename,
                                        true);
        @unlink($this->_tempFilename);
        $this->_tempFilename = null;
        return $res;
    }

}

