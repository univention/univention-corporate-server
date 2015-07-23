<?php 

$this->includeAtTemplateBase('includes/header.php'); 

$this->data['header'] = $this->t('{core:frontpage:page_title}');

SimpleSAML_Utilities::redirect('/ucs-overview');
		
$this->includeAtTemplateBase('includes/footer.php'); 
?>
