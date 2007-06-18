<?php if (!strstr($_SERVER['PHP_SELF'], 'javascript.php')): ?><script language="JavaScript" type="text/javascript">
<!--
<?php endif; ?>
function open_google_win(args)
{
    var url = "";
    for (var i=0; i < document.google.area.length; i++)
    {
        if (document.google.area[i].checked)
        {
            var val = document.google.area[i].value;
        }
    }

    var $lang='<?php echo substr($GLOBALS["prefs"]->getValue("language"),0,2); ?>';

    switch (val) {
	case "web":
    	url = "http://www.google.com/search?ie=UTF-8&oe=UTF-8&hl=" + $lang + "&q=";
	    break;

	case "images":
	    url = "http://images.google.com/images?ie=UTF-8&oe=UTF-8&hl=" + $lang + "&q=";
            break;

	case "groups":
	    url = "http://groups.google.com/groups?ie=UTF-8&oe=UTF-8&hl=" + $lang + "&q=";
            break;

	case "directory":
	    url = "http://www.google.com/search?lr=&ie=UTF-8&oe=UTF-8&hl=" + $lang + "&cat=gwd%2FTop&q=";
            break;

	case "news":
	    url = "http://news.google.com/news?ie=UTF-8&oe=UTF-8&hl=" + $lang + "&q=";
            break;

	default:
    	url = "http://www.google.com/search?ie=UTF-8&oe=UTF-8&hl=" + $lang + "&q=";
    }

    var name = "Google";
    var param = "toolbar=yes,location=yes,status=yes,scrollbars=yes,resizable=yes,width=800,height=600,left=0,top=0";
    url = url + escape(document.google.q.value);
    eval ("name = window.open(url, name, param)");
    if (!eval("name.opener")) eval("name.opener = self");
}

// -->
<?php if (!strstr($_SERVER['PHP_SELF'], 'javascript.php')): ?>// -->
</script>
<?php endif; ?>
