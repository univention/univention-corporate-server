<div class="turbaPager">
 <div class="leftFloat">
  <strong><?php echo _("Contacts displayed:") ?></strong>
<?php
if ($numDisplayed) {
    echo '[' . sprintf(_("%s to %s of %s"), $start, $end, $numitem) . ']';
} else {
    echo _("None");
}
echo '</div>';
if (isset($pager)) {
    echo $pager->render();
}
?>
 <div class="clear"></div>
</div>
