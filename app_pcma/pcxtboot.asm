
       ;INCLUDE bioss.htm ; bioss.htm defines layout of structures used by boot code.

OEM_ID  EQU		0DAH	

	ORG 7C00H		; requires target machine with at least 32 KB RAM
	SEGMENT CODE
ImageBase: 			  ; Boot sector is assembled at this fixed origin %Base alias %^ImageBase.
Entry: JMP Start     ; Skip structures allocated in the beginning of boot-sector.
       NOP
       DB OEM_ID

; Base BPB_FAT16. Size=0x19=25.
BytesPerSector      DW  0200H ; Size of HW sector, usualy 512.
SectorsPerCluster   DB  01H   ; Valid values 1,2,4,8,16,32,64,128.
ReservedSectors     DW  0001H ; NrOfSectors preceding FAT.
NumberOfFats        DB  02H   ;
RootEntries         DW  0040H ; Max number of YWORD entries in the root dir.
SmallSectors        DW  0140H ; 320 x 512 = 163840 bytes (160 KB). See also .LargeSectors.
MediaDescriptor     DB  0F0H  ; 0xF0 floppy disk, 0xF8 hard disk.
SectorsPerFat       DW  0001H ;
SectorsPerTrack     DW  0008H ;
NumberOfHeads       DW  0001H ;
HiddenSectors       DD  00000000H
LargeSectors        DD  00000000H
; Extended BPB_FAT16. Size=0x1A=26.
PhysicalDriveNumber DB  00H   ; 0x00 floppy disk, 0x80 hard disk.
Reserved            DB  00H   ;
ExtBootSignature    DB  29H   ; Or 0x28.
VolumeSerialNumber  DD  563D43D2H ; Randomly generated number.
VolumeLabel         DB  "NO NAME    " ; Space-padded to size=11.
FileSystemType      DB  "FAT12   "    ; Space-padded to size=8.

Dpt   	DB 11 DUP(0) ; Diskette Parameter Table (11 bytes) will be copied here, overwriting the Start: code.

; Immediately below the copied Dpt follow four memory variables LBA* for calculation of disk geometry
; These overwrite the code at Start:
;
LBAbase		EQU	 7C50H
LBAdata  	EQU  LBAbase + 0000H 	; DWORD with the number of 1st sector with data, immediately following the root-directory.
LBAcylinder EQU  LBAbase + 0004H    ; WORD with LBA translated for INT 0x13.
LBAroot     EQU  LBAbase + 0008H    ; DWORD with the number of 1st sector in root-directory entry.
LBAtrack    EQU  LBAbase + 0010H    ; BYTE with LBA translated for INT 0x13..
    
bLastTrack 	EQU 4
bHdSettle 	EQU	9

wClstrNo    EQU 01AH

IOSYS_SIZE	EQU	3					; number of sectors for IO.SYS file
DOS_SIZE	EQU	IOSYS_SIZE + 12		; total number of sectors for IO.SYS and MSDOS.SYS

	ASSUME CS:CODE, DS:CODE, SS:CODE, ES:CODE

	   ; Entry point jumps to this fixed label Start: at address %Boot+0x3E, where the boot code actually starts.
Start: CLI                ; Disable HW interrupts, as the stack is not settled yet.
       XOR AX,AX
       MOV SS,AX
       MOV SP, ImageBase ; Set machine stack just below the boot sector.
       PUSH SS
       POP ES
       MOV BX,0074H      ; Address of default DPT prepared by BIOS.
       LDS SI,SS:[BX]
       PUSH DS
	   PUSH SI
	   PUSH SS
	   PUSH BX
         MOV DI, Dpt
         MOV CX, 11
         CLD
         REP MOVSB        ; Copy DPT from BIOS memory to the Dpt:.
         PUSH ES
         POP DS           ; DS=ES=SS=0.
         MOV BYTE PTR [DI+bHdSettle],15
         MOV CX,[SectorsPerTrack]
         MOV [DI+bLastTrack],CL
         ; Modify the vector address of local DPT copy (Dpt) in BIOS memory.
         ;MOV WORD PTR [BX+2],AX ; PARA# Dpt.
         ;MOV WORD PTR [BX+0], Dpt
         STI
         ; Recalibrate floppy drive number DL=0.
         INT 13h ; AH=0 Reset disk system.
         JC Error
         XOR AX,AX
		 MOV DX,AX
         CMP [SmallSectors],AX
         JZ Large
         MOV CX,[SmallSectors]    ; 2880 sectors = 1.44 MB.
         MOV WORD PTR [LargeSectors],CX    ; Use .LargeSectors rather than .SmallSectors.
