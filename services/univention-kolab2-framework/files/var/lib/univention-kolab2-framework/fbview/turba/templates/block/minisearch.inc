<script language="JavaScript" type="text/javascript">
var busyExpanding = false;
function mini_search(e)
{
    if (e != undefined && !enter_key_trap(e)) {
        return;
    }

    if (document.busyExpanding) {
        return;
    }
    document.getElementById('turba_minisearch_searching').style.visibility = 'visible';
    document.getElementById('turba_minisearch_iframe').style.display = 'inline';

    if (document.frames) {
        var iframe = document.frames['turba_minisearch_iframe'];
    } else if (document.getElementById) {
        var iframe = document.getElementById('turba_minisearch_iframe');
    } else {
        return;
    }
    if (!iframe) {
        return;
    }

    var doc;
    if (iframe.contentDocument) {
        doc = iframe.contentDocument;
    } else if (iframe.contentWindow) {
        doc = iframe.contentWindow.document;
    } else if (iframe.document) {
        doc = iframe.document;
    } else {
        return true;
    }

    url = '<?php echo Horde::applicationUrl(Util::addParameter('minisearch.php', 1, 1), true) ?>';
    url = url + '<?php echo ini_get('arg_separator.output') ?>search=' + escape(document.getElementById('turba_minisearch').value);
    doc.location.replace(url);

}
</script>

<table width="100%" border="0" cellpadding="0" cellspacing="0"><tr><td class="control"><b><?php echo _("Quick Search") ?></b></td></tr>
<tr><td>
<input id="turba_minisearch" size="35" onchange="mini_search();" />
</td></tr>
<tr><td>
<input type="button" class="button" onclick="mini_search();" value="<?php echo _("Search") ?>" />
</td></tr>
</table>

<span id="turba_minisearch_searching" style="width:100%; color:red; visibility:hidden;"><?php echo _("Searching..."); ?></span>

<div><iframe id="turba_minisearch_iframe" style="width:100%; height:100px; border:none; display:none" src="<?php echo Horde::applicationUrl('minisearch.php') ?>"></iframe></div>
