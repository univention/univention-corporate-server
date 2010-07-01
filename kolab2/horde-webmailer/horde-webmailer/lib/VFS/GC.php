<?php
/**
 * Class for providing garbage collection for any VFS instance.
 *
 * $Horde: framework/VFS/lib/VFS/GC.php,v 1.1.2.3 2009-01-06 15:23:47 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package VFS
 */
class VFS_GC {

    /**
     * Garbage collect files in the VFS storage system.
     *
     * @param VFS &$vfs      The VFS object to perform garbage collection on.
     * @param string $path   The VFS path to clean.
     * @param integer $secs  The minimum amount of time (in seconds) required
     *                       before a file is removed.
     */
    function gc(&$vfs, $path, $secs = 345600)
    {
        /* A 1% chance we will run garbage collection during a call. */
        if (rand(0, 99) != 0) {
            return;
        }

        /* Use a backend-specific method if one exists. */
        if (is_callable(array($vfs, 'gc'))) {
            return $vfs->gc($path, $secs);
        }

        /* Make sure cleaning is done recursively. */
        $files = $vfs->listFolder($path, null, true, false, true);
        if (!is_a($files, 'PEAR_Error') && is_array($files)) {
            $modtime = time() - $secs;
            foreach ($files as $val) {
                if ($val['date'] < $modtime) {
                    $vfs->deleteFile($path, $val['name']);
                }
            }
        }
    }

}
