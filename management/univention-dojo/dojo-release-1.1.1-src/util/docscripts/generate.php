<?php

include_once('includes/dojo.inc');

$xml_file = fopen('api.xml', 'w');
$document = new DomDocument();
$api = $document->createElement('api');

$files = dojo_get_files();
foreach ($files as $set){
	list($namespace, $file) = $set;
	$contents = dojo_get_contents($namespace, $file);

	$resource = $document->createElement('resource');
	$resource->setAttribute('provides', $contents['#provides']);
	$resource->setAttribute('project', $contents['#project']);
	$resource->setAttribute('file', $file);

	unset($contents['#provides']);
	unset($contents['#project']);

	if ($contents['#requires']) {
		$requires = $document->createElement('requires');
		foreach ($contents['#requires'] as $set) {
			$require = $document->createElement('require');
			$require->setAttribute('environment', $set[0]);
			$require->setAttribute('resource', $set[1]);
			$requires->appendChild($require);
		}
		$resource->appendChild($requires);
	}
	
	unset($contents['#requires']);
	
	$vars = $document->createElement('vars');
	foreach ($contents as $name => $set) {
		$var = $document->createElement('var');
		$var->setAttribute('name', $name);

		unset($set['source']);

		if ($set['returns']) {
			$var->setAttribute('returns', $set['returns']);
		}
		unset($set['returns']);

		if ($set['type']) {
			$var->setAttribute('type', $set['type']);
		}
		unset($set['type']);
		
		if ($set['initialized']) {
			$var->setAttribute('initialized', $set['initialized']);
		}
		unset($set['initialized']);
		
		if ($set['prototype']) {
			$var->setAttribute('prototype', $set['prototype']);
			unset($set['prototype']);
		}
		
		if ($set['instance']) {
			$var->setAttribute('instance', $set['instance']);
			unset($set['instance']);
		}
		
		if ($set['private']) {
			$var->setAttribute('private', $set['private']);
			unset($set['private']);
		}
		
		if ($set['parameters']) {;
			$parameters = $document->createElement('parameters');
			foreach ($set['parameters'] as $parameter_name => $parameter_set) {
				$parameter = $document->createElement('parameter');
				$parameter->setAttribute('name', $parameter_name);

				if ($parameter_set['type']) {
					$parameter->setAttribute('type', $parameter_set['type']);
				}
				unset($parameter_set['type']);
				
				if ($paramter_set['optional']) {
					$paramter->setAttribute('optional', $parameter_set['optional']);
				}
				unset($parameter_set['optional']);

				if ($paramter_set['repeating']) {
					$paramter->setAttribute('repeating', $parameter_set['repeating']);
				}
				unset($parameter_set['repeating']);

				if ($parameter_set['summary']) {
					$summary = $document->createElement('summary');
					$summary->appendChild($document->createTextNode($parameter_set['summary']));
					$parameter->appendChild($summary);
				}
				unset($parameter_set['summary']);
				
				if (!empty($parameter_set)) {
					print_r($parameter_set);
					die('parameter');
				}
			}
			
			unset($set['parameters']);
		}

		if ($set['summary']) {
			$summary = $document->createElement('summary');
			$summary->appendChild($document->createTextNode($set['summary']));
			$var->appendChild($summary);
		}
		unset($set['summary']);
		
		if ($set['description']) {
			$description = $document->createElement('description');
			$description->appendChild($document->createTextNode($set['description']));
			$var->appendChild($description);
		}
		unset($set['description']);

		if ($set['chains']) {
			$chains = $document->createElement('chains');
			foreach ($set['chains'] as $type => $chain_set) {
				foreach ($chain_set as $parent) {
					$chain = $document->createElement('chain');
					$chain->setAttribute('type', $type);
					$chain->setAttribute('parent', $parent);
					$chains->appendChild($chain);
				}
			}
			$var->appendChild($chains);
		}
		unset($set['chains']);

		$vars->appendChild($var);
		if (!empty($set)) {
			print_r($set);
			die('resource');
		}
	}
	$resource->appendChild($vars);

	$api->appendChild($resource);
}

$document->appendChild($api);
fwrite($xml_file, $document->saveXML());
fclose($xml_file);

?>