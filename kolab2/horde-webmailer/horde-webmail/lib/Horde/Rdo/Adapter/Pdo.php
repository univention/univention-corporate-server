<?php
/**
 * @category Horde
 * @package Horde_Rdo
 */

/**
 * PDO Horde_Rdo_Adapter generic implementation. Provides most
 * functionality but must be extended with a concrete implementation
 * to fill in database-specific details.
 *
 * @category Horde
 * @package Horde_Rdo
 */
abstract class Horde_Rdo_Adapter_Pdo extends Horde_Rdo_Adapter {

    /**
     * PDO database connection object.
     *
     * @var PDO
     */
    protected $_db = null;

    /**
     * Free any resources that are open.
     */
    public function __destruct()
    {
        if ($this->_db) {
            $this->_db = null;
        }
    }

    /**
     * Use for SELECT and anything that returns rows.
     *
     * @param string $sql A full SQL query to run.
     * @param array $bindParams Any parameters to bind to the query.
     *
     * @return PDOStatement Result set.
     */
    public function select($sql, $bindParams = array())
    {
        $statement = $this->_db->prepare($sql);
        if (!$statement) {
            throw new Horde_Rdo_Exception(implode(', ', $this->_db->errorInfo()) . ', ' . $sql);
        }

        try {
            $statement->execute($bindParams);
        } catch (Exception $e) {
            throw new Horde_Rdo_Exception('Unable to excecute query: ' . $e->getMessage());
        }

        return $statement;
    }

    /**
     * Return a single value from a query. Useful for quickly getting
     * a value such as with a COUNT(*) query.
     *
     * @param string $sql The SQL to get one result from.
     *
     * @return mixed The first value of the first row matched by $sql.
     */
    public function selectOne($sql, $bindParams = array())
    {
        $statement = $this->_db->prepare($sql);
        if (!$statement->execute($bindParams)) {
            throw new Horde_Rdo_Exception(implode(', ', $statement->errorInfo()));
        }
        return $statement->fetchColumn();
    }

    /**
     * Return a single column from a query.
     *
     * @param string $sql The SQL to get one column from.
     *
     * @return mixed The first column of all rows matched by $sql.
     */
    public function selectCol($sql, $bindParams = array())
    {
        $statement = $this->_db->prepare($sql);
        if (!$statement->execute($bindParams)) {
            throw new Horde_Rdo_Exception(implode(', ', $statement->errorInfo()));
        }
        $column = array();
        while (($value = $statement->fetchColumn()) !== false) {
            $column[] = $value;
        }
        return $column;
    }

    /**
     * Use for INSERT, UPDATE, DELETE, and other queries that don't
     * return rows. Returns number of affected rows.
     *
     * @param string $sql The query to run.
     * @param array $bindParams Any parameters to bind to the query.
     *
     * @return integer The number of rows affected by $sql.
     */
    public function execute($sql, $bindParams = array())
    {
        $statement = $this->_db->prepare($sql);
        if (!$statement->execute($bindParams)) {
            throw new Horde_Rdo_Exception(implode(', ', $statement->errorInfo()));
        }
        return $statement->rowCount();
    }

    /**
     */
    public function beginTransaction()
    {
        return $this->_db->beginTransaction();
    }

    /**
     */
    public function commit()
    {
        return $this->_db->commit();
    }

    /**
     */
    public function rollBack()
    {
        return $this->_db->rollBack();
    }

    /**
     * Build a connection string and connect to the database server.
     */
    protected function _connect()
    {
        $dsn = $this->getOption('dsn');
        if (!$dsn) {
            $dsn = 'dbname=' . $this->getOption('database');
            if ($hs = $this->getOption('hostspec')) {
                $dsn .= ';host=' . $hs;
            }
        }

        $pdo_driver = $this->getOption('phptype');
        switch ($pdo_driver) {
        case 'mysqli':
            $pdo_driver = 'mysql';
            break;
        }

        try {
            $this->_db = new PDO($pdo_driver . ':' . $dsn,
                                 $this->getOption('username'),
                                 $this->getOption('password'));
            $this->_db->setAttribute(PDO::ATTR_STATEMENT_CLASS, array('Horde_Rdo_Adapter_Pdo_Cursor', array()));
            $this->_db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        } catch (Exception $e) {
            // Catch and re-throw this exception as a stack trace may
            // contain the database password.
            throw new Horde_Rdo_Exception('Connect failed: ' . $e->getMessage());
        }
    }

    /**
     * @param string $sequence The name of the sequence to get the
     * latest value in.
     *
     * @return integer The last auto-generated row id for $sequence
     */
    protected function _lastInsertId($sequence)
    {
        return $this->_db->lastInsertId($sequence);
    }

}
