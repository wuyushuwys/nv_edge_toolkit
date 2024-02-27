# Nvidia Edge Device Toolkit

NVIDIA Edge Device Control Toolkit
- Python toolkit to control Nvidia Edge devices
  -  Tested on TX2, Orin Nano
- **Current socket communication might not be efficient.**

## Installation
`pip install git+https://github.com/wuyushuwys/nv_edge_toolkit.git`

## Example

```python
# example.py
from device_toolkit import OrinNanoController
controller = OrinNanoController(name='orin', verbose=False)

# retrive controller specs
# You can retrieve them by component
print(controller.FAN.specs)
print(controller.CPU.specs)
print(controller.GPU.specs)
# or retrieve them by together
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
`sudo python examples/example.py` # Using **sudo** for the best efficiency in W/R
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
 - [PowerMonitor](https://docs.nvidia.com/jetson/archives/r35.4.1/DeveloperGuide/text/SD/PlatformPowerAndPerformance/JetsonOrinNanoSeriesJetsonOrinNxSeriesAndJetsonAgxOrinSeries.html#software-based-power-consumption-modeling)
   - VDD_IN (r)
   - VDD_CPU_GPU_CV (r)
   - VDD_SOC (r)

## Functions
  - cooldown(temp_bound: int): `cooldown the device until reach [temp_bound]`

### Notice
 - `sudo` for best efficiency
