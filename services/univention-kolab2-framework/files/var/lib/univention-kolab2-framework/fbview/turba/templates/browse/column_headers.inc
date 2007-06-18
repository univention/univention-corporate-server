<tr>
  <td class="control" align="left">
    <form method="post" name="contacts" action="<?php echo Horde::selfURL() ?>">
    <?php echo Util::formInput() ?>
    <table border="0" cellpadding="0" cellspacing="1" width="100%">
    <tr>
      <th class="item" width="1%" style="cursor:pointer;" onclick="document.contacts.checkAll.checked = !document.contacts.checkAll.checked; SelectAll();" align="left" nowrap="nowrap" width="8%"><input type="checkbox" name="checkAll" onclick="document.contacts.checkAll.checked = !document.contacts.checkAll.checked; SelectAll();" <?php echo Horde::getAccessKeyAndTitle(_("Check _All/None")) ?>" /></th>
      <th class="item" width="1%"><?php echo Horde::img('edit.gif', _("Edit")) ?></th>
      <th class="item" width="1%"><?php echo Horde::img('mime/vcard.gif', _("vCard"), '', $registry->getParam('graphics', 'horde')) ?></th>
      <th class="item" width="1%"><?php echo Horde::img('group.gif', _("Group")) ?></th>
      <th class="<?php echo ($prefs->getValue('sortby') == 0) ? 'selected' : 'item' ?>" width="<?php echo $width ?>%" align="left" nowrap="nowrap">
        <a class="widget" href="" onclick="Sort(0, <?php echo abs(1 - $prefs->getValue('sortdir')) ?>); return false; "><?php echo Horde::img($prefs->getValue('sortdir') ? 'za.gif' : 'az.gif', _("Sort Direction"), null, $registry->getParam('graphics', 'horde')) ?></a>
        <a class="widget" href="" onclick="Sort(0, <?php echo $prefs->getValue('sortdir') ?>); return false;"><?php echo $attributes['name']['label'] ?></a>
      </th>
    <?php for ($i = 1; $i <= count($columns); $i++): ?>
      <th class="<?php echo ($prefs->getValue('sortby') == $i) ? 'selected' : 'item' ?>" width="<?php echo $width ?>%" align="left" nowrap="nowrap">
        <a class="widget" href="" onclick="Sort(<?php echo $i ?>, <?php echo abs(1 - $prefs->getValue('sortdir')) ?>); return false; "><?php echo Horde::img($prefs->getValue('sortdir') ? 'za.gif' : 'az.gif', _("Sort Direction"), null, $registry->getParam('graphics', 'horde')) ?></a>
        <a class="widget" href="" onclick="Sort(<?php echo $i ?>, <?php echo $prefs->getValue('sortdir') ?>); return false;"><?php echo $attributes[$columns[$i-1]]['label'] ?></a>
      </th>
    <?php endfor; ?>
    </tr>
