/**
 * Horde Form Assign Field Javascript Class
 *
 * Provides the javascript class to accompany the Horde_Form assign field.
 *
 * $Horde: horde/js/src/form_assign.js,v 1.9.2.3 2009-01-06 15:24:43 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
*
* @author Jan Schneider <jan@horde.org>
 */

Horde_Form_Assign = {};

Horde_Form_Assign.deselectHeaders = function(form, elt, side)
{
    if (side) {
        document.forms[form].elements[elt + '__right'][0].selected = false;
    } else {
        document.forms[form].elements[elt + '__left'][0].selected = false;
    }
}

Horde_Form_Assign.move = function(form, elt, direction)
{
    var left = document.forms[form].elements[elt + '__left'];
    var right = document.forms[form].elements[elt + '__right'];

    var from, to;
    if (direction) {
        from = right;
        to = left;
    } else {
        from = left;
        to = right;
    }

    for (var i = 0; i < from.length; ++i) {
        if (from[i].selected) {
            to[to.length] = new Option(from[i].text, from[i].value);
            to[to.length - 1].ondblclick = function() {
                Horde_Form_Assign.move(form, elt, 1 - direction);
            }
            from[i] = null;
            --i;
        }
    }

    this.setField(form, elt);
}

Horde_Form_Assign.setField = function(form, elt)
{
    var left = document.forms[form].elements[elt + '__left'];
    var right = document.forms[form].elements[elt + '__right'];

    var values = '';
    var hit = false;
    for (var i = 0; i < left.options.length; ++i) {
        if (i == 0 && !left[i].value) {
            continue;
        }
        values += left.options[i].value + '\t';
        hit = true;
    }
    if (hit) {
        values = values.substring(0, values.length - 1);
    }
    values += '\t\t';
    hit = false;
    for (i = 0; i < right.options.length; ++i) {
        if (i == 0 && !right[i].value) {
            continue;
        }
        values += right.options[i].value + '\t';
        hit = true;
    }
    if (hit) {
        values = values.substring(0, values.length - 1);
    }
    document.forms[form].elements[elt + '__values'].value = values;
}
