<div class="header leftAlign">
 <?php echo htmlspecialchars($title) . ' (' . $tasks->count() . ')' ?>
 <?php if (!$print_view): ?>
 <a id="quicksearchL" href="<?php echo Horde::applicationUrl('search.php') ?>" title="<?php echo _("Search") ?>" onclick="$('quicksearchL').hide(); $('quicksearch').show(); $('quicksearchT').focus(); return false;"><?php echo Horde::img('search.png', _("Search"), '', $registry->getImageDir('horde')) ?></a>
 <div id="quicksearch" style="display:none">
  <input type="text" name="quicksearchT" id="quicksearchT" for="tasks-body" empty="tasks_empty" />
  <small>
   <a title="<?php echo _("Close Search") ?>" href="#" onclick="$('quicksearch').hide(); $('quicksearchT').value = ''; QuickFinder.filter($('quicksearchT')); $('quicksearchL').show(); return false;">X</a>
   <?php echo Horde::link(Horde::applicationUrl('search.php')) . _("More Options...") ?></a>
  </small>
 </div>
 <?php endif; ?>
</div>
