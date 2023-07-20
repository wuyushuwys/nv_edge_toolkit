import sh
import os
from sh import bash
# from enum import Enum
# from typing import Union
# import atexit

from .utils import (set_logging,
                   PASSWORD,
                   decode,
                   Device_Specs,
                   CPU_Specs,
                   GPU_Specs,
                   FAN_Specs
                   )

bash = sh.bash.bake('-c')


class Component():

    def __init__(self, logger, root, num=1, sudo=False) -> None:
        self.root = root
        self.num = num
        self._sudo = sudo
        self.logger = logger
        self._thermal_root = '/sys/devices/virtual/thermal'

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


class TX2CPU(Component):

    FREQ = [345600, 499200, 652800, 806400, 960000, 1113600, 1267200, 1420800, 1574400, 1728000, 1881600, 2035200]
    GOV = ["userspace", "schedutil"]

    def __init__(self, logger, root='/sys/devices/system/cpu', num=6, sudo=True) -> None:
        super(TX2CPU, self).__init__(logger=logger, root=root, num=num, sudo=sudo)
        self._throttling_bound = self.throttling

    @property
    def specs(self):
        self.logger.info("Retrive CPU specs")
        return CPU_Specs(gov=self.gov,
                         freq=self.freq,
                         temp=self.temp
                         )._asdict()
    
    @property
    def online(self):
        online = {}
        for cpu_idx in range(self.num):
            if self._sudo:
                with open(f'{self.root}/cpu{cpu_idx}/online', 'r') as f:
                    res = f.read().rstrip('\n')
                online[str(cpu_idx)] = eval(res)
            else:
                res = sh.cat(f'{self.root}/cpu{cpu_idx}/online')
                res = decode(res)
                online[str(cpu_idx)] = eval(res)
        self.logger.debug(f"get CPU online {online}")
        return online
    
    @online.setter
    def online(self, online):
        self.logger.debug(f'set CPU online {online}')
        if isinstance(online, int):
            online = {i: online for i in range(self.num)}
        elif isinstance(online, dict):
            pass
        else:
            NotImplementedError(f"Expected input type Dict or int, but got {type(online)}")
        if self._sudo:
            for idx, v in online.items():
                assert v==0 or v==1, f"online for {idx} can only be 0/1 but got {v}"
                with open(f"{self.root}/cpu{idx}/online", 'w', ) as f:
                    f.write(str(v))
        else:
            with sh.contrib.sudo(password=PASSWORD, _with=True):
                for idx, v in online.items():
                    assert v==0 or v==1, f"online for {idx} can only be 0/1 but got {v}"
                    bash(f"echo {v} > {self.root}/cpu{idx}/online")

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
            freq = {int(idx): int(v) for idx, v in freq.items()}
        else:
            NotImplementedError(f"Expected input type Dict/Str/Int, but got {type(freq)}")
        
        for idx, v in freq.items():
            assert v in self.FREQ, f"{v} for {idx} is not avaliable"
            if self._sudo:
                with open(f'{self.root}/cpu{idx}/cpufreq/scaling_setspeed', 'w') as f:
                    f.write(f'{v}')
            else:
                with sh.contrib.sudo(password=PASSWORD, _with=True):
                    bash(f"echo {v} > {self.root}/cpu{idx}/cpufreq/scaling_setspeed")

    @property
    def temp(self):
        if self._sudo:
            with open(f'{self._thermal_root}/thermal_zone0/temp', 'r') as f:
                res = eval(f.read().rstrip('\n'))
        else:
            res = sh.cat(f'{self._thermal_root}/thermal_zone0/temp')
            res = eval(decode(res))
        self.logger.debug(f"get CPU temp {res}")
        if res >= self._throttling_bound:
            self.logger.warning(f"Temperature higher than{self._throttling_bound}, CPU throttling has been enabled")
        return res
    
    @property
    def throttling(self):
        if self._sudo:
            with open(f'{self._thermal_root}/thermal_zone0/trip_point_1_temp', 'r') as f:
                res = eval(f.read().rstrip('\n'))
        else:
            res = sh.cat(f'{self._thermal_root}/thermal_zone0/trip_point_1_temp')
            res = decode(res)
        self.logger.debug(f"get CPU thermal throttling {res}")
        return res
    
    @throttling.setter
    def throttling(self, throttling):
        assert 10000 <= int(throttling) <= 99500, self.logger.error(f"CPU throttling value should between [10000, 99500] but got {throttling}")
        throttling = str(int(throttling))
        self._throttling_bound = int(throttling)
        self.logger.debug(f"set CPU thermal throttling {throttling}")
        if self._sudo:
            with open(f'{self._thermal_root}/thermal_zone0/trip_point_1_temp', 'w') as f:
                f.write(f'{throttling}')
        else:
            with sh.contrib.sudo(password=PASSWORD, _with=True):
                bash(f"echo {throttling} > {self._thermal_root}/thermal_zone0/trip_point_1_temp")


