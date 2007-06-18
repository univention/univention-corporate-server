<?php

require_once 'Horde/Notification/Listener.php';

/**
 * The Notification_Listener_javascript:: class provides functionality for
 * inserting javascript code from the message stack into the page.
 *
 * $Horde: framework/Notification/Notification/Listener/javascript.php,v 1.7 2004/04/07 14:43:11 chuck Exp $
 *
 * Copyright 2004 Jan Schneider <jan@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Notification
 */
class Notification_Listener_javascript extends Notification_Listener {

    /**
     * Constructor
     *
     * @access public
     */
    function Notification_Listener_javascript()
    {
        $this->_handles = array('javascript' => '');
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
        return 'javascript';
    }

    /**
     * Outputs the javascript code if there are any messages on the
     * 'javascript' message stack and if the 'notify_javascript' option is set.
     *
     * @access public
     *
     * @param array &$messageStack     The stack of messages.
     * @param optional array $options  An array of options.
     *                                 Options: 'noscript'
     */
    function notify(&$messageStack, $options = array())
    {
        if (count($messageStack)) {
            if (empty($options['noscript'])) {
                echo '<script language="JavaScript" type="text/javascript">';
                echo "\n<!--\n";
            }
            while ($message = array_shift($messageStack)) {
                $this->getMessage($message);
            }
            if (empty($options['noscript'])) {
                echo "//-->\n</script>\n";
            }
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
        echo $event->getMessage() . "\n";
    }

}
