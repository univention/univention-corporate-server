
;nt!DebugPrint:
;mov     r9d,r8d
;mov     r8d,edx
;mov     dx,word ptr [rcx]
;mov     rcx,qword ptr [rcx+8]
;mov     eax,1
;int     2Dh

public Int2dHandlerOld

extrn Int2dHandlerProc: proc

.code
Int2dHandlerNew proc
  ;pushf
  push rax
  push rcx
  push rdx
  push r8
  push r9
  push r10
  push r11
  sub rsp, 56
  mov QWORD PTR [rsp + 32], r9
  mov r9, r8
  mov r8, rdx
  mov rdx, rcx
  mov rcx, rax
  call Int2dHandlerProc
  add rsp, 56
  pop r11
  pop r10
  pop r9
  pop r8
  pop rdx
  pop rcx
  pop rax
  ;popf
  jmp QWORD PTR [Int2dHandlerOld]
Int2dHandlerNew endp

.data
Int2dHandlerOld QWORD 1

END
