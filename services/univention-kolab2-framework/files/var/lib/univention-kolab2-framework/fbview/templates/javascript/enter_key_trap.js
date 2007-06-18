/**
 * Javascript to trap for the enter key.
 *
 * $Horde: horde/templates/javascript/enter_key_trap.js,v 1.1 2003/10/23 22:05:27 mdjukic Exp $
 *
 * See the enclosed file COPYING for license information (LGPL). If you did not
 * receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @version $Revision: 1.1.2.1 $
 * @package horde
 */

function enter_key_trap(e)
{
    var keyPressed;

    if (document.layers) {
        keyPressed = String.fromCharCode(e.which);
    } else if (document.all) {
        keyPressed = String.fromCharCode(window.event.keyCode);
    } else if (document.getElementById) {
        keyPressed = String.fromCharCode(e.keyCode);
    }

    return (keyPressed == "\r" || keyPressed == "\n");
}
