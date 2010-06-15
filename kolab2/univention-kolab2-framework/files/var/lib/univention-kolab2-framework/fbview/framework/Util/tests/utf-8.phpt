--TEST--
UTF-8 String:: tests
--FILE--
<?php

require dirname(__FILE__) . '/../String.php';

/* The following strings were taken with permission from the UTF-8
 * sampler by Frank da Cruz <fdc@columbia.edu> and the Kermit Project
 * (http://www.columbia.edu/kermit/).  The original page is located at
 * http://www.columbia.edu/kermit/utf8.html */

// French 50
echo String::length('Je peux manger du verre, ça ne me fait pas de mal.', 'UTF-8') . "\n";

// Spanish 36
echo String::length('Puedo comer vidrio, no me hace daño.', 'UTF-8') . "\n";

// Portuguese 34
echo String::length('Posso comer vidro, não me faz mal.', 'UTF-8') . "\n";

// Brazilian Portuguese 34
echo String::length('Posso comer vidro, não me machuca.', 'UTF-8') . "\n";

// Italian 41
echo String::length('Posso mangiare il vetro e non mi fa male.', 'UTF-8') . "\n";

// English 39
echo String::length('I can eat glass and it doesn\'t hurt me.', 'UTF-8') . "\n";

// Norsk/Norwegian/Nynorsk 33 
echo String::length('Eg kan eta glas utan å skada meg.', 'UTF-8') . "\n";

// Svensk/Swedish 36
echo String::length('Jag kan äta glas utan att skada mig.', 'UTF-8') . "\n";

// Dansk/Danish 45
echo String::length('Jeg kan spise glas, det gør ikke ondt på mig.', 'UTF-8') . "\n";

// Deutsch/German 41
echo String::length('Ich kann Glas essen, ohne mir weh zu tun.', 'UTF-8') . "\n";

// Russian 38
echo String::length('Я могу есть стекло, оно мне не вредит.', 'UTF-8') . "\n";

?>
--EXPECT--
50
36
34
34
41
39
33
36
45
41
38
