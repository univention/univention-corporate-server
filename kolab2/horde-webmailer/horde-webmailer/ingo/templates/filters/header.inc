<script type="text/javascript">
function moveFromTo(from, to, upurl, downurl)
{
    var steps = to - from;
    if (steps < 0) {
        window.location = upurl + '&steps=' + -steps;
    } else if (steps > 0) {
        window.location = downurl + '&steps=' + steps;
    }
    return true;
}
</script>
<form method="post" name="filters" action="<?php echo Horde::applicationUrl('filters.php') ?>">
<?php Util::pformInput() ?>
<input type="hidden" name="actionID" value="" />
<div class="header">
 <?php echo _("Existing Rules") . ' ' . Help::link('ingo', 'filters_rules') ?>
</div>

<table width="100%" cellspacing="0" class="striped">
<thead>
 <tr class="item">
  <th width="1%"><?php echo _("Edit") ?></th>
  <th class="leftAlign"><?php echo _("Rule") ?></th>
  <th width="1%"><?php echo _("Enabled") ?></th>
  <?php if ($edit_allowed): ?>
  <th width="1%"></th>
  <th width="1%"></th>
  <th width="1%"><?php echo _("Move") ?></th>
  <?php endif; ?>
 </tr>
</thead>
<tbody>