class TX2GPU(Component):
        
    FREQ = [114750000, 216750000, 318750000, 420750000, 522750000, 624750000, 726750000, 
            854250000, 930750000, 1032750000, 1122000000, 1236750000, 1300500000]
    
    GOV = ["nvhost_podgov", "userspace"]

    def __init__(self, logger, root='/sys/devices/gpu.0/devfreq/17000000.gp10b', sudo=True) -> None:
        super(TX2GPU, self).__init__(logger=logger, root=root, sudo=sudo)
        self._throttling_bound = self.throttling
        self.min_freq = min(self.FREQ)
        self.max_freq = max(self.FREQ)

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
    def max_freq(self):
        if self._sudo:
            with open(f'{self.root}/max_freq', 'r') as f:
                res = eval(f.read().rstrip('\n'))
        else:
            res = sh.cat(f'{self.root}/max_freq')
            res = decode(res)
        self.logger.debug(f"get GPU max_freq {res}")
        return res
    
    @max_freq.setter
    def max_freq(self, freq):
        assert freq in self.FREQ, f"{freq} is not avaliable"
        if self._sudo:
            with open(f'{self.root}/max_freq', 'w') as f:
                f.write(f'{freq}')
            self.logger.debug(f"Set gpu max_freq {freq}")
        else:
            with sh.contrib.sudo(password=PASSWORD, _with=True):
                bash(f"echo {freq} > {self.root}/max_freq")
                self.logger.debug(f"Set gpu max_freq {freq}")
    
    @property
    def min_freq(self):
        if self._sudo:
            with open(f'{self.root}/min_freq', 'r') as f:
                res = eval(f.read().rstrip('\n'))
        else:
            res = sh.cat(f'{self.root}/min_freq')
            res = decode(res)
        self.logger.debug(f"get GPU min_freq {res}")
        return res
    
    @min_freq.setter
    def min_freq(self, freq):
        assert freq in self.FREQ, f"{freq} is not avaliable"
        if self._sudo:
            with open(f'{self.root}/min_freq', 'w') as f:
                f.write(f'{freq}')
            self.logger.debug(f"Set gpu min_freq {freq}")
        else:
            with sh.contrib.sudo(password=PASSWORD, _with=True):
                bash(f"echo {freq} > {self.root}/min_freq")
                self.logger.debug(f"Set gpu min_freq {freq}")

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
            with open(f'{self.root}/userspace/set_freq', 'w') as f:
                f.write(f'{freq}')
            self.logger.debug(f"Set gpu set_freq {freq}")
            # with open(f'{self.root}/max_freq', 'w') as f:
            #     f.write(f'{freq}')
            # self.logger.debug(f"Set gpu max_freq {freq}")
            # with open(f'{self.root}/min_freq', 'w') as f:
            #     f.write(f'{freq}')
            # self.logger.debug(f"Set gpu min_freq {freq}")
        else:
            with sh.contrib.sudo(password=PASSWORD, _with=True):
                bash(f"echo {freq} > {self.root}/userspace/set_freq")
                self.logger.debug(f"Set gpu set_freq {freq}")
                # bash(f"echo {freq} > {self.root}/max_freq")
                # self.logger.debug(f"Set gpu max_freq {freq}")
                # bash(f"echo {freq} > {self.root}/min_freq")
                # self.logger.debug(f"Set gpu min_freq {freq}")
    
    @property
    def temp(self):
        if self._sudo:
            with open(f'{self._thermal_root}/thermal_zone2/temp', 'r') as f:
                res = eval(f.read().rstrip('\n'))
        else:
            res = sh.cat(f'{self._thermal_root}/thermal_zone2/temp')
            res = eval(decode(res))
        self.logger.debug(f"get GPU temp {res}")
        if res >= self._throttling_bound:
            self.logger.warning(f"Temperature higher than{self._throttling_bound}, GPU throttling has been enabled")
        return res
    
    @property
    def throttling(self):
        if self._sudo:
            with open(f'{self._thermal_root}/thermal_zone2/trip_point_6_temp', 'r') as f:
                res = eval(f.read().rstrip('\n'))
        else:
            res = sh.cat(f'{self._thermal_root}/thermal_zone2/trip_point_6_temp')
            res = decode(res)
        self.logger.debug(f"get GPU thermal throttling {res}")
        return res
    
    @throttling.setter
    def throttling(self, throttling):
        assert 10000 <= int(throttling) <= 99500, self.logger.error(f"GPU throttling value should between [10000, 99500] but got {throttling}")
        throttling = str(int(throttling))
        self._throttling_bound = int(throttling)
        self.logger.debug(f"set GPU thermal throttling {throttling}")
        if self._sudo:
            with open(f'{self._thermal_root}/thermal_zone2/trip_point_6_temp', 'w') as f:
                f.write(f'{throttling}')
        else:
            with sh.contrib.sudo(password=PASSWORD, _with=True):
                bash(f"echo {throttling} > {self._thermal_root}/thermal_zone2/trip_point_6_temp")


