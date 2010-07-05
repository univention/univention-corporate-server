<br />

<?php $flags_val = $prefs->getValue('filter_seen') ?>
<form method="post" name="filtersettings" action="filters.php">
<?php Util::pformInput() ?>
<input type="hidden" name="actionID" value="settings_save" />
<h1 class="header">
 <?php echo _("Additional Settings") ?>
</h1>

<table width="100%" cellspacing="0">
  <tr>
    <td class="item" align="left">
      <input type="checkbox" id="show_filter_msg" name="show_filter_msg"<?php if ($prefs->getValue('show_filter_msg')) echo ' checked="checked"' ?> />&nbsp;
      <?php echo Horde::label('show_filter_msg', _("Display detailed notification when each filter is applied?")) ?>
    </td><td class="item" align="right" width="1%">
      <?php echo Help::link('ingo', 'pref-show_filter_msg') ?>
    </td>
  </tr><tr>
    <td class="item" align="left" width="99%"><?php echo Horde::label('filter_seen', _("Filter Options")) ?>&nbsp;
      <select id="filter_seen" name="filter_seen">
        <option value="0"<?php if (empty($flags_val)) echo ' selected="selected"' ?>><?php echo _("Filter All Messages") ?></option>
        <option value="<?php echo INGO_SCRIPT_FILTER_UNSEEN ?>"<?php if ($flags_val == INGO_SCRIPT_FILTER_UNSEEN) echo ' selected="selected"' ?>><?php echo _("Filter Only Unseen Messages") ?></option>
        <option value="<?php echo INGO_SCRIPT_FILTER_SEEN ?>"<?php if ($flags_val == INGO_SCRIPT_FILTER_SEEN) echo ' selected="selected"' ?>><?php echo _("Filter Only Seen Messages") ?></option>
      </select>
    </td><td class="item" align="right" width="1%">
      <?php echo Help::link('ingo', 'pref-filter_seen') ?>
    </td>
  </tr><tr>
    <td colspan="2" class="control">
      <input class="button" type="button" onclick="document.filtersettings.submit(); return true;" value="&nbsp;<?php echo _("Save Settings") ?>&nbsp;" />
    </td>
  </tr>
</table>
</form>
