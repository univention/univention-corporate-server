/**
 * Javascript code for finding all tables with classname "striped" and
 * dynamically striping their row colors, and finding all tables with
 * classname "sortable" and making them dynamically sortable.
 *
 * TODO: incorporate missing features (if wanted) and improvements
 * from http://tetlaw.id.au/view/blog/table-sorting-with-prototype/,
 * http://tablesorter.com/docs/, and
 * http://www.millstream.com.au/view/code/tablekit/
 *
 * $Horde: mnemo/js/src/tables.js,v 1.4.2.1 2007-12-20 14:17:41 jan Exp $
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

/* We do everything onload so that the entire document is present
 * before we start searching it for tables. */
if (window.addEventListener) {
    window.addEventListener('load', table_init, false);
} else if (window.attachEvent) {
    window.attachEvent('onload', table_init);
} else if (window.onload != null) {
    var old_onload = window.onload;
    window.onload = function(e)
    {
        old_onload(e);
        table_init();
    };
} else {
    window.onload = table_init;
}

var SORT_COLUMN_INDEX;

function table_init()
{
    if (!document.getElementsByTagName) {
        return;
    }
    tables = document.getElementsByTagName('table');
    for (var i = 0; i < tables.length; ++i) {
        if (hasClass(tables[i], 'striped')) {
            table_stripe(tables[i]);
        }
        if (hasClass(tables[i], 'sortable') && tables[i].id) {
            table_makeSortable(tables[i]);
        }
    }
}

function table_stripe(table)
{
    // The flag we'll use to keep track of whether the current row is
    // odd or even.
    var even = false;

    // Tables can have more than one tbody element; get all child
    // tbody tags and interate through them.
    var tbodies = table.childNodes;
    for (var c = 0; c < tbodies.length; ++c) {
        if (tbodies[c].tagName != 'TBODY') {
            continue;
        }

        var trs = tbodies[c].childNodes;
        for (var i = 0; i < trs.length; ++i) {
            if (trs[i].tagName == 'TR') {
                removeClass(trs[i], 'rowEven');
                removeClass(trs[i], 'rowOdd');
                addClass(trs[i], even ? 'rowEven' : 'rowOdd');

                // Flip from odd to even, or vice-versa.
                even = !even;
            }
        }
    }
}

function table_makeSortable(table)
{
    if (table.rows && table.rows.length > 0) {
        var firstRow = table.rows[0];
    }
    if (!firstRow) {
        return;
    }

    // We have a first row: assume it's the header, and make its
    // contents clickable links.
    for (var i = 0; i < firstRow.cells.length; ++i) {
        var cell = firstRow.cells[i];
        if (hasClass(cell, 'nosort')) {
            continue;
        }

        cell.columnIndex = i;
        cell.style.cursor = 'pointer';
        cell.onclick = function(e)
        {
            var e = e || window.event;

            if (e.target) {
                if (e.target.nodeType == 3) {
                    e.target = e.target.parentNode;
                }
            } else if (e.srcElement) {
                e.target = e.srcElement;
            }

            el = hasParent(e.target, 'A', 'TH');
            if (el && !hasClass(el, 'sortlink')) {
                return true;
            }

            table_resortTable(getParent(e.target, 'TH'));
            return false;
        }
    }
}

function table_getSortValue(el)
{
    if (typeof el == 'string') {
        return el.replace(/^\s+/, '').replace(/\s+$/, '')
    }
    if (typeof el == 'undefined') {
        return el;
    }

    // Use "sortval" if defined.
    if ((el.hasAttribute && el.hasAttribute('sortval')) ||
        typeof el['sortval'] != 'undefined') {
        return el.getAttribute('sortval');
    }

    if (el.innerText) {
        // Not needed but it is faster.
        return el.innerText.replace(/^\s+/, '').replace(/\s+$/, '');
    }

    var str = '';
    var cs = el.childNodes;
    var l = cs.length;
    for (var i = 0; i < l; ++i) {
        switch (cs[i].nodeType) {
        case 1:
            // ELEMENT_NODE
            str += table_getSortValue(cs[i]);
            break;

        case 3:
            // TEXT_NODE
            str += cs[i].nodeValue;
            break;
        }
    }

    return str.replace(/^\s+/, '').replace(/\s+$/, '');
}

