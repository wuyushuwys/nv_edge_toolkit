import sh
import os
from sh import bash
from enum import Enum

from .utils import (set_logging,
                   PASSWORD,
                   decode,
                   Device_Specs,
                   CPU_Specs,
                   GPU_Specs,
                   FAN_Specs,
                   parse_specs)

bash = sh.bash.bake('-c')

class COMPONENT(str, Enum):
    CPU='CPU'
    GPU='GPU'
    FAN='FAN'


class Component():

    def __init__(self, logger, root, num=1, sudo=False) -> None:
        self.root = root
        self.num = num
        self._sudo = sudo
        self.logger = logger
        self.thermal_root = '/sys/devices/virtual/thermal'

    @property
    def gov(self):
        pass

    @gov.setter
    def gov(self, gov):
        pass

    @property
    def freq(self):
        pass

    @freq.setter
    def freq(self, freq):
        pass

    @property
    def temp(self):
        pass


class CPU(Component):

    FREQ = [345600, 499200, 652800, 806400, 960000, 1113600, 1267200, 1420800, 1574400, 1728000, 1881600, 2035200]
    GOV = ["userspace", "schedutil"]

    def __init__(self, logger, root='/sys/devices/system/cpu', num=6, sudo=True) -> None:
        super(CPU, self).__init__(logger=logger, root=root, num=num, sudo=sudo)

    @property
    def specs(self):
        self.logger.info("Retrive CPU specs")
        return CPU_Specs(gov={k: v for k, v in self.gov.items()},
                         freq={k: v for k, v in self.freq.items()},
                         temp=self.temp
                         )._asdict()

    @property
    def gov(self):
        gov = {}
        for cpu_idx in range(self.num):
            if self._sudo:
                with open(f'{self.root}/cpu{cpu_idx}/cpufreq/scaling_governor', 'r') as f:
                    res = f.read().rstrip('\n')
                gov[str(cpu_idx)] = res
            else:
                res = sh.cat(f'{self.root}/cpu{cpu_idx}/cpufreq/scaling_governor')
                res = decode(res)
                gov[str(cpu_idx)] = res
        self.logger.debug(f"get CPU governors {gov}")
        return gov
    
    @gov.setter
    def gov(self, gov):
        self.logger.debug(f'set CPU governors {gov}')
        if isinstance(gov, str):
            gov = {i: gov for i in range(self.num)}
        elif isinstance(gov, dict):
            pass
        else:
            NotImplementedError(f"Expected input type Dict or Str, but got {type(gov)}")
        if self._sudo:
            for idx, v in gov.items():
                assert v in self.GOV, f"{v} for {idx} is not avaliable"
                with open(f"{self.root}/cpu{idx}/cpufreq/scaling_governor", 'w', ) as f:
                    f.write(v)
        else:
            with sh.contrib.sudo(password=PASSWORD, _with=True):
                for idx, v in gov.items():
                    assert v in self.GOV, f"{v} for {idx} is not avaliable"
                    bash(f"echo {v} > {self.root}/cpu{idx}/cpufreq/scaling_governor")

    @property
    def freq(self):
        freq = {}
        for cpu_idx in range(self.num):
            if self._sudo:
                with open(f'{self.root}/cpu{cpu_idx}/cpufreq/scaling_cur_freq', 'r') as f:
                    res = f.read().rstrip('\n')
                    freq[str(cpu_idx)] = eval(res)
            else:
                res = sh.cat(f'{self.root}/cpu{cpu_idx}/cpufreq/scaling_cur_freq')
                res = decode(res)
                freq[str(cpu_idx)] = eval(res.split()[0])
        self.logger.debug(f"get CPU frequencies {freq}")
        return freq

    @freq.setter
    def freq(self, freq):
        self.logger.debug(f'set CPU frequencies {freq}')
        if isinstance(freq, str) or isinstance(freq, int):
            freq = {i: freq for i in range(self.num)}
        elif isinstance(freq, dict):
            pass
        else:
            NotImplementedError(f"Expected input type Dict/Str/Int, but got {type(freq)}")
        if self._sudo:
            for idx, v in freq.items():
                with open(f'{self.root}/cpu{idx}/cpufreq/scaling_setspeed', 'w') as f:
                    f.write(f'{v}')
        else:
            with sh.contrib.sudo(password=PASSWORD, _with=True):
                for idx, v in freq.items():
                    assert v in self.FREQ, f"{v} for {idx} is not avaliable"
                    bash(f"echo {v} > {self.root}/cpu{idx}/cpufreq/scaling_setspeed")

    @property
    def temp(self):
        if self._sudo:
            with open(f'{self.thermal_root}/thermal_zone0/temp', 'r') as f:
                res = eval(f.read().rstrip('\n'))
        else:
            res = sh.cat(f'{self.thermal_root}/thermal_zone0/temp')
            res = eval(decode(res))
        self.logger.debug(f"get CPU temp {res}")
        return res


