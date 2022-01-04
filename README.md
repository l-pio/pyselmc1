# pySelMC1
An unofficial Python package to operate linear guides from Isel, e.g., Isel iLD 50 using an **Isel MC1** single-axis
motor controller via comport.

## Installation
Please simply copy the package directory to your workspace, and install the requirements by running:
```
$ pip install -r requirements.txt
```

## Usage
Supported commands:
```
# DNC commands
init(self, blocking=True)
move_relative(distance, velocity, blocking=True)
move_absolute(position, velocity, blocking=True)
get_pos()
read_port(n_port)
write_port(n_port, value, blocking=True)
release(blocking=True, timeout=10)
save_cnc_data(blocking=True)
flush_cnc_data(blocking=True)
clear_display_row(n_row, blocking=True)
print_to_display(n_row, n_column, text, blocking=True)
homing(blocking=True)
simulate_homing(blocking=True)
test_mode(state, blocking=True):    
get_version_info()
cmd_start(blocking=True)

# CNC commands: not implemented yet

# Control codes for immediate access to motor controller
cmd_stop()
cmd_reset()
cmd_break()
```
Minimum working example:
```
comport = 'COMx'  # Replace x by comport number
rail_length = 5.23
steps_per_meter = 1000000
with pyselmc1.Device(comport, rail_length, steps_per_meter) as device:
    device.init()
    device.homing()  # Blocking
    device.move_absolute(2, 0.4)  # Blocking
```
Another example can be found [here](./example.py).