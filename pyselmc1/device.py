import serial
from time import time


class Device:
    """Linear-guide device."""
    default_timeout = 5
    default_retry_attempts = 3  # Total number of retry attempts on timeout
    homing_velocity = 0.1  # Fixed HW setting

    def __init__(self, comport, rail_length, steps_per_meter, device_id=0):
        """Open connection to a device via comport."""
        # Initialize serial device
        self.serial_device = serial.Serial(
            comport,
            baudrate=19200,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            timeout=0.2
        )

        self.rail_length = rail_length
        self.steps_per_meter = steps_per_meter
        self.device_id = device_id
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
    
    def close(self):
        """Close connection to the device."""
        self.serial_device.close()

    def send_string(self, string):
        """Send string to device."""
        self.serial_device.write((string+'\r').encode('ascii'))
        
    def send_char(self, char_no):
        """Send character to device."""
        self.serial_device.write(char_no.to_bytes(1, 'big'))
  
    def receive_string(self):
        """Receive string from device."""
        return self.serial_device.readline().decode('ascii').rstrip()
    
    def send_dnc_cmd(self, cmd, arg, blocking=True, timeout=None, retry_attempts=0):
        """Send DNC command to device."""
        # Send DNC command
        string = '@%.d' % self.device_id + cmd + arg
        self.send_string(string)
        
        # Handle blocking commands
        if blocking:
            try:
                # Wait for acknowledgement
                return self.wait_for_ack(timeout)
            except TimeoutError:
                # Retry due to timeout
                if retry_attempts > 0:
                    return self.send_dnc_cmd(cmd, arg, blocking, timeout, retry_attempts-1)
                else:
                    raise ConnectionError('Maximum number of retries due to timeouts exceeded!')
    
    def wait_for_ack(self, timeout=None):
        """Wait for acknowledgement."""
        time0 = time()
        while True:
            rec = self.receive_string()
            
            if (timeout is not None) & (time() >= time0+timeout):
                # Error: timeout
                raise TimeoutError('Timeout occured while waiting for acknowledgement!')
            elif rec == '':
                # Serial timout
                pass
            elif rec[0] == '0':
                # Ack OK
                return rec[1:]  # Return value
            else:
                # Error: MC1 error code rec[0:1]
                raise Exception('MC1 error code: %s!' % rec[0])

    def init(self, blocking=True):
        """Initialize axis."""
        self.send_dnc_cmd('1', '0', blocking, self.default_timeout, self.default_retry_attempts)

    def move_relative(self, distance, velocity, blocking=True):
        """Move axis relatively."""
        timeout = self.default_timeout + abs(distance)/velocity
        
        distance_stp = round(distance*self.steps_per_meter)
        velocity_stp = round(velocity*self.steps_per_meter)
        arg = '%d,%d' % (distance_stp, velocity_stp)
    
        self.send_dnc_cmd('a', arg, blocking, timeout, 0)

    def read_port(self, n_port):
        """Read port."""
        value = self.send_dnc_cmd('b', str(n_port), True, self.default_timeout, self.default_retry_attempts)
        return value
    
    def write_port(self, n_port, value, blocking=True):
        """Write port."""
        arg = '%d,%d' % (n_port, value)
        self.send_dnc_cmd('B', arg, blocking, self.default_timeout, self.default_retry_attempts)
  
    def release(self, blocking=True, timeout=10):
        """Release axis if it is stuck."""
        self.send_dnc_cmd('F', '1', blocking, timeout, self.default_retry_attempts)
    
    def save_cnc_data(self, blocking=True):
        """Save CNC program."""
        self.send_dnc_cmd('i', '', blocking, self.default_timeout, self.default_retry_attempts)
  
    def flush_cnc_data(self, blocking=True):
        """Flush CNC data."""
        self.send_dnc_cmd('k', '', blocking, self.default_timeout, self.default_retry_attempts)
  
    def clear_display_row(self, n_row, blocking=True):
        """Clear display row."""
        self.send_dnc_cmd('l', str(n_row), blocking, self.default_timeout, self.default_retry_attempts)
  
    def print_to_display(self, n_row, n_column, text, blocking=True):
        """Print text to display."""
        arg = '%d,%d,%s' % (n_row, n_column, text)
        self.send_dnc_cmd('L', arg, blocking, self.default_timeout, self.default_retry_attempts)
    
    def move_absolute(self, position, velocity, blocking=True):
        """Move axis to an absolute position."""
        position0 = self.get_pos()
        timeout = self.default_timeout + abs(position-position0) / velocity
        
        position_stp = round(position * self.steps_per_meter)
        velocity_stp = round(velocity * self.steps_per_meter)
        arg = '%d,%d' % (position_stp, velocity_stp)
    
        self.send_dnc_cmd('M', arg, blocking, timeout, self.default_retry_attempts)
    
    def simulate_homing(self, blocking=True):
        """Simulate homing."""
        self.send_dnc_cmd('N', '1', blocking, self.default_timeout, self.default_retry_attempts)
  
    def get_pos(self):
        """Get axis position."""
        ret_string = self.send_dnc_cmd('P', '', True, self.default_timeout, self.default_retry_attempts)
        
        # Hex two's complement to Int
        pos_stp = int(ret_string, 16)
        if pos_stp >= 1 << len(ret_string) * 4:
            pos_stp -= 1 << len(ret_string) * 4
            
        pos = pos_stp / self.steps_per_meter
        return pos
  
    def homing(self, blocking=True):
        """Do homing."""
        # Worst case timeout
        timeout = self.default_timeout + self.rail_length / self.homing_velocity
        
        self.send_dnc_cmd('r', '1', blocking, timeout, self.default_retry_attempts)
    
    def cmd_start(self, blocking=True):
        """Start CNC program or motion."""
        self.send_dnc_cmd('s', '', blocking, self.default_timeout, self.default_retry_attempts)
  
    def test_mode(self, state, blocking=True):
        """Enable/disable test mode."""
        arg = {True: '1', False: '0'}[state]
        self.send_dnc_cmd('T', arg, blocking, self.default_timeout, self.default_retry_attempts)
    
    def get_version_info(self):
        """Get version info."""
        vers = self.send_dnc_cmd('V', '', True, self.default_timeout, self.default_retry_attempts)
        return vers

    def cmd_stop(self):
        """Stop motion immediately."""
        self.send_char(253)
    
    def cmd_reset(self):
        """Stop motion immediately and reset internal state."""
        self.send_char(254)
    
    def cmd_break(self):
        """Break motion immediately."""
        self.send_char(255)
