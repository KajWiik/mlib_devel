
rem Clean up the results directory
if exist results rmdir /S /Q results
mkdir results

rem Synthesize the VHDL Wrapper Files
echo 'Synthesizing vhdl sample design with XST';
xst -ifn xst.scr
copy ten_gig_eth_mac_v8_0_example_design.ngc .\results\
rem Copy the netlists generated by Coregen
echo 'Copying files from the netlist directory to the results directory'
copy ..\..\ten_gig_eth_mac_v8_0.ngc .\results\

rem  Copy the constraints files generated by Coregen
echo 'Copying files from constraints directory to results directory'
copy ..\example_design\ten_gig_eth_mac_v8_0_example_design.ucf .\results\

cd results

echo 'Running ngdbuild'
ngdbuild ten_gig_eth_mac_v8_0_example_design

echo 'Running map'
map ten_gig_eth_mac_v8_0_example_design -o mapped.ncd

echo 'Running par'
par -n 0 -s 1 -ol high -w mapped.ncd routed.dir mapped.pcf
copy /B routed.dir\*.ncd routed.ncd

echo 'Running trce'
trce -e 10 routed -o routed mapped.pcf

echo 'Running bitgen'
bitgen -w routed

echo 'Running netgen to create gate level VHDL model'
netgen -ofmt vhdl -sim -dir . -tm ten_gig_eth_mac_v8_0_example_design -w routed.ncd routed.vhd