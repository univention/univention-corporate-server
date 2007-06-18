<?PHP
/**
 * This example shows how to create an RDF document
 * with a few lines of code.
 * This can also be done with mode => simplexml
 *
 * @author Stephan Schmidt <schst@php.net>
 * @see    serializeIndexedArray.php
 */

    require_once 'XML/Serializer.php';

    $options = array(
                        "indent"         => "    ",
                        "linebreak"      => "\n",
                        "typeHints"      => false,
                        "addDecl"        => true,
                        "encoding"       => "UTF-8",
						"rootName"       => "rdf:RDF",
                        "rootAttributes" => array("version" => "0.91"),
						"defaultTagName" => "item"
                    );
    
    $serializer = new XML_Serializer($options);

    
    $rdf    =   array(
						"channel" => array(
											"title" => "Example RDF channel",
											"link"  => "http://www.php-tools.de",
											"image"	=>	array(
																"title"	=> "Example image",
																"url"	=>	"http://www.php-tools.de/image.gif",
																"link"	=>	"http://www.php-tools.de"
															),
											array(
												"title"	=> "Example item",
												"link"	=> "http://example.com"
											),
											array(
												"title"	=> "Another item",
												"link"	=> "http://example.com"
											),
											array(
												"title"	=> "I think you get it...",
												"link"	=> "http://example.com"
											)
										)
                    );
    
    $result = $serializer->serialize($rdf);
    
    if( $result === true ) {
        echo    "<pre>";
        echo    htmlentities($serializer->getSerializedData());
        echo    "</pre>";
    }
?>