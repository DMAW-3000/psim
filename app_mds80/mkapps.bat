rem del cstat.hex
rem del madiag.hex
del msbasic.hex

rem python ..\..\pyplm\pyplm.py -o -e extern_cpm.asm -s STATUS cstat.plm cstat.asm
rem ..\..\asw\bin\asw -g -cpu 8080 cstat.asm
rem ..\..\asw\bin\p2hex -F Intel cstat.p

rem ..\..\asw\bin\asw -g -cpu 8080 madiag.asm
rem ..\..\asw\bin\p2hex -F Intel madiag.p

..\..\asw\bin\asw -g -cpu 8080 msbasic.asm
..\..\asw\bin\p2hex -F Intel msbasic.p
