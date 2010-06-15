<?php

require_once 'Horde/Notification/Listener.php';

/**
 * The Notification_Listener_mobile:: class provides functionality for
 * displaying messages from the message stack on mobile devices.
 *
 * $Horde: framework/Notification/Notification/Listener/mobile.php,v 1.8 2004/04/07 14:43:11 chuck Exp $
 *
 * Copyright 2003-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Notification
 */
class Notification_Listener_mobile extends Notification_Listener {

    /**
     * The Horde_Mobile:: object that status lines should be added to.
     *
     * @var object Horde_Mobile $_mobile
     */
    var $_mobile = null;

    /**
     * Constructor
     *
     * @access public
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
     * @param object Horde_Mobile  The Horde_Mobile:: object to send
     *                             status lines to.
     */
    function setMobileObject(&$mobile)
    {
        $this->_mobile = &$mobile;
    }

    /**
     * Return a unique identifier for this listener.
     *
     * @access public
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
     * @access public
     *
     * @param array &$messageStack     The stack of messages.
     * @param optional array $options  An array of options.
     *                                 Options: 'nospace'
     */
    function notify(&$messageStack, $options = array())
    {
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
     * @access public
     *
     * @param array $message  One message hash from the stack.
     */
    function getMessage($message)
    {
        $event = $this->getEvent($message);
        $this->_mobile->add(new Horde_Mobile_text(sprintf(_("%s: %s"), $this->_handles[$message['type']], $event->getMessage())));
    }

}
