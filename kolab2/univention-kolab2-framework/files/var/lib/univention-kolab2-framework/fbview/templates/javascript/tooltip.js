var isIE = document.all ? true : false;
var activeTimeout;

if (!isIE) {
    document.captureEvents(Event.MOUSEMOVE);
    document.onmousemove = mousePos;
    var netX, netY;
}

function posX() {
    if (isIE) {
      tempX = document.body.scrollLeft + event.clientX;
    }
    if (tempX < 0) {
      tempX = 0;
    }
    return tempX;
}

function posY() {
    if (isIE) {
      tempY = document.body.scrollTop + event.clientY;
    }
    if (tempY < 0) {
     tempY = 0;
    }
    return tempY;
}

function mousePos(e) {
    netX = e.pageX;
    netY = e.pageY;
}

function tooltipShow(pX, pY, src) {
    if (pX < 1) {
        pX = 1;
    }
    if (pY < 1) {
        pY = 1;
    }
    if (isIE) {
        document.all.tooltip.style.visibility = 'visible';
        document.all.tooltip.innerHTML = src;
        document.all.tooltip.style.left = pX + 'px';
        document.all.tooltip.style.top = pY + 'px';
    } else {
        document.getElementById('tooltip').style.visibility = 'visible';
        document.getElementById('tooltip').style.left = pX + 'px';
        document.getElementById('tooltip').style.top = pY + 'px';
        document.getElementById('tooltip').innerHTML = src;
    }
}

function tooltipClose() {
    if (isIE) {
        document.all.tooltip.innerHTML = '';
        document.all.tooltip.style.visibility = 'hidden';
    } else {
        document.getElementById('tooltip').style.visibility = 'hidden';
        document.getElementById('tooltip').innerHTML = '';
    }
    clearTimeout(activeTimeout);
    window.status = '';
}

function tooltipLink(tooltext, statusline) {
    text = '<table cellspacing="0" cellpadding="4" border="0">';
    text += '<tr><td class="tooltip">' + tooltext + '</td></tr></table>';
    if (isIE) {
        xpos = posX();
        ypos = posY();
    } else {
        xpos = netX;
        ypos = netY;
    }
    activeTimeout = setTimeout('tooltipShow(xpos - 110, ypos + 15, text);', 300);
    window.status = statusline;
}

document.write('<div id="tooltip" style="position: absolute; visibility: hidden;"></div>');
