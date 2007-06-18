<?php
/**
 * $Horde: horde/util/google_example.php,v 1.1 2003/09/28 03:23:52 chuck Exp $
 */

$google_key = '';

define('HORDE_BASE', dirname(__FILE__));
require_once HORDE_BASE . '/lib/base.php';
require_once HORDE_BASE . '/lib/Search.php';

if (empty($google_key)) {
    exit('You must provide a Google API key.');
}

$google = &Horde_Search::singleton('google', array('key' => $key));
$result = $google->search(array('query' => Util::getFormData('q', 'horde')));

if ($result !== $false) {
    echo '<pre>';
    var_dump($result);
    echo '</pre>';
} else {
    echo 'Query failed.';
}
