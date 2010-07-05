<?php

require_once 'Horde/Notification/Listener.php';

/**
 * The Notification_Listener_javascript:: class provides functionality for
 * inserting javascript code from the message stack into the page.
 *
 * $Horde: framework/Notification/Notification/Listener/javascript.php,v 1.7.10.10 2009-01-06 15:23:29 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.0
 * @package Horde_Notification
 */
class Notification_Listener_javascript extends Notification_Listener {

    /**
     * Constructor
     */
    function Notification_Listener_javascript()
    {
        $this->_handles = array('javascript' => '',
                                'javascript-file' => '');
    }

    /**
     * Return a unique identifier for this listener.
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
     * @param array &$messageStack     The stack of messages.
     * @param array $options  An array of options. Options: 'noscript'
     */
    function notify(&$messageStack, $options = array())
    {
        if (!count($messageStack)) {
            return;
        }

        if (empty($options['noscript'])) {
            echo '<script type="text/javascript">//<![CDATA[' . "\n";
        }

        $files = array();
        while ($message = array_shift($messageStack)) {
            $event = $this->getEvent($message);
            if ($message['type'] == 'javascript') {
                echo $event->getMessage() . "\n";
            } elseif ($message['type'] == 'javascript-file') {
                $files[] = $event->getMessage();
            }
        }

        if (empty($options['noscript'])) {
            echo "//]]></script>\n";
            if (count($files)) {
                foreach ($files as $file) {
                    echo '<script type="text/javascript" src="' . $file . '"></script>' . "\n";
                }
            }
        }
    }

    /**
     * Outputs one message.
     *
     * @param array $message  One message hash from the stack.
     */
    function getMessage($message)
    {
    }

}
