<?php
/**
 * An item returned from a folder list.
 *
 * $Horde: framework/VFS/lib/VFS/ListItem.php,v 1.1.2.1 2007-12-20 13:50:21 jan Exp $
 *
 * Copyright 2002-2007 Jon Wood <jon@jellybob.co.uk>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jon Wood <jon@jellybob.co.uk>
 * @package VFS
 */
class VFS_ListItem {

    /**
     * VFS path
     *
     * @var string
     */
    var $_path;

    /**
     * Filename
     *
     * @var string
     */
    var $_name;

    /**
     * File permissions (*nix format: drwxrwxrwx)
     *
     * @var string
     */
    var $_perms;

    /**
     * Owner user
     *
     * @var string
     */
    var $_owner;

    /**
     * Owner group
     *
     * @var string
     */
    var $_group;

    /**
     * Size.
     *
     * @var string
     */
    var $_size;

    /**
     * Last modified date.
     *
     * @var string
     */
    var $_date;

    /**
     * Type
     *   .*      --  File extension
     *   **none  --  Unrecognized type
     *   **sym   --  Symlink
     *   **dir   --  Directory
     *
     * @var string
     */
    var $_type;

    /**
     * Type of target if type is '**sym'.
     * NB. Not all backends are capable of distinguishing all of these.
     *   .*        --  File extension
     *   **none    --  Unrecognized type
     *   **sym     --  Symlink to a symlink
     *   **dir     --  Directory
     *   **broken  --  Target not found - broken link
     *
     * @var string
     */
    var $_linktype;

    /**
     * Constructor
     *
     * Requires the path to the file, and it's array of properties,
     * returned from a standard VFS::listFolder() call.
     *
     * @param string $path      The path to the file.
     * @param array $fileArray  An array of file properties.
     */
    function VFS_ListItem($path, $fileArray)
    {
        $this->_path = $path . '/' . $fileArray['name'];
        $this->_name = $fileArray['name'];
        $this->_dirname = $path;
        $this->_perms = $fileArray['perms'];
        $this->_owner = $fileArray['owner'];
        $this->_group = $fileArray['group'];
        $this->_size = $fileArray['size'];
        $this->_date = $fileArray['date'];
        $this->_type = $fileArray['type'];
        $this->_linktype = $fileArray['linktype'];
    }

}
