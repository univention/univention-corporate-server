<?php
/**
 * @package Kolab_Storage
 *
 * $Horde: framework/Kolab_Storage/lib/Horde/Kolab/Storage.php,v 1.2.2.3 2009-01-06 15:23:17 jan Exp $
 */

/** Load the handler for the folder list management. */
require_once 'Horde/Kolab/Storage/List.php';

/**
 * The Kolab_Storage class provides the means to access the Kolab server
 * storage for groupware objects.
 *
 * To get access to the folder handling you would do the following:
 *
 *   <code>
 *     require_once 'Horde/Kolab/Storage.php';
 *     $folder = Kolab_Storage::getFolder('INBOX/Calendar');
 *   </code>
 *
 *  or (in case you are dealing with share identifications):
 *
 *   <code>
 *     require_once 'Horde/Kolab/Storage.php';
 *     $folder = Kolab_Storage::getShare(Auth::getAuth(), 'event');
 *   </code>
 *
 * To access data in a share (or folder) you need to retrieve the
 * corresponding data object:
 *
 *   <code>
 *     require_once 'Horde/Kolab/Storage.php';
 *     $folder = Kolab_Storage::getShareData(Auth::getAuth(), 'event');
 *   </code>
 *
 * $Horde: framework/Kolab_Storage/lib/Horde/Kolab/Storage.php,v 1.2.2.3 2009-01-06 15:23:17 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @package Kolab_Storage
 */
class Kolab_Storage {

    /**
     * Return the folder object corresponding to the share of the
     * specified type (e.g. "contact", "event" etc.).
     *
     * @param string $share   The id of the share.
     * @param string $type    The share type.
     *
     * @return Kolab_Folder|PEAR_Error The folder object representing
     *                                 the share.
     */
    function &getShare($share, $type)
    {
        $list = &Kolab_List::singleton();
        $share = $list->getByShare($share, $type);
        return $share;
    }

    /**
     * Return the folder object.
     *
     * @param string $folder   The name of the folder.
     *
     * @return Kolab_Folder|PEAR_Error The folder object.
     */
    function &getFolder($folder)
    {
        $list = &Kolab_List::singleton();
        $share = $list->getFolder($folder);
        return $share;
    }

    /**
     * Return a data object for accessing data in the specified
     * folder.
     *
     * @param Kolab_Folder $folder    The folder object.
     * @param string $data_type       The type of data we want to
     *                                access in the folder.
     * @param int    $data_format     The version of the data format
     *                                we want to access in the folder.
     *
     * @return Kolab_Data|PEAR_Error The data object.
     */
    function &getData(&$folder, $data_type = null, $data_format = 1)
    {
        if (empty($data_type)) {
            $data_type = $folder->getType();
        }
        $data = $folder->getData($data_type, $data_format);
        return $data;
    }

    /**
     * Return a data object for accessing data in the specified
     * share.
     *
     * @param string $share        The id of the share.
     * @param string $type         The share type.
     * @param string $data_type    The type of data we want to
     *                             access in the folder.
     * @param int    $data_format  The version of the data format
     *                             we want to access in the folder.
     *
     * @return Kolab_Data|PEAR_Error The data object.
     */
    function &getShareData($share, $type, $data_type = null, $data_format = 1)
    {
        $folder = Kolab_Storage::getShare($share, $type);
        if (is_a($folder, 'PEAR_Error')) {
            return $folder;
        }
        $data = Kolab_Storage::getData($folder, $data_type, $data_format);
        return $data;
    }

    /**
     * Return a data object for accessing data in the specified
     * folder.
     *
     * @param string $folder       The name of the folder.
     * @param string $data_type    The type of data we want to
     *                             access in the folder.
     * @param int    $data_format  The version of the data format
     *                             we want to access in the folder.
     *
     * @return Kolab_Data|PEAR_Error The data object.
     */
    function &getFolderData($folder, $data_type = null, $data_format = 1)
    {
        $folder = Kolab_Storage::getFolder($folder);
        if (is_a($folder, 'PEAR_Error')) {
            return $folder;
        }
        $data = Kolab_Storage::getData($folder, $data_type, $data_format);
        return $data;
    }
}

