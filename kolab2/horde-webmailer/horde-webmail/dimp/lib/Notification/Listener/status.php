<?php

require_once IMP_BASE . '/lib/Notification/Listener/status.php';
require_once 'Horde/Notification/Event.php';

/**
 * The Notification_Listener_status_dimp:: class extends the
 * Notification_Listener_status_imp:: class to return all messages instead of
 * printing them.
 *
 * $Horde: dimp/lib/Notification/Listener/status.php,v 1.12.2.3 2009-01-06 15:22:39 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @package Horde_Notification
 */
class Notification_Listener_status_dimp extends Notification_Listener_status_imp {

    /**
     * The notified message stack.
     *
     * @var array
     */
    var $_messageStack = array();

    /**
     * Returns all status message if there are any on the 'status' message
     * stack.
     *
     * @param array &$messageStack  The stack of messages.
     * @param array $options        An array of options.
     */
    function notify(&$messageStack, $options = array())
    {
        while ($message = array_shift($messageStack)) {
            $event = @unserialize($message['event']);
            $this->_messageStack[] = array('type' => $message['type'],
                                           'flags' => $message['flags'],
                                           'message' => is_object($event)
                                               ? $event->getMessage()
                                               : null);
        }
    }

    /**
     * Handle every message of type dimp.*; otherwise delegate back to
     * the parent.
     *
     * @param string $type  The message type in question.
     *
     * @return boolean  Whether this listener handles the type.
     */
    function handles($type)
    {
        if (substr($type, 0, 5) == 'dimp.') {
            return true;
        }
        return parent::handles($type);
    }

    /**
     * Returns the message stack.
     * To return something useful, notify() needs to be called first.
     *
     * @param boolean $encode  Encode HTML entities?
     *
     * @return array  List of message hashes.
     */
    function getStack($encode = false)
    {
        $msgs = $this->_messageStack;
        if (!$encode) {
            return $msgs;
        }

        for ($i = 0, $mcount = count($msgs); $i < $mcount; ++$i) {
            if (!in_array('content.raw', $this->getFlags($msgs[$i]))) {
                $msgs[$i]['message'] = htmlspecialchars($msgs[$i]['message'], ENT_COMPAT, NLS::getCharset());
            }
        }

        return $msgs;
    }

}
