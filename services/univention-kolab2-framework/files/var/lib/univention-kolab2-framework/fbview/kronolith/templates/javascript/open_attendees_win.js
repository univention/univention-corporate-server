<?php if (!strstr($_SERVER['PHP_SELF'], 'javascript.php')): ?><script language="JavaScript" type="text/javascript">
<!--
<?php endif; ?>
function open_attendees_win(args)
{
    var url = "<?php echo Horde::url($GLOBALS['registry']->applicationWebPath('%application%/attendees.php', 'kronolith')) ?>";
    if (url.indexOf('?') == -1) glue = '?';
    else glue = '<?php echo ini_get('arg_separator.output') ?>';
    var now = new Date();
    var name = "attendees_window_" + now.getTime();
    if (args != "") {
        url = url + glue + args + '<?php echo ini_get('arg_separator.output') ?>' + "uniq=" + now.getTime();
    } else {
        url = url + glue + "uniq=" + now.getTime();
    }
    var Width = screen.width;
    if (Width > 775) {
        Width = 700;
    } else {
        Width -= 75;
    }
    var Height = screen.height;
    if (Height > 725) {
        Height = 650;
    } else {
        Height -= 75;
    }
    param = "toolbar=no,location=no,status=yes,scrollbars=yes,resizable=yes,width=" + Width + ",height=" + Height + ",left=0,top=0";
    name = window.open(url, name, param);
    if (!eval("name.opener")) {
        name.opener = self;
    }
}
<?php if (!strstr($_SERVER['PHP_SELF'], 'javascript.php')): ?>// -->
</script>
<?php endif; ?>
