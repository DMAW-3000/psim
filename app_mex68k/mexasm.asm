;********************************************************************
;							Section AS
;********************************************************************
	SECTION AS
	
	PUBLIC CODE68K

;* EVALUATE EXPRESSION
;*  NUMBER PLUS OR MINUS NUMBER....
;*
EV       DS        0
         MOVE.L    D7,-(A7)            ;SAVE D7
         CLR.L     D7
GETEXP21 BSR.S     GETFIELD            ;GET NUMBER
         ADD.L     D0,D7               ;D7 = NUMBER BEING BUILT
GETEXP15 MOVE.B    (A5)+,D1            ;D1 = TERMINATING CHAR
         CLR.L     D0                  ;D0 = NEXT NUMBER (=0 1ST TIME)
         CMP.B     #'+',D1
         BEQ       GETEXP21            ;PLUS
         CMP.B     #'-',D1
         BNE.S     GETEXP39            ;NOT MINUS
         BSR.S     GETFIELD            ;GET NEXT NUMBER
         SUB.L     D0,D7
         BRA       GETEXP15
 
GETEXP39 MOVE.L    D7,D0               ;D0 = VALUE BUILT
         SUB.L     #1,A5               ;A5 = CHAR AFTER EXPRESSION
         MOVE.L    (A7)+,D7            ;RESTORE D7
         RTS
 
GETFIELD DS        0
         CMP.B     #'*',(A5)
         BNE.S     GETF305

         MOVE.L    D4,D0               ;D0 = PROGRAM COUNTER
         ADD.L     #1,A5
         BRA.S     GETF333

GETF305  CMP.B     #$27,(A5)
         BNE.S     GETF325             ;NOT LITERAL

         ADD.L     #1,A5
         CLR.L     D0

         MOVE.W    TLENGTH(A1),D1      ;D1 = SIZE
         BEQ.S     GETF308             ;.B = 0
         LSR.W     #5,D1               ;.W = 1
         SUB.L     #1,D1               ;.L = 3
GETF308

GETF311  LSL.L     #8,D0
         MOVE.B    (A5)+,D0
         CMP.B     #$27,(A5)
         BEQ.S     GETF312             ;CLOSING QUOTE
         DBF       D1,GETF311
         BRA.S     ER1                 ;OVERFLOW                      1,2

GETF312  ADD.L     #1,A5               ;MOVE PAST CLOSING QUOTE
         BRA.S     GETF314

GETF313  LSL.L     #8,D0
GETF314  DBF       D1,GETF313          ;LEFT NORNALIZE
         BRA.S     GETF333

GETF325  BSR       GETDECNU            ;GET DECIMAL NUMBER            1,2
         BNE.S     ER1                 ;MESSED UP NUMBER              1,2

GETF333  RTS

XBASE    DS        0
;* FIND AND SET SIZE
;* BIT 5432109876543210
;*     ........00......  = BYTE
;*     ........01......  = WORD
;*     ........10......  = LONG
;*
FSIZE    OR.W      TLENGTH(A1),D2       ;   SET SIZE BITS
         RTS

;*  D0 = VALUE 0 - 7
;*  D1 = 0 IF D@     = 1 IF A@
GETREGD  CLR.L     D1
         CMP.B     #'D',(A5)+
         BNE.S     ER1                 ;.                             1,2
GET41    CLR.L     D0
         MOVE.B    (A5)+,D0
         SUB.B     #'0',D0
         BMI.S     ER1                 ;.                             1,2
         CMP.B     #$7,D0
         BGT.S     ER1                 ;.                             1,2
         RTS

GETREGA  CLR.L     D1
         MOVE.B    #8,D1
         CMP.B     #'A',(A5)+
         BNE.S     ER1                 ;.                             1,2
         BRA       GET41

GETREGAD CLR       D1
         MOVE.B    (A5)+,D0
         CMP.B     #'D',D0
         BEQ       GET41
         MOVE.B    #8,D1
         CMP.B     #'A',D0
         BEQ       GET41
ER1      BRA       ER                  ;.                             1,2
 
EADA     MOVE.W    #$1FD,D7            ;DATA ALTERABLE ONLY
         BRA.S     EA
 
EAC      MOVE.W    #$7E4,D7            ;CONTROL ONLY
         BRA.S     EA
 
EAM      MOVE.W    #$1FC,D7            ;MEMORY ALTERABLE ONLY
         BRA.S     EA
 
EAZ      MOVE.W    #$800,D7            ;IMMEDIATE ONLY
         BRA.S     EA

EADADDR  MOVE.W    #$FFD,D7;  DATA ADDRESSING
         BRA.S     EA

EAA      MOVE.W    #$1FF,D7 ;           ALTERABLE ADDRESSING
         BRA.S     EA

EAALL    MOVE.W    #$FFF,D7  ;ALL MODES

;*  ...............1  D@                DATA REGISTER
;*  ..............1.  A@
;*  .............1..  (A@)
;*  ............1...  -(A@)
;*  ...........1....  (A@)+
;*  ..........1.....  DATA(A@)
;*  .........1......  DATA(A@,R@)
;*  ........1.......  DATA  (SHORT)
;*  .......1........  DATA  (LONG)
;*  ......1.........  DATA(PC)
;*  .....1..........  DATA(PC,R@)
;*  ....1...........  #DATA
;*  1...............  SPECIAL CASE JMP.L
 
;* D0 = VALUE CALCULATED
;* D2 = MASK WORD (1ST WORD OF INSTRUCTION)
;* D3 = OFFSET FOR DATA STORE (TDATA+..)
;* D4 = EXTENSION WORD
;* D5 = <DATA>
;* D6 = MODE AS BUILT   .........XXXXXX
;* D7 = MODES ALLOWED
;*
;* A4 = BASE ADDRESS FOR DATA STORE (TDATA+..)[A4,D3]
EA       DS        0
         CLR.L     D5         ;         ZERO VALUE
         CLR.L     D6          ;        MODE = 000000
         MOVE.B    (A5),D0
         CMP.B     #'#',D0
         BNE.S     EA10

;* IMMEDIATE MODE
         BTST      #11,D7
         BEQ       ER1                 ;.                             1,2

         MOVE.B    #$3C,D6      ;       D6 = MODE  111100
         ADD.L     #1,A5;

         BSR       EV              ;    EVALUATE EXPRESSION
         MOVE.L    D0,D5            ;   D5 = VALUE

         TST.B     TLSPEC(A1)        ;  .                             1,3
         BEQ.S     EA0633             ; .SIZE NOT SPECIFIED (.W ASSUMED)

         MOVE.W    TLENGTH(A1),D0
         BEQ.S     EA0635              ;.BYTE

         TST.B     D0
         BMI.S     EA0637              ;.LONG

EA0633   BSR       EA16BIT             ;.WORD     -32K TO +64K
EA0634   MOVE.W    D5,(A4,D3)
         ADD.B     #2,TNB(A1)          ;BYTE COUNT
         ADD.L     #2,D3               ;OFFSET
         RTS

EA0635   BSR       EA8BIT              ;-127 TO +255
         BNE       ER1
         BRA       EA0634

EA0637   MOVE.L    D5,(A4,D3)
         ADD.B     #4,TNB(A1)
         ADD.L     #4,D3
         RTS
 
EA10     DS        0
         CMP.B     #'-',(A5)
         BNE.S     EA11

         CMP.B     #'(',1(A5)
         BNE       EA41                ;MAY BE "-<DATA>

         ADD.L     #2,A5
         MOVE.W    #$0020,D6           ;MODE = -(A@)    100AAA

         BTST      #4,D7
         BEQ       ER1                 ;THIS MODE NOT ALLOWED         1,2

         BSR       GETREGA
         OR.W      D0,D6

         CMP.B     #')',(A5)+
         BNE.S     ER3                 ;NO CLOSING PARIN              1,2
         RTS

EA11     CMP.B     #'A',D0
         BNE.S     EA21

         MOVE.B    #$08,D6             ;MODE = 001...
         BTST      #1,D7
         BEQ.S     ER3                 ;MODE NOT ALLOWED              1,2

         BSR       GETREGA
         OR.W      D0,D6
         RTS

EA21     CMP.B     #'D',D0
         BNE.S     EA31

         BTST      #0,D7
         BEQ.S     ER3                 ;MODE NOT ALLOWED              1,2

         BSR       GETREGD             ;MODE = D@   000AAA
         OR.W      D0,D6
         RTS
 
EA31     CMP.B     #'(',D0
         BNE.S     EA41

;* POSSIBLE
;*  (A@)
;*  (A@)+
;*  (A@,R@)  IMPLIED ZERO DISPLACEMENT
;*
         ADD.L     #1,A5
         BSR       GETREGA
         OR.W      D0,D6

         MOVE.B    (A5)+,D0
         CMP.B     #',',D0
         BEQ       EA5116              ;MODE = (A@,R@)  ;IMPLIED D5 = 0 DATA

         CMP.B     #')',D0             ;LOOK FOR CLOSING )
         BNE.S     ER3                 ;.                             1,2

         CMP.B     #' ',(A5)           ;LOOK FOR BLANK
         BEQ.S     EA35                ;MODE = (A@)

         CMP.B     #'+',(A5)
         BNE.S     EA35
         ADD.L     #1,A5

         OR.W      #$18,D6   ;MODE = 011...    (A@)+

         BTST      #3,D7
         BEQ.S     ER3        ;         MODE NOT ALLOWED              1,2

EA34     RTS                           ;.                             1,2

EA35     OR.W      #$10,D6     ;        MODE = 010...   (A@)

         BTST      #2,D7
         BNE       EA34         ;       MODE ALLOWED                  1,2
