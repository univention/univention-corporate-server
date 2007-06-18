<?php
/**
 * An item returned from a folder list.
 *
 * $Horde: framework/VFS/VFS/ListItem.php,v 1.11 2004/04/08 18:33:17 slusarz Exp $
 *
 * Copyright 2002-2004 Jon Wood <jon@jellybob.co.uk>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jon Wood <jon@jellybob.co.uk>
 * @version $Revision: 1.1.2.1 $
 * @package VFS
 * @since   Horde 2.2
 */
class VFS_ListItem {

    /**
     * VFS path
     *
     * @var string $_path
     */
    var $_path;

    /**
     * Filename
     *
     * @var string $_name
     */
    var $_name;

    /**
     * File permissions (*nix format: drwxrwxrwx)
     *
     * @var string $_perms
     */
    var $_perms;

    /**
     * Owner user
     *
     * @var string $_owner
     */
    var $_owner;

    /**
     * Owner group
     *
     * @var string $_group
     */
    var $_group;

    /**
     * Size.
     *
     * @var string $_size
     */
    var $_size;

    /**
     * Last modified date.
     *
     * @var string $_date
     */
    var $_date;

    /**
     * Type
     *   .*      --  File extension
     *   **none  --  Unrecognized type
     *   **sym   --  Symlink
     *   **dir   --  Directory
     *
     * @var string $_type
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
     * @var string $_linktype
     */
    var $_linktype;

    /**
     * Constructor
     *
     * Requires the path to the file, and it's array of properties,
     * returned from a standard VFS::listFolder() call.
     *
     * @access public
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
