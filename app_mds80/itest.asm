;
; Timer/interrupt test
;


vec6		equ		0030h
reboot		equ		0f800h

timer_0		equ		0e0h
timer_1		equ		0e1h
timer_2		equ		0e2h
timer_cntl	equ		0e3h

int_cntl	equ		0feh
int_mask	equ		0fch
int_rvrt	equ		0fdh


	org 0100h
	
start:
	di
	mvi a, 12h
	out int_rvrt
	mvi a, 0ffh
	out int_mask
	
	lxi	h, vec6
	mvi m, 0c3h
	inx h
	lxi b, intr_handler
	mov m, c
	inx h
	mov m, b
	
	mvi a, 0bfh
	out int_mask
	xra a
	out int_cntl
	ei
	
	mvi a, 34h
	out	timer_cntl
	
	xra a
	out timer_0
	mvi a, 10h
	out timer_0
	nop
rtimer:	
	xra a
	out timer_cntl
	nop
	in	timer_0
	nop
	in  timer_0
	lhld intr_count
	mov a,h
	cpi 1
	jz mon_ret
	jmp rtimer
	
mon_ret:
	mvi a, 0ffh
	out int_mask
	xra a
	lxi h, vec6
	mov m,a
	inx h
	mov m,a
	inx h
	mov m,a
	rst 1

	
intr_handler:
	push h
	push psw
	lhld intr_count
	inx h
	shld intr_count
	mvi a, 06h
	out int_rvrt
	pop psw
	pop h
	ei
	ret
	
intr_count dw 0