ER3      BRA       ER            ;      MODE NOT ALLOWED              1,2
 
;* POSSIBLE
;*   <DATA>   SHORT
;*   <DATA>   LONG
;*   <DATA>(A@)
;*   <DATA>(A@,R@)
;*   <DATA>(A@,R@.W)
;*   <DATA>(A@,R@.L)
;*   <DATA>(PC)
;*   <DATA>(PC,R@)
;*   <DATA>(PC,R@.W)
;*   <DATA>(PC,R@.L)
;*
EA41     BSR       EV              ;    EVALUATE EXPRESSION
         MOVE.L    D0,D5          ;     D5 = <DATA>

         MOVE.B    (A5),D0
         CMP.B     #',',D0
         BEQ.S     EA4102
         CMP.B     #' ',D0
         BNE.S     EA4120

;*  <DATA>         ONLY
;* CHECK IF NEGATIVE NUMBER
EA4102   MOVE.L    D5,D0
         BPL.S     EA4105           ;   POSITIVE NUMBER
         NOT.L     D0                ;  .                             1,3
EA4105   AND.W     #$8000,D0         ;  .                             1,3
         TST.L     D0
         BNE.S     EA4135            ;  .LONG

;*  <DATA>.W
         BTST      #7,D7
         BNE.S     EA4127             ; SHORT ALLOWED                 1,1
         BTST      #15,D7             ; .                             1,1
         BEQ       ER3                ; MODE NOT ALLOWED              1,2
         BRA.S     EA4135             ; SPECIAL CASE (JMP.L)          1,1

EA4127   OR.W      #$38,D6             ;EA = ABSOULTE SHORT           1,1
         MOVE.W    D5,(A4,D3)          ;D5 = DATA
         ADD.B     #2,TNB(A1)          ;BYTE COUNT
         ADD.L     #2,D3
         RTS

;*EA4134   CMP.B     #'L',D0
;*        BNE       ER3                 ;.                             1,2

;*  <DATA>.L
EA4135   OR.W      #$39,D6             ;EA = ABSOLUTE LONG
         MOVE.L    D5,(A4,D3)
         ADD.B     #4,TNB(A1)          ;BYTE COUNT
         ADD.L     #4,D3
         BTST      #8,D7
         BEQ       ER3                 ;MODE NOT ALLOWED              1,2
         RTS

EA4120   ADD.L     #1,A5               ;.                             1,3
         CMP.B     #'(',D0             ;.                             1,3
         BNE       ER3                 ;.                             1,2

         CMP.B     #'P',(A5)
         BEQ       EA61

