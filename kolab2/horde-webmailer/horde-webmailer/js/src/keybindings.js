/**
 * Javascript library to handle a set of keybindings.
 *
 * The user should include this script, and then call setKeybinding(key,
 * callback) for each keybinding that is desired. This script will take care
 * of listening for keypresses and mapping them to the callback functions, or
 * doing nothing if no callback is set.
 *
 * $Horde: horde/js/src/keybindings.js,v 1.9.2.1 2007-12-20 15:01:31 jan Exp $
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @package Horde
 */

/**
 * A hash of keybindings.
 *
 * @var _keyMap
 */
var _keyMap = [];

/**
 * Set up the keypress listener.
 */
document.onkeyup = keyHandler;

/**
 * Sets up a callback for a keycode.
 *
 * @param key       The keycode to trigger on.
 * @param callback  The function to call when "key" is pressed. Should be a
 *                  function. It gets the event and the keycode as parameters,
 *                  so that you can use one function to handle multiple keys if
 *                  you like.
 */
function setKeybinding(key, callback)
{
    if (typeof _keyMap[key] == 'undefined') {
        _keyMap[key] = [];
    }

    if (typeof callback == 'function') {
        _keyMap[key].push(callback);
    } else {
        _keyMap[key].push(new Function('e', 'key', callback + '(e, key);'));
    }
}

/**
 * Invoked by the JavaScript event model when a key is pressed. Gets
 * the keycode (attempts to handle all browsers) and looks to see if
 * we have a handler defined for that key. If so, call it.
 *
 * @param e  The event to handle. Should be a keypress.
 */
function keyHandler(e)
{
    e = e || window.event;

    var key;
    if (e.keyCode) {
        key = e.keyCode;
    } else if (e.which) {
        key = e.which;
    }

    /* If there's a handler defined for the key that was pressed, call
     * it, passing in the keycode and the event. */
    if (_keyMap[key]) {
        for (var i = 0; i < _keyMap[key].length; ++i) {
            if (_keyMap[key][i](e, key)) {
                e.returnValue = false;
                if (typeof e.preventDefault == 'function') {
                    e.preventDefault();
                } else {
                    e.returnValue = true;
                }
                break;
            }
        }
    }
}
