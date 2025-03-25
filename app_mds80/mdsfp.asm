
ram_addr	equ		0100h
rom_addr	equ		ram_go
rom_size	equ		ram_go_end - ram_go

rom_go		equ		0f800h

intr_mask	equ		0fch

	org 0000h

rom_start:
	di
	mvi a, 0ffh
	out intr_mask

	lxi h, ram_addr
	mvi b, rom_size
	lxi d, rom_addr
rom_loop:
	ldax d
	mov m, a
	inx h
	inx d
	dcr b
	jnz rom_loop
	jmp ram_addr
	
ram_go:
	nop
	jmp  rom_go
	
ram_go_end:

	
	