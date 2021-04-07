<?php
// based on /usr/share/simplesamlphp/www/admin/metadata-converter.php
set_error_handler(function($errno, $errstr, $errfile, $errline) {
	throw new ErrorException($errstr, 0, $errno, $errfile, $errline);
});

$xmldata = file_get_contents("php://stdin");
require_once('/usr/share/simplesamlphp/lib/_autoload.php');
\SimpleSAML\Utils\XML::checkSAMLMessage($xmldata, 'saml-meta');
$entities = SimpleSAML_Metadata_SAMLParser::parseDescriptorsString($xmldata);
foreach ($entities as $entityId => &$entity) {
	$entityMetadata = $entity->getMetadata20SP();
	unset($entityMetadata['entityDescriptor']);
	print('$metadata['.var_export($entityId, true).'] = ' . var_export($entityMetadata, true).";\n");
}
