import pyselmc1


if __name__ == '__main__':
    comport = 'COM2'
    rail_length = 5.23
    steps_per_meter = 1000000

    with pyselmc1.Device(comport, rail_length, steps_per_meter) as device:
        device.print_to_display(1, 1, 'Hello World!')
        device.init()
        device.write_port(0, 0)  # Reset port 0
        device.homing()
        for pos in [0.5, 1, 1.5, 2]:
            device.move_absolute(pos, 0.4)  # Blocking
        device.write_port(0, 1 << 0)  # Set port 0, pin 0
