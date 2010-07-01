  <tr>
    <td align="center">
      <table>
        <tr>
<?php if ($actionID != 'show_active'): ?>
          <td>
            <form method="post" name="activate_script" action="<?php echo Horde::applicationUrl('script.php') ?>">
              <?php Util::pformInput() ?>
              <input type="hidden" name="actionID" value="action_activate" />
              <input class="button" type="submit" name="submit" value="<?php echo _("Activate Script") ?>" />
            </form>
          </td>
          <td>
            <form method="post" name="deactivate_script" action="<?php echo Horde::applicationUrl('script.php') ?>">
              <?php Util::pformInput() ?>
              <input type="hidden" name="actionID" value="action_deactivate" />
              <input class="button" type="submit" name="submit" value="<?php echo _("Deactivate Script") ?>" />
            </form>
          </td>
          <td>
            <form method="post" name="show_active_script" action="<?php echo Horde::applicationUrl('script.php') ?>">
              <?php Util::pformInput() ?>
              <input type="hidden" name="actionID" value="show_active" />
              <input class="button" type="submit" name="submit" value="<?php echo _("Show Active Script") ?>" />
            </form>
          </td>
<?php else: ?>
          <td>
            <form method="post" name="show_current_script" action="<?php echo Horde::applicationUrl('script.php') ?>">
              <?php Util::pformInput() ?>
              <input class="button" type="submit" name="submit" value="<?php echo _("Show Current Script") ?>" />
            </form>
          </td>
<?php endif; ?>
        </tr>
      </table>
    </td>
  </tr>
</table>
