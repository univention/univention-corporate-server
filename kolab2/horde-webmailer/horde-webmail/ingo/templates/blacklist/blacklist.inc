<form method="post" name="filters" action="<?php echo Horde::applicationUrl('blacklist.php') ?>">
<?php Util::pformInput() ?>
<input type="hidden" name="actionID" value="rule_update" />
<input type="hidden" name="new_folder_name" value="" />

<h1 class="header">
 <?php echo _("Blacklist") ?>
 <?php echo Help::link('ingo', 'blacklist') ?>
<?php if (!empty($bl_rule['disable'])): ?>
  &nbsp;[<span style="color:red"><?php echo _("Disabled") ?></span>]
<?php endif; ?>
</h1>

<table width="100%" cellspacing="0">
  <tr class="item0">
    <td>
      <?php echo _("Action for blacklisted addresses:") ?><br />
      <input type="radio" name="action" id="action_delete" value="delete" <?php if (empty($blacklist_folder)) echo 'checked="checked" ' ?>/> <?php echo Horde::label('action_delete', _("_Delete message completely")) ?><br />
<?php if ($have_mark): ?>
      <input type="radio" name="action" id="action_mark" value="mark" <?php if ($blacklist_folder == INGO_BLACKLIST_MARKER) echo 'checked="checked" ' ?>/> <?php echo Horde::label('action_mark', _("Mar_k message as deleted")) ?><br />
<?php endif; ?>
      <input type="radio" name="action" id="action_folder" value="folder" <?php if (!empty($blacklist_folder) && ($blacklist_folder != INGO_BLACKLIST_MARKER)) echo 'checked="checked" ' ?>/> <?php echo Horde::label('action_folder', _("_Move message to folder:")) ?>
      <label for="actionvalue" class="hidden"><?php echo _("Select target folder") ?></label>
      <?php echo $folder_list ?>
    </td>
    <td width="40" align="right">
      <?php echo Help::link('ingo', 'blacklist-action') ?>&nbsp;
    </td>
  </tr>
  <tr class="item1">
    <td align="left">
      <?php echo Horde::label('blacklist', _("_Enter each address on a new line:")) ?><br />
      <textarea name="blacklist" id="blacklist" rows="15" cols="80"><?php echo htmlspecialchars(implode("\n", $blacklist->getBlacklist())) ?></textarea>
    </td>
    <td width="40" align="right">
      <?php echo Help::link('ingo', 'blacklist-addresses') ?>&nbsp;
    </td>
  </tr>
  <tr>
    <td class="control" colspan="2">
      <input class="button" type="submit" value="&nbsp;<?php echo _("Save") ?>&nbsp;" />
      <input class="button" type="button" onclick="document.location.href='<?php echo Horde::applicationUrl('filters.php', true) ?>'" value="<?php echo _("Return to Rules List") ?>" />
    </td>
  </tr>
</table>
</form>
