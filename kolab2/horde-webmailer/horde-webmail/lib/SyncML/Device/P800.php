<?php
/**
 * P800/P900/P910:
 * ---------------
 * Charset:
 * This device is able to handle UTF-8 and sends its XML packages in UTF8.
 * However even though the XML itself is UTF-8, it expects the enclosed
 * vcard-data to be ISO-8859-1 unless explicitly stated otherwise (using the
 * CHARSET option, which is deprecated for VCARD 3.0)
 *
 * Encoding:
 * String values are encoded "QUOTED-PRINTABLE"
 *
 * Other:
 * This devices handles tasks and events in one database.
 *
 * As the P800 was the first device to work with package, most of the
 * required conversions are in Device.php's default handling.
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * $Horde: framework/SyncML/SyncML/Device/P800.php,v 1.7.2.14 2009-01-06 15:23:39 jan Exp $
 *
 * @author  Karsten Fourmont <karsten@horde.org>
 * @package SyncML
 */
class SyncML_Device_P800 extends SyncML_Device {

    /**
     * Convert the content.
     *
     * @param string $content       The content to convert.
     * @param string $contentType   The contentType of the content.
     * @return array                array($newcontent, $newcontentType):
     *                              the converted content and the
     *                              (possibly changed) new ContentType.
     */
    function convertClient2Server($content, $contentType)
    {
        list($content, $contentType) =
            parent::convertClient2Server($content, $contentType);

        /* P800 sends categories as "X-Category". Remove the "X-".
         * @todo: This hack only works with a single category. */
        $content = preg_replace('/(\r\n|\r|\n)CATEGORIES:X-/', '\1CATEGORIES:',
                                $content, 1);

        /* P800 sends all day events as s.th. like
         * DTSTART:20050505T000000Z^M
         * DTEND:20050505T240000Z^M
         * This is no longer an all day event when converted to local timezone.
         * So manually handle this. */
        if (preg_match('/(\r\n|\r|\n)DTSTART:.*T000000Z(\r\n|\r|\n)/',
                       $content) &&
            preg_match('/(\r\n|\r|\n)DTEND:(\d\d\d\d)(\d\d)(\d\d)T240000Z(\r\n|\r|\n)/',
                       $content, $m)) {
            $content = preg_replace(
                '/(\r\n|\r|\n)DTSTART:(.*)T000000Z(\r\n|\r|\n)/',
                "$1DTSTART;VALUE=DATE:$2$3", $content);
            /* End timestamp must be converted to next day's date. Or maybe
             * not? */
            $s = date('Ymd', mktime(0, 0, 0, $m[3], $m[4], $m[2]) /* + 24*3600 */);
            $content = preg_replace(
                '/(\r\n|\r|\n)DTEND:(.*)T240000Z(\r\n|\r|\n)/',
                "$1DTEND;VALUE=DATE:$s$3", $content);
        }

        $GLOBALS['backend']->logFile(
            SYNCML_LOGFILE_DATA,
            "\ninput converted for server ($contentType):\n$content\n");

        return array($content, $contentType);
    }

    /**
     * Converts the content from the backend to a format suitable for the
     * client device.
     *
     * Strips the uid (primary key) information as client and server might use
     * different ones.
     *
     * @param string $content      The content to convert
     * @param string $contentType  The content type of content as returned
     *                             from the backend
     * @param string $database     The server database URI.
     *
     * @return array  Three-element array with the converted content, the
     *                (possibly changed) new content type, and encoding type
     *                (like b64 as used by Funambol).
     */
    function convertServer2Client($content, $contentType, $database)
    {
        list($content, $contentType, $encodingType) =
            parent::convertServer2Client($content, $contentType, $database);

        /* Convert all day events. */
        if (preg_match('/(\r\n|\r|\n)DTSTART:(\d{8})T000000/',
                       $content)
            && preg_match('/(\r\n|\r|\n)DTEND:(\d\d\d\d)(\d\d)(\d\d)T235959/',
                          $content, $m)) {
            /* @TODO: This is for P990. Check if it's different for P900.
             * This might require T000000Z rather than T000000 */

            /* The P990 seems to require this to recognize an entry as all day: */
            $a = $m[1] . 'X-EPOCAGENDAENTRYTYPE:EVENT';
            $content = preg_replace('/(\r\n|\r|\n)DTSTART:(\d{8})T000000/',
                                    "$a$1DTSTART:$2T000000", $content);
            /* End date must be converted to timestamp. */
            $s = date('Ymd', mktime(0, 0, 0, $m[3], $m[4]+1, $m[2]));
            $content = preg_replace('/(\r\n|\r|\n)DTEND:(\d{8})T235959/',
                                    "$1DTEND:${s}T000000", $content);
        }

        $l = "\noutput converted for client ($contentType):\n" . $content . "\n";
        $GLOBALS['backend']->logFile(SYNCML_LOGFILE_DATA, $l);

        return array($content, $contentType, $encodingType);
    }

    /**
     * Some devices like the Sony Ericsson P800/P900/P910 handle vtodos (tasks)
     * and vevents in the same "calendar" sync.
     * This requires special actions on our side as we store this in different
     * databases (nag and kronolith).
     * This function could directly return true but tries to be a bit more
     * generic so it might work for other phones as well.
     */
    function handleTasksInCalendar()
    {
        $di = $_SESSION['SyncML.state']->deviceInfo;

        if (isset($di->CTCaps['text/x-vcalendar']) &&
            !empty($di->CTCaps['text/x-vcalendar']['BEGIN']->ValEnum['VEVENT']) &&
            !empty($di->CTCaps['text/x-vcalendar']['BEGIN']->ValEnum['VTODO'])) {
            return true;
        }

        return parent::handleTasksInCalendar();
    }

    /**
     * Send individual status response for each Add,Delete,Replace.
     * The P800 class of devices seem to have trouble with too many
     * status responses. So omit them for these (and only these),
     */
    function omitIndividualSyncStatus()
    {
        return true;
    }

}
