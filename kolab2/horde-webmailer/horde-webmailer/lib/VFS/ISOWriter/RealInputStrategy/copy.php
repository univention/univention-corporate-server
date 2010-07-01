<?php

/**
 * Strategy for copying input tree out of a VFS
 *
 * $Horde: framework/VFS_ISOWriter/ISOWriter/RealInputStrategy/copy.php,v 1.1.8.9 2009-01-06 15:23:48 jan Exp $
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
class VFS_ISOWriter_RealInputStrategy_copy extends VFS_ISOWriter_RealInputStrategy {

    var $_tempPath = null;

    function getRealPath()
    {
        if (is_null($this->_tempPath)) {
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

            $this->_tempPath = tempnam($tmp, 'isod');
            @unlink($this->_tempPath);

            $res = $this->_copyToTempPath();
            if (is_a($res, 'PEAR_Error')) {
                return $res;
            }
        }

        return $this->_tempPath;
    }

    function finished()
    {
        return VFS_ISOWriter_RealInputStrategy_copy::_removeRecursive($this->_tempPath);
    }

    function _removeRecursive($path)
    {
        $dh = @opendir($path);
        if (!is_resource($dh)) {
            return PEAR::raiseError(sprintf(_("Could not open directory \"%s\"."),
                                            $path));
        }
        while (($ent = readdir($dh)) !== false) {
            if ($ent == '.' || $ent == '..') {
                continue;
            }

            $full = sprintf('%s/%s', $path, $ent);
            if (is_dir($full)) {
                $res = VFS_ISOWriter_RealInputStrategy_copy::_removeRecursive($full);
                if (is_a($res, 'PEAR_Error')) {
                    return $res;
                }
            } else {
                if (!@unlink($full)) {
                    return PEAR::raiseError(sprintf(_("Could not unlink \"%s\"."),
                                                    $full));
                }
            }
        }
        closedir($dh);

        if (!@rmdir($path)) {
            return PEAR::raiseError(sprintf(_("Could not rmdir \"%s\"."), $full));
        }
    }

    function _copyToTempPath()
    {
        $dirStack = array('');

        while (count($dirStack) > 0) {
            $dir = array_shift($dirStack);
            if (empty($dir)) {
                $target = $this->_tempPath;
            } else {
                $target = sprintf('%s/%s', $this->_tempPath, $dir);
            }
            if (!@mkdir($target)) {
                return PEAR::raiseError(sprintf(_("Could not mkdir \"%s\"."), $target));
            }

            $sourcePath = $this->_sourceRoot;
            if (!empty($dir)) {
                $sourcePath .= '/' . $dir;
            }

            $list = $this->_sourceVfs->listFolder($sourcePath, null, true);
            if (is_a($list, 'PEAR_Error')) {
                return $list;
            }

            foreach ($list as $entry) {
                if ($entry['type'] == '**dir') {
                    if (empty($dir)) {
                        $dirStack[] = $entry['name'];
                    } else {
                        $dirStack[] = sprintf('%s/%s', $dir, $entry['name']);
                    }
                } else {
                    $data = $this->_sourceVfs->read($sourcePath, $entry['name']);
                    if (is_a($data, 'PEAR_Error')) {
                        return $data;
                    }

                    $targetFile = sprintf('%s/%s', $target, $entry['name']);
                    $fh = @fopen($targetFile, 'w');
                    if (!is_resource($fh)) {
                        return PEAR::raiseError(sprintf(_("Could not open \"%s\" for writing."), $targetFile));
                    }
                    if (fwrite($fh, $data) != strlen($data)) {
                        return PEAR::raiseError(sprintf(_("Error writing \"%s\"."), $targetFile));
                    }
                    fclose($fh);
                }
            }
        }
    }

}
