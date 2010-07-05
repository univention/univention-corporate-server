<?php
/**
 * The SyncML_Device_Sync4JMozilla:: class provides functionality that is
 * specific to the Sync4JMozilla Plugin. See
 * http://sourceforge.net/projects/sync4jmozilla/
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * $Horde: framework/SyncML/SyncML/Device/Sync4JMozilla.php,v 1.3.2.5 2009-01-06 15:23:39 jan Exp $
 *
 * @author  Karsten Fourmont <karsten@horde.org>
 * @package SyncML
 */
class SyncML_Device_Sync4JMozilla extends SyncML_Device {

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


        /* The plugin does currently not handle lines that are both folded
         * and QUOTED-PRINTABLE encoded. Like this one with a note "abc":
         * NOTE;ENCODING=QUOTED-PRINTABLE;CHARSET=UTF-8:=
         * a=
         * bc
         */

        if (preg_match_all('/\r\n[^:]*ENCODING=QUOTED-PRINTABLE[^:]*:.*?=\r\n.*?[^=](?=\r\n)/mis', $content, $m)) {
            foreach($m[0] as $v) {
                /* Remove line folding */
                $content = str_replace($v,str_replace("=\r\n", '', $v), $content);
            }
        }
        $l = "\noutput converted for client ($contentType):\n" . $content . "\n";
        $GLOBALS['backend']->logFile(SYNCML_LOGFILE_DATA, $l);

        return array($content, $contentType, $encodingType);
    }

}
