<?php

$this->includeAtTemplateBase('includes/header.php');
$this->data['header'] = $this->t('{core:frontpage:page_title}');

#SimpleSAML_Utilities::redirect('/univention/');

$this->includeAtTemplateBase('includes/footer.php');
