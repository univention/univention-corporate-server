<?php
/**
 * The Notification_Event:: class provides a container for passing
 * messages to Notification_Listener classes.
 *
 * $Horde: framework/Notification/Notification/Event.php,v 1.5.2.9 2009-01-06 15:23:28 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Hans Lellelid <hans@velum.net>
 * @since   Horde 3.0
 * @package Horde_Notification
 */
class Notification_Event {

    /**
     * The message being passed.
     * @var string
     * @access private
     */
    var $_message = '';

    /**
     * If passed, sets the message for this event.
     *
     * @param string $message  The text message for this event.
     */
    function Notification_Event($message = null)
    {
        if (!is_null($message)) {
            $this->setMessage($message);
        }
    }

    /**
     * Sets the text message for this event.
     *
     * @param string $message  The text message to display.
     */
    function setMessage($message)
    {
        $this->_message = $message;
    }

    /**
     * Gets the text message for this event.
     *
     * @return string  The text message to display.
     */
    function getMessage()
    {
        return $this->_message;
    }

}