class GPU(Component):
        
    FREQ = [114750000,
        216750000,
        318750000,
        420750000,
        522750000,
        624750000,
        726750000,
        854250000,
        930750000,
        1032750000,
        1122000000,
        1236750000,
        1300500000]
    
    GOV = ["nvhost_podgov", "userspace"]

    def __init__(self, logger, root='/sys/devices/gpu.0/devfreq/17000000.gp10b', sudo=True) -> None:
        super(GPU, self).__init__(logger=logger, root=root, sudo=sudo)

    @property
    def specs(self):
        self.logger.info("Retrive GPU specs")
        return GPU_Specs(gov=self.gov,
                         freq=self.freq,
                         temp=self.temp
                         )._asdict()

    @property
    def gov(self):
        if self._sudo:
            with open(f'{self.root}/governor', 'r') as f:
                res = f.read().rstrip('\n')
        else:
            res = sh.cat(f'{self.root}/governor')
            res = decode(res)
        self.logger.debug(f"get GPU governor {res}")
        return res

    @gov.setter
    def gov(self, gov):
        self.logger.debug(f'set GPU governor {gov}')
        assert gov in self.GOV, f"{gov} is not avaliable"
        if self._sudo:
            with open(f'{self.root}/governor', 'w') as f:
                f.write(gov)
        else:
            with sh.contrib.sudo(password=PASSWORD, _with=True):
                bash(f"echo {gov} > {self.root}/governor")

    @property
    def freq(self):
        if self._sudo:
            with open(f'{self.root}/cur_freq', 'r') as f:
                res = eval(f.read().rstrip('\n'))
        else:
            res = sh.cat(f'{self.root}/cur_freq')
            res = decode(res)
        self.logger.debug(f"get GPU clock {res}")
        return res
    
    @freq.setter
    def freq(self, freq):
        assert freq in self.FREQ, f"{freq} is not avaliable"
        if self._sudo:
            with open(f'{self.root}/max_freq', 'w') as f:
                f.write(f'{freq}')
            self.logger.debug(f"Set gpu max_freq {freq}")
            with open(f'{self.root}/min_freq', 'w') as f:
                f.write(f'{freq}')
            self.logger.debug(f"Set gpu min_freq {freq}")
        else:
            with sh.contrib.sudo(password=PASSWORD, _with=True):
                bash(f"echo {freq} > {self.root}/max_freq")
                self.logger.debug(f"Set gpu max_freq {freq}")
                bash(f"echo {freq} > {self.root}/min_freq")
                self.logger.debug(f"Set gpu min_freq {freq}")
    
    @property
    def temp(self):
        if self._sudo:
            with open(f'{self.thermal_root}/thermal_zone2/temp', 'r') as f:
                res = eval(f.read().rstrip('\n'))
        else:
            res = sh.cat(f'{self.thermal_root}/thermal_zone2/temp')
            res = eval(decode(res))
        self.logger.debug(f"get GPU temp {res}")
        return res


class FAN(Component):

    def __init__(self, logger, root='/sys/devices/pwm-fan', sudo=True) -> None:
        super(FAN, self).__init__(logger=logger, root=root, sudo=sudo)

    @property
    def specs(self):
        self.logger.info("Retrive FAN specs")
        return FAN_Specs(speed=self.speed,
                         temp=self.temp,
                         )._asdict()
    
    @property
    def control(self):
        if self._sudo:
            with open(f'{self.root}/temp_control', 'r') as f:
                res = eval(f.read().rstrip('\n'))
        else:
            res = sh.cat(f'{self.thermal_root}/temp_control')
            res = eval(decode(res))
        self.logger.debug("get FAN temp control flag")

    @control.setter
    def control(self, flag):
        flag = flag if isinstance(flag, int) else int(flag)
        assert flag == 0 or flag == 1, f"flag should be 0/1 but got {flag}"
        self.logger.debug(f"set FAN temp control to {flag}")
        if self._sudo:
            with open(f'{self.root}/temp_control', 'w') as f:
                f.write(f'{flag}')
        else:
            with sh.contrib.sudo(password=PASSWORD, _with=True):
                bash(f"echo {flag} > {self.root}/temp_control")
        

    @property
    def speed(self):
        if self._sudo:
            with open(f'{self.root}/target_pwm', 'r') as f:
                res = eval(f.read().rstrip('\n'))
        else:
            res = sh.cat(f'{self.root}/target_pwm')
            res = decode(res)
        self.logger.debug(f"get FAN speed {res}")
        return res

    @speed.setter
    def speed(self, freq):
        assert isinstance(freq, int)
        assert 0 <= float(freq) <=255, f"{freq} should between [0, 255]"
        self.logger.debug(f"set FAN speed {freq}")
        if self._sudo:
            with open(f'{self.root}/target_pwm', 'w') as f:
                f.write(f'{freq}')
        else:
            with sh.contrib.sudo(password=PASSWORD, _with=True):
                bash(f"echo {freq} > {self.root}/target_pwm")
    
    @property
    def temp(self):
        if self._sudo:
            with open(f'{self.thermal_root}/thermal_zone7/temp', 'r') as f:
                res = eval(f.read().rstrip('\n'))
        else:
            res = sh.cat(f'{self.thermal_root}/thermal_zone7/temp')
            res = eval(decode(res))
        self.logger.debug(f"get FAN temp {res}")
        return res


class TX2Controller(object):

    def __init__(self, name="TX2Controller", verbose=True, sudo=os.geteuid() == 0):
        self.logger = set_logging(name=name, filename=f"{name}.txt", verbose=verbose)
        self.GPU=GPU(self.logger, sudo=sudo)
        self.CPU=CPU(self.logger, sudo=sudo)
        self.FAN=FAN(self.logger, sudo=sudo)
        self.logger.info(f"Root Mode: {sudo}")
        if sudo:
            self.logger.warning(f"Slower if without sudo permission")
        self._reset()

    @property
    def specs(self):
        return Device_Specs(
            CPU=self.CPU.specs,
            GPU=self.GPU.specs,
            FAN=self.FAN.specs
        )._asdict()

    @specs.setter
    def specs(self, specs: dict):
        for k, spec_dict in specs.items():
            module = getattr(self, k)
            for k, v in spec_dict.items():
                setattr(module, k, v)
        
    
    def _reset(self):
        self.logger.info('Reset configurations')
        self.CPU.gov = 'schedutil'
        self.GPU.gov = 'nvhost_podgov'
        self.FAN.speed = 0