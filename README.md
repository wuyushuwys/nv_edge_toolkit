# Device Toolkit

NVIDIA Jetson Control Toolkit

## Installation
`pip install git+https://github.com/wuyushuwys/DeviceToolkit.git`

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
