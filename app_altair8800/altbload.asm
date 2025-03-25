;
; BASIC Loaders
;
; FC00 = ROM Loader (176 000 oct)
;        Copies the BASIC image stored at E000 in ROM into RAM 
;        and starts execution
;
; FC20 = Cassette Loader 4K (176 040 oct)
;        Loads 4KB of casette data over SER2 port
;
; FC40 = Cassette Loader 8K (176 100 oct)
;        Loads 8KB of cassette data over SER2 port
;
; FCC0 = Common utilties
;

ram_addr		equ		00000h

rom_addr_4k		equ		0e000h
rom_size_4k		equ		01000h

mon_rom_addr	equ		0fd00h

	org 03ffeh
stack dw

	org 0fc00h
rom_load_4k:
	lxi h, (ram_addr + rom_size_4k) - 1
	lxi b, rom_size_4k
	lxi d, (rom_addr_4k + rom_size_4k) - 1
rom_4k_loop:
	ldax d
	mov m, a
	dcx h
	dcx d
	dcx b
	mov a, c
	ora b
	jnz rom_4k_loop
	inx h
	pchl
	
	org 0fc20h
cas_load_4k:
	call init_sio2
	lxi h, cas_4k_loop
	shld stack
	lxi h, 00faeh
	lxi sp, stack + 2
cas_4k_loop:
	dcx sp
	dcx sp
	in	06h
	rrc
	rnc
break:
	in	07h
	dcx h
	mov m,a
	mov a,l
	ora h
	rnz
	pchl
	
	org 0fc40h
cas_load_8k:
	call init_sio2
	lxi h, cas_8k_loop
	shld stack
	lxi	h, 01fc2h
cas_8k_loop:
	lxi sp, stack
	in 06h
	rrc
	rnc
	in 07h
	dcx h
	mov m,a
	mov a,l
	ora h
	rnz
	pchl
	

	org 0fcc0h

init_sio2:
	mvi		a,03h             ;RESET 2SIO BOARD
    out		06h
    mvi     a,021Q         ;INITIALIZE 2SIO BOARD
	out		06h
	ret
	