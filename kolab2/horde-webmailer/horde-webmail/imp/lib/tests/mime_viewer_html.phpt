--TEST--
 tests.
--FILE--
<?php

require_once 'Horde.php';
require_once 'Horde/MIME/Viewer.php';
require_once dirname(dirname(__FILE__)) . '/MIME/Viewer/html.php';

class MockRegistry {
    function getImageDir()
    {
        return '';
    }
}

$registry = new MockRegistry();
$mock_part = null;
$v = new IMP_MIME_Viewer_html($mock_part);

// Test regex for converting links to open in a new window.
echo $v->_openLinksInNewWindow('foo') . "\n";
echo $v->_openLinksInNewWindow('example@example.com') . "\n";
echo $v->_openLinksInNewWindow('foo <a href="#bar">Anchor</a>') . "\n";
echo $v->_openLinksInNewWindow('foo <a href="http://www.example.com/">example</a>') . "\n";
echo $v->_openLinksInNewWindow('foo <a target="foo" href="http://www.example.com/">example</a>') . "\n";
echo $v->_openLinksInNewWindow('foo <a href="http://www.example.com/" target="foo">example</a>') . "\n";
echo $v->_openLinksInNewWindow('foo <a mailto="example@example.com">Example Email</a>') . "\n";
echo $v->_openLinksInNewWindow('<map name="Map"><area shape="rect" coords="32,-2,293,29" href="http://www.example.com/"></map>') . "\n";
echo $v->_openLinksInNewWindow('<map name="Map"><area shape="rect" coords="32,-2,293,29" href="http://www.example.com/" target="foo"></map>') . "\n";
echo "\n";

// Test regex for hiding images.
echo preg_replace_callback($v->_img_regex, array($v, '_blockImages'),
                           '<img src="http://example.com/image.png">') . "\n";
echo preg_replace_callback($v->_img_regex, array($v, '_blockImages'),
                           '<img src="http://example.com/image.png" />') . "\n";
echo preg_replace_callback($v->_img_regex, array($v, '_blockImages'),
                           '<td  background=http://example.com/image.png>') . "\n";
echo preg_replace_callback($v->_img_regex, array($v, '_blockImages'),
                           "<img src= http://example.com/image.png alt='Best flight deals'  border=0>") . "\n";
echo preg_replace_callback($v->_img_regex, array($v, '_blockImages'),
                           '<foo style="background:url(http://example.com/image.png)">') . "\n";
echo preg_replace_callback($v->_img_regex, array($v, '_blockImages'),
                           '<foo style="background: transparent url(http://example.com/image.png) repeat">') . "\n";
echo preg_replace_callback($v->_img_regex, array($v, '_blockImages'),
                           '<foo style="background-image:url(http://example.com/image.png)">') . "\n";
echo preg_replace_callback($v->_img_regex, array($v, '_blockImages'),
                           '<foo style="background: transparent url(http://example.com/image.png) repeat">
<foo style="background-image:url(http://example.com/image.png)">') . "\n";

?>
--EXPECT--
foo
example@example.com
foo <a href="#bar">Anchor</a>
foo <a target="_blank" href="http://www.example.com/">example</a>
foo <a   target="_blank" href="http://www.example.com/">example</a>
foo <a  href="http://www.example.com/"  target="_blank">example</a>
foo <a target="_blank" mailto="example@example.com">Example Email</a>
<map name="Map"><area target="_blank" shape="rect" coords="32,-2,293,29" href="http://www.example.com/"></map>
<map name="Map"><area  shape="rect" coords="32,-2,293,29" href="http://www.example.com/"  target="_blank"></map>

<img src="/spacer_red.png" blocked="http%3A%2F%2Fexample.com%2Fimage.png">
<img src="/spacer_red.png" blocked="http%3A%2F%2Fexample.com%2Fimage.png" />
<td  background="/spacer_red.png" blocked="http%3A%2F%2Fexample.com%2Fimage.png">
<img src="/spacer_red.png" blocked="http%3A%2F%2Fexample.com%2Fimage.png" alt='Best flight deals'  border=0>
<foo style="background:url('/spacer_red.png')" blocked="http%3A%2F%2Fexample.com%2Fimage.png">
<foo style="background: transparent url('/spacer_red.png') repeat" blocked="http%3A%2F%2Fexample.com%2Fimage.png">
<foo style="background-image:url('/spacer_red.png')" blocked="http%3A%2F%2Fexample.com%2Fimage.png">
<foo style="background: transparent url('/spacer_red.png') repeat" blocked="http%3A%2F%2Fexample.com%2Fimage.png">
<foo style="background-image:url('/spacer_red.png')" blocked="http%3A%2F%2Fexample.com%2Fimage.png">
