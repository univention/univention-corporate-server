/**
 * Generic function to add an event handler to any DOM element.
 *
 * $Horde: horde/js/addEvent.php,v 1.1.2.3 2007-01-02 13:55:04 jan Exp $
 *
 * Copyright 2005-2007 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

/**
 * Adds the given event to an element. If the element already has
 * handlers for the event, the new event is appended.
 *
 * @param object element   The element to add the event to.
 * @param string event     The name of the event.
 * @param string|function function  The javascript to execute.
 */
function addEvent(element, event, code)
{
    if (!element) {
        return false;
    }

    // Assign new anonymous function if we're passed a js string
    // instead of a function reference.
    if (typeof code == 'string') {
        code = new Function(code);
    }

    if (element.addEventListener) {
        element.addEventListener(event.replace(/on/, ''), code, false);
    } else if (element.attachEvent) {
        element.attachEvent(event, code);
    } else if (element.onload != null) {
        eval('var OldEvent = element.' + event);
        newCode = Function(e)
        {
            oldEvent(e);
            code();
        };
        eval('element.' + event + ' = newCode');
    } else {
        eval('element.' + event + ' = code');
    }

    return true;
}
