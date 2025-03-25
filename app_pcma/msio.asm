;-----------------------------------------------------------------------------
; DOS 1.0 IBMBIO.COM (disk image MD5 73c919cecadf002a7124b7e8bfe3b5ba)
;   http://www.pagetable.com/
;-----------------------------------------------------------------------------


SECTOR_SIZE     equ     0200H          ; size of a sector
DOS_SIZE        equ     10000           ; max size of IBMDOS.COM in bytes
PAUSE_KEY       equ     7200H          ; scancode + charcode of PAUSE key
KEYBUF_NEXT     equ     041AH          ; next character in keyboard buffer
KEYBUF_FREE     equ     041CH          ; next free slot in keyboard buffer
KEYBUF          equ     041EH          ; keyboard buffer data
LOGICAL_DRIVE   equ     0504H          ; linear address of logical drive byte
SEG_DOS         equ     0D0H            ; segment in which DOS will run
SEG_BIO         equ     070H            ; segment in which BIO is running

;-----------------------------------------------------------------------------

                org 0000H              ; segment 0x0070
				ASSUME CS:CODE, DS:CODE, SS:CODE, ES:CODE

                jmp     INIT            ; 0x0070:0x0000 entry point
                jmp     STATUS          ; 0x0070:0x0003 check for keypress
                jmp     INP             ; 0x0070:0x0006 get key from keyboard
                jmp     OUTP            ; 0x0070:0x0009 send character to screen
                jmp     PRINT           ; 0x0070:0x000C send character to printer
                jmp     AUXIN           ; 0x0070:0x000F get character from serial
                jmp     AUXOUT          ; 0x0070:0x0012 send character to serial
                jmp     READ            ; 0x0070:0x0015 read sector(s) from disk (INT 0x25)
                jmp     WRITE           ; 0x0070:0x0018 write sector(s) to disk  (INT 0x26)
                jmp     DSKCHG          ; 0x0070:0x001B check for disk change
				jmp     SETDATE     	; 0x0070:0x001E Set date
				jmp     SETTIME     	; 0x0070:0x0021 Set time
				jmp     GETTIME     	; 0x0070:0x0024 Get time and date
				jmp		FLUSH       	; 0x0070:0x0027 Clear console input buffer
				jmp		MAPDEV      	; 0x0070:0x002A Dynamic disk table mapper
	

;-----------------------------------------------------------------------------

                dw SEG_DOS              ; ???
                dw TXT_VERSION          ; ???
TXT_VERSION     db 'BIOS Version 1.00'
                db ' '+80H
                db '22-Jul-81',0
	
ERR_PAPER       db 13,10,'Out of pape','r'+80H,13,10,0
ERR_PRINTER     db 13,10,'Printer faul','t'+80H,13,10,0
ERR_AUX         db 13,10,'Aux I/O erro','r'+80H,13,10,0
				
;-----------------------------------------------------------------------------
; Interrupt 0x1B handler: Control+Break handler
;-----------------------------------------------------------------------------
int_1B:         mov     byte ptr cs:[next_char], 3; put code for Ctrl+C
                iret                    ; into keyboard queue


;-----------------------------------------------------------------------------
; Interrupt 0x00 handler: Division by Zero
;-----------------------------------------------------------------------------
int_00:         sti
                push    ax
                push    dx
                mov     dx, ERR_DIVIDE
                call    print_string
                pop     dx
                pop     ax
                int     23H            ; exit program through Ctrl+C path
				
;-----------------------------------------------------------------------------
; Interrupt 0x00 handler: Single Step
; Interrupt 0x03 handler: Breakpoint
; Interrupt 0x04 handler: Overflow
;-----------------------------------------------------------------------------

iret1:          iret                    ; empty interrupt handler

ERR_DIVIDE      db 13,10,'Divide overflo','w'+80H,13,10,0

