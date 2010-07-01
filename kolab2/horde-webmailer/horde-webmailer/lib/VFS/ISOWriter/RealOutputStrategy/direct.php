<?php

/**
 * Strategy for directly writing output file to VFS.
 *
 * $Horde: framework/VFS_ISOWriter/ISOWriter/RealOutputStrategy/direct.php,v 1.1.8.9 2009-01-06 15:23:49 jan Exp $
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
class VFS_ISOWriter_RealOutputStrategy_direct extends VFS_ISOWriter_RealOutputStrategy {

    function getRealFilename()
    {
        /* So we shouldn't be accessing _getNativePath().  If we had real
         * access control, that would be protected and we'd be a friend, as
         * that is the point of this excercise. */
        $filename = $this->_targetVfs->_getNativePath($this->_targetFile);

        /* Make sure the path to the file exists. */
        $dir = dirname($filename);
        while (!@is_dir($dir)) {
            if (!@mkdir($dir, 0755)) {
                return PEAR::raiseError(sprintf(_("Could not mkdir \"%s\"."),
                                                $dir));
            }
            $dir = dirname($dir);
        }

        return $filename;
    }

    function finished()
    {
        /* Nothing to do. */
    }

}

