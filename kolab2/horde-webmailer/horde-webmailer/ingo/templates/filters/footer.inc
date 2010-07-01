</tbody>
</table>
<?php if ($createrule || $canapply): ?>
<div class="control" style="padding:2px">
<?php if ($createrule): ?>
 <input class="button" type="button" onclick="window.location='<?php echo addslashes($rule_url) ?>'" value="&nbsp;<?php echo _("New Rule") ?>&nbsp;" />
<?php endif; if ($canapply): ?>
 <input class="button" type="button" onclick="document.filters.actionID.value='apply_filters';document.filters.submit(); return true;" value="&nbsp;<?php echo _("Apply Filters") ?>&nbsp;" />
<?php endif; endif; ?>
</div>
</form>
