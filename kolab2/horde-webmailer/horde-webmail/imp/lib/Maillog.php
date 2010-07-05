<?php

require_once 'Horde/History.php';

/**
 * The IMP_Maillog:: class contains all functions related to handling
 * logging of responses to individual e-mail messages.
 *
 * $Horde: imp/lib/Maillog.php,v 1.15.10.16 2009-01-06 15:24:04 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package IMP
 */
class IMP_Maillog {

    /**
     * Create a log entry.
     *
     * @param string $type    Either 'forward', 'redirect', 'reply', or 'mdn'.
     * @param mixed $msg_ids  Either a single Message-ID or an array of
     *                        Message-IDs to log.
     * @param string $data    Any additional data to store. For 'forward' and
     *                        'redirect' this is the list of recipients the
     *                        message was sent to. For 'mdn' this is the
     *                        MDN-type of the message that was sent.
     */
    function log($type, $msg_ids, $data = null)
    {
        $history = &Horde_History::singleton();

        if (!is_array($msg_ids)) {
            $msg_ids = array($msg_ids);
        }

        foreach ($msg_ids as $val) {
            switch ($type) {
            case 'forward':
                $params = array('recipients' => $data, 'action' => 'forward');
                break;

            case 'mdn':
                $params = array('type' => $data, 'action' => 'mdn');
                break;

            case 'redirect':
                $params = array('recipients' => $data, 'action' => 'redirect');
                break;

            case 'reply':
                $params = array('action' => 'reply');
                break;
            }

            $r = $history->log(IMP_Maillog::_getUniqueHistoryId($val), $params);

            /* On error, log the error message only since informing the user
             * is just a waste of time and a potential point of confusion,
             * especially since they most likely don't even know the message
             * is being logged. */
            if (is_a($r, 'PEAR_Error')) {
                $entry = sprintf('Could not log message details to Horde_History. Error returned: %s', $r->getMessage());
                Horde::logMessage($entry, __FILE__, __LINE__, PEAR_LOG_ERR);
            }
        }
    }

    /**
     * Retrieve any history for the given Message-ID.
     *
     * @param string $msg_id  The Message-ID of the message.
     *
     * @return DataTreeObject  The DataTreeObject object containing the log
     *                         information, or PEAR_Error on error.
     */
    function &getLog($msg_id)
    {
        $history = &Horde_History::singleton();
        $log = &$history->getHistory(IMP_Maillog::_getUniqueHistoryId($msg_id));
        return $log;
    }

    /**
     * Determines if an MDN notification of a certain type has been sent
     * previously for this message-ID.
     *
     * @param string $msg_id  The Message-ID of the message.
     * @param string $type    The type of MDN.
     *
     * @return boolean  True if a MDN has been sent for this message with
     *                  the given type.
     */
    function sentMDN($msg_id, $type)
    {
        $msg_history = IMP_Maillog::getLog($msg_id);
        if ($msg_history && !is_a($msg_history, 'PEAR_Error')) {
            foreach ($msg_history->getData() as $entry) {
                if (($entry['action'] == 'mdn') && ($entry['type'] == $type)) {
                    return true;
                }
            }
        }

        return false;
    }

    /**
     * Retrieve any history for the given Message-ID and display via the
     * Horde notification system.
     *
     * @param string $msg_id  The Message-ID of the message.
     */
    function displayLog($msg_id)
    {
        global $notification, $prefs;

        $msg_history = IMP_Maillog::getLog($msg_id);
        if ($msg_history && !is_a($msg_history, 'PEAR_Error')) {
            foreach ($msg_history->getData() as $entry) {
                $msg = null;
                if (isset($entry['desc'])) {
                    $msg = $entry['desc'];
                } else {
                    switch ($entry['action']) {
                    case 'forward':
                        $msg = sprintf(_("You forwarded this message on %%s to the following recipients: %s."), $entry['recipients']);
                        break;

                    case 'mdn':
                        /* We don't display 'mdn' log entries. */
                        break;

                    case 'redirect':
                        $msg = sprintf(_("You redirected this message to %s on %%s."), $entry['recipients']);
                        break;

                    case 'reply':
                        $msg = _("You replied to this message on %s.");
                        break;
                    }
                }
                if ($msg) {
                    $notification->push(htmlspecialchars(@sprintf($msg, strftime($prefs->getValue('date_format') . ' ' . $prefs->getValue('time_format'), $entry['ts']))), 'imp.' . $entry['action']);
                }
            }
        }
    }

    /**
     * Delete the log entries for a given list of Message-IDs.
     *
     * @param mixed $msg_ids  Either a single Message-ID or an array
     *                        of Message-IDs to delete.
     */
    function deleteLog($msg_ids)
    {
        if (!is_array($msg_ids)) {
            $msg_ids = array($msg_ids);
        }
        $msg_ids = array_map(array('IMP_Maillog', '_getUniqueHistoryId'), $msg_ids);

        $history = &Horde_History::singleton();
        return $history->removeByNames($msg_ids);
    }

    /**
     * Generate the unique log ID for a forward/reply/redirect event.
     *
     * @access private
     *
     * @param string $msgid  The Message-ID of the original message.
     *
     * @return string  The unique log ID to use with Horde_History::.
     */
    function _getUniqueHistoryId($msgid)
    {
        if (is_array($msgid)) {
            return '';
        }

        return implode('.', array('imp', str_replace('.', '*', Auth::getAuth()), $msgid));
    }

}
