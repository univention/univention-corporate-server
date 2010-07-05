<?php
/**
 * Class for providing a generic UI for any VFS instance.
 *
 * $Horde: framework/VFS/lib/VFS/Browser.php,v 1.1.2.3 2009-01-06 15:23:47 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @package VFS
 */
class VFS_Browser {

    /**
     * The VFS instance that we are browsing.
     *
     * @var VFS
     */
    var $_vfs;

    /**
     * The directory where the templates to use are.
     *
     * @var string
     */
    var $_templates;

    /**
     * Constructor
     *
     * @param VFS &$vfs          A VFS object.
     * @param string $templates  TODO
     */
    function VFS_Browser(&$vfs, $templates)
    {
        if (isset($vfs)) {
            $this->_vfs = $vfs;
        }
        $this->_templates = $templates;
    }

    /**
     * Set the VFS object in the local object.
     *
     * @param VFS &$vfs  A VFS object.
     */
    function setVFSObject(&$vfs)
    {
        $this->_vfs = &$vfs;
    }

    /**
     * TODO
     *
     * @param string $path       TODO
     * @param boolean $dotfiles  TODO
     * @param boolean $dironly   TODO
     */
    function getUI($path, $dotfiles = false, $dironly = false)
    {
        $this->_vfs->listFolder($path, $dotfiles, $dironly);
    }

}
