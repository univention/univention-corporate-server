/**
 * Javascript code for attaching an onkeydown listener to textarea and
 * text input elements to prevent loss of data when the user hits the
 * ESC key.
 *
 * This code is only relevant for IE.
 *
 * $Horde: imp/js/src/ieEscGuard.js,v 1.6.2.1 2007-12-20 13:59:22 jan Exp $
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

/* Finds all text inputs (input type="text") and textarea tags, and attaches
* the onkeydown listener to them to avoid ESC clearing the text. */
if (Prototype.Browser.IE) {
    document.observe('dom:loaded', function() {
        /* Only attach to textareas and <input type="text"> tags. */
        [ $$('TEXTAREA'), $$('INPUT[type="text"]') ].flatten().each(function(t) {
            t.observe('keydown', function(e) { return e.keyCode != 27; });
        });
    });
}
