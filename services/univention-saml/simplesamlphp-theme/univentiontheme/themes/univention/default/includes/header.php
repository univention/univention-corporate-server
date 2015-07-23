<?php


/**
 * Support the htmlinject hook, which allows modules to change header, pre and post body on all pages.
 */
$this->data['htmlinject'] = array(
	'htmlContentPre' => array(),
	'htmlContentPost' => array(),
	'htmlContentHead' => array(),
);


$jquery = array();
if (array_key_exists('jquery', $this->data)) $jquery = $this->data['jquery'];

if (array_key_exists('pageid', $this->data)) {
	$hookinfo = array(
		'pre' => &$this->data['htmlinject']['htmlContentPre'], 
		'post' => &$this->data['htmlinject']['htmlContentPost'], 
		'head' => &$this->data['htmlinject']['htmlContentHead'], 
		'jquery' => &$jquery, 
		'page' => $this->data['pageid']
	);
		
	SimpleSAML_Module::callHooks('htmlinject', $hookinfo);	
}

// - o - o - o - o - o - o - o - o - o - o - o - o -

/**
 * Do not allow to frame simpleSAMLphp pages from another location.
 * This prevents clickjacking attacks in modern browsers.
 *
 * If you don't want any framing at all you can even change this to
 * 'DENY', or comment it out if you actually want to allow foreign
 * sites to put simpleSAMLphp in a frame. The latter is however
 * probably not a good security practice.
 */
header('X-Frame-Options: SAMEORIGIN');

?><!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<meta name="viewport" content="target-densitydpi=device-dpi, width=device-width, height=device-height, initial-scale=1.0" />
<title>Univention Corporate Server Single-Sign-On</title>

	<link rel="icon" type="image/icon" href="/favicon.ico" />

<?php	
if ($this->isLanguageRTL()) {
?>
	<link rel="stylesheet" type="text/css" href="/<?php echo $this->data['baseurlpath']; ?>resources/default-rtl.css" />
<?php
}
?>
	<meta name="robots" content="noindex, nofollow" />
<?php	
if(array_key_exists('head', $this->data)) {
	echo '<!-- head -->' . $this->data['head'] . '<!-- /head -->';
}

// read and sort available languages and prepare an array to later display them
$jsonfile = file_get_contents('/var/www/ucs-overview/languages.json');
$json = json_decode($jsonfile, true);
if($json != NULL) {
	function sort_by_label($a, $b) {
		return(strcasecmp($a['label'], $b['label']));
	}
	// hardcode english
	$en_us_found = false;
	foreach($json AS $entry) {
		if($entry['id'] === 'en-US'){
			$en_us_found = true;
		}
	}
	if(! $en_us_found) {
		$json[] = array ('id' => 'en-US', 'label' => 'English');
	}
	// sort entries and prepare html code
	usort($json, "sort_by_label");
	foreach($json AS $entry) {
		$splitarray = explode('-', $entry['id']);
		$langstring = $splitarray[0];
		$langlinkarray[] = array(
			"id" => $entry['id'],
			"label" => $entry['label'],
			"href" => SimpleSAML_Utilities::addURLparameter(SimpleSAML_Utilities::selfURL(), array($this->languageParameterName => $langstring ))
		);
	}
}
?>

<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="/ucs-overview/js/dijit/themes/dijit.css">
<link rel="stylesheet" href="/ucs-overview/css/bootstrap.css">
<link rel="stylesheet" href="/ucs-overview/css/ucs.css">

<script type="text/javascript">
	var availableLocales = <?php echo json_encode($langlinkarray); ?>;
</script>
<script type="text/javascript" src="/ucs-overview/js/ucs/query.js"></script>
<script type="text/javascript" src="/ucs-overview/js/dojo/dojo.js"></script>
<?php
/** don't display language switcher when e.g. forms were sent */
if ($_SERVER['REQUEST_METHOD'] == 'POST') {
?>
<style type="text/css">
	<!--
	#dropDownButton {
		display: none!important;
	}
	-->
</style>
<?php
}
?>
</head>
<body>
	<div id="wrap">
		<div id="site-header">
			<div class="container">
				<div id="title">
					<h1><?php echo($this->t('{univentiontheme:univention:serverwelcome}')); ?></h1>
					<h2><?php echo($this->configuration->getValue('hostfqdn', '')); ?></h2>
				</div>
				<div id="header-left"></div>
				<div id="header-right">
					<div id="dropDownButton"></div>	
				</div>
			</div>
		</div>
