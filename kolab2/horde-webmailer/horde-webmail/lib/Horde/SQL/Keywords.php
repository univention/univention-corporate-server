<?php
/**
 * This class provides a parser which can construct an SQL WHERE
 * clause from a Google-like search expression.
 *
 * $Horde: framework/SQL/SQL/Keywords.php,v 1.2.10.9 2009-01-06 15:23:33 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * The expression recognizes boolean "AND", "OR", and "NOT" (providing
 * no operator between keywords implies "AND"), like so:
 *
 *   cat and dog
 *   cat or dog
 *   cat and not dog
 *
 * If no operator appears between keywords or quoted strings, "AND" is
 * assumed.  A comma can be used instead of "OR":
 *
 *   cat dog
 *   cat, dog
 *   cat not dog
 *
 * The parser recognizes parentheses, so complex expressions can be
 * created:
 *
 *   cat and not (dog or puppy)
 *
 * Quoted strings are also recognized, and are taken as literal
 * keywords:
 *
 *   "cat and dog"
 *
 * Parsing is designed to be as fuzzy as possible, so it shouldn't
 * error unless people search for "AND", "OR", or "NOT" without
 * quoting it or use unbalanced parentheses.
 *
 * @author  Jason M. Felice <jason.m.felice@gmail.com>
 * @since   Horde 3.0
 * @package Horde_SQL
 */
class Horde_SQL_Keywords {

    /**
     * Parse a keyword expression.
     *
     * @param string $column        This is the SQL field name the resulting
     *                              expression should test against.
     * @param string $expr          This is the keyword expression we want to
     *                              parse.
     * @return mixed the query expression or a PEAR_Error on failure.
     */
    function parse($column, $expr)
    {
        /* First pass - scan the string for tokens.  Bare words are
         * tokens, or the user can quote strings to have embedded
         * spaces, keywords, or parentheses.  Parentheses can be used
         * for grouping boolean operators, and the boolean operators
         * AND, OR, and NOT are all recognized.
         *
         * The tokens are returned in the $tokens array -- an array of
         * strings.  Each string in the array starts with either a `!'
         * or a `='.  `=' is a bare word or quoted string we are
         * searching for, and `!' indicates a boolean operator or
         * parenthesis.  A token that starts with a '.'  indicates a
         * PostgreSQL word boundary search. */
        $tokens = array();
        while (!empty($expr)) {
            $expr = preg_replace("/^\s+/", "", $expr);
            if (empty($expr)) {
                break;
            }
            if (substr($expr,0,1) == '(') {
                $expr = substr($expr, 1);
                $token = '!(';
            } elseif (substr($expr, 0, 1) == ')') {
                $expr = substr($expr, 1);
                $token = '!)';
            } elseif (substr($expr, 0, 1) == ',') {
                $expr = substr($expr, 1);
                $token = '!OR';
            } elseif (preg_match("/^(AND|OR|NOT)([^a-z].*)?$/i", $expr,
                                 $matches)) {
                $token = '!' . strtoupper($matches[1]);
                $expr = substr($expr, strlen($matches[1]));
            } elseif (preg_match("/^\"(([^\"]|\\[0-7]+|\\[Xx][0-9a-fA-F]+|\\[^Xx0-7])*)\"/",
                                 $expr, $matches)) {
                $token = '=' . stripcslashes($matches[1]);
                $expr = substr($expr, strlen($matches[0]));
            } elseif (preg_match("/^[^\\s\\(\\),]+/", $expr, $matches)) {
                $token = '=' . $matches[0];
                $expr = substr($expr,strlen($token)-1);
            } else {
                return PEAR::raiseError('Syntax error in search terms');
            }
            if ($token == '!AND') {
                /* !AND is implied by concatenation. */
                continue;
            }
            $tokens[] = $token;
        }

        /* Call the expression parser. */
        return Horde_SQL_Keywords::_parseKeywords1($column, $tokens);
    }

    function _parseKeywords1($column, &$tokens)
    {
        if (count($tokens) == 0) {
            return PEAR::raiseError('Empty search terms');
        }
        $lhs = Horde_SQL_Keywords::_parseKeywords2($column, $tokens);
        if (is_a($lhs, 'PEAR_Error')) {
            return $lhs;
        }
        if (count($tokens) == 0 || $tokens[0] != '!OR') {
            return $lhs;
        }
        array_shift($tokens);
        $rhs = Horde_SQL_Keywords::_parseKeywords1($column, $tokens);
        if (is_a($rhs, 'PEAR_Error')) {
            return $rhs;
        }
        return "($lhs OR $rhs)";
    }

    function _parseKeywords2($column, &$tokens)
    {
        $lhs = Horde_SQL_Keywords::_parseKeywords3($column, $tokens);
        if (is_a($lhs, 'PEAR_Error')) {
            return $lhs;
        }
        if (sizeof($tokens) == 0 || $tokens[0] == '!)' || $tokens[0] == '!OR') {
            return $lhs;
        }
        $rhs = Horde_SQL_Keywords::_parseKeywords2($column, $tokens);
        if (is_a($rhs, 'PEAR_Error')) {
            return $rhs;
        }
        return "($lhs AND $rhs)";
    }

    function _parseKeywords3($column, &$tokens)
    {
        if ($tokens[0] == '!NOT') {
            array_shift($tokens);
            $lhs = Horde_SQL_Keywords::_parseKeywords4($column, $tokens);
            if (is_a($lhs, 'PEAR_Error')) {
                return $lhs;
            }
            return "(NOT $lhs)";
        }
        return Horde_SQL_Keywords::_parseKeywords4($column, $tokens);
    }

    function _parseKeywords4($column, &$tokens)
    {
        if ($tokens[0] == '!(') {
            array_shift($tokens);
            $lhs = Horde_SQL_Keywords::_parseKeywords1($column, $tokens);
            if (is_a($lhs, 'PEAR_Error')) {
                return $lhs;
            }
            if (sizeof($tokens) == 0 || $tokens[0] != '!)') {
                return PEAR::raiseError('Expected ")"');
            }
            array_shift($tokens);
            return $lhs;
        }

        if (substr($tokens[0], 0, 1) != '=' &&
            substr($tokens[0], 0, 2) != '=.') {
            return PEAR::raiseError('Expected bare word or quoted search term');
        }

        $val = strtolower(substr(array_shift($tokens), 1));
        $val = addslashes(ereg_replace("([\\%])", "\\\\1", $val));

        return "(LOWER($column) LIKE '%$val%')";
    }

}
