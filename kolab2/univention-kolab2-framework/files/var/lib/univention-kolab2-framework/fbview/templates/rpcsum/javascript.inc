<script language="JavaScript" type="text/javascript">
<!--

var cancelSubmit = false;

var fields = new Array(
<?php for ($i = 0; $i < count($rpc_servers); $i++): ?>
    new Array(
        "<?php echo addslashes($rpc_servers[$i]['url']) ?>",
        "<?php echo addslashes($rpc_servers[$i]['user']) ?>"
    )<?php if ($i + 1 < count($rpc_servers)) echo ','; ?>

<?php endfor; ?>
);

function newChoice()
{
    var action = document.prefs.server.options[document.prefs.server.selectedIndex].value;

    if (action == -1) {
        document.prefs.save.value = '<?php echo _('Create') ?>';
        document.prefs.reset();
    } else {
        document.prefs.save.value = '<?php echo _('Change') ?>';
        updateForm(action);
    }
}

function updateForm(server)
{
    document.prefs.edit_server.value = server;
    document.prefs.url.value =  fields[server][0];
    document.prefs.user.value = fields[server][1];
}

function clearForm()
{
    document.prefs.edit_server.value = '';
    document.prefs.url.value =  fields[server][0];
    document.prefs.user.value = fields[server][1];
    document.prefs.server.selectedIndex = 0;
    cancelSubmit = true;
}

function checkSubmit()
{
    cancel = cancelSubmit;
    cancelSubmit = false;
<?php if ($browser->getBrowser() == 'msie' && $browser->getMajor() >= 4): ?>
    window.event.returnValue = !cancel;
<?php endif; ?>
    return !cancel;
}

//-->
</script>