class TX2FAN(Component):

    def __init__(self, logger, root='/sys/devices/pwm-fan', sudo=True) -> None:
        super(TX2FAN, self).__init__(logger=logger, root=root, sudo=sudo)
        self.rpm_path = '/sys/devices/generic_pwm_tachometer/hwmon/hwmon1/rpm'

    @property
    def specs(self):
        self.logger.info("Retrive FAN specs")
        return FAN_Specs(control=self.control,
                         speed=self.speed,
                         temp=self.temp,
                         )._asdict()
    
    @property
    def control(self):
        if self._sudo:
            with open(f'{self.root}/temp_control', 'r') as f:
                res = eval(f.read().rstrip('\n'))
        else:
            res = sh.cat(f'{self.root}/temp_control')
            res = eval(decode(res))
        self.logger.debug(f"get FAN temp control {res}")

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
    def rpm(self):
        if self._sudo:
            with open(self.rpm_path, 'r') as f:
                res = eval(f.read().rstrip('\n'))
        else:
            res = sh.cat(self.rpm_path)
            res = eval(decode(res))
        self.logger.debug(f"get FAN rpm {res}")
        return res
    
    @property
    def temp(self):
        if self._sudo:
            with open(f'{self._thermal_root}/thermal_zone7/temp', 'r') as f:
                res = eval(f.read().rstrip('\n'))
        else:
            res = sh.cat(f'{self._thermal_root}/thermal_zone7/temp')
            res = eval(decode(res))
        self.logger.debug(f"get FAN temp {res}")
        return res


