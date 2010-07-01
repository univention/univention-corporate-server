<?php
/**
 * The SyncML_Device_Nokia:: class provides functionality that is
 * specific to the Nokia SyncML clients.
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * $Horde: framework/SyncML/SyncML/Device/Nokia.php,v 1.2.2.12 2009-08-18 17:21:11 jan Exp $
 *
 * @author  Karsten Fourmont <karsten@horde.org>
 * @package SyncML
 */
class SyncML_Device_Nokia extends SyncML_Device {

    /**
     * Converts the content received from the client for the backend.
     *
     * @param string $content      The content to convert.
     * @param string $contentType  The content type of the content.
     *
     * @return array  Two-element array with the converted content and the
     *                (possibly changed) new content type.
     */
    function convertClient2Server($content, $contentType)
    {
        list($content, $contentType) =
            parent::convertClient2Server($content, $contentType);

        /* At least the Nokia E series seems to prefix category values with
         * X-, see bugs #6849 and #7824. */
        $di = $_SESSION['SyncML.state']->deviceInfo;
        if ($di->Mod[0] == 'E') {
            $content = preg_replace('/(\r\n|\r|\n)CATEGORIES:X-/',
                                    '\1CATEGORIES:', $content, 1);
        }

        $GLOBALS['backend']->logFile(
            SYNCML_LOGFILE_DATA,
            "\nInput converted for server ($contentType):\n$content\n");

        return array($content, $contentType);
    }

    function convertServer2Client($content, $contentType, $database)
    {
        $database = $GLOBALS['backend']->_normalize($database);

        list($content, $contentType, $encodingType) =
            parent::convertServer2Client($content, $contentType, $database);

        $content = preg_replace('/(\r\n|\r|\n)PHOTO;ENCODING=b[^:]*:(.+?)(\r\n|\r|\n)/',
                                '\1PHOTO;ENCODING=BASE64:\1\2\1\1',
                                $content, 1);

        $GLOBALS['backend']->logFile(
            SYNCML_LOGFILE_DATA,
            "\nOutput converted for client ($contentType):\n$content\n");

        return array($content, $contentType);
    }

    function handleTasksInCalendar()
    {
        return true;
    }

    /**
     * Some devices accept datetimes only in local time format:
     * DTSTART:20061222T130000
     * instead of the more robust (and default) UTC time:
     * DTSTART:20061222T110000Z
     */
    function useLocalTime()
    {
        return true;
    }

}
