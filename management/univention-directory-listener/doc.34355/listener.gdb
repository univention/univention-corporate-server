define udl_print_cache
  set $cache = $arg0
  set $i = 0
  while ($i < $cache.attribute_count)
    printf "%s:\n", $cache.attributes[$i]->name
    set $j = 0
    while ($j < $cache.attributes[$i]->value_count)
      printf " %s\n", $cache.attributes[$i]->values[$j]
      set $j++
    end
    set $i++
  end
end
document udl_print_cache
Dump UDL cache entry at base §arg0
end

# Internal use within LDAP
handle SIGPIPE pass nostop norpint

# vim:set ft=gdb:
