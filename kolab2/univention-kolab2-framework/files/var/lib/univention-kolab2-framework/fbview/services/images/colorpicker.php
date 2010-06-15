<?php
/*
 * $Horde: horde/services/images/colorpicker.php,v 1.14 2004/01/01 16:17:37 jan Exp $
 *
 * Copyright 2002-2004 Michael Cochrane <mike@graftonhall.co.nz>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

@define('HORDE_BASE', dirname(__FILE__) . '/../..');
require_once HORDE_BASE . '/lib/base.php';

$title = _("Color Picker");
require HORDE_TEMPLATES . '/common-header.inc';

$form = Util::getFormData('form');
$target = Util::getFormData('target');

echo Horde::img('colorpicker.png', '', 'id="colorpicker" onclick="changeColor(getColor(event)); return false;" onmousemove="demoColor(getColor(event)); return false;" style="cursor:crosshair;background-color:white;padding:1px"'); 
?>

<div id="colorDemo" style="background-color:white;width:100px;height:20px;padding:1px"></div>
<script language="Javascript" type="text/javascript">
<!--
function changeColor(color)
{
    if (parent.opener.closed) {
        alert("<?php echo addslashes(_("The Options window has closed. Exiting.")) ?>");
        this.close();
        return;
    }

    if (!parent.opener.document.<?php echo $form ?>) {
        alert("<?php echo addslashes(_("This window must be called from an Options window")) ?>");
        this.close();
        return;
    }
    
    parent.opener.document.<?php echo $form ?>["<?php echo $target ?>"].value = color;
    parent.opener.document.<?php echo $form ?>["<?php echo $target ?>"].style.backgroundColor = color;

    this.close();
}

function demoColor(color)
{
    var target = document.getElementById("colorDemo");
    target.style.backgroundColor = color;
}

function getColor(event) {
    var img = document.getElementById("colorpicker");

    var x = event.clientX - 10;
    var y = event.clientY - 10;
    
    var rmax = 0;
    var gmax = 0;
    var bmax = 0;
    
    if (y <= 32) {
        rmax = 255;
        gmax = (y / 32.0) * 255;
        bmax = 0;
    } else if (y <= 64) {
        y = y - 32;
        rmax = 255 - (y / 32.0) * 255;
        gmax = 255;
        bmax = 0;
    } else if (y <= 96) {
        y = y - 64;
        rmax = 0;
        gmax = 255;
        bmax = (y / 32.0) * 255;
    } else if (y <= 128) {
        y = y - 96;
        rmax = 0;
        gmax = 255 - (y / 32.0) * 255;
        bmax = 255;
    } else if (y <= 160) {
        y = y - 128;
        rmax = (y / 32.0) * 255;
        gmax = 0;
        bmax = 255;
    } else {
        y = y - 160;
        rmax = 255;
        gmax = 0;
        bmax = 255 - (y / 32.0) * 255;
    }

    if (x <= 50) {
        var r = Math.floor(rmax * x / 50.0);
        var g = Math.floor(gmax * x / 50.0);
        var b = Math.floor(bmax * x / 50.0);
        
        return makeColor(r,g,b);
    } else {
        x = x - 50;
        var r = Math.floor(rmax + (x / 50.0) * (255 - rmax));    
        var g = Math.floor(gmax + (x / 50.0) * (255 - gmax));    
        var b = Math.floor(bmax + (x / 50.0) * (255 - bmax));   
        return makeColor(r,g,b);
    }
}

function makeColor(r, g, b)
{
    color = "#";
    color += hex(Math.floor(r / 16));
    color += hex(r % 16);
    color += hex(Math.floor(g / 16));
    color += hex(g % 16);
    color += hex(Math.floor(b / 16));
    color += hex(b % 16);
    return color;
}

function hex(Dec)
{   
    if (Dec == 10) return "A";
    if (Dec == 11) return "B";
    if (Dec == 12) return "C";
    if (Dec == 13) return "D";
    if (Dec == 14) return "E";
    if (Dec == 15) return "F";
    return "" + Dec;
}
//-->
</script>
</body>
</html>

