#!/usr/bin/python
import math   # This will import math module
from CRCCCITT import CRCCCITT

#class Equation:
def equ_pb_mda(Vx, Vy):
    alfa = math.sqrt(2)/2
    P = [0,0,0,0,0,0,0,0]
    P[0] =  Vx
    P[1] =  alfa*Vx + alfa*Vy
    P[2] =  Vy
    P[3] = -alfa*Vx + alfa*Vy
    P[4] = -Vx
    P[5] = -alfa*Vx - alfa*Vy
    P[6] = -Vy
    P[7] =  alfa*Vx - alfa*Vy
    return P

def equ2_pb_mda(Vx, Vy):
    alfa = math.sqrt(2)-1
    P = [0,0,0,0,0,0,0,0]
    P[0] =  Vx + alfa*Vy
    P[1] =  alfa*Vx + Vy
    P[2] = -alfa*Vx + Vy
    P[3] = -Vx + alfa*Vy
    P[4] = -Vx - alfa*Vy
    P[5] = -alfa*Vx - Vy
    P[6] =  alfa*Vx - Vy
    P[7] =  Vx - alfa*Vy
    return P

def equ_mda1(Vx, Vy):
    P = [0,0,0,0]
    P[0] = -Vy
    P[1] = Vx
    P[2] = Vy
    P[3] = -Vx
    return P

def equ_mda2(Vx, Vy):
    alfa = math.sqrt(2)/2
    P = [0,0,0,0,0,0,0,0]
    P[0] =  Vx
    P[1] =  alfa*Vx + alfa*Vy
    P[2] =  Vy
    P[3] = -alfa*Vx + alfa*Vy
    P[4] = -Vx
    P[5] = -alfa*Vx - alfa*Vy
    P[6] = -Vy
    P[7] =  alfa*Vx - alfa*Vy
    return P

def equ2_mda2(Vx, Vy):
    alfa = math.sqrt(2)-1
    P = [0,0,0,0,0,0,0,0]
    P[0] =  Vx + alfa*Vy
    P[1] =  alfa*Vx + Vy
    P[2] = -alfa*Vx + Vy
    P[3] = -Vx + alfa*Vy
    P[4] = -Vx - alfa*Vy
    P[5] = -alfa*Vx - Vy
    P[6] =  alfa*Vx - Vy
    P[7] =  Vx - alfa*Vy
    return P

'''12bit'''
ADC_SOLUTION = 0xFFF
byteorder = 'little'

def calc_adc_register_unipolar(channel, value, max_phy):
    dac = value/max_phy*ADC_SOLUTION
    reg = int(dac)*0x100 + channel*0x100000
    return reg.to_bytes(4, byteorder)

def calc_adc_register(channel, value, max_phy):
    dac = (max_phy - value)/max_phy*(ADC_SOLUTION/2)
    reg = int(dac)*0x100 + channel*0x100000
    return reg.to_bytes(4, byteorder)
	
def reg_mla(value, max_phy):
    frame = b'#'
    frame += b'\0\0\0'
    length = 4 + 4*1
    frame += length.to_bytes(4, byteorder)
    '''add body'''
    frame += b'A'
    frame += b'\1'
    length = 4
    frame += length.to_bytes(2, byteorder)
    frame +=calc_adc_register_unipolar(0, value, max_phy)
    '''add crc'''
    mycrc = CRCCCITT().calculate(frame)
    frame += mycrc.to_bytes(2, byteorder)
    return frame

def reg_pb_mda(ls_phase, max_phy):
    frame = b'#'
    frame += b'\0\0\0'
    length = 4*2 + 4*8
    frame += length.to_bytes(4, byteorder)
    '''add body'''
    frame += b'A'
    frame += b'\4'
    length = 16
    frame += length.to_bytes(2, byteorder)
    frame +=calc_adc_register(3, ls_phase[0], max_phy)
    frame +=calc_adc_register(4, ls_phase[4], max_phy)
    frame +=calc_adc_register(5, ls_phase[1], max_phy)
    frame +=calc_adc_register(6, ls_phase[5], max_phy)
    frame += b'B'
    frame += b'\4'
    length = 16
    frame += length.to_bytes(2, byteorder)
    frame +=calc_adc_register(3, ls_phase[2], max_phy)
    frame +=calc_adc_register(4, ls_phase[6], max_phy)
    frame +=calc_adc_register(5, ls_phase[3], max_phy)
    frame +=calc_adc_register(6, ls_phase[7], max_phy)
    '''add crc'''
    mycrc = CRCCCITT().calculate(frame)
    frame += mycrc.to_bytes(2, byteorder)
    return frame

def reg_mda1(ls_phase, max_phy):
    frame = b'#'
    frame += b'\0\0\0'
    length = 4*2 + 4*4
    frame += length.to_bytes(4, byteorder)
    '''add body'''
    frame += b'A'
    frame += b'\2'
    length = 8
    frame += length.to_bytes(2, byteorder)
    frame +=calc_adc_register(1, ls_phase[0], max_phy)
    frame +=calc_adc_register(2, ls_phase[1], max_phy)
    frame += b'B'
    frame += b'\2'
    length = 8
    frame += length.to_bytes(2, byteorder)
    frame +=calc_adc_register(1, ls_phase[2], max_phy)
    frame +=calc_adc_register(2, ls_phase[3], max_phy)
    '''add crc'''
    mycrc = CRCCCITT().calculate(frame)
    frame += mycrc.to_bytes(2, byteorder)
    return frame

def reg_mda2(ls_phase, max_phy):
    frame = b'#'
    frame += b'\0\0\0'
    length = 4*2 + 4*8
    frame += length.to_bytes(4, byteorder)
    '''add body'''
    frame += b'C'
    frame += b'\4'
    length = 16
    frame += length.to_bytes(2, byteorder)
    frame +=calc_adc_register(3, ls_phase[0], max_phy)
    frame +=calc_adc_register(4, ls_phase[4], max_phy)
    frame +=calc_adc_register(5, ls_phase[1], max_phy)
    frame +=calc_adc_register(6, ls_phase[5], max_phy)
    frame += b'D'
    frame += b'\4'
    length = 16
    frame += length.to_bytes(2, byteorder)
    frame +=calc_adc_register(3, ls_phase[2], max_phy)
    frame +=calc_adc_register(4, ls_phase[6], max_phy)
    frame +=calc_adc_register(5, ls_phase[3], max_phy)
    frame +=calc_adc_register(6, ls_phase[7], max_phy)
    '''add crc'''
    mycrc = CRCCCITT().calculate(frame)
    frame += mycrc.to_bytes(2, byteorder)
    return frame

def init_reg_all():
    frame = b'#'
    frame += b'\0\0\0'
    length = 4
    frame += length.to_bytes(4, byteorder)
    '''add body'''
    frame += b'I'
    frame += b'\0'
    length = 0
    frame += length.to_bytes(2, byteorder)
    '''add crc'''
    mycrc = CRCCCITT().calculate(frame)
    frame += mycrc.to_bytes(2, byteorder)
    return frame
	
if __name__ == '__main__':
    lst = equ2_mda2(1.2, 5.5)
    frame = reg_mda2(lst,40)
    print(lst)
    print(frame)
    
    
