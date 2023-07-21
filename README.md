# Device Toolkit

NVIDIA Jetson Control Toolkit

## Installation
`pip install git+https://github.com/wuyushuwys/DeviceToolkit.git`

## Example

```python
# example.py
from device_toolkit import OrinNanoController
controller = OrinNanoController(name='orin', verbose=False)

# retrive controller specs
# You can retrive them by component
print(controller.FAN.specs)
print(controller.CPU.specs)
print(controller.GPU.specs)
# or retrive them by together
print(controller.specs)

# Set fan pwm (we say speed here) to 0
controller.FAN.speed = 0

# Set cpu governor to userspace
controller.CPU.governor = 'userspace'

# Set gpu governor to userspace
controller.GPU.governor = 'userspace'

# Reset controller to default
controller.reset()
```
`sudo python examples/example.py` # Using **sudo** for the best efficieny in W/R
## Dependencies
 - python3>=3.8
 - sh

## Support Devices
 - Jetson TX2
 - Jetson Orin nano

## Support Components
 - FAN
   - pwm (rw)
   - rpm (r)
   - temperature (r)
 - CPU
   - online (rw)
   - frequency (rw)
   - governor (rw)
   - temperature (r)
 - GPU
   - frequency (rw)
   - governor (rw)
   - temperature (r)

### Notice
 - `sudo` for best efficiency
