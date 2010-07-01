      </table>
    </td>
    <td width="40" align="right">
      <?php echo Help::link('ingo', 'rule-matches') ?>&nbsp;
    </td>
  </tr>

  <tr class="item0">
    <td>
      <em><?php echo Horde::label('action', _("Do this:")) ?></em>
      <br />
      <select onchange="document.rule.submit(); return true;" id="action" name="action">
        <?php echo $actionselect ?>
      </select>
      <?php echo $actionvaluelabel ?>
      <?php echo $actionvalue ?>
    </td><td width="40" align="right">
      <?php echo Help::link('ingo', 'rule-action') ?>&nbsp;
    </td>
  </tr>

<?php if ($current_action->flags && $ingo_script->imapFlags()): ?>
  <tr class="item0">
    <td>
      <em><?php echo _("Mark message as:") ?></em>
      <br />
      <table cellspacing="0">
        <tr>
          <td>
            <input type="checkbox" id="seen" name="flags[]" value="<?php echo INGO_STORAGE_FLAG_SEEN ?>"<?php echo (INGO_STORAGE_FLAG_SEEN & $rule['flags']) ? ' checked="checked" ' : '' ?>/><?php echo Horde::label('seen', _("Seen")) ?>&nbsp;
          </td><td>
            <input type="checkbox" id="flagged" name="flags[]" value="<?php echo INGO_STORAGE_FLAG_FLAGGED ?>"<?php echo (INGO_STORAGE_FLAG_FLAGGED & $rule['flags']) ? ' checked="checked" ' : '' ?>/><?php echo Horde::label('flagged', _("Flagged For Followup")) ?>&nbsp;
          </td><td>
            <input type="checkbox" id="answered" name="flags[]" value="<?php echo INGO_STORAGE_FLAG_ANSWERED ?>"<?php echo (INGO_STORAGE_FLAG_ANSWERED & $rule['flags']) ? ' checked="checked" ' : '' ?>/><?php echo Horde::label('answered', _("Answered")) ?>&nbsp;
          </td><td>
            <input type="checkbox" id="deleted" name="flags[]" value="<?php echo INGO_STORAGE_FLAG_DELETED ?>"<?php echo (INGO_STORAGE_FLAG_DELETED & $rule['flags']) ? ' checked="checked" ' : '' ?>/><?php echo Horde::label('deleted', _("Deleted")) ?>&nbsp;
          </td>
        </tr>
      </table>
    </td>
    <td width="40" align="right">
      <?php echo Help::link('ingo', 'rule-mark') ?>&nbsp;
    </td>
  </tr>
<?php endif; ?>

<?php if ($ingo_script->stopScript()): ?>
  <tr class="item1">
    <td align="left">
      <input type="checkbox" id="stop" name="stop" value="1"<?php echo ($rule['stop']) ? ' checked="checked"' : '' ?> /> <?php echo Horde::label('stop', _("Stop checking if this rule matches?")) ?>
    </td>
    <td width="40" align="right">
      <?php echo Help::link('ingo', 'rule-stop') ?>&nbsp;
    </td>
  </tr>
<?php endif; ?>

  <tr>
    <td class="control" colspan="2">
      <input class="button" type="button" onclick="document.rule.actionID.value='rule_save';document.rule.submit(); return true;" value="&nbsp;<?php echo _("Save") ?>&nbsp;" />
      <input class="button" type="button" onclick="document.location.href='<?php echo Horde::applicationUrl('filters.php', true) ?>'" value="<?php echo _("Return to Filters List") ?>" />
    </td>
  </tr>
</table>
</form>
