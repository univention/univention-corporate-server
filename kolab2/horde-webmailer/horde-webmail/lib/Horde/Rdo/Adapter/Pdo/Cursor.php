<?php
/**
 * @category Horde
 * @package Horde_Rdo
 */

/**
 * @category Horde
 * @package Horde_Rdo
 */
class Horde_Rdo_Adapter_Pdo_Cursor extends PDOStatement {

    /**
     */
    protected function __construct()
    {
        $this->setFetchMode(PDO::FETCH_ASSOC);
    }

}
