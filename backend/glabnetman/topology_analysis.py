# -*- coding: utf-8 -*-
# ToMaTo (Topology management software) 
# Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

class Result():
	def __init__(self):
		self.problems=[]
		self.warnings=[]
		self.hints=[]
		
	def res(self):
		return {"problems": self.problems, "warnings": self.warnings, "hints": self.hints}
	

def analyze(top):
	res = Result()
	if len(top.devices_all()) == 0:
		res.problems.append("No devices specified")
	_check_fully_connected(top, res)
	_check_interface_connection_count(top, res)
	_check_connectors_connection_count(top, res)
	_check_real_connectors(top, res)
	_check_connectors_ip_structure(top, res)
	_check_connection_performance(top, res)
	return res.res()

def _check_fully_connected(top, res):
	reachable=set()
	todo=set()
	unreachable=set()
	#put everything in unreachable
	for device in top.devices_all():
		unreachable.add(device)
	if len(unreachable)==0:
		return
	#select a starting device and put it in todo
	start=iter(unreachable).next()
	todo.add(start)
	while len(todo)>0:
		cur=iter(todo).next()
		#mark cur as reachable and done
		reachable.add(cur)
		unreachable.remove(cur)
		todo.remove(cur)
		for interface in cur.interfaces_all():
			if interface.connection:
				for connection in interface.connection.connector.connections_all():
					dev=connection.interface.device
					if not dev in reachable:
						todo.add(dev)
	if len(unreachable):
		res.warnings.append("Topology is not fully connected, e.g. %s and %s" % (iter(reachable).next().name, iter(unreachable).next().name ) )
	
def _check_interface_connection_count(top,res):
	con={}
	for device in top.devices_all():
		for interface in device.interfaces_all():
			con[repr(interface)]=[]
	for connector in top.connectors_all():
		for connection in connector.connections_all():
			con[repr(connection.interface)].append(connector)
	for interface, connectors in con.iteritems():
		if len(connectors)==0:
			res.warnings.append("Interface %s is not connected" % interface)
		if len(connectors)>1:
			res.problems.append("Interface %s is connected multiple times" % interface)
				
def _check_connectors_connection_count(top,res):
	for connector in top.connectors_all():
		if len(connector.connections_all())==0:
			res.problems.append("Connector %s is not connected" % connector.name)
		if len(connector.connections_all())==1 and not connector.type == "real":
			res.warnings.append("Connector %s is only connected once" % connector.name)
			
def _check_real_connectors(top,res):
	real=[]
	for connector in top.connectors_all():
		if connector.type == "real":
			real.append(connector)
	if len(real)==0:
		res.warnings.append("No real network connector used")
	if len(real)>1:
		res.hints.append("Multiple real world connectors can be joined")

def _check_connectors_ip_structure(top,res):
	for connector in top.connectors_all():
		ip_addresses=set()
		dhcp_clients=set()
		for connection in connector.connections_all():
			if connection.interface.is_configured():
				if connection.interface.configuredinterface.ip4address:
					ip=connection.interface.configuredinterface.ip4address
					if ip in ip_addresses:
						res.warnings.append("Duplicate IP address %s on %s" % ( ip, connector.name ) )
						ip_addresses.add(ip)
				if connection.interface.configuredinterface.use_dhcp:
					dhcp_clients.add(connection.interface.device.name)
		if len(dhcp_clients)>0 and not connector.type=="real":
			res.hints.append("No dhcp server configured on %s but clients configured to use dhcpd: %s" % ( connector.name, ", ".join(dhcp_clients) ) )
				
def _check_connection_performance(top,res):
	for connector in top.connectors_all():
		for connection in connector.connections_all():
			if connection.is_emulated():
				if connection.emulatedconnection.lossratio:
					r=connection.emulatedconnection.lossratio
					if (r<0.0) or (r>1.0):
						res.problems.append("Loss ratio for %s must be in [0..1]" % repr(connection))
					if r==1:
						res.warnings.append("Loss ratio for %s set to 1, that means no connection" % repr(connection))