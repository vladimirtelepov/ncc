#!/bin/bash

# this script run binary in ida and shows predicted labels for decompiled functions
# works only on linux, please read README before run
# please replace path to programs below
# dont run this script in directory which contain folder tmp with your files
ida_path="/home/vladimir/.wine/drive_c/Program Files/IDA 7.2/idat64.exe"
llvm_dis="llvm-dis-6.0"
mcsema_lift="mcsema-lift-4.0"
app="/home/vladimir/programming/ncc"

cfg_out="$1.cfg"
cfg_log="$1.log"
bc_out="$1.bc"
ll_out="$1.ll"

startdir=$PWD
wine "$ida_path" -B -S"get_cfg.py --output $cfg_out --log_file $cfg_log --arch amd64 --os linux --entrypoint main" $1
mcsemaliftcmd="$mcsema_lift --output $bc_out --arch amd64 --os linux --cfg $cfg_out"
$mcsemaliftcmd
discmd="$llvm_dis $bc_out -o $ll_out"
$discmd
mkdir tmp
python3 get_functions.py $ll_out
cp tmp/* "$app/inference/ir_test"
rm -r "$app/inference/seq_test/" 2> /dev/null
cd $app
appcmd="python3 train_task_classifyapp.py --inference True --input_file $1"
$appcmd
rm -r "$app/inference/seq_test/" 2> /dev/null
rm $app/inference/ir_test/*
rm $app/inference/ir_test/.* 2> /dev/null
cd $startdir
rm $bc_out
rm $cfg_log
rm $cfg_out
rm $ll_out
rm -r tmp 2> /dev/null