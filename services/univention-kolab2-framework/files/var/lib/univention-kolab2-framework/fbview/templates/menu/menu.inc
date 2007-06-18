<table border="0" cellpadding="0" cellspacing="0" width="100%">
  <tr>
    <td class="menu">
      <table border="0" width="100%">
        <tr>
          <?php
          foreach ($menu as $m) {
              echo Menu::createItem($m['url'], $m['text'], $m['icon'], $m['icon_path']);
          }
          ?>
          <td width="100%">&nbsp;</td><!-- spacer -->
        </tr>
      </table>
    </td>
  </tr>
</table><br />

<?php
$GLOBALS['notification']->notify(array('listeners' => 'status'));
