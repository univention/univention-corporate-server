<script type="text/javascript">

if (window.addEventListener) {
    window.addEventListener('load', printWin, false);
} else if (window.attachEvent) {
    window.attachEvent('onload', printWin);
} else if (window.onload != null) {
    var oldOnLoad = window.onload;
    window.onload = function(e)
    {
        oldOnLoad(e);
        printWin();
    };
} else {
    window.onload = printWin;
}

window.onerror = handle_error;
window.onafterprint = function() {
    window.close();
}

function printWin()
{
    if (window.print) {
        window.print();
    } else {
        handle_error();
    }
}

function handle_error()
{
    window.alert('<?php echo addslashes(_("Your browser does not support this print option. Press Control/Command + P to print.")) ?>');
    return true;
}

</script>