;-----------------------------------------------------------------------------
; print zero-terminated string at DS:DX
;-----------------------------------------------------------------------------
print_string:   xchg    si, dx
prints1:        lodsb
                and     al, 7FH        ; clear bit 7 (XXX why?)
                jz      prints2         ; zero-terminated
                callf   SEG_BIO:OUTP    ; print character
                jmp     prints1         ; loop
prints2:        xchg    si, dx
                ret
				
;-----------------------------------------------------------------------------
				
conv_status     db 80H,40H,20H,10H,9,8,4,3,2; BIOS error codes
                db 1,2,6,0CH,4,0CH,4,8,0,0CH,0CH; IBMBIO error codes

;-----------------------------------------------------------------------------
; read/write an arbirtary number of sectors
;-----------------------------------------------------------------------------
rw_tracks       or      al, al
                jz      ret2            ; nothing to read
                mov     ah, 9
                sub     ah, cl
                cmp     ah, al          ; more sectors than left in track?
                jbe     skip3           ; no
                mov     ah, al          ; otherwise, read up to end of track
skip3           push    ax
                mov     al, ah
                call    rw_sectors ; reads/writes up to 8 sectors
                pop     ax
                sub     al, ah          ; decrease sectors to read
                shl     ah, 1
                add     bh, ah          ; advance pointer by sectors * 0x0200
                jmp     rw_tracks       ; continue
				
;-----------------------------------------------------------------------------

int_13_err      xchg    ax, di
                mov     ah, 0
                int     13H            ; disk reset
                dec     si
                jz      translate       ; retries exhausted
                mov     ax, di
                cmp     ah, 80H        ; in the "timeout (not ready)" case,
                jz      translate       ; we don't retry (this would take forever)
                pop     ax
                jmp     retry
translate       push    cs
                pop     es
                mov     ax, di
                mov     al, ah          ; status
                mov     cx, 0AH
                mov     di, conv_status
                repne scasb
                mov     al, [di+9]
                mov     cx, [num_sectors]
                mov     sp, [temp_sp]   ; clean up stack
                pop     ds
                pop     es
                stc                     ; error
                retf

rw_one_sector   mov     al, 1


; reads/writes one or more sectors that are on the same track
rw_sectors      mov     si, 5           ; number of retries
                mov     ah, [int_13_cmd]
retry           push    ax
                int     13H            ; perform the read/write
                jc      int_13_err
                pop     ax
                sub     byte ptr [num_sectors], al
                add     cl, al          ; calculate next sector number
                cmp     cl, 8           ; exceeds track?
                jbe     ret2            ; no
                inc     ch              ; next track
                mov     cl, 1           ; sector 1
ret2            ret

;-----------------------------------------------------------------------------
; send character to printer
;  AL = character
;  all registers preserved
;-----------------------------------------------------------------------------
PRINT           push    ax
                push    dx
                mov     byte ptr cs:[printer_retry], 0
printer_again   mov     dx, 0           ; printer port #0
                mov     ah, 0
                int     17h            ; send character to printer
                mov     dx, ERR_PAPER
                test    ah, 20h
                jnz     printer_error   ; out of paper error
                mov     dx, ERR_PRINTER
                test    ah, 5
                jz      pop_dx_ax_retf  ; no timeout error, return
                xor     byte ptr cs:[printer_retry], 1
                jnz     printer_again   ; on a timeout, try twice
printer_error   call    print_string
pop_dx_ax_retf  pop     dx
                pop     ax
                retf
				
;-----------------------------------------------------------------------------
; get character from serial
;  AL = character
;  all other registers preserved
;-----------------------------------------------------------------------------
AUXIN           push    dx
                push    ax
                mov     dx, 0           ; serial port #0
                mov     ah, 2
                int     14h            ; get character from serial port
                mov     dx, ERR_AUX
                test    ah, 0Eh        ; framing, parity or overrun?
                jz      aux_noerr       ; no error
                call    print_string