class TX2Controller(object):

    def __init__(self, name="TX2Controller", verbose=True, sudo=os.geteuid() == 0):
        self.logger = set_logging(name=name, verbose=verbose)
        self.GPU=TX2GPU(self.logger, sudo=sudo)
        self.CPU=TX2CPU(self.logger, sudo=sudo)
        self.FAN=TX2FAN(self.logger, sudo=sudo)
        self.logger.info(f"Root Mode: {sudo}")
        if not sudo:
            self.logger.warning(f"Slower if without sudo permission")
        self._reset()
        # atexit.register(self._reset)

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
        self.CPU.online = 1
        self.CPU.gov = 'schedutil'
        self.CPU.throttling = 95500
        self.GPU.gov = 'nvhost_podgov'
        self.GPU.throttling = 95500
        self.FAN.speed = 60
        self.FAN.control = 1
        
    def reset(self):
        self._reset()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()


class OrinNanoCPU(Component):
    
    FREQ = [115200, 192000, 268800, 345600, 422400, 499200, 576000, 652800, 
            729600, 806400, 883200, 960000, 1036800, 1113600, 
            1190400, 1267200, 1344000, 1420800, 1497600, 1510400]
    GOV = ["userspace", "schedutil"]

    def __init__(self, logger, root='/sys/devices/system/cpu', num=6, sudo=True) -> None:
        super(OrinNanoCPU, self).__init__(logger=logger, root=root, num=num, sudo=sudo)
        self._throttling_bound = self.throttling
        self.gov = "schedutil"

    @property
    def specs(self):
        self.logger.info("Retrive CPU specs")
        return CPU_Specs(gov=self.gov,
                         freq=self.freq,
                         temp=self.temp
                         )._asdict()
    
    @property
    def online(self):
        online = {}
        for cpu_idx in range(self.num):
            if self._sudo:
                with open(f'{self.root}/cpu{cpu_idx}/online', 'r') as f:
                    res = f.read().rstrip('\n')
                online[str(cpu_idx)] = eval(res)
            else:
                res = sh.cat(f'{self.root}/cpu{cpu_idx}/online')
                online[str(cpu_idx)] = eval(res)
        self.logger.debug(f"get CPU online {online}")
        return online
    
    @online.setter
    def online(self, online):
        self.logger.debug(f'set CPU online {online}')
        if isinstance(online, int):
            online = {i: online for i in range(self.num)}
        elif isinstance(online, dict):
            pass
        else:
            NotImplementedError(f"Expected input type Dict or int, but got {type(online)}")
        if self._sudo:
            for idx, v in online.items():
                assert v==0 or v==1, f"online for {idx} can only be 0/1 but got {v}"
                with open(f"{self.root}/cpu{idx}/online", 'w', ) as f:
                    f.write(str(v))
        else:
            with sh.contrib.sudo(password=PASSWORD, _with=True):
                for idx, v in online.items():
                    assert v==0 or v==1, f"online for {idx} can only be 0/1 but got {v}"
                    bash(f"echo {v} > {self.root}/cpu{idx}/online")

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
                gov[str(cpu_idx)] = res.rstrip('\n')
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
                freq[str(cpu_idx)] = eval(res.split()[0])
        self.logger.debug(f"get CPU frequencies {freq}")
        return freq

    @freq.setter
    def freq(self, freq):
        self.logger.debug(f'set CPU frequencies {freq}')
        if isinstance(freq, str) or isinstance(freq, int):
            freq = {i: freq for i in range(self.num)}
        elif isinstance(freq, dict):
            freq = {int(idx): int(v) for idx, v in freq.items()}
        else:
            NotImplementedError(f"Expected input type Dict/Str/Int, but got {type(freq)}")
        
        for idx, v in freq.items():
            assert v in self.FREQ, f"{v} for {idx} is not avaliable"
            if self._sudo:
                with open(f'{self.root}/cpu{idx}/cpufreq/scaling_setspeed', 'w') as f:
                    f.write(f'{v}')
            else:
                with sh.contrib.sudo(password=PASSWORD, _with=True):
                    bash(f"echo {v} > {self.root}/cpu{idx}/cpufreq/scaling_setspeed")

    @property
    def min_freq(self):
        freq = {}
        for cpu_idx in range(self.num):
            if self._sudo:
                with open(f'{self.root}/cpu{cpu_idx}/cpufreq/scaling_min_freq', 'r') as f:
                    res = f.read().rstrip('\n')
                    freq[str(cpu_idx)] = eval(res)
            else:
                res = sh.cat(f'{self.root}/cpu{cpu_idx}/cpufreq/scaling_min_freq')
                freq[str(cpu_idx)] = eval(res.split()[0])
        self.logger.debug(f"get CPU scaling_min_freq {freq}")
        return freq

    @min_freq.setter
    def min_freq(self, freq):
        self.logger.debug(f'set CPU scaling_min_freq {freq}')
        if isinstance(freq, str) or isinstance(freq, int):
            freq = {i: freq for i in range(self.num)}
        elif isinstance(freq, dict):
            freq = {int(idx): int(v) for idx, v in freq.items()}
        else:
            NotImplementedError(f"Expected input type Dict/Str/Int, but got {type(freq)}")
        
        for idx, v in freq.items():
            assert v in self.FREQ, f"{v} for {idx} is not avaliable"
            if self._sudo:
                with open(f'{self.root}/cpu{idx}/cpufreq/scaling_min_freq', 'w') as f:
                    f.write(f'{v}')
            else:
                with sh.contrib.sudo(password=PASSWORD, _with=True):
                    bash(f"echo {v} > {self.root}/cpu{idx}/cpufreq/scaling_min_freq")

    @property
    def temp(self):
        if self._sudo:
            with open(f'{self._thermal_root}/thermal_zone0/temp', 'r') as f:
                res = f.read().rstrip('\n')
        else:
            res = sh.cat(f'{self._thermal_root}/thermal_zone0/temp')
        self.logger.debug(f"get CPU temp {res}")
        if eval(res) >= self._throttling_bound:
            self.logger.warning(f"Temperature higher than{self._throttling_bound}, CPU throttling has been enabled")
        return eval(res)
    
    @property
    def throttling(self):
        if self._sudo:
            with open(f'{self._thermal_root}/thermal_zone0/trip_point_1_temp', 'r') as f:
                res = f.read().rstrip('\n')
        else:
            res = sh.cat(f'{self._thermal_root}/thermal_zone0/trip_point_1_temp')
        self.logger.debug(f"get CPU thermal throttling {res}")
        return eval(res)
    
    @throttling.setter
    def throttling(self, throttling):
        assert 10000 <= int(throttling) <= 99500, self.logger.error(f"CPU throttling value should between [10000, 99500] but got {throttling}")
        throttling = str(int(throttling))
        self._throttling_bound = int(throttling)
        self.logger.debug(f"set CPU thermal throttling {throttling}")
        if self._sudo:
            with open(f'{self._thermal_root}/thermal_zone0/trip_point_1_temp', 'w') as f:
                f.write(f'{throttling}')
        else:
            with sh.contrib.sudo(password=PASSWORD, _with=True):
                bash(f"echo {throttling} > {self._thermal_root}/thermal_zone0/trip_point_1_temp")


