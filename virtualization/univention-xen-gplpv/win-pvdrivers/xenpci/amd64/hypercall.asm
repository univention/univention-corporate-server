.data

; look up 'fastcall' in the ddk help for the calling convention for amd64

; called with
;  address of function in rcx
;  p1 in rdx
;  p2 in r8

; linux code is
; #define _hypercall2(type, name, a1, a2)
; ({
;   long __res, __ign1, __ign2;
;   asm volatile (
;     "call hypercall_page + ("STR(__HYPERVISOR_##name)" * 32)"
;     : "=a" (__res), "=D" (__ign1), "=S" (__ign2)
;     : "1" ((long)(a1)), "2" ((long)(a2))
;     : "memory" );
;   (type)__res;
; })

.code
_hypercall1 proc
    push rdi
    push rsi
    mov rdi, rdx
    mov rax, rcx
    call rax
    pop rsi
    pop rdi
    ret
_hypercall1 endp

_hypercall2 proc
    push rdi
    push rsi
    mov rdi, rdx
    mov rsi, r8
    mov rax, rcx
    call rax
    pop rsi
    pop rdi
    ret
_hypercall2 endp

_hypercall3 proc
    push rdi
    push rsi
    mov rdi, rdx
    mov rsi, r8
    mov rdx, r9
    mov rax, rcx
    call rax
    pop rsi
    pop rdi
    ret
_hypercall3 endp
END
