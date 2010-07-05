<form method="post" name="filters" action="<?php echo Horde::applicationUrl('whitelist.php') ?>">
<?php Util::pformInput() ?>
<input type="hidden" name="actionID" value="rule_update" />
<h1 class="header">
  <?php echo _("Whitelist") ?>
  <?php echo Help::link('ingo', 'whitelist') ?>
<?php if (!empty($wl_rule['disable'])): ?>
  &nbsp;[<span style="color:red"><?php echo _("Disabled") ?></span>]
<?php endif; ?>
</h1>
<table cellspacing="0" cellpadding="0">
  <tr class="item0">
    <td align="left">
      <?php echo Horde::label('whitelist', _("Wh_itelist addresses:")) ?><br />
      <textarea name="whitelist" id="whitelist" rows="15" cols="80"><?php echo htmlspecialchars(implode("\n", $whitelist->getWhitelist())) ?></textarea>
    </td>
    <td align="right">
      <?php echo Help::link('ingo', 'whitelist-addresses') ?>&nbsp;
    </td>
  </tr>
  <tr>
    <td colspan="2" class="control">
      <input class="button" type="submit" value="&nbsp;<?php echo _("Save") ?>&nbsp;" />
      <input class="button" type="button" onclick="document.location.href='<?php echo Horde::applicationUrl('filters.php', true) ?>'" value="<?php echo _("Return to Rules List") ?>" />
    </td>
  </tr>
</table>
</form>
