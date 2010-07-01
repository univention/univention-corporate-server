<script type="text/javascript">
var busyExpanding = false;
function mini_search()
{
    if (busyExpanding) {
        return false;
    }
   $('turba_minisearch_searching',
     'turba_minisearch_close',
     'turba_minisearch_iframe').invoke('show');
}
function hide_mini_search()
{
   $('turba_minisearch_searching',
     'turba_minisearch_close',
     'turba_minisearch_iframe').invoke('hide');
   $('turba_minisearch_iframe').src = 'about:blank';
}
</script>

<form name="turba_minisearch" action="<?php echo Horde::applicationUrl('minisearch.php') ?>" onsubmit="mini_search();" target="turba_minisearch_iframe">
<?php Util::pformInput() ?>
<?php echo Horde::label('search', _("Search for: ")) ?>
<input name="search" id="search" size="35" />
<input type="submit" class="button" value="<?php echo _("Search") ?>" />
<input type="submit" class="button" style="display:none" value="<?php echo _("Close") ?>" id="turba_minisearch_close" onclick="hide_mini_search(); return false;" />
<span id="turba_minisearch_searching" style="display:none"><?php echo Horde::img('loading.gif', '', '', $GLOBALS['registry']->getImageDir('horde'))?></span>
</form>

<div><iframe id="turba_minisearch_iframe" name="turba_minisearch_iframe" style="width:100%;border:none;display:none" frameborder="0" src="about:blank"></iframe></div>
