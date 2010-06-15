<table border="0" align="center" width="95%" cellpadding="3" cellspacing="2">
<tr class="header">
    <td class="header">
        <b><?php printf(_("%s Maintenance Operations - Confirmation"), $registry->getParam('name', $module)); ?></b>
    </td>
</tr>
<tr><td>&nbsp;</td></tr>
<tr>
    <td class="light">
        <span class="header"><?php echo _("Notice") ?>
        <span class="smallheader"><?php printf(_(" &#151; %s is ready to perform the maintenance operations checked below."), $registry->getParam('name'), $module); ?>
        <br />
        <?php echo _("Check the box for any operation(s) you want to perform at this time.") ?></span></span>
    </td>
</tr>
<tr><td>&nbsp;</td></tr>
