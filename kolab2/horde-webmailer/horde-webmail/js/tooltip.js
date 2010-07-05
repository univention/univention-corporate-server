/**
 * Horde Tooltip Javascript
 *
 * Provides the javascript to display tooltips.
 *
 * $Horde: horde/js/tooltip.js,v 1.2.10.2 2005-05-01 16:53:30 chuck Exp $
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

var activeTimeout;

if (typeof document.captureEvents != 'undefined') {
    document.captureEvents(Event.MOUSEMOVE);
    document.onmousemove = mousePos;
    var netX, netY;
}

function posX()
{
    tempX = document.body.scrollLeft + event.clientX;
    if (tempX < 0) {
        tempX = 0;
    }
    return tempX;
}

function posY()
{
    tempY = document.body.scrollTop + event.clientY;
    if (tempY < 0) {
        tempY = 0;
    }
    return tempY;
}

function mousePos(e)
{
    netX = e.pageX;
    netY = e.pageY;
}

function tooltipShow(pX, pY, src)
{
    if (pX < 1) {
        pX = 1;
    }
    if (pY < 1) {
        pY = 1;
    }
    if (document.getElementById) {
        tt = document.getElementById('tooltip');
        tt.style.left = pX + 'px';
        tt.style.top = pY + 'px';
        tt.style.visibility = 'visible';
        tt.innerHTML = src;
    } else {
        document.all.tooltip.style.left = pX + 'px';
        document.all.tooltip.style.top = pY + 'px';
        document.all.tooltip.style.visibility = 'visible';
        document.all.tooltip.innerHTML = src;
    }
}

function tooltipClose()
{
    if (document.getElementById) {
        tt = document.getElementById('tooltip');
        tt.style.visibility = 'hidden';
        tt.innerHTML = '';
    } else {
        document.all.tooltip.style.visibility = 'hidden';
        document.all.tooltip.innerHTML = '';
    }
    clearTimeout(activeTimeout);
    window.status = '';
}

function tooltipLink(tooltext, statusline)
{
    text = '<div class="tooltip">' + tooltext + '</div>';
    if (typeof document.captureEvents != 'undefined') {
        xpos = netX;
        ypos = netY;
    } else {
        xpos = posX();
        ypos = posY();
    }
    activeTimeout = setTimeout('tooltipShow(xpos - 110, ypos + 15, text);', 300);
    window.status = statusline;
}

document.write('<div id="tooltip" style="position:absolute; visibility:hidden;"></div>');
