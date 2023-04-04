<?php

$this->data['header'] = $this->t('{core:frontpage:page_title}');
$this->includeAtTemplateBase('includes/header.php');

#SimpleSAML\Utilities::redirect('/univention/');
if ($this->data['isadmin']) {
	echo '<p class="float-r youareadmin">' . $this->t('{core:frontpage:loggedin_as_admin}') . '</p>';
} else {
	echo '<p class="float-r youareadmin"><a href="' . $this->data['loginurl'] . '">' . $this->t('{core:frontpage:login_as_admin}') . '</a></p>';
}
$this->includeAtTemplateBase('includes/footer.php');
