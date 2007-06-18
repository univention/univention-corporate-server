<script language="JavaScript" type="text/javascript">
<!--

var da = (document.all) ? 1 : 0;
var pr = (window.print) ? 1 : 0;
var mac = (navigator.userAgent.indexOf("Mac") != -1);

function printWin()
{
    if (pr) {
        // NS4+, IE5+
        window.print();
    } else if (!mac) {
        // IE3 and IE4 on PC
        VBprintWin();
    } else {
        // everything else
        handle_error();
    }
}

window.onerror = handle_error;
window.onafterprint = function() {window.close()}

function handle_error()
{
    window.alert('<?php echo addslashes(_("Your browser does not support this print option. Press Control/Option + P to print.")) ?>');
    return true;
}

if (!pr && !mac) {
    if (da) {
        // This must be IE4 or greater
        wbvers = "8856F961-340A-11D0-A96B-00C04FD705A2";
    } else {
        // this must be IE3.x
        wbvers = "EAB22AC3-30C1-11CF-A7EB-0000C05BAE0B";
    }

    document.write("<OBJECT ID=\"WB\" WIDTH=\"0\" HEIGHT=\"0\" CLASSID=\"CLSID:");
    document.write(wbvers + "\"> </OBJECT>");
}

// -->
</script>

<script language="VBSCript" type="text/vbscript">
<!--

sub window_onunload
    on error resume next
    ' Just tidy up when we leave to be sure we aren't
    ' keeping instances of the browser control in memory
    set WB = nothing
end sub

sub VBprintWin
    OLECMDID_PRINT = 6
    on error resume next

    ' IE4 object has a different command structure
    if da then
        call WB.ExecWB(OLECMDID_PRINT, 1)
    else
        call WB.IOleCommandTarget.Exec(OLECMDID_PRINT, 1, "", "")
    end if
end sub

' -->
</script>

<script language="JavaScript" type="text/javascript">
<!--
printWin();
// -->
</script>
