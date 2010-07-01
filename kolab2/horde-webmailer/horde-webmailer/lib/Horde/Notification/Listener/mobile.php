<?php

require_once 'Horde/Notification/Listener/status.php';

/**
 * The Notification_Listener_mobile:: class provides functionality for
 * displaying messages from the message stack on mobile devices.
 *
 * $Horde: framework/Notification/Notification/Listener/mobile.php,v 1.8.10.12 2009-01-06 15:23:29 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 3.0
 * @package Horde_Notification
 */
class Notification_Listener_mobile extends Notification_Listener_status {

    /**
     * The Horde_Mobile:: object that status lines should be added to.
     *
     * @var Horde_Mobile
     */
    var $_mobile = null;

    /**
     * Constructor
     */
    function Notification_Listener_mobile()
    {
        $this->_handles = array('horde.error'   => _("ERR"),
                                'horde.success' => _("SUCCESS"),
                                'horde.warning' => _("WARN"),
                                'horde.message' => _("MSG"));
    }

    /**
     * Associate a Horde_Mobile:: object with the listener.
     *
     * @param Horde_Mobile  The Horde_Mobile:: object to send status lines to.
     */
    function setMobileObject(&$mobile)
    {
        $this->_mobile = &$mobile;
    }

    /**
     * Return a unique identifier for this listener.
     *
     * @return string  Unique id.
     */
    function getName()
    {
        return 'mobile';
    }

    /**
     * Outputs the status line if there are any messages on the 'mobile'
     * message stack.
     *
     * @param array &$messageStack  The stack of messages.
     * @param array $options        An array of options. Options: 'nospace'
     */
    function notify(&$messageStack, $options = array())
    {
        if (!$this->_mobile) {
            parent::Notification_Listener_status();
            return parent::notify($messageStack, $options);
        }

        if (count($messageStack)) {
            while ($message = array_shift($messageStack)) {
                $this->getMessage($message);
            }
            $t = &$this->_mobile->add(new Horde_Mobile_text("\n"));
            $t->set('linebreaks', true);
        }
    }

    /**
     * Outputs one message.
     *
     * @param array $message  One message hash from the stack.
     */
    function getMessage($message)
    {
        if (!$this->_mobile) {
            parent::Notification_Listener_status();
            return parent::getMessage($message);
        }

        $event = $this->getEvent($message);
        $this->_mobile->add(new Horde_Mobile_text($this->_handles[$message['type']] . ': ' . strip_tags($event->getMessage())));
    }

}
