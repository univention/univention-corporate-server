<div id="menu" style="overflow:hidden">
 <?php if (!empty($conf['logo']['image']) || !Util::getFormData('mozbar')): ?>
 <span class="leftFloat"<?php if (empty($conf['logo']['image'])) echo ' id="themelogo"' ?>>
 <?php
 if (!empty($conf['logo']['image'])) {
     if (!empty($conf['logo']['link'])) {
         echo Horde::link($conf['logo']['link'], null, null, '_top');
     }
     echo Horde::img($conf['logo']['image'], '', '', '');
     if (!empty($conf['logo']['link'])) {
         echo '</a>';
     }
 } else {
     echo '&nbsp;';
 }
 ?>
 </span>
 <div class="clear">&nbsp;</div>
 <?php endif; ?>
</div>

<div id="expandedSidebar" style="overflow:hidden">
 <span id="expandButton" class="rightFloat"><?php if (!$is_mozbar) echo Horde::link('#', _("Collapse Sidebar"), '', '', 'HordeSidebar.toggleMenuFrame(); return false;', _("Collapse Sidebar")) . Horde::img('hide_panel.png') . '</a>' ?></span>
 <div id="sidebarPanel">
  <?php $tree->renderTree() ?>
 </div>
</div>

<div id="hiddenSidebar">
 <?php echo Horde::link('#', '', '', '', 'HordeSidebar.toggleMenuFrame(); return false;') . Horde::img('show_panel.png') . '</a>' ?>
</div>

<script type="text/javascript">
var horde_sidebar_rtl = <?php echo $rtl ? 'true' : 'false' ?>,
    horde_sidebar_cols = <?php echo (isset($prefs) ? $prefs->getValue('sidebar_width') : 150) ?>,
    horde_sidebar_domain = '<?php echo htmlspecialchars($GLOBALS['conf']['cookie']['domain']) ?>',
    horde_sidebar_path = '<?php echo $GLOBALS['conf']['cookie']['path'] ?>',
    horde_sidebar_refresh = <?php echo intval($prefs->getValue('menu_refresh_time')) ?>,
    horde_sidebar_url = '<?php echo Horde::applicationUrl('services/portal/sidebar.php') ?>';
</script>

<?php if (isset($GLOBALS['notification'])) $GLOBALS['notification']->notify(array('listeners' => array('javascript'))) ?>

</body>
</html>
