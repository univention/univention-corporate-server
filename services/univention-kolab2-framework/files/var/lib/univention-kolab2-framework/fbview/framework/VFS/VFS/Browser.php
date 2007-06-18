<?php
/**
 * Class for providing a generic UI for any VFS instance.
 *
 * $Horde: framework/VFS/VFS/Browser.php,v 1.8 2004/04/08 18:33:17 slusarz Exp $
 *
 * Copyright 2002-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.2
 * @package VFS
 */
class VFS_Browser {

    /**
     * The VFS instance that we are browsing.
     *
     * @var object VFS $_vfs
     */
    var $_vfs;

    /**
     * The directory where the templates to use are.
     *
     * @var string $_templates
     */
    var $_templates;

    /**
     * Constructor
     *
     * @access public
     *
     * @param object VFS &$vfs   A VFS object.
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
     * @access public
     *
     * @param object VFS &$vfs  A VFS object.
     */
    function setVFSObject(&$vfs)
    {
        $this->_vfs = &$vfs;
    }

    /**
     * TODO
     *
     * @access public
     *
     * @param string $path                TODO
     * @param optional boolean $dotfiles  TODO
     * @param optional boolean $dironly   TODO
     */
    function getUI($path, $dotfiles = false, $dironly = false)
    {
        $this->_vfs->listFolder($path, $dotfiles, $dironly);
    }

}
