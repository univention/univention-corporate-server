<h2><?php echo htmlspecialchars($tasklist->get('name')) ?></h2>
<?php if ($desc = $tasklist->get('desc')): ?>
<p><em><?php echo htmlspecialchars($desc) ?></em></p>
<?php endif; ?>
<p>
 <?php printf(_("Task List owned by %s."), $owner_name) ?>
 <?php echo _("To subscribe to this task list from another program, use this URL: ") ?>
</p>
<p class="tasklist-info-url">
 <?php echo htmlspecialchars($subscribe_url) ?>
</p>
