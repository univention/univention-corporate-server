/* vim: set expandtab tabstop=4 shiftwidth=4 foldmethod=marker: */
/**
 * Javascript to add events to form elements
 *
 * Copyright 2004 Matt Kynaston <matt@kynx.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Matt Kynaston <matt@kynx.org>
 * @package Horde
 */

/**
 * Adds the given event to an element. If the element already has script for
 * the event, the new event is appended.
 * 
 * @param       Element         obj             the element to add event to
 * @param       string          name            the name of the event
 * @param       string          onchange        the onchange javascript 
 */
function addEvent(obj, name, js)
{
    if (obj) {
        // get existing events
        eval('events = obj.' + name);
        events = (events) ? events.toString() : '';
        events = events.substring(
                    events.indexOf('{') + 1, 
                    events.lastIndexOf('}'));
        events = events.replace(/\n/g, '').split(';');
        
        // return events should always be last, and are overridden
        // by any added ones, so always return a Macromedia-style 
        // document.MM_retVal
        count = events.length;
        last = '';
        while (last == '') {
            last = events.pop();
            count--;
        }
        is_return = (last.indexOf('return ') != -1);
        if (js.indexOf('return ') != -1 && is_return) {
            events.push(js);
        }
        else {
            if (is_return) {
                events.push(js);
                events.push(last);
            }
            else {
                events.push(last);
                events.push(js);
            }
        }
        
        js = events.join(';'); 

        // assign new anonymous function to event
        func = new Function(js);
        return eval('obj.' + name + '=func'); 
    }
    else {
        return false;
    }
}

/**
 * Returns given value as a number, or zero if NaN
 * @param       mixed   val
 * @return      Number
 */
function toNumber(val) 
{
    if (isNaN(val)) {
        return 0;
    }
    else {
        return Number(val);
    }
}

/**
 * Sets the enabled state of one element based on the values of another
 * 
 * Takes four or more arguments, in the form...
 *   checkEnabled(source, target, true, value1, value2, value3...)
 *
 * @param   Element    src      the element to check
 * @param   string     target   the element to enable/disable
 * @param   boolean    enabled  whether to enable or disable the target
 * @param   mixed               the value to check against
 */
function checkEnabled() 
{
    if (arguments.length > 2) {
        objSrc = arguments[0];
        objTarget = objSrc.form.elements[arguments[1]];
        enabled = arguments[2];
        toggle = false;
        if (objTarget) {
            switch (objSrc.type.toLowerCase()) {
                case 'select-one' :
                    val = objSrc.options[objSrc.selectedIndex].value;
                    break;
                case 'select-multiple' :
                    val = new Array();
                    count = 0;
                    for (i=0; i<objSrc.length; i++) {
                        if (objSrc.options[i].selected) {
                            val[count] = objSrc.options[i].value;
                        }
                    }
                    break;
                case 'checkbox' :
                    if (objSrc.checked) {
                        val = objSrc.value;
                        toggle = true;
                    }
                default :
                    val = objSrc.value;
            }
            for (i=3; i<arguments.length; i++) {
                if (typeof(val) == 'object' && (arguments[i] in val)) {
                    toggle = true;
                    break;
                }
                else if (arguments[i] == val) {
                    toggle = true;
                    break;
                }
            }
            
            objTarget.disabled = (toggle) ? !enabled : enabled;
            if (!objTarget.disabled) {
                // objTarget.focus();
            }
        }
    }
}

/**
 * Sets the target field to the sum of a range of fields 
 *
 * Takes three or more arguments, in the form:
 *    sumFields(form, target, field1, field2, field3...)
 * @param       Form            objFrm          the form to check
 * @param       string          target          the name of the target element
 * @param       string                          one or more field names to sum
 */
function sumFields() 
{
    if (arguments.length > 2) {
        objFrm = arguments[0];
        objTarget = objFrm.elements[arguments[1]];
        sum = 0;
        if (objTarget) {
            for (i=2; i<arguments.length; i++) {
                objSrc = objFrm.elements[arguments[i]];
                if (objSrc) {
                    switch (objSrc.type.toLowerCase()) {
                        case 'select-one':
                            sum += toNumber(objSrc.options[objSrc.selectedIndex].value);
                            break;
                        case 'select-multiple' :
                            for (j=0; j<objSrc.length; j++) {
                                sum += toNumber(objSrc.options[j].value);
                            }
                            break;
                        case 'checkbox' :
                            if (objSrc.checked) {
                                sum += toNumber(objSrc.value);
                            }
                            break;
                        default :
                            sum += toNumber(objSrc.value);
                    }
                }
            }
            objTarget.value = sum;
        }
    }
}