;* <DATA>(A@.......
         BSR       EA16BITS            ;-32K TO +32K

         BSR       GETREGA
         OR.W      D0,D6

         MOVE.B    (A5),D0
         CMP.B     #')',D0
         BNE.S     EA5115

;* <DATA>(A@)
         ADD.L     #1,A5

         BTST      #5,D7
         BEQ       ER4                 ;MODE NOT ALLOWED              1,2

         OR.W      #$0028,D6           ;MODE = 101AAA

         CMP.L     #$10000,D5
         BPL       ER4                 ;.                             1,2

         MOVE.W    D5,(A4,D3)
         ADD.B     #2,TNB(A1)
         ADD.L     #2,D3
         RTS
 
EA5115   BSR       COMMA

;*  <DATA>(A@,-----    ADDRESS REGISTER WITH INDEX
EA5116   EXT.L     D5
         BSR       EA8BITS             ;-128 TO +127
         BNE.      ER4                 ;.                             1,2
         AND.W     #$00FF,D5
         OR.W      #$0030,D6           ;MODE  110---

         BTST      #6,D7
         BEQ       ER4                 ;MODE NOT ALLOWED              1,2

         BSR       GETREGAD
         OR.W      D1,D0
         ROR.W     #4,D0
         OR.W      D0,D5               ;EXTENSION WORD

;* BIT 11 EXTENSION WORD
;*   0 = SIGN EXTENDED, LOW ORDER INTEGER IN INDEX REGISTER
;*   1 = LONG VALUE IN INDEX REGISTER  (DEFAULT)
;*
         MOVE.B    (A5)+,D0
         CMP.B     #')',D0
         BEQ.S     EA5119              ;DEFAULT   .W

         CMP.B     #'.',D0
         BNE.S     ER4                 ;.                             1,2

         MOVE.B    (A5)+,D0
         CMP.B     #'W',D0
         BEQ.S     EA5118

         CMP.B     #'L',D0
         BNE.S     ER4                 ;NEITHER .W NOR .L             1,2

         OR.W      #$0800,D5           ;EXTENSION WORD, W/L BIT = .L

EA5118   CMP.B     #')',(A5)+
         BNE.S     ER4                 ;NO CLOSING ")"                1,2

EA5119   MOVE.W    D5,(A4,D3)
         ADD.B     #2,TNB(A1)
         ADD.L     #2,D3
EA5119E  RTS                           ;.                             1,2
 
;*  <DATA>(P-----
EA61     ADD.L     #1,A5
         CMP.B     #'C',(A5)+
         BNE       ER

         SUB.L     PCOUNTER(A1),D5     ;D5 = D5 - PC
         SUB.L     #2,D5               ;D5 = D5 - (PC + 2)

         MOVE.B    (A5)+,D0
         CMP.B     #')',D0
         BNE.S     EA71

;*  <DATA>(PC)
         OR.W      #$3A,D6             ;MODE = 111010

         BSR.S     EA16BITS            ;-32K TO +32K
         MOVE.W    D5,(A4,D3)
         ADD.B     #2,TNB(A1)
         ADD.L     #2,D3

         BTST      #9,D7
         BNE       EA5119E             ;.                             1,2
ER4      BRA       ER                  ;.                             1,2

;*  <DATA>(PC----          PROGRAM COUNTER WITH INDEX
EA71     MOVE.W    #$003B,D6           ;MODE = 111011

         CMP.B     #',',D0
         BNE       ER4                 ;.                             1,2

         BTST      #10,D7
         BEQ       ER4                 ;MODE NOT ALLOWED              1,2

         BSR.S     EA8BITS             ;-128 TO +127
         BNE       ER4                 ;.                             1,2

         AND.W     #$00FF,D5           ;D5 = VALUE
         BSR       GETREGAD
         OR.W      D1,D0


         ROR.W     #4,D0
         OR.W      D0,D5               ;D5 = EXTENSION WORD

         MOVE.B    (A5)+,D0
         CMP.B     #')',D0
         BEQ.S     EA7115              ;DEFAULT  .W

         CMP.B     #'.',D0
         BNE       ER4                 ;.                             1,2

         MOVE.B    (A5)+,D0
         CMP.B     #'W',D0
         BEQ.S     EA7113

         CMP.B     #'L',D0
         BNE       ER4                 ;.                             1,2
         OR.W      #$0800,D5           ;EXTENSION WORD W/L = .L

EA7113   CMP.B     #')',(A5)+
         BNE       ER4                 ;NO CLOSING ")"                1,2

EA7115   MOVE.W    D5,(A4,D3)
         ADD.B     #2,TNB(A1)
         ADD.L     #2,D3
         RTS
 
;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*
;*
;*        ROUTINES TO TEST FOR VALID EFFECTIVE ADDRESSES
;*
;*        EA16BIT   tests that -32768 <= D5 <= 65535.  (signed or unsigned)
;*        EA16BITS  tests that -32768 <= D5 <= 32767.  (signed only)
;*        EA8BIT    tests that   -128 <= D5 <=   255.  (signed or unsigned)
;*        EA8BITS   tests that   -128 <= D5 <=   127.  (signed only)
;*
;*        The 16-bit tests branch to ER if invalid, else return.
;*        The  8-bit tests return condition codes <EQ> if valid, else <NE>.
;*        D5 is preserved unless a branch to ER results.
;*        D1 is destroyed.
;*
;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*;*

EA16BIT:
         BSR.S     EA16BITC            ;CHECK RANGE -32768 TO 32767.  IF
         MOVE.L    D5,D1               ;INVALID, CHECK WHETHER THE HIGH 16
         SWAP      D1                  ;BITS ARE 0 (WHICH IMPLIES THAT
         TST.W     D1                  ;D5 <= 65535).  IF NOT, FALL THRU TO
         BEQ.S     EASEX               ;THE 16-BIT SIGNED TEST--WE WILL
;*                                       FAIL AND GO TO ER.

EA16BITS:
         PEA       ER(PC)              ;SET UP TO RETURN TO ER IF INVALID.

EA16BITC MOVE.L    #$7FFF,D1           ;D1  <--  2^16-1.
         BRA.S     EAS                 ;GO TO THE COMMON TEST ROUTINE.


EA8BIT:
         BSR.S     EA8BITC             ;CHECK RANGE -128 TO 127.  IF INVALID,
         MOVE.L    D5,D1               ;CHECK WHETHER THE HIGH 24 BITS ARE
         LSR.L     #8,D1               ;0 (WHICH IMPLIES THAT D5 <= 255).
         RTS                           ;*

EA8BITS:
         BSR.S     EA8BITC             ;JUST CHECK FOR -127 <= D5 <= 128.
         RTS                           ;(BSR PUTS NEEDED ADDRESS ON STACK!)

EA8BITC  MOVE.L    #$7F,D1             ;D1  <--  2^8 - 1.

;*                  ;*;*;* NOTE: THIS ROUTINE PLAYS WITH THE STACK ;*;*;*
EAS      CMP.L     D1,D5               ;IF D5 > 2^N-1, RETURN WITH <NE> (INVAL).
         BGT.S     EASEX               ;*
         NOT.L     D1                  ;IF D5 < -2^N,  RETURN WITH <NE> (INVAL).
         CMP.L     D1,D5               ;*
         BLT.S     EASEX               ;*

         ADD.L     #4,A7               ;POP THE RETURN ADDRESS OFF THE STACK,
         CLR.L     D1                  ;SET <EQ> (VALID), AND RETURN.

EASEX    RTS

ADR      MACRO 	 adr
         DC.W    adr-XBASE
         ENDM
		 
TBLKEYS  DS        0         ;INDEX
         ADR       MABCD      ;0  ABCD SBCD
		 ADR       MADD       ;1  ADD  SUB
         ADR       MADDA      ;2  ADDA CMPA SUBA
         ADR       MADDI      ;3  ADDI CMPI SUBI
         ADR       MADDQ      ;4  ADDQ SUBQ
         ADR       MADDX      ;5  ADDX SUBX
         ADR       MAND       ;6  AND  EOR OR
         ADR       MASL       ;7  ASL  LSL ROL ROXL
         ADR       MDBCC      ;8  DBCC
         ADR       MBCHG      ;9  BCHG
         ADR       MBRA       ;10  BRA  BSR  BCC
         ADR       MBSET      ;11  BSET
         ADR       MCHK       ;12  CHK  DIVS DIVU MILS MULU
         ADR       MCLR       ;13  CLR NEG NEGX NOT TST
         ADR       MCMPM      ;14  CMPM
         ADR       MMOVEQ     ;15  MOVEQ
         ADR       MEXG       ;16  EXG
         ADR       MEXT       ;17  EXT
         ADR       MJMP       ;18  JMP  JSR
         ADR       MLEA       ;19  LEA
         ADR       MLINK      ;20  LINK
         ADR       MMOVE      ;21  MOVE
         ADR       MCMMD2     ;22  NOP RESET RTE RTR RTS TRAPV
         ADR       MSTOP      ;23  STOP
         ADR       MSWAP      ;24  SWAP
         ADR       MTRAP      ;25  TRAP
         ADR       MUNLK      ;26  UNLK
         ADR       MMOVEM     ;27  MOVEM
         ADR       MANDI      ;28  ANDI EORI ORI
         ADR       MSCC       ;29  NBCD SCC TAS
         ADR       MBCLR      ;30  BCLR
         ADR       MBTST      ;31  BTST
         ADR       MMOVEA     ;32  MOVEA
         ADR       MMOVEP     ;33  MOVEP
         ADR       MCMP       ;34  CMP
         ADR       MEOR       ;35  EOR
         ADR       MPEA       ;36  PEA
         ADR       MDC        ;37  DC.W
		 
;* \1,\2 = MNEUMONIC (\2 SIGN BIT SET AS LAST CHARACTER)
;* \3    = INDEX TO TABLKEYS
;* \4,\5 = FIRST WORD MASK
;* \6    = NO OPERAND ALLOWED IF SIGN SET
;* \7    = .S ALLOWED (.W NOT ALLOWED)                                1,2
OPC      MACRO	   mnem1, mnem2, idx, msk4, msk5, noop, sflag
         DC.B      'mnem1','mnem2'+128
         DC.B      idx+noop+sflag,$msk4,$msk5
         ENDM
		 
NOC      EQU       128                 ;(BIT 7 SET) NO OPERAND
NW       EQU       $40                 ;(BIT 6 SET) .W NOT ALLOWED    1,2
TBLOPC   OPC       ABC,D,0,C1,00,0,0    ; ABCD
         OPC       ADD,A,2,D0,C0,0,0    ; ADDA
         OPC       ADD,I,3,06,00,0,0    ; ADDI
         OPC       ADD,Q,4,50,00,0,0    ; ADDQ
         OPC       ADD,X,5,D1,00,0,0    ; ADDX
         OPC       AD,D,1,D0,00,0,0     ; ADD
         OPC       AND,I,28,02,00,0,0   ; ANDI
         OPC       AN,D,6,C0,00,0,0     ; AND
         OPC       AS,L,7,E1,00,0,0     ; ASL
         OPC       AS,R,07,E0,00,0,0    ; ASR
         OPC       BR,A,10,60,00,0,NW   ; BRA
         OPC       BH,I,10,62,00,0,NW    ;  BHI
         OPC       BL,S,10,63,00,0,NW    ;  BLS
         OPC       BC,C,10,64,00,0,NW    ;  BCC
         OPC       BC,S,10,65,00,0,NW    ;  BCS
         OPC       BN,E,10,66,00,0,NW    ;  BNE
         OPC       BE,Q,10,67,00,0,NW    ;  BEQ
         OPC       BV,C,10,68,00,0,NW    ;  BVC
         OPC       BV,S,10,69,00,0,NW    ;  BVS
         OPC       BP,L,10,6A,00,0,NW     ; BPL
         OPC       BM,I,10,6B,00,0,NW    ;  BMI
         OPC       BG,E,10,6C,00,0,NW    ;  BGE
         OPC       BL,T,10,6D,00,0,NW    ;  BLT
         OPC       BG,T,10,6E,00,0,NW    ;  BGT
         OPC       BL,E,10,6F,00,0,NW    ;  BLE
         OPC       BCH,G,9,01,40,0,0    ; BCHG
         OPC       BCL,R,30,01,80,0,0    ;BCLR      DYNAMIC
         OPC       BSE,T,11,01,C0,0,0    ;BSET
         OPC       BS,R,10,61,00,0,NW    ;BSR
         OPC       BTS,T,31,01,00,0,0    ;BTST
         OPC       B,T,10,60,00,0,NW     ; BT
         OPC       CH,K,12,41,80,0,0     ;CHK
         OPC       CL,R,13,42,00,0,0     ;CLR
         OPC       CMP,A,2,B0,C0,0,0     ;CMPA
         OPC       CMP,I,3,0C,00,0,0     ;CMPI                          1,1
         OPC       CMP,M,14,B1,08,0,0    ;CMPM
         OPC       CM,P,34,B0,00,0,0     ; CMP
         OPC       DB,T,8,50,C8,0,NW     ;DBT
         OPC       DB,F,8,51,C8,0,NW     ;DBF
         OPC       DBR,A,8,51,C8,0,NW    ;DBRA
         OPC       DBH,I,8,52,C8,0,NW    ;DBHI
         OPC       DBL,S,8,53,C8,0,NW    ;DBLS
         OPC       DBC,C,8,54,C8,0,NW    ;DBCC
         OPC       DBC,S,8,55,C8,0,NW    ;DBCS
         OPC       DBN,E,8,56,C8,0,NW    ;DBNE
         OPC       DBE,Q,8,57,C8,0,NW    ;DBEQ
         OPC       DBV,C,8,58,C8,0,NW    ;DBVC
         OPC       DBV,S,8,59,C8,0,NW    ;DBVS
         OPC       DBP,L,8,5A,C8,0,NW    ;DBPL
         OPC       DBM,I,8,5B,C8,0,NW    ;DBMI
         OPC       DBG,E,8,5C,C8,0,NW    ;DBGE
         OPC       DBL,T,8,5D,C8,0,NW    ;DBLT
         OPC       DBG,T,8,5E,C8,0,NW    ;DBGT
         OPC       DBL,E,8,5F,C8,0,NW    ;DBLE
         OPC       DC.,W,37,00,00,0,0    ;DC.W  (WORD ONLY)
         OPC       DIV,S,12,81,C0,0,0    ;DIVS
         OPC       DIV,U,12,80,C0,0,0    ;DIVU
         OPC       EOR,I,28,0A,00,0,0    ;EORI
         OPC       EO,R,35,B1,00,0,0     ; EOR
         OPC       EX,G,16,C1,00,0,0     ;EXG
         OPC       EX,T,17,48,00,0,0     ;EXT
         OPC       JM,P,18,4E,C0,0,NW    ;JMP
         OPC       JS,R,18,4E,80,0,NW    ;JSR
         OPC       LE,A,19,41,C0,0,0     ;LEA
         OPC       LIN,K,20,4E,50,0,0    ;LINK
         OPC       LS,L,7,E3,08,0,0      ;LSL
         OPC       LS,R,07,E2,08,0,0     ;LSR
         OPC       MOVE,A,32,00,04,0,0   ;MOVEA
         OPC       MOVE,M,27,48,80,0,0   ;MOVEM
         OPC       MOVE,P,33,01,08,0,0   ;MOVEP
         OPC       MOVE,Q,15,70,00,0,0   ;MOVEQ
         OPC       MOV,E,21,00,00,0,0    ;MOVE
         OPC       MUL,S,12,C1,C0,0,0    ;MULS
         OPC       MUL,U,12,C0,C0,0,0    ;MULU
         OPC       NBC,D,29,48,0,0,0     ;NBCD
         OPC       NEG,X,13,40,00,0,0    ;NEGX
         OPC       NE,G,13,44,00,0,0     ;NEG
         OPC       NO,P,22,4E,71,NOC,0   ;NOP
         OPC       NO,T,13,46,00,0,0     ;NOT
         OPC       OR,I,28,00,00,0,0     ;ORI
         OPC       O,R,6,80,00,0,0       ;OR
         OPC       PE,A,36,48,40,0,0     ;PEA
         OPC       RESE,T,22,4E,70,NOC,0 ;RESET
         OPC       RO,L,7,E7,18,0,0      ;ROL
         OPC       RO,R,07,E6,18,0,0     ;ROR
         OPC       ROX,L,7,E5,10,0,0     ;ROXL
         OPC       ROX,R,07,E4,10,0,0    ;ROXR
         OPC       RT,E,22,4E,73,NOC,0   ;RTE
         OPC       RT,R,22,4E,77,NOC,0   ;RTR
         OPC       RT,S,22,4E,75,NOC,0   ;RTS
         OPC       SBC,D,0,81,00,0,0     ;SBCD
         OPC       S,F,29,51,C0,0,0      ;SF
         OPC       SH,I,29,52,C0,0,0     ;SHI
         OPC       SL,S,29,53,C0,0,0     ;SLS
         OPC       SC,C,29,54,C0,0,0     ;SCC
         OPC       SC,S,29,55,C0,0,0     ;SCS
         OPC       SN,E,29,56,C0,0,0     ;SNE
         OPC       SE,Q,29,57,C0,0,0     ;SEQ
         OPC       SV,C,29,58,C0,0,0     ;SVC
         OPC       SV,S,29,59,C0,0,0     ;SVS
         OPC       SP,L,29,5A,C0,0,0     ;SPL
         OPC       SM,I,29,5B,C0,0,0     ;SMI
         OPC       SG,E,29,5C,C0,0,0     ;SGE
         OPC       SL,T,29,5D,C0,0,0     ;SLT
         OPC       SG,T,29,5E,C0,0,0     ;SGT
         OPC       SL,E,29,5F,C0,0,0     ;SLE
         OPC       STO,P,23,4E,72,0,0    ;STOP
         OPC       S,T,29,50,C0,0,0      ;ST
         OPC       SUB,A,2,90,C0,0,0     ;SUBA
         OPC       SUB,I,3,04,00,0,0     ;SUBI
         OPC       SUB,Q,4,51,00,0,0     ;SUBQ
         OPC       SUB,X,5,91,00,0,0     ;SUBX
         OPC       SU,B,1,90,00,0,0      ;SUB
         OPC       SWA,P,24,48,40,0,0    ;SWAP
         OPC       TA,S,29,4A,C0,0,0     ;TAS                         1,2
         OPC       TRAP,V,22,4E,76,NOC,0 ;TRAPV
         OPC       TRA,P,25,4E,40,0,0    ;TRAP
         OPC       TS,T,13,4A,00,0,0     ;TST
         OPC       UNL,K,26,4E,58,0,0    ;UNLK
		 DC.B	   0
TBLOPCE  DS        0
         
;* WITHOUT LABEL FIELD
;* 012345678901234567890123456789012345678901234567890
;* AAAAAA DDDDDDDDDDDDDDDDDDDD OPCODE  OPERAND
;*        FDATA                FOC     FOP

;* 012345678901234567890123456789012345678901234567890
;* AAAAAA DDDDDDDDDDDDDDDDDDDD LLLLLLLL OPCODE  OPERAND
;*        FDATA                FOL      FOC     FOP

;* A3 = STORE POINTER
;* A4 = PROGRAM COUNTER
;* A5 = SOURCE PTR BEGINNING
;* A6 = SOURCE PTR END+1
;*
OUTBSIZE EQU       80       ; BUFFER SIZE
FDATA    EQU       10        ;OFFSET TO DATA
FOL      EQU       31        ;OFFSET TO LABEL
FOC      EQU       31        ;OFFSET TO OP-CODE (NO LABEL FIELD)
FOP      EQU       39        ;OFFSET TO OPERAND (NO LABEL FIELD)

CODE68K  LINK      A1,#0-(ESKE-ESKB)
         MOVE.L    A1,LINK(A7)         ;SAVE LINKAGE
         MOVE.L    A7,A1               ;A1 = BASE REGISTER TO DATA

         MOVE.B    #' ',(A6)           ;INSURE LAST CHAR IS SPACE

         MOVE.L    A3,A0
         MOVE.L    #OUTBSIZE-1,D0
M300     MOVE.B    #' ',(A0)+          ;SPACE FILL BUFFER
         DBRA      D0,M300
         SUB.L     #2,A0
         MOVE.L    A0,PTRBUFE(A1)      ;PTR TO END OF BUFFER

         MOVE.L    A4,PCOUNTER(A1)     ;FORMAT PC
         MOVE.L    A4,D4               ;D4 = P-COUNTER
         MOVE.L    A4,D0

         MOVE.L    A6,-(A7)            ;SAVE A6                       1,1
         MOVE.L    A3,A6
         BSR       FRELADDR            ;FORM RELATIVE ADDRESS
         MOVE.L    (A7)+,A6            ;RESTORE A6                    1,1

         MOVE.L    #1,D7               ;POSSIBLE ERROR CODE
         MOVE.L    A4,D0
         ROR.L     #1,D0
         BMI       ERDONE              ;PC ODD ADDRESS

         MOVE.L    #FOL,D7             ;POSSIBLE ERROR CODE
         CMP.B     #' ',(A5)+
         BNE       ERDONE              ;1ST CHAR NOT SPACE

         MOVE.B    #2,TNB(A1)          ;INZ # OF BYTES
         MOVE.W    #$40,TLENGTH(A1)    ;SIZE = .W (DEFAULT)
         CLR.B     TLSPEC(A1)          ;DEFAULT (SIZE NOT SPECIFIED)

         MOVE.L    A3,A0               ;A0 = STORE ADDRESS
         ADD.L     #FOC,A0

M340     BSR       GETCHARF            ;GET PAST SPACES               1,1
         CMP.B     #' ',D0
         BEQ       M340

         SUB.L     #1,A5               ;FORMAT OP-CODE
M350     BSR       GETCHARF            ;.                             1,1
         MOVE.B    D0,(A0)+
         CMP.B     #'.',D0
         BNE.S     M352

         MOVE.B    (A5),TLSPEC(A1)     ;NOT DEFAULT                   1,2
         CMP.B     #'W',(A5)
         BEQ.S     M352
         CMP.B     #'S',(A5)
         BEQ.S     M352                ;.SHORT = .WORD
         CLR.W     TLENGTH(A1)
         CMP.B     #'B',(A5)
         BEQ.S     M352                ;SIZE = .W
         MOVE.W    #$80,TLENGTH(A1)
         CMP.B     #'L',(A5)
         BNE       ERF                 ;.                             1,1

M352     CMP.B     #' ',D0
         BNE       M350                ;NOT SPACE CONTINUE

;* SEARCH OP-CODE TABLE
         LEA       TBLOPC(PC),A0       ;A0 = PTR TO TABLE OF CODES
M410     MOVE.L    A3,A2               ;A3 = START OF STORE BUFFER
         ADD.L     #FOC,A2             ;A2 = PTR TO OP-CODE JUST FORMATTED

M415     MOVE.B    (A0)+,D0            ;XXXXXXDD
         EXT.W     D0                  ;XXXXSSDD  SIGN EXTENDED
         AND.B     #$7F,D0
         CMP.B     (A2)+,D0
         BNE.S     M420                ;NON-MATCH
         TST.W     D0
         BPL       M415                ;SIGN RESET; CONTINUE
         BRA.S     M430                ;MATCH COMPLETE

M420     TST.W     D0                  ;SEQUENCE TO NEXT CODE
         BMI.S     M426
M424     MOVE.B    (A0)+,D0
         BPL       M424                ;FINISH THIS OP-CODE
M426     ADD.L     #3,A0               ;ADJUST PTR TO TABLE
         LEA       TBLOPCE(PC),A2
         CMP.L     A0,A2
         BGE       M410

M428     MOVE.L    #FOC,D7             ;ERROR CODE
         BRA       ERDONE

;* GET GOTO INDEX
;* GET FIRST WORD MASK
M430     MOVE.B    (A2),D0             ;MUST TERMINATE OP-CODE
         CMP.B     #' ',D0             ;WITH SPACE OR PERIOD
         BEQ.S     M432
         CMP.B     #'.',D0
         BNE       M428                ;ERROR
M432

         CLR.L     D0
         MOVE.B    (A0)+,D0            ;D0 =  KEYS  INDEX
         MOVE.B    D0,D1               ;D1 =  KEYS (INDEX)
         AND.B     #$3F,D0             ;D0 =        INDEX             1,2
         ASL.L     #1,D0               ;INDEX ;* TWO                   1,2
         MOVE.B    (A0)+,D2
         LSL.W     #8,D2
         MOVE.B    (A0)+,D2            ;D2 = FIRST WORD MASK
         MOVE.W    D2,TDATA(A1)

;* INSURE .S .W MATCH OP-CODE                                         1,2
         MOVE.B    TLSPEC(A1),D3       ;D3 = .n SPECIFIED             1,2
         BEQ.S     M4326               ;NOT SPECIFIED                 1,2
         BTST      #6,D1               ;.                             1,2
         BEQ.S     M4324               ;.W ALLOWED (.S NOT ALLOWED)   1,2
         CMP.B     #'W',D3             ;.                             1,2
         BEQ       M428                ;.W NOT ALLOWED                1,2
         CMP.B     #'B',D3             ;.                             1,2
         BEQ       M428                ;.B NOT ALLOWED                1,2
         BRA.S     M4326               ;.                             1,2

M4324    CMP.B     #'S',D3             ;                              1,2
         BEQ       M428                ;.S NOT ALLOWED                1,2
M4326

;* CALCULATE GOTO ADDRESS
         LEA       TBLKEYS(PC),A0      ;A0 = PTR TO KEYS
         MOVE.W    (A0,D0),D0          ;D0 = 16 BIT OFFSET
         LEA       XBASE(PC),A2        ;A2 = BASE ADDRESS
         ADD.L     D0,A2               ;A2 = COMPUTED GO TO  ADDRESS

;* FORMAT OPERAND IF REGUIRED
         TST.B     D1                  ;LOOK AT KEY
         BMI.S     M440                ;OPERAND NOT REQUIRED

         MOVE.L    A3,A0
         ADD.L     #FOP,A0             ;STORE POINTER
         MOVE.L    A0,PTROP(A1)        ;POINTER TO OPERAND (FORMATED)
M435     BSR.S     GETCHARF            ;D0 = CHAR                     1,1
         CMP.B     #' ',D0
         BEQ       M435                ;SKIP SPACES

M437     MOVE.B    D0,(A0)+            ;MOVE REST OF SOURCE LINE
         BSR.S     GETCHARF            ;D0 = CHAR                     1,1
         CMP.L     A5,A6               ;.                             1,1
         BPL       M437                ;.                             1,1
         MOVE.L    A0,PTRBUFE(A1)      ;POINTER TO END FORMATED SOURCE
         MOVE.L    A0,A6               ;A6 = POINTER TO END OF SOURCE
M440

         MOVE.L    PTROP(A1),A5        ;A5 = PTR TO OPERAND
         LEA       TDATA+2(A1),A4      ;      A4 = BASE ADDR FOR DATA STORE
         CLR.L     D3                  ;D3 = OFFSET FOR DATA STORE
         JMP       (A2)                ;GOTO ROUTINE
;*                                      D2 = MASK
;*                                      D4 = P-COUNTER
 

COMMA    CMP.B     #',',(A5)+
         BNE.S     ER                  ;NOT COMMA
         RTS

GETCHAR  CMP.L     A5,A6
         BMI.S     ER
         MOVE.B    (A5)+,D0
         RTS

GETCHARF CMP.L     A5,A6               ;.                             1,1
         BMI.S     ERF
         MOVE.B    (A5)+,D0
         RTS

ERF      MOVE.L    A0,A5               ;.                             1,1

ER       MOVE.L    A5,D7               ;D7 = ERROR FLAG
         SUB.L     A3,D7               ;..& POSITION OF ERROR
ERDONE   CLR.L     D6                  ;D6 = (ZERO) BYTE COUNT
         BRA.S     CMMD35

CMMD2    CMP.B     #' ',(A5)           ;.                             1,2
         BNE       ER                  ;OPERAND DID NOT END WITH SPACE  1,2

MCMMD2   DS        0                   ;NO OPERAND SEQUENCE
         MOVE.W    D2,TDATA(A1)

         MOVE.B    TNB(A1),D3          ;FORMAT DATA
         MOVE.L    D3,D6               ;D7 = NUMBER OF BYTES
         LEA       TDATA(A1),A2        ;A2 = PTR TO HEX DATA
         MOVE.L    A3,A6               ;D3 = NUMBER OF BYTES
         ADD.L     #FDATA,A6           ;A6 = STORE PTR
FPR315   MOVE.B    (A2)+,D0
         BSR       PNT2HX
         SUB.L     #1,D3
         BNE       FPR315              ;MORE BYTES

         CLR.L     D7                  ;RESET ERROR FLAG

CMMD35   MOVEM.L   TDATA(A1),D0-D2     ;D0-D2 = DATA

         MOVE.L    PTRBUFE(A1),A6      ;A6 = POINTER TO END OF BUFFER

         MOVE.L    PCOUNTER(A1),A4     ;A4 = ORGINAL PC

         MOVE.L    LINK(A1),A1
         UNLK      A1
         RTS                           ;RETURN TO REQUESTOR
;*                                      A3 = POINTER TO START OF BUFFER
;*                                      D6 = NUMBER OF BYTES ASSEMBLED
;*                                      D7 = ERROR FLAG (POSITION)

 
;*  SIZE = BYTE
;*    DY,DX
;*    -(AY),-(AX)
;*    ....RX@.SS...RY@
MABCD    DS        0                   ;(INDEX 0) ABCD SBCD
         TST.B     TLSPEC(A1)
         BEQ.S     MABCD9              ;DEFAULT SIXE = BYTE
         CMP.W     #$00,TLENGTH(A1)
         BNE       ER                  ;NOT .B
MABCD9

         MOVE.W    #$11,D7
         BSR       EA

         BSR       COMMA

         MOVE.L    D6,D0
         AND.W     #7,D0
         OR.W      D0,D2

         BTST      #5,D6
         BEQ.S     MABCD55             ;D@,D@ MODE

         OR.W      #$0008,D2           ;-(A@),-(A@) MODE

         MOVE.W    #$10,D7
         BSR       EA

         AND.W     #7,D6
         ROR.W     #7,D6
         OR.W      D6,D2
         BRA       CMMD2

MABCD55  BSR       GETREGD             ;D@,D@
         ROR.W     #7,D0
         OR.W      D0,D2
CMMD2S10 BRA       CMMD2

 
MCMP     DS        0                   ;(INDEX 34)
         BSR       EAALL
         MOVE.L    D6,D4               ;D4 = SOURCE MODE

         BSR.S     COMMAS20

         CMP.B     #'A',(A5)
         BEQ       MADDA21             ;DESTINATION = A@

         CMP.B     #$3C,D4
         BEQ.S     MCMP56              ;SOURCE  ....I  #<DATA>,...

         BSR       FSIZE

         MOVE.W    #$009,D7
         BSR       EA                  ;D@ + (A@)+
         MOVE.L    D6,D0               ;MMMRRR
         AND.W     #$38,D0             ;MMM...

         BEQ.S     MCMP39              ;DESTINATION  D@

         CMP.B     #$18,D0
         BNE       ER

         AND.W     #$F,D6              ;(AY)+,(AX)+                   1,2
         ROR.W     #7,D6                ;                             1,2
         OR.W      D6,D2               ;....AX@.........              1,2
         OR.W      #$0100,D2           ;...1AX@.........              1,2

         MOVE.L    D4,D0
         AND.W     #$38,D0
         CMP.W     #$18,D0
         BNE       ER                  ;NOT (A@)+
         AND.W     #$F,D4              ;............1AY@              1,2
         OR.W      D4,D2
         BRA       CMMD2

;*  <EA>,D@
MCMP39   ROR.W     #7,D6
         OR.W      D6,D2

         OR.W      D4,D2
         BRA.S     CMMD2S11

MCMP56   MOVE.W    #$0C00,D2           ;#<DATA>,<EA>      MASK = CMPI

         BSR       FSIZE

         BSR       EADA
         OR.W      D6,D2
CMMD2S11 BRA       CMMD2S10

COMMAS20 BRA       COMMA
 
MADD     DS        0                   ;(INDEX 1)
         BSR       EAALL
         MOVE.L    D6,D4               ;D4 = SOURCE MODE

         BSR       COMMAS20

         CMP.B     #'A',(A5)
         BEQ       MADDA21             ;DESTINATION = A@

         CMP.B     #$3C,D4
         BEQ.S     MADD56              ;SOURCE  ....I  #<DATA>,...

         BSR       FSIZE

         MOVE.W    #$1FF,D7
         BSR       EA                  ;ALTERABLE + D@
         MOVE.L    D6,D0               ;MMMRRR
         AND.W     #$38,D0             ;MMM...
         BNE.S     MADD46              ;DESTINATION NOT  D@

;*  <EA>,D@
         ROR.W     #7,D6
         OR.W      D6,D2

         OR.W      D4,D2
         BRA       CMMD2S11

MADD46   DS        0                   ;D@,<EA>
         OR.W      #$100,D2

         ROR.W     #7,D4
         OR.W      D4,D2               ;<EA> AS DESTINATION

         OR.W      D6,D2               ;D@  AS SOURCE
         BRA       CMMD2S11

MADD56   MOVE.L    D2,D0               ;#<DATA>,<EA>
         MOVE.W    #$0600,D2           ;MASK = ADDI

         CMP.W     #$D000,D0
         BEQ.S     MADD58
         MOVE.W    #$400,D2            ;MASK = SUBI
MADD58

         BSR       FSIZE

         BSR       EADA                ;DATA ALTERABLE ONLY
         OR.W      D6,D2
         BRA       CMMD2S11
 
MADDI    MOVE.L    PTROP(A1),A5        ;(INDEX 3) CMPI
         BSR       FSIZE

         BSR       EAZ

         BSR       COMMAS20

         BSR       EADA                ;DATA ALTERABLE ONLY
         OR.W      D6,D2
         BRA       CMMD2S11
 
;*  SIZE =  BYTE, WORD, LONG
;*  #<DATA>,SR
;*  #<DATA>,<EA>    DATA ALTERABLE ONLY
MANDI    DS        0                   ;(INDEX 28) ANDI EORI ORI
         BSR       FSIZE

         BSR       EAZ

         BSR       COMMAS20

         CMP.B     #'S',(A5)
         BEQ.S     MANDI23

         BSR       EADA
         OR.W      D6,D2
         BRA       CMMD2S11

MANDI23  CMP.B     #'R',1(A5)          ;#<DATA>,SR
         BNE       ER
         CMP.W     #$0080,TLENGTH(A1)
         BEQ       ER                  ;.L NOT ALLOWED WITH SR
         OR.W      #$003C,D2
         ADD.L     #2,A5               ;POINTER TO END OF OPERAND     1,2
         BRA       CMMD2
 
MADDA    DS        0                   ;(INDEX 2)
         BSR       EAALL
         OR.W      D6,D2

         BSR       COMMA

MADDA21  OR.W      D6,D2
         MOVE.W    TLENGTH(A1),D0
         BEQ       ER                  ;.BYTE NOT ALLOWED
         LSL.W     #1,D0               ;.W = 011......
         OR.W      #$00C0,D0           ;.L = 111......
         OR.W      D0,D2

         BSR       GETREGA
         ROR.W     #7,D0
         OR.W      D0,D2
         BRA       CMMD2
 
MADDQ    DS        0                   ;(INDEX 4)
         BSR       FSIZE

         BSR       GETIMM

         TST.L     D0
         BEQ       ER                  ;DATA = ZERO
         CMP.B     #9,D0
         BPL       ER                  ;VALUE TOO BIG
         AND.W     #$7,D0              ;MAKE 8 = 0
         ROR.W     #7,D0               ;SHIFT DATA TO BITS 9-11
         OR.W      D0,D2

         BSR       COMMA

         BSR       EAA                 ;ALTERABLE ADDRESSING

         OR.W      D6,D2
         MOVE.L    D2,D0
         AND.W     #$C0,D0
         BNE.S     MADDQ25

;* BYTE SIZE; ADDRESS REGISTER DIRECT NOT ALLOWED
         MOVE.L    D2,D0
         AND.W     #$38,D0
         CMP.B     #$08,D0
         BEQ       ER
MADDQ25  BRA       CMMD2
 
;* SIZE = BYTE, WORD, LONG
;*    DY,DX
;*    -(AY),-(AX)
;*    ....RX@.SS...RY@
MADDX    DS        0   ;                (INDEX 5)
         BSR       FSIZE

         MOVE.W    #$11,D7
         BSR       EA

         BSR       COMMA

         MOVE.L    D6,D0
         AND.W     #7,D0
         OR.W      D0,D2

         BTST      #5,D6
         BEQ.S     MADDX5              ;D@,D@ MODE

         OR.W      #$0008,D2           ;-(A@),-(A@) MODE

         MOVE.W    #$10,D7
         BSR       EA

         AND.W     #7,D6
         ROR.W     #7,D6
         OR.W      D6,D2
         BRA       CMMD2

MADDX5   BSR       GETREGD             ;D@,D@
         ROR.W     #7,D0
         OR.W      D0,D2
         BRA       CMMD2
 
;*  SIZE = BYTE, WORD, LONG
;*         <EA>,D@
;*         D@,<EA>
MAND     BSR       FSIZE               ;(INDEX 6)

         CMP.B     #'#',(A5)
         BEQ.S     MAND90

         BSR       A5TODEST            ;MOVE A5 TO DESTINATION

         MOVE.B    (A5),D0             ;D0 = 1ST CHAR OF DESTINATION
         MOVE.L    PTROP(A1),A5        ;A5 = POINTER TO OPERAND
		 
MYBREAK
         CMP.B     #'D',D0
         BEQ.S     MAND77

         OR.W      #$0100,D2           ; D@,<EA>

         BSR       GETREGD
         ROR.W     #7,D0
         OR.W      D0,D2

         BSR       COMMA

         BSR       EAM                 ;ALTERABLE MEMORY
         OR.W      D6,D2
         BRA       CMMD2

MAND77   BSR       EADADDR             ;<EA>,D@
         OR.W      D6,D2

         BSR       COMMA

         BSR       GETREGD
         ROR.W     #7,D0
         OR.W      D0,D2
         BRA       CMMD2

MAND90   AND.W     #$F000,D2
         CMP.W     #$C000,D2
         BEQ.S     MAND97               ;AND
         MOVE.W    #$0000,D2           ;CHANGE TO "ORI"
MAND91   BRA       MANDI
MAND97   MOVE.W    #$0200,D2          ; CHANGE TO "ADDI"
         BRA       MAND91
 
MEOR     BSR       FSIZE               ;(INDEX 35)

         CMP.B     #'#',(A5)
         BEQ.S     MEOR90

         BSR       GETREGD
         ROR.W     #7,D0
         OR.W      D0,D2

         BSR       COMMA

         BSR       EADA                ;DATA ALTERABLE ADDRESSING
         OR.W      D6,D2
         BRA       CMMD2

MEOR90   MOVE.L    PTROP(A1),A5        ;A5 = POINTER TO OPERAND
         MOVE.W    #$0A00,D2           ;CHANGE TO "EORI"
         BRA       MANDI

A5TODEST CLR.L     D1                  ;MOVE A5 TO DESTINATION
A5300    BSR       GETCHAR
         CMP.B     #'(',D0
         BNE.S     A5305
         MOVE.L    D0,D1
A5305    CMP.B     #')',D0
         BEQ       A5TODEST
         CMP.B     #',',D0
         BNE       A5300
         TST       D1
         BNE       A5300
         RTS
 
MASL     DS        0                   ;(INDEX 7)
;*         ASL     LSL     ROL     ROXL
;*  MASKS  E000    E008    E018    E010
;*         E0C0    E2C0    E6C0    E4C0   SHIFT MEMORY

         BSR       FSIZE

         MOVE.B    (A5)+,D0
         CMP.B     #'#',D0
         BNE.S     MSL200

;*  #<COUNT>,D@
         BSR       EV
         CMP.L     #8,D0
         BGT       ER                  ;GREATER THAN 8

         AND.B     #$7,D0              ;MAKE 8 INTO 0
MSL150   ROR.W     #7,D0
         AND.W     #$F1FF,D2
         OR.W      D0,D2               ;COUNT/REG

         BSR       COMMA

         BSR       GETREGD
         OR.W      D0,D2
         BRA       CMMD2

MSL200   DS        0                   ;D@,D@
         CMP.B     #'D',D0
         BNE.S     MSL300

;*        D@,D@
         OR.W      #$20,D2
         SUB.L     #1,A5
         BSR       GETREGD
         BRA       MSL150

MSL300   DS        0                   ;<EA>      SHIFT MEMORY
         SUB.L     #1,A5
         OR.W      #$00C0,D2           ;SIZE = MEMORY

         AND.W     #$FFC0,D2           ;REMOVE "SHIFT MEMORY" BITS

         CMP.W     #$0040,TLENGTH(A1)
         BNE.S     ER2                 ;NOT .WORD                     1,2

         BSR       EAM
         OR.W      D6,D2
         BRA       CMMD2
 
MSCC     BSR       SIZEBYTE            ;(INDEX 29) NBCD SCC TAS

         BSR       EADA                ;DATA ALTERABLE ONLY
         OR.W      D6,D2
         BRA       CMMD2
 
MBCHG    DS        0                   ;(9)
         CMP.B     #'#',(A5)
         BNE.S     MB200

         MOVE.W    #$0840,D2           ;NEW OP-CODE MASK

MB100    ADD.L     #1,A5
         BSR       EV                  ;EVALUATE EXPRESSION
         CMP.L     #33,D0
         BGT.S     ER2                 ;(MODULO 32)                   1,2
         MOVE.W    D0,TDATA+2(A1)
         ADD.L     #2,D3               ;STORE POINTER

         ADD.B     #2,TNB(A1)          ;.                             1,2

MB105    BSR       COMMA               ;.                             1,2

         BSR       EADA                ;DESTINATION
         OR.W      D6,D2

         TST.B     TLSPEC(A1)          ;..                            1,2
         BEQ.S     MB185               ;DEFAULT                       1,2

         AND.W     #$0038,D6           ;.                             1,2
         BNE.S     MB145               ;DESTINATION <EA> WAS NOT D@   1,2

         CMP.W     #$80,TLENGTH(A1)    ;DESTINATION <EA> WAS D@       1,2
         BEQ.S     MB185               ;LENGTH IS .L                  1,2
ER2      BRA       ER                  ;.                             1,2

MB145    TST.W     TLENGTH(A1)         ;.                             1,2
         BNE       ER2                 ;NOT BYTE LENGTH               1,2

MB185    BRA       CMMD2       ;        .                             1,2

MB200    BSR       GETREGD             ;DYNAMIC
         ROR.W     #7,D0
         OR.W      D0,D2

         BRA       MB105               ;.                             1,2

MBSET    CMP.B     #'#',(A5)           ;(INDEX 11) BCLR BSET
         BNE       MB200

         MOVE.W    #$08C0,D2
         BRA       MB100

MBCLR    CMP.B     #'#',(A5)           ;(INDEX 30)
         BNE       MB200

         MOVE.W    #$0880,D2
         BRA       MB100

MBTST    CMP.B     #'#',(A5)           ;(INDEX 31)
         BNE       MB200

         MOVE.W    #$0800,D2
         BRA       MB100
 
MDBCC    DS        0                   ;(INDEX 8)
         BSR       GETREGD
         OR.W      D0,D2

         BSR       COMMA
         BSR.S     EVSR
         BRA.S     MBRA23

;*  SIZE   .S  =  .W   (DEFAULT)
;*         .L  =  .L
MBRA     DS        0                   ;(INDEX 10)
         BSR.S     EVSR

         CMP.W     #$0080,TLENGTH(A1)
         BEQ.S     MBRA23              ;FORCED LONG

         BSR       EA8BITS             ;-128 TO +127
         BNE.S     MBRA23              ;NOT 8 BIT VALUE

         OR.B      D5,D2
         BRA       CMMD2               ;.SHORT

EVER     BRA       ER                  ;ERROR HANDLER                 1,1

MBRA23   TST.B     TLSPEC(A1)
         BEQ.S     MBRA27
         CMP.W     #$0040,TLENGTH(A1)
         BEQ       EVER                ;.S SPECIFIED                  1,1
MBRA27

         MOVE.L    D4,D5               ;RESTORE D5
         BSR       EA16BITS            ;-32K TO +32K
         MOVE.W    D5,TDATA+2(A1)
         ADD.B     #2,TNB(A1)
         BRA       CMMD2

EVSR     BSR       EV
         CMP.B     #' ',(A5)           ;.                             1,1
         BNE       EVER                ;DID NOT TERMINATE WITH SPACE  1,1

         MOVE.L    D0,D5
         ASR.L     #1,D0
         BCS       EVER                ;ODD VALUE                     1,1
         MOVE.L    PCOUNTER(A1),D4
         ADD.L     #2,D4               ;D4 = PC + 2
         SUB.L     D4,D5
         BEQ       EVER                ;ZERO; SPECIAL CASE ERROR      1,1
         MOVE.L    D5,D4
         RTS
 
MCHK     DS        0                   ;(INDEX 12) CHK DIV MUL
         BSR       SIZEWORD

         BSR       EADADDR             ;DATA ADDRESSING ONLY
         OR.W      D6,D2

         BSR       COMMA

         BSR       GETREGD
         ROR.W     #7,D0
         OR.W      D0,D2

         BRA       CMMD2

MCLR     DS        0                   ;(INDEX 13)
         BSR       FSIZE

         BSR       EADA                ;DATA ALTERABLE ONLY
         OR.W      D6,D2
         BRA       CMMD2

;* SIZE = BYTE, WORD, LONG
MCMPM    DS        0                   ;(INDEX 14)
         BSR       FSIZE

         MOVE.W    #$0008,D7
         BSR       EA                  ;-(A@)   ONLY
         AND.W     #7,D6
         OR.W      D6,D2

         BSR       COMMA

         MOVE.W    #$0008,D7
         BSR       EA
         AND.W     #7,D6
         ROR.W     #7,D6
         OR.W      D6,D2
         BRA       CMMD2
 
MEXG     DS        0                   ;(INDEX 16)
         BSR       SIZELONG

         BSR       GETREGAD
         MOVE.L    D0,D4               ;D4 = REG NUMBER
         MOVE.L    D1,D5               ;D5 = REG TYPE

         BSR       COMMA               ;TEST FOR COMMA

         BSR       GETREGAD

         CMP.L     D1,D5
         BEQ.S     MEXG35              ;BOTH REGS THE SAME

;*  DX,AY  OR  AY,DX
         OR.W      #$88,D2             ;MODE
         TST.B     D1
         BNE.S     MEXG25

         EXG.L     D0,D4               ;SWAP SOURCE & DESTINATION

MEXG25   OR.W      D0,D2               ;.......MMMMMYYY
         ROR.W     #7,D4
         OR.W      D4,D2               ;....XXXMMMMMYYY
         BRA       CMMD2

MEXG35   OR.W      #$0040,D2           ;OP-MODE
         TST.B     D1
         BEQ       MEXG25              ;DX,DY

         OR.W      #$0048,D2           ;AX,AY
         BRA       MEXG25

  
MEXT     DS        0                   ;(INDEX 17)
         TST.W     TLENGTH(A1)
         BEQ       ER                  ;BYTE SIZE NOT ALLOWED

         BSR       FSIZE               ;.W = ........10......
         ADD.W     #$0040,D2           ;.L = ........11......

         BSR       GETREGD
         OR.W      D0,D2
         BRA       CMMD2
 
MMOVEM   DS        0                   ;(INDEX 27)
         MOVE.W    TLENGTH(A1),D0      ;SIZE BITS  76 TO 6
         BEQ       ER                  ;BYTE       00  ERROR
         LSR.W     #1,D0               ;WORD       01    0
         AND.W     #$0040,D0           ;LONG       10    1
         OR.W      D0,D2

         ADD.B     #2,TNB(A1)          ;NUMBER OF BYTES
         ADD.L     #2,D3               ;FORCE STORE PTR PAST MASK

         CMP.B     #'A',(A5)
         BEQ.S     MMM44
         CMP.B     #'D',(A5)
         BEQ.S     MMM44

;*    <EA>,<REGISTER LIST>              MEMORY TO REGISTER
         OR.W      #$0400,D2           ;DIRECTION BIT

         MOVE.W    #$7EC,D7            ;MODES ALLOWED                 1,1
         BSR       EA
         OR.W      D6,D2

         BSR       COMMA

         BSR.S     MMM48               ;.                             1,2
         BRA       CMMD2               ;.                             1,2


;*   <REGISTER LIST>,<EA>               ;REGISTER TO MEMORY
MMM44    DS        0

;* EVALUATE DESTINATION FIRST
MMM46    BSR       GETCHAR
         CMP.B     #',',D0             ;FIND COMMA
         BNE       MMM46

         MOVE.W    #$1F4,D7            ;MODES ALLOWED                 1,1
         BSR       EA
         OR.W      D6,D2
         MOVE.L    A5,PENDOP(A1)       ;END OF OPERAND                1,2
         MOVE.L    PTROP(A1),A5
         BSR.S     MMM48               ;EVALUATE REGISTERS            1,2
         MOVE.L    PENDOP(A1),A5       ;POINTER TO END OF OPERAND     1,2
         BRA       CMMD2               ;.                             1,2
    
;*        D6 = CORRESPONDENCE MASK
;*        D4 = CONTROL  $FF '-' '/'
MMM48    CLR.L     D6                  ;MASK                          1,2
         MOVE.L    #-1,D4              ;CONTROL = $FF

RL111    BSR       GETCHAR
         CMP.B     #',',D0
         BEQ.S     RL114               ;DONE; FOUND COMMA             1,2
         CMP.B     #' ',D0             ;.;                             1,2
         BNE.S     RL115               ;NOT SPACE                     1,2
RL114    RTS       ;DONE                ;.                             1,2

RL115    CMP.B     #'/',D0             ;.                             1,2
         BNE.S     RL444

         TST.B     D4                  ;CONTROL
         BMI       ER
         MOVE.L    D0,D4               ;CONTROL = '/'
RL333    BSR       GETREGAD
         OR.B      D0,D1               ;D1 = BIT POSITION
         MOVE.B    D1,D5               ;D5 = LAST REGISTER ENTERED
         BSR.S     SETBIT
         BRA       RL111

RL444    CMP.B     #'-',D0
         BNE.S     RL666

         CMP.B     #'/',D4             ;CONTROL
         BNE       ER
         MOVE.L    D0,D4               ;CONTROL = '-'
         BSR       GETREGAD
         OR.B      D0,D1
         MOVE.L    D1,D7               ;D7 = NOW REGISTER
         MOVE.B    D5,D0               ;D5 = LAST REG
BREAK
         EOR.B     D1,D0
         AND.B     #$38,D0
         BNE       ER                  ;NOT MATCED SET
         CMP.B     D1,D5
         BPL       ER

RL555    ADD.L     #1,D5
         MOVE.L    D5,D1
         BSR.S     SETBIT
         CMP.B     D7,D5
         BMI       RL555
         BRA       RL111

RL666    TST.B     D4
         BPL       ER
         MOVE.B    #'/',D4             ;CONTROL = '/'
         SUB.L     #1,A5
         BRA       RL333
 
SETBIT   LEA       MTBL(PC),A0         ;SET BIT IN CORRESPONDENCE MASK
         MOVE.L    D2,D0
         AND.W     #$38,D0
         CMP.W     #$20,D0
         BNE.S     RL30                ;NOT PREDECREMENT
         MOVE.B    (A0,D1),D1          ;D1 = BIT  (FOR SURE)
RL30     BSET      D1,D6

         MOVE.W    D6,TDATA+2(A1)      ;SAVE CORRESPONDENCE MASK
         RTS

MTBL     DC.B      15,14,13,12,11,10,9,8,7,6,5,4,3,2,1,0
 
;*   D@,<DATA>(A@)
;*   <DATA>(A@),D@
;*         (A@),D@            FORCED TO 0(A@),D0
;*         D@,(A@)            FORCED TO D0,0(A@)
;*
;*  SIZE = WORD, LONG
MMOVEP   DS        0                   ;(INDEX 33)
         MOVE.W    TLENGTH(A1),D0
         BEQ       ER                  ;.BYTE NOT ALLOWED
         LSR.W     #1,D0
         AND.W     #$0040,D0
         OR.W      D0,D2               ;SIZE

         MOVE.W    #$25,D7
         BSR       EA                  ;D6 = MODE

         BSR       COMMA

         MOVE.L    D6,D0
         AND.W     #$38,D0
         CMP.B     #$0,D0
         BEQ.S     MMP344              ;D@,<DATA>(A@)

;*    <DATA>(A@),D@
         BSR       GETREGD
         ROR.W     #7,D0
         OR.W      D0,D2               ;D@
         BRA.S     MMP348

MMP344   OR.W      #$0080,D2           ;REGISTER TO MEMORY

         ROR.W     #7,D6
         OR.W      D6,D2               ;D@

         MOVE.W    #$24,D7
         BSR       EA
MMP348   MOVE.L    D6,D0
         AND.W     #7,D6
         OR.W      D6,D2               ;A@

         AND.W     #$38,D0
         CMP.B     #$10,D0
         BNE.S     MMP368              ;<DATA>(A@)

         CLR.W     TDATA+2(A1)      ;<DATA> FORCED TO ZERO;  "(A@)"
         ADD.B     #2,TNB(A1)        ;  NUMBER OF BYTES
         ADD.L     #2,D3             ;  STORE POINTER
MMP368   BRA CMMD2
 
MMOVEQ   DS        0                  ; (INDEX 34)
         BSR       GETIMM
         MOVE.L    D0,D5

         BSR       EA8BITS            ; -128 TO +127
         BNE       ER
         OR.B      D5,D2              ; D5 = VALUE

         BSR       COMMA

         BSR       GETREGD            ; D@
         ROR.W     #7,D0

MMQ20    OR.W      D0,D2
         BSR.S     SIZELONG
         BRA       CMMD2

SIZELONG TST.B     TLSPEC(A1)          ;MUST BE .LONG
         BEQ.S     SI201               ;DEFAULT SIZE OK
         CMP.W     #$0080,TLENGTH(A1)
         BNE.S     ER10                ;NOT .LONG
SI201    RTS

SIZEWORD CMP.W     #$0040,TLENGTH(A1)  ;MUST BE .WORD
         BEQ       SI201    ; [RTS]
ER10     BRA       ER

SIZEBYTE TST.B     TLSPEC(A1)
         BEQ.S     SI222               ;DEFAULT SIZE OK
         TST.W     TLENGTH(A1)
         BNE       ER10
SI222    RTS
 
MMOVE    DS        0                   ;(INDEX 21)
         CMP.B     #'S',(A5)
         BNE.S     MM40
         MOVE.W    #$40C0,D2          ; SR,<EA>
         ADD.L     #1,A5
         CMP.B     #'R',(A5)+
         BNE       ER10

         BSR       COMMA

         BSR       EADA                ;DATA ALTERABLE ONLY (DESTINATION)

MM315    OR.W      D6,D2
         BSR       SIZEWORD
         BRA       CMMD2

MM40     CMP.B     #'U',(A5)
         BNE.S     MM50
         ADD.L     #1,A5
         CMP.B     #'S',(A5)+
         BNE       ER10
         CMP.B     #'P',(A5)+
         BNE       ER10

         BSR       COMMA

         MOVE.W    #$4E68,D2           ;USP,A@
         BSR       GETREGA
         BRA       MMQ20

;* GET EXCEPTIONS FROM DESTINATION
MM50     DS        0

         BSR       A5TODEST            ;MOVE A5 TO DESTINATION

         MOVE.B    (A5)+,D0
         CMP.B     #'C',D0
         BNE.S     MM60
         CMP.B     #'C',(A5)+
         BNE       ER10
         CMP.B     #'R',(A5)+
         BNE       ER10
         MOVE.W    #$44C0,D2           ;<EA>,CCR

MM508    MOVE.L    A5,PENDOP(A1)       ;SAVE POINTER                  1,2
         MOVE.L    PTROP(A1),A5        ;A5 = POINTER TO OPERAND

         BSR       EADADDR    ;DATA ADDRESSING ONLY (SOURCE)
         MOVE.L    PENDOP(A1),A5       ;.                             1,2
         BRA       MM315

MM60     CMP.B     #'S',D0
         BNE.S     MM70
         MOVE.W    #$46C0,D2           ;<EA>,SR
         CMP.B     #'R',(A5)+
         BNE       ER
         BRA       MM508

MM70     CMP.B     #'U',D0
         BNE.S     MM80
         MOVE.W    #$4E60,D2           ;A@,USP
         CMP.B     #'S',(A5)+
         BNE       ER
         CMP.B     #'P',(A5)+
         BNE       ER

         MOVE.L    A5,PENDOP(A1)       ;.                             1,2
         MOVE.L    PTROP(A1),A5
         BSR       GETREGA
         MOVE.L    PENDOP(A1),A5       ;RESTORE A5                    1,2
         BRA       MMQ20

MM80     MOVE.L    PTROP(A1),A5        ;A5 = POINTER TO SOURCE FIELD
         BSR       FSIZE               ;GET SIZE (BITS  7 - 6)
         LSL.W     #6,D2               ;ADJUST TO(BITS 13-12)
         BTST      #13,D2
         BNE.S     MM804               ;.L 10 TO 10
         ADD.W     #$1000,D2           ;.W 01 TO 11
         OR.W      #$1000,D2           ;.B 00 TO 01
MM804    BSR       EAALL               ;SOURCE; ALL MODES ALLOWED
         OR.W      D6,D2

;* IF BITE SIZE; "ADDRESS REGISTER DIRECT" NOT ALLOWED
         MOVE.L    D2,D0
         AND.W     #$3000,D0
         CMP.W     #$1000,D0           ;.                             1,2
         BNE.S     MM806               ;NOT .B SIZE
         AND.B     #$38,D6             ;.                             1,2
         CMP.B     #$08,D6
         BEQ       ER
MM806    DS        0

         BSR       COMMA

         MOVE.W    #$1FF,D7            ;DATA ALTERABLE + A@
         BSR       EA


         MOVE.L    D6,D0               ;DESTINATION
         AND.W     #$0038,D0
         CMP.W     #$0008,D0
         BEQ.S     MMOVEA1             ;A@ MAKE MOVEA

;* POSITION REGISTER AND MODE OF DESTINATION
MM825    ROR.L     #3,D6               ;RRR............. .............MMM
         ROR.W     #3,D6               ;                 MMM.............
         SWAP      D6                  ;MMM............. RRR.............
         ROL.W     #3,D6               ;                 .............RRR
         ROL.L     #1,D6               ;MM.............. ............RRRM
         ROL.L     #8,D6               ;................ ....RRRMMM......
         OR.W      D6,D2
         BRA       CMMD2
 
MMOVEA1  CLR.L     D3
         MOVE.B    #2,TNB(A1)

MMOVEA   DS        0                   ;(INDEX 32)
         MOVE.L    PTROP(A1),A5        ;A5 = POINTER TO OPERAND

         MOVE.W    TLENGTH(A1),D2      ;D0 = SIZE                     1,2
         BEQ       ER                  ;.BYTE NOT ALLOWED

         LSL.W     #6,D2               ;.SIZE                         1,2
         BTST      #12,D2              ;.                             1,2
         BEQ.S     MMA225              ;.L = ..10                     1,2
         OR.W      #$3000,D2           ;.W = ..11                     1,2
MMA225

         BSR       EAALL               ;ALL MODES ALLOWED
         OR.W      D6,D2

         BSR       COMMA

         MOVE.W    #$0002,D7           ;A@ ONLY
         BSR       EA
         BRA       MM825

 
MJMP     DS        0                   ;(INDEX 18)
         TST.B     TLSPEC(A1)          ;.                             1,1
         BEQ.S     MJMP32              ;DEFAULT (ALLOW EITHER .S OR .L) 1,1
         MOVE.W    TLENGTH(A1),D0      ;.                             1,1
         BEQ       ER                  ;.B NOT ALLOWED                1,1
         MOVE.W    #$6E4,D7            ;D7 = MODES ALLOWED            1,1
         CMP.W     #$40,D0             ;.                             1,1
         BEQ.S     MJMP22              ;.S SPECIFIED (.W ACCEPTED)    1,1
         MOVE.W    #$8764,D7           ;MODE FOR .L                   1,1
MJMP22   BSR       EA                  ;.                             1,1
         BRA.S     MJMP42              ;.                             1,1

MJMP32   BSR       EAC                 ;CONTROL ADDRESSING ONLY       1,1
MJMP42   OR.W      D6,D2               ;.                             1,1
         BRA       CMMD2

;* SIZE = LONG
MLEA     DS        0                   ;(INDEX 19)
         BSR       SIZELONG

         BSR       EAC    ;   CONTROL ADDRESSING ONLY
         OR.W      D6,D2

         BSR       COMMA

         BSR       GETREGA
         ROR.W     #7,D0
         OR.W      D0,D2
         BRA       CMMD2

 
;* SIZE = LONG
MPEA     DS        0                   ;(INDEX 36)
         BSR       SIZELONG

         BSR       EAC      ; CONTROL ADDRESSING ONLY
         OR.W      D6,D2
         BRA       CMMD2

MSWAP    DS        0                   ;(INDEX 24)
;* SIZE WORD
         CMP.W     #$0040,TLENGTH(A1)
         BNE       ER                  ;NOT .W

         BSR       GETREGD             ;D@ ONLY
         OR.W      D0,D2
         BRA       CMMD2
 
GETIMM   CMP.B     #'#',(A5)+
         BNE       ER

         BSR       EV                  ;EVALUATE EXPRESSION
         RTS                           ;D0 = VALUE

MLINK    BSR       GETREGA             ;(INDEX 20)
         OR.W      D0,D2

         BSR       COMMA

         BSR       GETIMM
         MOVE.L    D0,D5
         BSR       EA16BITS            ;-32K TO +32K
         MOVE.W    D0,TDATA+2(A1)

         ADD.B     #2,TNB(A1)
         BRA       CMMD2

MSTOP    DS        0                   ;(INDEX 23)
;* UNSIZED
         BSR       GETIMM
         CMP.L     #$00010000,D0
         BCC       ER
         MOVE.W    D0,TDATA+2(A1)
         ADD.B     #2,TNB(A1)
         BRA       CMMD2

MTRAP    DS        0                   ;(INDEX 25)
         BSR       GETIMM
         CMP.L     #16,D0
         BCC       ER
         OR.W      D0,D2
         BRA       CMMD2
 
MUNLK    DS        0                   ;(INDEX 26)
;* UNSIZED
         BSR       GETREGA
         OR.W      D0,D2
         BRA       CMMD2
		 
MDC      DS        0                   ;(INDEX 37) .W ONLY ALLOWED
         BSR       EV
         MOVE.L    D0,D5
         BSR       EA16BIT             ;ONLY .W ALLOWED     -32K TO +64K
         MOVE.W    D5,D2
         BRA       CMMD2
		 
		 ORG	 0
ESKB     DS        0
TDATA    DS.B      10
TNB      DS.B      1
TLSPEC   DS.B      1
TLENGTH  DS.W      1
PCOUNTER DS.L      1
PTROP    DS.L      1                   ;POINTER TO OPERAND
PENDOP   DS.L      1                   ;POINTER END OF OPERAND
PTRBUFE  DS.L      1                   ;POINTER TO END OF FORMATED SOURCE
LINK     DS.L      1                   ;SAVE FOR UNLINK
ESKE     DS.B      0
	
	ENDSECTION AS
	