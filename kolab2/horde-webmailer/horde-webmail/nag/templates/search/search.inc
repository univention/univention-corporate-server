<form method="get" name="search" action="list.php">
<?php Util::pformInput() ?>
<input type="hidden" name="actionID" value="search_tasks" />

<h1 class="header">
 <?php echo _("Task Search") ?>
</h1>

<div class="headerbox" style="padding:3px">

<p>
 <strong><?php echo Horde::label('search_pattern', _("Search _Text:")) ?></strong><br />
 <input name="search_pattern" id="search_pattern" type="text" size="50" maxlength="100" />
</p>

<p>
 <strong><?php echo _("Search In:") ?></strong><br />
 <input id="name" name="search_name" type="checkbox" checked="checked" /> <?php echo Horde::label('name', _("N_ame")) ?><br />
 <input id="desc" name="search_desc" type="checkbox" /> <?php echo Horde::label('desc', _("_Description")) ?><br />
 <input id="category" name="search_category" type="checkbox" /> <?php echo Horde::label('category', _("_Category")) ?>
</p>

<p>
 <strong><?php echo _("Search:") ?></strong><br />
 <input id="all" name="search_completed" type="radio" value="1" checked="checked" /> <?php echo Horde::label('all', _("_All Tasks")) ?><br />
 <input id="incomplete" name="search_completed" type="radio" value="0" /> <?php echo Horde::label('incomplete', _("Incomplete Tasks")) ?><br />
 <input id="complete" name="search_completed" type="radio" value="2" /> <?php echo Horde::label('complete', _("Completed Tasks")) ?><br />
</p>

<p>
 <input type="submit" class="button" value="<?php echo _("Search") ?>" />
</p>

</div>

</form>