Large:   MOV AL,[NumberOfFats]    ; 2.
         MUL [SectorsPerFat]     ; 9.
         ADD AX, WORD PTR [HiddenSectors] ; 0
         ADC DX, WORD PTR [HiddenSectors + 2] ; 0.
         ADD AX,[ReservedSectors] ; 1.
         ADC DX,0 
		 MOV WORD PTR [LBAroot+0],AX
         MOV WORD PTR [LBAroot+2],DX
         MOV WORD PTR [LBAdata+0],AX
         MOV WORD PTR [LBAdata+2],DX
         MOV AX,32               ; 32.
         MUL [RootEntries]       ; 224.
         MOV BX,[BytesPerSector]  ; 512.
         ADD AX,BX
         DEC AX
         DIV BX                               ; Divide root-dir size by sector size (512).
         ADD WORD PTR [LBAdata+0],AX ; +14.
         ADC WORD PTR [LBAdata+2],0
         MOV BX, 0500H                       ; Memory address where to read disk sectors.
         MOV DX, WORD PTR [LBAroot+2]
         MOV AX, WORD PTR [LBAroot+0]
		 CALL LBAtranslate
		 JB Error
         MOV AL,1
         CALL ReadSec                       ; Read the directory entry.
         JB Error
Break:
         MOV DI,BX
         MOV CX,8+3                           ; Filename size.
         MOV SI,IOSYS
         REPE CMPSB                           ; The first file in dir must be IO.SYS.
         JNE Error
         LEA DI,[BX+32]          ; The next dir entry should be MSDOS.SYS.
         MOV CX,8+3                           ; Filename size. SI points to MSDOS.SYS.
         REPE CMPSB                           ; Check if MSDOS.SYS it at expected position on disk.
         JE Loader ; Load the contents of IO.SYS at address 0x00700 and start its entry 0x0070:0.
Error:   MOV SI, Message
         CALL Display
         XOR AX,AX
         INT 16h                              ; Wait for any key pressed.
       POP SI
	   POP DS
	   POP [SI+0]
	   POP [SI+2]
       INT 19h ; Invoke the bootstrap loader. Try to boot again with a better disk.
Error2:POP AX
	   POP AX
	   POP AX
       JMP Error
	   
Loader: ; IO.SYS file loader reads the sectors of IO.SYS and MSDOS.SYS to the address 0x00700.
        MOV AX,[BX+wClstrNo] ; BX=0x500 points to the directory entry of IO.SYS.
        DEC AX
		DEC AX
        MOV BL,[SectorsPerCluster] ; 1.
        XOR BH,BH
        MUL BX
        ADD AX, WORD PTR [LBAdata+0]
        ADC DX, WORD PTR [LBAdata+2]
        MOV BX, 0700H        ; Memory address where to read.
        MOV CX, DOS_SIZE             ; Read contiguous sectorsof IO.SYS and MSDOS.SYS
NextSec:PUSH AX
        PUSH DX
		PUSH CX
          CALL LBAtranslate ; Convert the cluster number in DX:AX to C/H/S geometry.
          JC Error2
          MOV AL,1
          CALL ReadSec      ; Read AL sectors to address BX.
        POP CX
		POP DX
		POP AX
        JC Error
        ADD AX,1             ; Prepare to read the next cluster.
        ADC DX,0
        ADD BX,[BytesPerSector]
        LOOP NextSec
        MOV CH,[MediaDescriptor]
        MOV DL,[PhysicalDriveNumber]
        MOV BX, WORD PTR [LBAdata+0]
        MOV AX, WORD PTR [LBAdata+2]
        JMPF 0070H:0         ; Start the code in IO.SYS.

Display:
        LODSB
        OR AL,AL
        JZ Return           ; Return when the string is completely displayed.
        MOV AH, 0EH
        MOV BX, 0007H
        INT 10h              ; Output character AL on screen, advance cursor.
        JMP Display
		 
LBAtranslate:     ; Subprocedure which translates LBA in DX:AX
                  ; (cluster number, 19 for root-dir, 33 for data) to the disk geometry.
        CMP DX,[SectorsPerTrack] ; 8.
        JNB RetCF
        DIV [SectorsPerTrack] ; AX=track number, DX=sector number in the track.
        INC DL
        MOV [LBAtrack],DL
        XOR DX,DX
        DIV [NumberOfHeads] ; 1.
        MOV [Reserved],DL   ; This BPB member is misused for the  head number.
        MOV [LBAcylinder],AX
        CLC
        RET
RetCF:  STC                             ; Signalize return with error.
Return  RET
		
ReadSec:	;Subprocedure which reads AL sectors to memory at ES:BX from translated disk address.
        MOV AH,2
        MOV DX,[LBAcylinder]
        MOV CL,6
        SHL DH,CL
        OR DH,[LBAtrack]
        MOV CX,DX
        XCHG CH,CL
        MOV DL,[PhysicalDriveNumber]
        MOV DH,[Reserved] ; Head number.
        INT 13H ; Read AL sectors starting from CL to ES:BX by BIOS service.
        RET

Message:DB 13,10,"Disk/boot error"
        DB 13,10,"Replace and press any key when ready"
        DB 13,10,0
IOSYS:  DB "IO      SYS"         ; File names of MS DOS boot files.
        DB "MSDOS   SYS"
		DB 0, 0
        DB 055H,0AAH             ; Boot sector end signature.
