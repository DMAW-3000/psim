rem del cstat.hex
rem del madiag.hex
del msbasic.hex

python ..\..\pyplm\pyplm.py -o -e extern_cpm.asm -s STATUS cstat.plm cstat.asm
..\..\asw\bin\asw -g -cpu 8080 cstat.asm
..\..\asw\bin\p2hex -F Intel cstat.p

..\..\asw\bin\asw -g -cpu 8080 madiag.asm
..\..\asw\bin\p2hex -F Intel madiag.p

rem ..\..\asw\bin\asw -g -cpu 8080 msbasic.asm
rem ..\..\asw\bin\p2hex -F Intel msbasic.p
