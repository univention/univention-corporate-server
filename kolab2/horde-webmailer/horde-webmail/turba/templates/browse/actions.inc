<div class="control nowrap">
<?php if ($hasDelete) {
          echo Horde::widget('#', $this->getType() == 'list' ? _("Remove from this list") : _("Delete"), 'widget', '', "Submit('delete'); return false;", $this->getType() == 'list' ? _("_Remove from this list") : _("_Delete")) . ' | ';
      }
      if ($hasEdit) {
          echo Horde::widget('#', _("Edit"), 'widget', '', "document.contacts.action='" . Horde::applicationUrl('edit.php') . "'; Submit('groupedit'); return false;", _("Edit")) . ' | ';
      }
?>
 <?php if ($hasExport): ?>
 <?php echo Horde::widget('#', _("Export"), 'widget', '', "document.contacts.action='" . Horde::applicationUrl('data.php') . "'; Submit('select'); return false;", _("Export")) . ' | ' ?>
 <?php endif; ?>
 <?php if (!empty($copymove_source_options)): $id = md5(mt_rand()); ?>
 <form style="display:inline" name="f<?php echo $id ?>" action="javascript:void(0);" onsubmit="return false;">
 <?php
         if ($hasDelete) {
             echo Horde::link('#', _("Move"), 'widget', '', "CopyMove('move', document.f" . $id . '.s' . $id . "); return false;") . _("Move") . '</a>, ';
         }
         echo Horde::link('#', _("Copy"), 'widget', '', "CopyMove('copy', document.f" . $id . '.s' . $id . "); return false;") . _("Copy") . '</a>';
   ?>
  <label for="s<?php echo $id ?>" class="hidden"><?php echo _("Target Address Book") ?></label>
  <select name="s<?php echo $id ?>" id="s<?php echo $id ?>">
   <option value=""><?php echo _("to a different Address Book") ?></option>
   <?php echo $copymove_source_options ?>
  </select>
 </form> |
 <?php endif; ?>

 <?php if ($addToList): $id = md5(mt_rand()); ?>
 <form style="display:inline; background:inherit;" name="f<?php echo $id ?>" action="javascript:void(0);" onsubmit="return false;">
  <?php echo Horde::link('#', _("Add to"), 'widget', '', "Add(document.f" . $id . '.s' . $id . "); return false;") . _("Add") . '</a>' ?>
 <label for="s<?php echo $id ?>" class="hidden"><?php echo _("Target Contact List") ?></label>
 <select name="s<?php echo $id ?>" id="s<?php echo $id ?>">
  <option value=""><?php echo _("to a Contact List") ?></option>
  <option value="" disabled="disabled">- - - - - - - - -</option>
  <?php foreach ($addToList as $list): ?>
  <?php if (is_array($list)): ?>
  <option value="<?php echo $list['source'] . ($list['key'] ? ':' . $list['key'] : '') ?>"><?php echo $list['name'] ?></option>
  <?php else: ?>
  <option value="" disabled="disabled"><?php echo $list ?></option>
  <?php endif; endforeach; ?>
 </select>
 </form>
 <?php endif; ?>

<?php
$browse_link = Horde::applicationUrl('browse.php');
if ($this->getType() == 'directory' &&
    !empty($cfgSources[$default_source]['map']['__type'])) {
    printf(_("Show %s"), Horde::widget(Util::addParameter($browse_link, 'show', 'lists'), _("Show Lists"), 'widget', '', '', _("_Lists")) . ', ' .
        Horde::widget(Util::addParameter($browse_link, 'show', 'contacts'), _("Show Contacts"), 'widget', '', '', _("_Contacts")) . ', ' .
        Horde::widget(Util::addParameter($browse_link, 'show', 'all'), _("Show Both"), 'widget', '', '', _("Both")));
}
?>
</div>
