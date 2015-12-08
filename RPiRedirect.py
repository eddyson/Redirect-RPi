#!/usr/bin/python
# coding: utf-8

# (C)2002-2003 Chris Liechti <cliechti@gmx.net>
# redirect data from a TCP/IP connection to a serial port and vice versa
# requires Python 2.2 'cause socket.sendall is used

import os
import serial
import socket
import sqlite3 as lite
import subprocess
import sys
import threading
import time
from datetime import datetime


# conectar com o banco de dados
class DB_Config:
    def __init__(self):
        self.con = lite.connect('/home/pi/RPiConfig.db')
        self.con.row_factory = lite.Row

    def select(self):
        self.sql = 'select * from terminal'
        self.rs = self.con.execute(self.sql)
        self.rg = self.rs.fetchone()
        self.rg_cp = self.rg.keys()
        self.rg_db = dict(zip(self.rg_cp,self.rg))
        return self.rg_db

    def fecha_db(self):
        self.con.close()
        
# arquivo de log
log_nome = 'RPiLog.txt'

# definir campos
db = DB_Config()
reg = db.select()
db.fecha_db()

local =             reg['local']
dispositivo =       reg['dispositivo']
ip_local =          reg['ip_local']
mascara_rede =      reg['mascara_rede']
porta_local =       reg['porta_local']
protocolo =         reg['protocolo']
ip_servidor =       reg['ip_servidor']
porta_servidor =    reg['porta_servidor']
baud_rate =         reg['baud_rate']
parity =            reg['parity']
data_bits =         reg['data_bits']
stop_bits =         reg['stop_bits']
arq_log =           reg['arq_log']


#definir protocolo
_UDP = protocolo == 'UDP'

#ativar de tela
_RCA = False

#ativar log
_LOG = arq_log == 'A'
if _LOG:
    #abrir arquivo log
    #log = open('/var/www/redirect/log.txt','w')
    log = open(os.path.join(os.getcwd(), log_nome),'w')
    log.write('LOCAL: '+ip_local+'| SERVIDOR: '+ip_servidor+'\n')
    log.flush()

# configurar ip local
ret = subprocess.call('ifconfig eth0 down',shell=True)
ip = 'ifconfig eth0 '+ip_local+' netmask '+mascara_rede+' up'
ret = subprocess.call(ip,shell=True)


try:
    True
except NameError:
    True = 1
    False = 0

def dataHora():
    dh=datetime.now()
    ano=str(dh.year)
    dia=str(dh.day)
    mes=str(dh.month)
    hor=str(dh.hour)
    mnt=str(dh.minute)
    seg=str(dh.second)
    if len(dia)==1: dia=dia.zfill(2)
    if len(mes)==1: mes=mes.zfill(2)
    if len(hor)==1: hor=hor.zfill(2)
    if len(mnt)==1: mnt=mnt.zfill(2)
    if len(seg)==1: seg=seg.zfill(2)
    return dia+'/'+mes+'/'+ano+' - '+hor+':'+mnt+':'+seg

class Redirector:
    def __init__(self, serial, socket):
        self.serial = serial
        self.socket = socket

    def shortcut(self):
        """
        connect the serial port to the tcp port by copying everything 
        from one side to the other
        """
        self.alive = True
        self.thread_read = threading.Thread(target=self.reader)
        self.thread_read.setDaemon(1)
        self.thread_read.start()
        self.writer()
    
    def reader(self):
        """
        loop forever and copy serial->socket
        """
        while self.alive:
            try:
                data = self.serial.read(1)              #read one, blocking
                time.sleep(0.1)
                n = self.serial.inWaiting()             #look if there is more
                if n:
                    data = data + self.serial.read(n)   #and get as much as possible
                if data:
                    if _UDP:
                        self.socket.sendto(data,(ip_servidor,porta_servidor))
                    else:
                        self.socket.sendall(data)           #send it over TCP
                    if _LOG:
                        log.write(dataHora()+': SERIAL=>TCP/UDP '+data+'\n')
                        log.flush()
                    if _RCA: print dataHora()+': SERIAL=>TCP/UDP '+data
            except socket.error, msg:
                print msg
                #probably got disconnected
                break
        self.alive = False
    
    def writer(self):
        """
        loop forever and copy socket->serial
        """
        while self.alive:
            try:
                if _UDP:
                    data,ender = self.socket.recvfrom(1024)
                else:
                    data = self.socket.recv(1024)
                if not data:
                    break
                self.serial.write(data)                 #get a bunch of bytes and send them
                if _LOG:
                    log.write(dataHora()+': TCP/UDP=>SERIAL '+data+'\n')
                    log.flush()
                if _RCA: print dataHora()+': TCP/UDP=>SERIAL '+data
            except socket.error, msg:
                print msg
                #probably got disconnected
                break
        self.alive = False
        self.thread_read.join()

    def stop(self):
        """Stop copying"""
        if self.alive:
            self.alive = False
            self.thread_read.join()


if __name__ == '__main__':
    #ser = serial.Serial()
    ser = serial.Serial('/dev/ttyAMA0',
                        baud_rate,
                        data_bits,
                        parity,
                        stop_bits)
    ser.timeout = 1
    localport = int(porta_local)
    print "--- TCP/IP to Serial redirector --- type Ctrl-C / BREAK to quit"
    print 'LOCAL: ',ip_local,'SERVIDOR: ',ip_servidor

    try:
        ser.open()
    except serial.SerialException, e:
        print "Não pode abrir porta serial %s: %s" % (ser.portstr, e)
        sys.exit(1)
    if _UDP:
        srv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        srv.bind( ('', localport) )
    else:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.bind( ('', localport) )
        srv.listen(1)
    #sys.exit()
    while 1:
        try:
            if not _UDP:
                #print "Aguardando por conexão..."
                connection, addr = srv.accept()
                #print 'Conectado por ', addr
                #enter console->serial loop
                r = Redirector(ser, connection)
                print 'Disconectado'
                connection.close()
            else:
                r = Redirector(ser,srv)
            #redireciona
            r.shortcut()
        except socket.error, msg:
            print msg

    print "\n--- exit ---"
