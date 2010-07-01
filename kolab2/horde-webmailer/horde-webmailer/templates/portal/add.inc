<?php if ($layout->isChanged($row, $col)): ?>
<a id="block"></a>
<?php endif; ?>

<p class="header"><?php echo _("Add Here:") ?></p>

<div style="padding:2px">
 <form action="<?php echo Horde::selfUrl() ?>#block" method="post">
 <?php Util::pformInput() ?>
 <input type="hidden" name="row" value="<?php echo $row ?>" />
 <input type="hidden" name="col" value="<?php echo $col ?>" />
 <input type="hidden" name="action" value="save-resume" />
 <?php echo $blocks->getBlocksWidget() ?>
 <input type="submit" class="button" value="<?php echo _("Add") ?>" />
 </form>
</div>
