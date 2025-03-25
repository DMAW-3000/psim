python ..\..\pyplm\pyplm.py -o -t mon -e extern_mon.asm -s PLMTEST ptest.plm ptest.asm
..\..\asw\bin\asw -g -cpu 8080 ptest.asm
..\..\asw\bin\p2hex -F Intel ptest.p
copy ptest.hex tapein.txt


