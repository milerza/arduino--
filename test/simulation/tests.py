#!/usr/bin/env python

import sys
import unittest
import pysimulavr
from adapter import SimulavrAdapter

Sim = SimulavrAdapter()

class PinMonitor(pysimulavr.HasPinNotifyFunction):

    def __init__(self, dev, name, timestamps = True, values = None):
        pysimulavr.HasPinNotifyFunction.__init__(self)
        self.state = 't'
        self.name = name
        if values is None:
            self.values = []
        else:
            self.values = values

        self.timestamps = timestamps
        self.dev = dev
        
        dev.GetPin(name).RegisterCallback(self)

    def PinStateHasChanged(self, pin):
        pv = pin.toChar()
        if self.state != pv:
            self.state = pv
            if self.timestamps:
                self.values.append((self.name, pv, Sim.getCurrentTime()))
            else:
                self.values.append((self.name, pv))

class Atmega328PinTest(unittest.TestCase):

    def tearDown(self):
        Sim.Reset()

    def checkPWMValue(self, a, b, msg):
        # Up to two cycles deviation are ok
        delta_ok = 2

        if abs(a - b) <= delta_ok * Sim.cycleLength:
            return True

        delta = (a - b) / Sim.cycleLength
        self.fail(('%d cpu cycles deviation: ' % delta) + msg) 

    def checkPWMValues(self, values, ocr, prescaler=64, reset=256, fast=False):
        # assumes normal PWM mode, i.e. timer counts up
        high = ocr * prescaler * Sim.cycleLength
        low = (reset - ocr) * prescaler * Sim.cycleLength

        if not fast:
            high = high * 2
            low = low * 2

        if len(values) < 4:
            self.fail('Not enough values for PWM check ' + str(values))

        for i, v in enumerate(values):
            if i > 3:
                l = v[2] - last
                if v[1] == 'H':
                    # transition to H is end of low period
                    self.checkPWMValue(
                        l, low, 'pwm cycle %d (H): %s' % (i, str(values)))
                else:
                    self.checkPWMValue(
                        l, high, 'pwm cycle %d (L): %s' % (i, str(values)))
                    
            last = v[2]

    def testDigitalPins(self):
        '''Test Digital pins and numbering'''
        dev = Sim.loadDevice('atmega328', 'atmega328_digital_pins.elf')
        dev.RegisterTerminationSymbol('exit')

        values = []
        pins = [PinMonitor(dev, 'D%d' % i, False, values)
                for i in range(8)]
        pins.extend([PinMonitor(dev, 'B%d' % i, False, values)
                      for i in range(6)])

        Sim.doRun()

        self.assertEquals(
            values, [('D0', 'L'), ('D0', 'H'), ('D1', 'L'), ('D1', 'H'),
                      ('D2', 'L'), ('D2', 'H'), ('D3', 'L'), ('D3', 'H'),
                      ('D4', 'L'), ('D4', 'H'), ('D5', 'L'), ('D5', 'H'),
                      ('D6', 'L'), ('D6', 'H'), ('D7', 'L'), ('D7', 'H'),
                      ('B0', 'L'), ('B0', 'H'), ('B1', 'L'), ('B1', 'H'),
                      ('B2', 'L'), ('B2', 'H'), ('B3', 'L'), ('B3', 'H'),
                      ('B4', 'L'), ('B4', 'H'), ('B5', 'L'), ('B5', 'H')])

    def testPWMPins(self):
        '''Test PWM Pins'''
        dev = Sim.loadDevice('atmega328', 'atmega328_pwm_pins.elf')
        dev.RegisterTerminationSymbol('exit')

        b1 = PinMonitor(dev, 'B1')
        b2 = PinMonitor(dev, 'B2')
        b3 = PinMonitor(dev, 'B3')
        d3 = PinMonitor(dev, 'D3')
        d5 = PinMonitor(dev, 'D5')
        d6 = PinMonitor(dev, 'D6')

        Sim.doRun()

        # Timer0
        # The OCR of D5 is set to 4
        self.checkPWMValues(d5.values, 4, prescaler=1, fast=True)
        # The OCR of D6 is set to 8
        self.checkPWMValues(d6.values, 8, prescaler=1, fast=True)

        # Timer1
        # The OCR of B1 is set to 4
        self.checkPWMValues(b1.values, 16, prescaler=1, fast=False)
        # The OCR of B2 is set to 8
        self.checkPWMValues(b2.values, 32, prescaler=1, fast=False)

        # Timer2
        # The OCR of B3 is set to 64
        self.checkPWMValues(b3.values, 64, prescaler=8, fast=False)
        # The OCR of D2 is set to 128
        self.checkPWMValues(d3.values, 128, prescaler=8, fast=False)
 
if __name__ == '__main__':

    # run test verbose. This is a bit hackish
    try:
        sys.argv.index('-v')
    except ValueError:
        sys.argv.append('-v')
    
    unittest.main()


