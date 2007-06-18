<?php
/**
 * The Notification_Event:: class provides a container for passing
 * messages to Notification_Listener classes.
 *
 * $Horde: framework/Notification/Notification/Event.php,v 1.4 2004/01/01 15:16:09 jan Exp $
 *
 * Copyright 2002-2004 Hans Lellelid <hans@velum.net>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Hans Lellelid <hans@velum.net>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Notification
 */
class Notification_Event {

    /**
     * The message being passed.
     * @var string $_message
     * @access private
     */
    var $_message = '';

    /**
     * If passed, sets the message for this event.
     *
     * @param string  $message (optional) The text message for this event.
     * @access public
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
     * @param string  $message   The text message to display.
     * @access public
     */
    function setMessage($message)
    {
        $this->_message = $message;
    }

    /**
     * Gets the text message for this event.
     *
     * @return string   The text message to display.
     * @access public
     */
    function getMessage()
    {
        return $this->_message;
    }

}
