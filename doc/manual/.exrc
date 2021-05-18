" To make use this file an entry `set exrc` is needed in your vimrc file
" Within a paragraph `gqit` can be used for auto-aligning the [i]nner [t]ag,
" see `:help gq` in Vims help.
"
" * The alignment will break lines by looking for line-endings, e.g. one of .!?
" * if there is a version number in the text block it may be misaligned and
"   that must manually be fixed afterwards
" * The function will keep existing line breaks. If you want to reformat a
"   whole paragraph, it is possible by joining the lines together first,
"   e.g. use `V` and select lines, then `J` to join them, `V` again and `gq`

function! MyFormatExpr(start, end)
    silent execute a:start.','.a:end.'s/[.!?]\zs  */\r'.repeat('\t', indent(v:lnum) / &tabstop).'/g'
endfunction


autocmd FileType xml setlocal
\ formatexpr=MyFormatExpr(v:lnum,v:lnum+v:count-1)
\ formatoptions-=tc
\ smartindent
\ softtabstop=2
\ tabstop=2
\ shiftwidth=2
\ noexpandtab