class OrinNanoGPU(Component):
        
    FREQ = [306000000, 408000000, 510000000, 612000000, 624750000]
    
    GOV = ["nvhost_podgov", "userspace"]

    def __init__(self, logger, root='/sys/devices/gpu.0/devfreq/17000000.ga10b', sudo=True) -> None:
        super(OrinNanoGPU, self).__init__(logger=logger, root=root, sudo=sudo)
        self._throttling_bound = self.throttling
        self.min_freq = min(self.FREQ)
        self.max_freq = max(self.FREQ)
        self.gov = "nvhost_podgov"

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
    def max_freq(self):
        if self._sudo:
            with open(f'{self.root}/max_freq', 'r') as f:
                res = eval(f.read().rstrip('\n'))
        else:
            res = sh.cat(f'{self.root}/max_freq')
            res = eval(res)
        self.logger.debug(f"get GPU max_freq {res}")
        return res
    
    @max_freq.setter
    def max_freq(self, freq):
        assert freq in self.FREQ, f"{freq} is not avaliable"
        if self._sudo:
            with open(f'{self.root}/max_freq', 'w') as f:
                f.write(f'{freq}')
            self.logger.debug(f"Set gpu max_freq {freq}")
        else:
            with sh.contrib.sudo(password=PASSWORD, _with=True):
                bash(f"echo {freq} > {self.root}/max_freq")
                self.logger.debug(f"Set gpu max_freq {freq}")
    
    @property
    def min_freq(self):
        if self._sudo:
            with open(f'{self.root}/min_freq', 'r') as f:
                res = eval(f.read().rstrip('\n'))
        else:
            res = sh.cat(f'{self.root}/min_freq')
            res = eval(res)
        self.logger.debug(f"get GPU min_freq {res}")
        return res
    
    @min_freq.setter
    def min_freq(self, freq):
        assert freq in self.FREQ, f"{freq} is not avaliable"
        if self._sudo:
            with open(f'{self.root}/min_freq', 'w') as f:
                f.write(f'{freq}')
            self.logger.debug(f"Set gpu min_freq {freq}")
        else:
            with sh.contrib.sudo(password=PASSWORD, _with=True):
                bash(f"echo {freq} > {self.root}/min_freq")
                self.logger.debug(f"Set gpu min_freq {freq}")

    @property
    def freq(self):
        if self._sudo:
            with open(f'{self.root}/cur_freq', 'r') as f:
                res = eval(f.read().rstrip('\n'))
        else:
            res = sh.cat(f'{self.root}/cur_freq')
            res = eval(res)
        self.logger.debug(f"get GPU clock {res}")
        return res
    
    @freq.setter
    def freq(self, freq):
        assert freq in self.FREQ, f"{freq} is not avaliable"
        if self._sudo:
            with open(f'{self.root}/userspace/set_freq', 'w') as f:
                f.write(f'{freq}')
            self.logger.debug(f"Set gpu set_freq {freq}")
            # with open(f'{self.root}/max_freq', 'w') as f:
            #     f.write(f'{freq}')
            # self.logger.debug(f"Set gpu max_freq {freq}")
            # with open(f'{self.root}/min_freq', 'w') as f:
            #     f.write(f'{freq}')
            # self.logger.debug(f"Set gpu min_freq {freq}")
        else:
            with sh.contrib.sudo(password=PASSWORD, _with=True):
                bash(f"echo {freq} > {self.root}/userspace/set_freq")
                self.logger.debug(f"Set gpu set_freq {freq}")
                # bash(f"echo {freq} > {self.root}/max_freq")
                # self.logger.debug(f"Set gpu max_freq {freq}")
                # bash(f"echo {freq} > {self.root}/min_freq")
                # self.logger.debug(f"Set gpu min_freq {freq}")
    
    @property
    def temp(self):
        if self._sudo:
            with open(f'{self._thermal_root}/thermal_zone1/temp', 'r') as f:
                res = eval(f.read().rstrip('\n'))
        else:
            res = sh.cat(f'{self._thermal_root}/thermal_zone1/temp')
            res = eval(res)
        self.logger.debug(f"get GPU temp {res}")
        if res >= self._throttling_bound:
            self.logger.warning(f"Temperature higher than{self._throttling_bound}, GPU throttling has been enabled")
        return res
    
    @property
    def throttling(self):
        if self._sudo:
            with open(f'{self._thermal_root}/thermal_zone2/trip_point_1_temp', 'r') as f:
                res = eval(f.read().rstrip('\n'))
        else:
            res = sh.cat(f'{self._thermal_root}/thermal_zone2/trip_point_1_temp')
            res = eval(res)
        self.logger.debug(f"get GPU thermal throttling {res}")
        return res
    
    @throttling.setter
    def throttling(self, throttling):
        assert 10000 <= int(throttling) <= 99500, self.logger.error(f"GPU throttling value should between [10000, 99500] but got {throttling}")
        throttling = str(int(throttling))
        self._throttling_bound = int(throttling)
        self.logger.debug(f"set GPU thermal throttling {throttling}")
        if self._sudo:
            with open(f'{self._thermal_root}/thermal_zone2/trip_point_1_temp', 'w') as f:
                f.write(f'{throttling}')
        else:
            with sh.contrib.sudo(password=PASSWORD, _with=True):
                bash(f"echo {throttling} > {self._thermal_root}/thermal_zone2/trip_point_1_temp")


