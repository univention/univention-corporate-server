<?php
// 
function getTmpDir($dir) {
	// try to find the umc directory with timestamp
	$dirs = glob("${dir}_*");
	if (count($dirs)) {
		$dir = $dirs[0];
	}
	return $dir;
}

// if anything goes wrong, 'umc/' is the standard directory
$umcDir = getTmpDir("umc");
$cssDir = getTmpDir("css");

?>
<html>
	<head>
		<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
		<link rel="stylesheet" href="/dojo/dojo/resources/dojo.css" type="text/css"></link>
		<link rel="stylesheet" href="/dojo/dijit/themes/claro/claro.css" type="text/css"></link>
		<link rel="stylesheet" href="/dojo/dojox/grid/resources/Grid.css" type="text/css"></link>
		<link rel="stylesheet" href="/dojo/dojox/grid/resources/claroGrid.css" type="text/css"></link>
		<link rel="stylesheet" href="/dojo/dojox/grid/enhanced/resources/EnhancedGrid.css" type="text/css"></link>
		<link rel="stylesheet" href="/dojo/dojox/grid/enhanced/resources/claro/EnhancedGrid.css" type="text/css"></link>
		<link rel="stylesheet" href="/dojo/dojox/form/resources/CheckedMultiSelect.css" type="text/css"></link>
		<link rel="stylesheet" href="/dojo/dojox/widget/Dialog/Dialog.css" type="text/css"></link>
		<link rel="stylesheet" href="/dojo/dojox/widget/Standby/Standby.css" type="text/css"></link>
		<link rel="stylesheet" href="/dojo/dojox/widget/Toaster/Toaster.css" type="text/css" />
		<script type="text/javascript">
			var dojoConfig = {
				isDebug: true,
				debugAtAllCosts: true,
				locale: 'en-us',
				modulePaths: {
					umc: "/umc/<?php echo "$umcDir"; ?>"
				}
			};
		</script>
		<script type="text/javascript" src="/dojo-src/dojo/dojo.js"></script>
		<script type="text/javascript" src="<?php echo "$umcDir"; ?>/app.js"></script>
		<link rel="stylesheet" href="<?php echo "$cssDir"; ?>/style.css" />
	</head>
	<body class="claro">
	<div id="header" class="umcHeader" style="position: absolute; left: 0px; right: 0px;"></div>
	</body>
</html>
