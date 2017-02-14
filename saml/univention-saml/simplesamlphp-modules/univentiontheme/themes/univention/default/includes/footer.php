<?php
if (!empty($this->data['htmlinject']['htmlContentPost'])) {
	foreach ($this->data['htmlinject']['htmlContentPost'] as $c) {
		echo $c;
	}
}
?>
</body>
</html>