class OrinNanoFAN(Component):

    def __init__(self, logger, root='/sys/class/hwmon', sudo=True) -> None:
        super(OrinNanoFAN, self).__init__(logger=logger, root=root, sudo=sudo)
        self.rpm_path = '/sys/class/hwmon/hwmon0/rpm'
        self.control_dict = {1: 'start', 0: 'stop'}

    @property
    def specs(self):
        self.logger.info("Retrive FAN specs")
        return dict(speed=self.speed, rpm=self.rpm)
    
    @property
    def control(self):
        try:
            with sh.contrib.sudo(password=PASSWORD, _with=True):
                res = bash(f"systemctl is-active nvfancontrol.service").rstrip('\n')
                res = 1 if res == 'active' else 0
        except sh.ErrorReturnCode_3:
            res = 0 # 'inactive'
        self.logger.debug(f"get FAN temp control {res}")
        return res

    @control.setter
    def control(self, flag):
        flag = flag if isinstance(flag, int) else int(flag)
        assert flag == 0 or flag == 1, f"flag should be 0/1 but got {flag}"
        self.logger.debug(f"set FAN temp control to {flag}")
        with sh.contrib.sudo(password=PASSWORD, _with=True):
            bash(f"systemctl {self.control_dict[flag]} nvfancontrol.service")
        
    @property
    def speed(self):
        if self._sudo:
            with open(f'{self.root}/hwmon2/pwm1', 'r') as f:
                res = eval(f.read().rstrip('\n'))
        else:
            res = sh.cat(f'{self.root}/hwmon2/pwm1')
            res = eval(res)
        self.logger.debug(f"get FAN speed {res}")
        return res

    @speed.setter
    def speed(self, freq):
        assert isinstance(freq, int)
        assert 0 <= float(freq) <=255, f"{freq} should between [0, 255]"
        self.logger.debug(f"set FAN speed {freq}")
        if self._sudo:
            with open(f'{self.root}/hwmon2/pwm1', 'w') as f:
                f.write(f'{freq}')
        else:
            with sh.contrib.sudo(password=PASSWORD, _with=True):
                bash(f"echo {freq} > {self.root}/hwmon2/pwm1")
    
    @property
    def rpm(self):
        if self._sudo:
            with open(self.rpm_path, 'r') as f:
                res = eval(f.read().rstrip('\n'))
        else:
            res = sh.cat(self.rpm_path)
            res = eval(res)
        self.logger.debug(f"get FAN rpm {res}")
        return res


class OrinNanoController(object):

    def __init__(self, name="TX2Controller", verbose=True, sudo=os.geteuid() == 0):
        self.logger = set_logging(name=name, verbose=verbose)
        self.GPU=OrinNanoGPU(self.logger, sudo=sudo)
        self.CPU=OrinNanoCPU(self.logger, sudo=sudo)
        self.FAN=OrinNanoFAN(self.logger, sudo=sudo)
        self.logger.info(f"Root Mode: {sudo}")
        if not sudo:
            self.logger.warning(f"Slower if without sudo permission")
        self._reset()
        self.CPU.min_freq = self.CPU.FREQ[0]
        # atexit.register(self._reset)

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
        self.CPU.online = 1
        self.CPU.gov = 'schedutil'
        self.CPU.min_freq = 729600
        self.CPU.throttling = 99000
        self.GPU.gov = 'nvhost_podgov'
        self.GPU.throttling = 99000
        self.FAN.speed = 0
        self.FAN.control = 1
        
    def reset(self):
        self._reset()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()


if __name__ == "__main__":
    with OrinNanoController() as controller:
        pass