function table_resortTable(th)
{
    table = getParent(th, 'TABLE');
    sortColumn = th.columnIndex;
    sortDown = 0;

    // Loop through <thead> to find the current sort column and
    // direction.
    theads = table.tHead.getElementsByTagName('th');
    for (var i = 0; i < theads.length; ++i) {
        if (th == theads[i]) {
            if (hasClass(theads[i], 'sortup')) {
                removeClass(theads[i], 'sortup');
                addClass(theads[i], 'sortdown');
            } else if (hasClass(theads[i], 'sortdown')) {
                removeClass(theads[i], 'sortdown');
                addClass(theads[i], 'sortup');
                sortDown = 1;
            } else {
                addClass(theads[i], 'sortdown');
            }
        } else {
            removeClass(theads[i], 'sortup');
            removeClass(theads[i], 'sortdown');
        }
    }

    // Work out a type for the column
    if (table.rows.length <= 1) {
        return;
    }

    var itm = table_getSortValue(table.rows[1].cells[sortColumn]);
    sortfn = table_sort_caseinsensitive;
    if (itm.match(/^\d\d[\/\.-]\d\d[\/\.-]\d\d(\d\d)?$/)) {
        sortfn = table_sort_date;
    } else if (itm.match(/^[£$€¥]/)) {
        sortfn = table_sort_currency;
    } else if (itm.match(/^[\d\.]+$/)) {
        sortfn = table_sort_numeric;
    }

    SORT_COLUMN_INDEX = sortColumn;

    // Don't mix up seperate tbodies; sort each in turn.
    for (var i = 0; i < table.tBodies.length; ++i) {
        trs = table.tBodies[i].getElementsByTagName('tr');
        newRows = [];
        for (var j = 0; j < trs.length; ++j) {
            newRows[j] = trs[j];
        }

        newRows.sort(sortfn);
        if (sortDown) {
            newRows.reverse();
        }

        // We appendChild rows that already exist to the tbody, so it
        // moves them rather than creating new ones. Don't do
        // sortbottom rows.
        for (var j = 0; j < newRows.length; ++j) {
            if (!hasClass(newRows[j], 'sortbottom')) {
                table.tBodies[i].appendChild(newRows[j]);
            }
        }

        // Do sortbottom rows only.
        for (var j = 0; j < newRows.length; ++j) {
            if (hasClass(newRows[j], 'sortbottom')) {
                table.tBodies[i].appendChild(newRows[j]);
            }
        }
    }

    // If we just resorted a striped table, re-stripe it.
    if (hasClass(table, 'striped')) {
        table_stripe(table);
    }

    // Finally, see if we have a callback function to trigger.
    if (typeof(table_sortCallback) == 'function') {
        table_sortCallback(table.id, th.id, sortDown);
    }
}

function getParent(el, pTagName)
{
    if (el == null) {
        return null;
    } else if (pTagName == null) {
        return el.parentNode;
    } else if (el.nodeType == 1 && el.tagName.toLowerCase() == pTagName.toLowerCase()) {
        // Gecko bug, supposed to be uppercase.
        return el;
    } else {
        return getParent(el.parentNode, pTagName);
    }
}

function table_sort_date(a, b)
{
    // Two digit years less than 50 are treated as 20XX, greater than
    // 50 are treated as 19XX.
    aa = table_getSortValue(a.cells[SORT_COLUMN_INDEX]);
    bb = table_getSortValue(b.cells[SORT_COLUMN_INDEX]);
    if (aa.length == 10) {
        dt1 = aa.substr(6, 4) + aa.substr(3, 2) + aa.substr(0, 2);
    } else {
        yr = aa.substr(6, 2);
        if (parseInt(yr) < 50) {
            yr = '20' + yr;
        } else {
            yr = '19' + yr;
        }
        dt1 = yr + aa.substr(3, 2) + aa.substr(0, 2);
    }
    if (bb.length == 10) {
        dt2 = bb.substr(6, 4) + bb.substr(3, 2) + bb.substr(0, 2);
    } else {
        yr = bb.substr(6, 2);
        if (parseInt(yr) < 50) {
            yr = '20' + yr;
        } else {
            yr = '19' + yr;
        }
        dt2 = yr + bb.substr(3, 2) + bb.substr(0, 2);
    }
    if (dt1 == dt2) {
        return 0;
    } else if (dt1 < dt2) {
        return -1;
    }
    return 1;
}

function table_sort_currency(a, b)
{
    aa = table_getSortValue(a.cells[SORT_COLUMN_INDEX]).replace(/[^0-9.]/g, '');
    bb = table_getSortValue(b.cells[SORT_COLUMN_INDEX]).replace(/[^0-9.]/g, '');
    return parseFloat(aa) - parseFloat(bb);
}

function table_sort_numeric(a, b)
{
    aa = parseFloat(table_getSortValue(a.cells[SORT_COLUMN_INDEX]));
    if (isNaN(aa)) {
        aa = 0;
    }
    bb = parseFloat(table_getSortValue(b.cells[SORT_COLUMN_INDEX]));
    if (isNaN(bb)) {
        bb = 0;
    }
    return aa - bb;
}

function table_sort_caseinsensitive(a, b)
{
    aa = table_getSortValue(a.cells[SORT_COLUMN_INDEX]).toLowerCase();
    bb = table_getSortValue(b.cells[SORT_COLUMN_INDEX]).toLowerCase();
    if (aa == bb) {
        return 0;
    } else if (aa < bb) {
        return -1;
    }
    return 1;
}

function table_sort_default(a,b)
{
    aa = table_getSortValue(a.cells[SORT_COLUMN_INDEX]);
    bb = table_getSortValue(b.cells[SORT_COLUMN_INDEX]);
    if (aa == bb) {
        return 0;
    } else if (aa < bb) {
        return -1;
    }
    return 1;
}

/**
 * DOM utility functions.
 */
function hasParent(el, tagName, tagStop)
{
    if (el.tagName == tagName) {
        return el;
    } else if (tagStop != null && el.tagName == tagStop) {
        return false;
    } else {
        return hasParent(getParent(el), tagName, tagStop);
    }
}

function addClass(el, className)
{
    el.className += el.className ? ' ' + className : className;
}

function removeClass(el, className)
{
    el.className = el.className.replace(new RegExp(' ?' + className + ' ?'), '');
}

function hasClass(el, className)
{
    return (el.className.indexOf(className) != -1);
}
