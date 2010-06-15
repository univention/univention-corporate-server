<tr><td>
<table width="100%" border="0" cellspacing="0" cellpadding="1">
<tr>
  <td align="left" nowrap="nowrap" class="control">
    <?php echo Horde::widget('', $listType == 'list' ? _("Remove from this list") : _("Delete"), 'widget', '', "Submit('delete'); return false;", $listType == 'list' ? _("_Remove from this list") : _("_Delete")) . '</a>' ?>
  </td>

<?php if (!empty($add_source_options)): ?>
  <td align="left" nowrap="nowrap" class="control">
    <form name='copymove' action="javascript:void(0);" onsubmit="return false;">
     |
    <?php echo Horde::link('', _("Move"), 'widget', '', "CopyMove('move'); return false;") . _("Move") . '</a> | ';
          echo Horde::link('', _("Copy"), 'widget', '', "CopyMove('copy'); return false;") . _("Copy") . '</a>' ?>
    <select name="targetAddressbook">
      <option value=""><?php echo _("to Selected Address Book") ?></option>
      <?php echo $add_source_options ?>
    </select>
    </form>
  </td>
<?php endif; ?>

<?php if (!empty($cfgSources[$source]['map']['__type'])): ?>
  <td align="left" nowrap="nowrap" class="control">
    <form name='targetList' action="javascript:void(0);" onsubmit="return false;">
     |
    <?php echo Horde::link('', _("Add to"), 'widget', '', "Add(); return false;") . _("Add to") . '</a>' ?>
    <select name="listList">
      <option value=""><?php echo _("Select List") ?></option>
      <option value="">-----</option>
      <option value="*new*"><?php echo _("New List") ?></option>
      <option value="">-----</option>
<?php foreach ($addToList as $list): ?>
      <option value="<?php echo $list['key'] ?>"><?php echo $list['name'] ?></option>
<?php endforeach; ?>
    </select>
    </form>
  </td>
<?php endif; ?>

  <td align="right" nowrap="nowrap" width="100%" class="control">
<?php
$browse_link = Util::addParameter(Horde::applicationUrl('browse.php'), 'source', $source);
if ($listType == 'directory' && !empty($cfgSources[$source]['map']['__type'])) {
    echo Horde::widget(Util::addParameter($browse_link, 'show', 'lists'), _("Show Lists"), 'widget', '', '', _("Show _Lists")) . ' | ';
    echo Horde::widget(Util::addParameter($browse_link, 'show', 'contacts'), _("Show Contacts"), 'widget', '', '', _("Show _Contacts")) . ' | ';
    echo Horde::widget(Util::addParameter($browse_link, 'show', 'all'), _("Show All"), 'widget', '', '', _("Sho_w All"));
} elseif ($listType == 'list' && !empty($cfgSources[$source]['map']['__type'])) {
    echo Horde::widget(Util::addParameter($browse_link, 'show', 'all'), sprintf(_("Back to %s"), $cfgSources[$source]['title']), 'widget', '', '', sprintf(_("Ba_ck to %s"), $cfgSources[$source]['title']));
} elseif ($listType == 'search') {
    if ($conf['search']['cache']) {
        $search_link = Util::addParameter(Horde::applicationUrl('search.php'), 'source', $source);
        echo Horde::widget(Util::addParameter($search_link, 'clear', '1'), _("Clear Search"), 'widget', '', '', _("C_lear Search"));
    } else {
        echo '&nbsp;';
    }
}
?>
  </td>
</tr>
</table>
</td></tr>