aux_noerr       pop     dx
                mov     ah, dh          ; restore AH
                pop     dx
                retf
				
;-----------------------------------------------------------------------------
; send character to serial
;  AL = character
;  all registers preserved
;-----------------------------------------------------------------------------
AUXOUT          push    ax
                push    dx
                mov     ah, 1
                mov     dx, 0
                int     14h            ; send character to serial port
                test    ah, 80h        ; timeout error?
                jz      pop_dx_ax_retf  ; no all fine
                mov     dx, ERR_AUX
                jmp     printer_error
	
;-----------------------------------------------------------------------------
; emulated functions
;-----------------------------------------------------------------------------
	
GETTIME:
				mov		ax, cs:[time_ax]
				mov		cx, cs:[time_cx]
				mov		dx, cs:[time_dx]
				retf
				
SETDATE:
				mov		cs:[time_ax], ax
				retf
				
SETTIME:
				mov		cs:[time_cx], cx
				mov		cs:[time_dx], dx			
FLUSH:
MAPDEV:
				retf

;-----------------------------------------------------------------------------
; check for keypress
;  AL = character
;  Z  = set if no character
;  all other registers preserved
;-----------------------------------------------------------------------------
STATUS          mov     al, cs:[next_char]; check for waiting character
                or      al, al
                jnz     char_avail      ; yes, return it
                push    dx
                xchg    ax, dx
                mov     ah, 1
                int     16H            ; otherwise get key (don't clear)
                jz      status_exit     ; no key
                cmp     ax, PAUSE_KEY   ; PAUSE key?
                jnz     status_exit
                mov     al, 10H        ; convert into Ctrl+P
                or      al, al


status_exit     mov     ah, dh          ; restore original AH
                pop     dx
char_avail      retf

;-----------------------------------------------------------------------------
; get key from keyboard
;  AL = character
;  all other registers preserved
;-----------------------------------------------------------------------------
again           xchg    ax, dx
                pop     dx
INP             mov     al, 0
                xchg    al, cs:[next_char]; get and clear waiting character
                or      al, al
                jnz     inp_exit        ; there is no character waiting
                push    dx
                xchg    ax, dx
                mov     ah, 0
                int     16h            ; then read character from keyboard
                or      ax, ax
                jz      again
                cmp     ax, PAUSE_KEY
                jnz     not_pause2
                mov     al, 10h        ; Ctrl+P
not_pause2      cmp     al, 0
                jnz     skip1           ; key with ASCII representation
                mov     cs:[next_char], ah; return scancode next time
skip1           mov     ah, dh          ; restore AH
                pop     dx
inp_exit        retf

;-----------------------------------------------------------------------------
; send character to screen
;  AL = character
;  all registers preserved
;-----------------------------------------------------------------------------
OUTP            push    bp
                push    ax
                push    bx
                push    si
                push    di
                mov     ah, 0EH
                mov     bx, 7
                int     10H            ; print character
                pop     di
                pop     si
                pop     bx
                pop     ax
                pop     bp
                retf
				
;-----------------------------------------------------------------------------
; READ  - read sector(s) from disk
; WRITE - write sector(s) to disk
;  al     drive number (0-3)
;  ds:bx  buffer
;  cx     count
;  dx     logical block number
;-----------------------------------------------------------------------------
driveb			jmp read_write

READ            mov     ah, 2           ; BIOS code "read"
				cmp		al, 0
				jne		driveb
                jmp     read_write
WRITE           mov     ah, 3           ; BIOS code "write"
read_write      push    es
                push    ds
                push    ds
                pop     es              ; ES := DS
                push    cs
                pop     ds              ; DS := CS
                mov     [temp_sp], sp   ; save sp for function abort
                mov     [int_13_cmd], ah; save whether it was read or write

				xchg    ax, dx
                mov     dh, 8           ; convert LBA to CHS
                div     dh              ; al = track (starts at 0)
                inc     ah              ; ah = sector (starts at 1)
                xchg    al, ah          ; track and sector
                xchg    ax, cx          ; cx = t/s, ax = count
                mov     [num_sectors], ax; count
                mov     dh, 0
; work around DMA hardware bug in case I/O spans a 64 KB boundary
; by using a temporary buffer
                mov     di, es          ; destination segment
                shl     di, 1
                shl     di, 1           ; make es:bx a linear address
                shl     di, 1           ; (discard upper bits)
                shl     di, 1
                add     di, bx
                add     di, SECTOR_SIZE-1; last byte of sector (linear)
                jc      across_64k      ; sector overflows it
                xchg    bx, di          ; bx = last byte, di = buffer
                shr     bh, 1           ; sector index in memory
                mov     ah, 80H        ; 0x80 sectors fit into 64 KB
                sub     ah, bh          ; sectors until 64 KB boundary
                mov     bx, di          ; bx = buffer
                cmp     ah, al          ; compare to number of sectors
                jbe     skip2           ; they fit into 64 KB, cap num
                mov     ah, al          ; don't cap number of sectors
skip2           push    ax
                mov     al, ah          ; al = count
                call    rw_tracks
                pop     ax
                sub     al, ah          ; requested = done?
                jz      rw_done         ; yes, exit
across_64k      dec     al              ; one sector less
                push    ax
                cld
                push    bx
                push    es              ; save data pointer
                cmp     byte ptr [int_13_cmd], 2
                jz      across_64k_read ; write case follows
                mov     si, bx
                push    cx
                mov     cx, SECTOR_SIZE/2; copy first sector
                push    es
                pop     ds
                push    cs
                pop     es
                mov     di, temp_sector
                mov     bx, di
                rep movsw               ; copy into IBMBIO local data
                pop     cx
                push    cs
                pop     ds
                call    rw_one_sector   ; write last sector
                pop     es
                pop     bx
                jmp     across_64k_end
across_64k_read mov     bx, temp_sector
                push    cs
                pop     es
                call    rw_one_sector   ; read last sector into temp buffer
                mov     si, bx
                pop     es
                pop     bx
                mov     di, bx
                push    cx
                mov     cx, SECTOR_SIZE/2
                rep movsw               ; copy out
                pop     cx
across_64k_end  add     bh, 2           ; continue 0x0200 after that
                pop     ax
                call    rw_tracks
rw_done         pop     ds
                pop     es
                clc                     ; success
                retf

;-----------------------------------------------------------------------------
; check for disk change
;  AH = flag (1=changed)
;-----------------------------------------------------------------------------
DSKCHG          mov     ah, 0           ; the IBM PC can't detect disk change
				retf			

;-----------------------------------------------------------------------------

; this is passed to MSDOS.SYS
num_floppies    db 4                    ; 
floppy_list     db 0
				dw parameters
			    db 1
                dw parameters
				db 2
                dw parameters
				db 3
                dw parameters
				
parameters      dw SECTOR_SIZE			; 512 bytes
                db 1                    ; (sectors/cluster-1) will be decremented by 1, then used
                dw 1					; number of reserved clusters
                db 2					; number of FATs
                dw 64					; number of root dir entries
                dw 320                  ; number of total sectors
				
;-----------------------------------------------------------------------------

int_13_cmd      db 2     
temp_sp         dw 0     
num_sectors     dw 0
printer_retry   db 0                    ; count for printer retries
next_char       db 0                    ; extra character in keyboard queue

time_ax			dw 0					; emulate clock
time_cx			dw 0
time_dx			dw 0

temp_sector:
;-----------------------------------------------------------------------------
; entry point from boot sector
;  assumes DX = 0
;-----------------------------------------------------------------------------

INIT:           cli
                mov     ax, cs
                mov     ds, ax
				xor		ax, ax
                mov     ss, ax
                mov     sp, 700H; set stack used during init; overwrite end of boot loader
                sti
                int     13H            ; reset disk 0 (AX,DX = 0)
				mov     al, 0A3H        ; 2400 8N1
                int     14H           ; initialize serial port
                mov     ah, 1
                int     17H            ; initialize printer
				
				int		12H				; get memory size in AX (unit 1KB blocks)
				mov		cx, 6
				shl		ax, cl			; convert to 16 byte pages
				mov		dx, ax			; pass value to DOS init in DX
				
                int     11H            ; get system info
				and     ax, 0C0H        ; number of floppies in bits 6 and 7
                mov     cx, 6
                shr     ax, cl          ; (floppies-1)
                add     ax, 1           ; floppies
                and     ax, 3           ; will become 0 for 4 floppies
                mov     [num_floppies], al
four_floppies:  push    ds
                mov     ax, 0
                mov     ds, ax          ; DS := 0x0000
                mov     ax, SEG_BIO     ; target segment for interrupt vectors
                mov     [6EH], ax      ; set INT 1Bh segment
                mov     word ptr [6CH], int_1B; set INT 1Bh offset
                mov     word ptr [00H], int_00; set INT 00h offset
                mov     [02H], ax      ; set INT 00h segment
                mov     bx, iret1       ; set INT 00h offset
                mov     [04H], bx      ; set INT 01h offset (empty)
                mov     [06H], ax      ; set INT 01h segment
                mov     [0CH], bx      ; set INT 03h offset (empty)
                mov     [0EH], ax      ; set INT 03h segment
                mov     [10H], bx      ; set INT 04h offset (empty)
                mov     [12H], ax      ; set INT 04h segment
                mov     ax, 50H
                mov     ds, ax          ; DS := 0x0050
                mov     word ptr [00H], 0   ; clear 0x0500 in DOS Comm. Area (???)
                pop     ds
                mov     si, num_floppies; pass in pointer to structure
                callf    SEG_DOS:0       ; init DOS (returns DS = memory for COMMAND.COM)
				
                sti
                mov     dx, 0100H      ; 0x0100 in COMMAND.COM segment
                mov     ah, 1AH
                int     21H            ; set disk transfer area address
				
                mov     cx, [06H]      ; remaining memory size
                sub     cx, 0100H      ; - Program Segment Prefix = bytes to read
                mov     bx, ds
                mov     ax, cs
                mov     ds, ax
                mov     dx, FCB_command_com; File Control Block
                mov     ah, 0FH
                int     21H            ; DOS: open COMMAND.COM
                or      al, al
                jnz     error_command   ; error opening COMMAND.COM
                mov     word ptr [FCB_command_com+21H], 0; random record field
                mov     word ptr [FCB_command_com+23H], 0;  := 0x00000000
                mov     word ptr [FCB_command_com+0EH], 1; record length = 1 byte
                mov     ah, 27H
                int     21H            ; DOS: read
                jcxz    error_command   ; read 0 bytes -> error
                cmp     al, 1
                jnz     error_command   ; end of file not reached -> error
                mov     ds, bx
                mov     es, bx          ; DS := ES := SS := COMMAND.COM
                mov     ss, bx
                mov     sp, 40H        ; 64 byte stack in PSP (XXX interrupts are on!)
                xor     ax, ax
                push    ax              ; push return address 0x0000 (int 0x20)
                mov     dx, [80H]      ; get new DTA address
                mov     ah, 1AH
                int     21H            ; set disk transfer area address
                push    bx              ; segment of COMMAND.COM
                mov     ax, 0100H      ; offset of COMMAND.COM entry
                push    ax
                retf                    ; run COMMAND.COM
				
error_command:  mov     dx, ERR_COMMANDCOM ; "rnBad or missing Command Interprete"
                call    print_string
halt:           hlt

FCB_command_com db 1, 'COMMAND CO','M'+80H
                db 25 dup(0)
		
ERR_COMMANDCOM  db 13,10,'Bad or missing Command Interprete','r'+80H,13,10,0

	