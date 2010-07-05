<?php

require_once 'Horde/MIME/Viewer/zip.php';

/**
 * The MIME_Viewer_zip class renders out the contents of ZIP files in HTML
 * format and allows downloading of extractable files.
 *
 * $Horde: imp/lib/MIME/Viewer/zip.php,v 1.25.10.13 2009-01-06 15:24:09 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_MIME_Viewer
 */
class IMP_MIME_Viewer_zip extends MIME_Viewer_zip {

    /**
     * The IMP_Contents object, needed for the _callback() function.
     *
     * @var IMP_Contents
     */
    var $_contents;

    /**
     * Render out the currently set contents.
     *
     * @param array $params  An array with a reference to a  MIME_Contents
     *                       object.
     *
     * @return string  Either the list of zip files or the data of an
     *                 individual zip file.
     */
    function render($params)
    {
        $contents = &$params[0];

        $data = $this->mime_part->getContents();
        $text = '';

        /* Send the requested file. Its position in the zip archive is located
         * in 'zip_attachment'. */
        if (Util::getFormData('zip_attachment')) {
            require_once 'Horde/Compress.php';
            $zip = &Horde_Compress::singleton('zip');
            $fileKey = Util::getFormData('zip_attachment') - 1;
            $zipInfo = $zip->decompress(
                $data, array('action' => HORDE_COMPRESS_ZIP_LIST));
            /* Verify that the requested file exists. */
            if (isset($zipInfo[$fileKey])) {
                $text = $zip->decompress(
                    $data,
                    array('action' => HORDE_COMPRESS_ZIP_DATA,
                          'info' => &$zipInfo,
                          'key' => $fileKey));
                if (empty($text)) {
                    $text = '<pre>' . _("Could not extract the requested file from the Zip archive.") . '</pre>';
                } else {
                    $this->mime_part->setType('application/octet-stream');
                    $this->mime_part->setName(basename($zipInfo[$fileKey]['name']));
                }
            } else {
                $text = '<pre>' . _("The requested file does not exist in the Zip attachment.") . '</pre>';
            }
        } else {
            $this->_contents = $contents;
            $text = parent::_render($data, array($this, '_callback'));
        }

        return $text;
    }

    /**
     * The function to use as a callback to parent::_render().
     *
     * @access private
     *
     * @param integer $key  The position of the file in the zip archive.
     * @param array $val    The information array for the archived file.
     *
     * @return string  The content-type of the output.
     */
    function _callback($key, $val)
    {
        $name = preg_replace('/(&nbsp;)+$/', '', $val['name']);
        if (!empty($val['size']) && (strstr($val['attr'], 'D') === false) &&
            ((($val['method'] == 0x8) && Util::extensionExists('zlib')) ||
             ($val['method'] == 0x0))) {
            $old_name = $this->mime_part->getName();
            $this->mime_part->setName(basename($name));
            $val['name'] = str_replace(
                $name,
                $this->_contents->linkView(
                    $this->mime_part, 'download_render', $name,
                    array('jstext' => sprintf(_("View %s"),
                                              str_replace('&nbsp;', ' ', $name)),
                          'class' => 'fixed',
                          'viewparams' => array(
                              'ctype' => 'application/zip',
                              'zip_attachment' => (urlencode($key) + 1)))),
                $val['name']);
            $this->mime_part->setName($old_name);
        }

        return $val;
    }

}
