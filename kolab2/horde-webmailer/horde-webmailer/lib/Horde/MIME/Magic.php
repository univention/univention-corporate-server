<?php

require_once 'Horde/Util.php';

/**
 * The MIME_Magic:: class provides an interface to determine a
 * MIME type for various content, if it provided with different
 * levels of information.
 *
 * $Horde: framework/MIME/MIME/Magic.php,v 1.52.8.18 2009-01-06 15:23:20 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_MIME
 */
class MIME_Magic {

    /**
     * Returns a copy of the MIME extension map.
     *
     * @access private
     *
     * @return array  The MIME extension map.
     */
    function _getMimeExtensionMap()
    {
        static $mime_extension_map;

        if (!isset($mime_extension_map)) {
            require dirname(__FILE__) . '/mime.mapping.php';
        }

        return $mime_extension_map;
    }

    /**
     * Returns a copy of the MIME magic file.
     *
     * @access private
     *
     * @return array  The MIME magic file.
     */
    function _getMimeMagicFile()
    {
        static $mime_magic;

        if (!isset($mime_magic)) {
            require dirname(__FILE__) . '/mime.magic.php';
        }

        return $mime_magic;
    }

    /**
     * Attempt to convert a file extension to a MIME type, based
     * on the global Horde and application specific config files.
     *
     * If we cannot map the file extension to a specific type, then
     * we fall back to a custom MIME handler 'x-extension/$ext', which
     * can be used as a normal MIME type internally throughout Horde.
     *
     * @param string $ext  The file extension to be mapped to a MIME type.
     *
     * @return string  The MIME type of the file extension.
     */
    function extToMIME($ext)
    {
        if (empty($ext)) {
           return 'application/octet-stream';
        } else {
            $ext = String::lower($ext);
            $map = MIME_Magic::_getMimeExtensionMap();
            $pos = 0;
            while (!isset($map[$ext]) && $pos !== false) {
                $pos = strpos($ext, '.');
                if ($pos !== false) {
                    $ext = substr($ext, $pos + 1);
                }
            }

            if (isset($map[$ext])) {
                return $map[$ext];
            } else {
                return 'x-extension/' . $ext;
            }
        }
    }

    /**
     * Attempt to convert a filename to a MIME type, based on the global Horde
     * and application specific config files.
     *
     * @param string $filename  The filename to be mapped to a MIME type.
     * @param boolean $unknown  How should unknown extensions be handled? If
     *                          true, will return 'x-extension/*' types.  If
     *                          false, will return 'application/octet-stream'.
     *
     * @return string  The MIME type of the filename.
     */
    function filenameToMIME($filename, $unknown = true)
    {
        $pos = strlen($filename) + 1;
        $type = '';

        $map = MIME_Magic::_getMimeExtensionMap();
        for ($i = 0;
             $i <= $map['__MAXPERIOD__'] &&
                 strrpos(substr($filename, 0, $pos - 1), '.') !== false;
             $i++) {
            $pos = strrpos(substr($filename, 0, $pos - 1), '.') + 1;
        }
        $type = MIME_Magic::extToMIME(substr($filename, $pos));

        if (empty($type) ||
            (!$unknown && (strpos($type, 'x-extension') !== false))) {
            return 'application/octet-stream';
        } else {
            return $type;
        }
    }

    /**
     * Attempt to convert a MIME type to a file extension, based
     * on the global Horde and application specific config files.
     *
     * If we cannot map the type to a file extension, we return false.
     *
     * @param string $type  The MIME type to be mapped to a file extension.
     *
     * @return string  The file extension of the MIME type.
     */
    function MIMEToExt($type)
    {
        if (empty($type)) {
            return false;
        }

        $key = array_search($type, MIME_Magic::_getMimeExtensionMap());
        if ($key === false) {
            list($major, $minor) = explode('/', $type);
            if ($major == 'x-extension') {
                return $minor;
            }
            if (strpos($minor, 'x-') === 0) {
                return substr($minor, 2);
            }
            return false;
        } else {
            return $key;
        }
    }

    /**
     * Uses variants of the UNIX "file" command to attempt to determine the
     * MIME type of an unknown file.
     *
     * @param string $path      The path to the file to analyze.
     * @param string $magic_db  Path to the mime magic database.
     *
     * @return string  The MIME type of the file.  Returns false if the file
     *                 type isn't recognized or an error happened.
     */
    function analyzeFile($path, $magic_db = null)
    {
        /* If the PHP Mimetype extension is available, use that. */
        if (Util::extensionExists('fileinfo')) {
            if (empty($magic_db)) {
                $res = @finfo_open(FILEINFO_MIME);
            } else {
                $res = @finfo_open(FILEINFO_MIME, $magic_db);
            }
            if ($res) {
                $type = finfo_file($res, $path);
                finfo_close($res);

                /* Remove any additional information. */
                foreach (array(';', ',', '\\0') as $separator) {
                    $pos = strpos($type, $separator);
                    if ($pos !== false) {
                        $type = rtrim(substr($type, 0, $pos));
                    }
                }

                if (preg_match('|^[a-z0-9]+/[.-a-z0-9]+$|i', $type)) {
                    return $type;
                }
            }
        }

        if (Util::extensionExists('mime_magic')) {
            return trim(mime_content_type($path));
        } else {
            /* Use a built-in magic file. */
            $mime_magic = MIME_Magic::_getMimeMagicFile();
            if (!($fp = @fopen($path, 'rb'))) {
                return false;
            }
            while (list($offset, $odata) = each($mime_magic)) {
                while (list($length, $ldata) = each($odata)) {
                    @fseek($fp, $offset, SEEK_SET);
                    $lookup = @fread($fp, $length);
                    if (!empty($ldata[$lookup])) {
                        fclose($fp);
                        return $ldata[$lookup];
                    }
                }
            }
            fclose($fp);
        }

        return false;
    }


    /**
     * Uses variants of the UNIX "file" command to attempt to determine the
     * MIME type of an unknown byte stream.
     *
     * @param string $data      The file data to analyze.
     * @param string $magic_db  Path to the mime magic database.
     *
     * @return string  The MIME type of the file.  Returns false if the file
     *                 type isn't recognized or an error happened.
     */
    function analyzeData($data, $magic_db = null)
    {
        /* If the PHP Mimetype extension is available, use that. */
        if (Util::extensionExists('fileinfo')) {
            if (empty($magic_db)) {
                $res = @finfo_open(FILEINFO_MIME);
            } else {
                $res = @finfo_open(FILEINFO_MIME, $magic_db);
            }
            if (!$res) {
                return false;
            }

            $type = finfo_buffer($res, $data);
            finfo_close($res);

            /* Remove any additional information. */
            $pos = strpos($type, ';');
            if ($pos !== false) {
                $type = rtrim(substr($type, 0, $pos));
            }
            $pos = strpos($type, ',');
            if ($pos !== false) {
                $type = rtrim(substr($type, 0, $pos));
            }
            return $type;
        }

        /* Use a built-in magic file. */
        $mime_magic = MIME_Magic::_getMimeMagicFile();
        while (list($offset, $odata) = each($mime_magic)) {
            while (list($length, $ldata) = each($odata)) {
                $lookup = substr($data, $offset, $length);
                if (!empty($ldata[$lookup])) {
                    return $ldata[$lookup];
                }
            }
        }

        return false;
    }

}
