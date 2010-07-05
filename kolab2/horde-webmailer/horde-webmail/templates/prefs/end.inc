 <p>
  <input type="submit" class="button" value="<?php echo _("Save Options") ?>" />&nbsp;
  <input type="reset" class="button" value="<?php echo _("Undo Changes") ?>" />&nbsp;
  <?php if (count($prefGroups) > 1): ?><input type="button" id="prefs_return" class="button" value="<?php echo _("Return to Options") ?>" onclick="document.prefs.actionID.value=0; document.prefs.group.value=''; document.prefs.submit();" /><?php endif; ?>
 </p>
</div>
</form>
