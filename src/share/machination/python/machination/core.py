##########################################################################
# Machination
# Copyright (c) 2014, Alexandre ACEBEDO, All rights reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3.0 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library.
##########################################################################

import re
import os
import yaml
import subprocess
import sys
import pwd
import shutil


from machination.constants import MACHINATION_INSTALLDIR
from machination.constants import MACHINATION_USERINSTANCESDIR
from machination.constants import MACHINATION_CONFIGFILE_NAME

from machination.globals import MACHINE_TEMPLATE_REGISTRY


from machination.enums import Provider
from machination.enums import Provisioner
from machination.enums import Architecture

from machination.exceptions import PathNotExistError
from machination.exceptions import InvalidArgumentValue
from machination.exceptions import InvalidYAMLException
from machination.exceptions import InvalidMachineTemplateException

from machination.helpers import accepts

# #
# Class representing a network interface
#
class NetworkInterfaceInstance(yaml.YAMLObject):
    yaml_tag = "!NetworkInterfaceInstance"
    _ipAddr = None
    _macAddr = None
    _hostname = None
    _hostInterface = None

    # ##
    # Constructor
    # ##
    @accepts(None, str, str, str, None)
    def __init__(self, ipAddr, macAddr, hostInterface, hostname="None"):
      # Check each given argument
      # IP Address can be also dhcp
      if re.match("^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|dhcp$", ipAddr):
        self._ipAddr = ipAddr
      else:
        raise InvalidArgumentValue("ipAddr",ipAddr)
      if re.match("^([0-9a-fA-F]{2}[\.:-]){5}([0-9a-fA-F]{2})$", macAddr):
        self._macAddr = macAddr
      else:
        raise InvalidArgumentValue("macAddr",macAddr)

      if hostname == None or (type(hostname) is str and re.match("^([0-9a-zA-Z]*)$", hostname)):
        self._hostname = hostname
      else:
        raise InvalidArgumentValue("hostname",hostname)
        
      if hostInterface == None or (type(hostInterface) is str):
        self._hostInterface = hostInterface
      else:
        raise InvalidArgumentValue("hostInterface",hostInterface)


    # ##
    # Simple getters
    # ##
    def getIPAddr(self):
      return self._ipAddr

    def getMACAddr(self):
      return self._macAddr
      
    def getHostInterface(self):
      return self._hostInterface

    def getHostname(self):
      if self._hostname == None:
        return ""
      else:
        return self._hostname

    # ##
    # ToString method
    # ##
    def __str__(self):
      res = ""
      if self._hostname != None :
          res = self._hostname + "|"
      return res + self.getIPAddr() + "|" + self.getMACAddr() + "|" + self.getHostInterface()

    # ##
    # Function to dump a network interface to yaml
    # ##
    @classmethod
    def to_yaml(cls, dumper, data):
      representation = {
                         "ip_addr" : data.getIPAddr(),
                         "mac_addr" : data.getMACAddr(),
                         "host_interface" : data.getHostInterface()
                         }
      # Only dump the hostname if it has been set
      if data.getHostname() != None:
          representation["hostname"] = data.getHostname()
      return dumper.represent_mapping(data.yaml_tag, representation)

    # ##
    # Function to retrieve an object from yaml
    # ##
    @classmethod
    def from_yaml(cls, loader, node):
      representation = loader.construct_mapping(node, deep=True)
      # Need to check if IP Address or MAC Address are available
      if not "ip_addr" in representation.keys():
        raise InvalidYAMLException("Invalid Network Interface: Missing IP address")

      if not "mac_addr" in representation.keys():
        raise InvalidYAMLException("Invalid Network Interface: Missing MAC address")
      
      if not "host_interface" in representation.keys():
        raise InvalidYAMLException("Invalid Network Interface: Missing Host interface")

      hostname = None
      if "hostname" in representation.keys():
        hostname = representation["hostname"]

      return NetworkInterfaceInstance(representation["ip_addr"],  representation["mac_addr"], representation["host_interface"], hostname)

# #
# Class representing a network interface
#
class NetworkInterfaceTemplate(yaml.YAMLObject):
    yaml_tag = "!NetworkInterfaceTemplate"
    _ipAddr = None
    _hostname = None

    # ##
    # Constructor
    # ##
    @accepts(None, str, None)
    def __init__(self, ipAddr, hostname="None"):
      # Check each given argument
      # IP Address can be also dhcp
      if re.match("^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|dhcp$", ipAddr):
        self._ipAddr = ipAddr
      else:
        raise InvalidArgumentValue("ipAddr",ipAddr)
      
      if hostname == None or (type(hostname) is str and re.match("^([0-9a-zA-Z]*)$", hostname)):
        self._hostname = hostname
      else:
        raise InvalidArgumentValue("hostname",hostname)

    # ##
    # Simple getters
    # ##
    def getIPAddr(self):
      return self._ipAddr
    
    def getHostname(self):
      if self._hostname == None:
        return ""
      else:
        return self._hostname

    # ##
    # ToString method
    # ##
    def __str__(self):
      res = ""
      if self._hostname != None :
          res = self._hostname + "|"
      return res + self.getIPAddr() + "|" + self.getMACAddr() + "|" + self.getHostInterface()

    # ##
    # Function to dump a network interface to yaml
    # ##
    @classmethod
    def to_yaml(cls, dumper, data):
      representation = {
                         "ip_addr" : data.getIPAddr(),
                         }
      # Only dump the hostname if it has been set
      if data.getHostname() != None:
          representation["hostname"] = data.getHostname()
      return dumper.represent_mapping(data.yaml_tag, representation)

    # ##
    # Function to retrieve an object from yaml
    # ##
    @classmethod
    def from_yaml(cls, loader, node):
      representation = loader.construct_mapping(node, deep=True)
      # Need to check if IP Address or MAC Address are available
      if not "ip_addr" in representation.keys():
        raise InvalidYAMLException("Invalid Network Interface: Missing IP address")

      hostname = None
      if "hostname" in representation.keys():
        hostname = representation["hostname"]

      return NetworkInterfaceTemplate(representation["ip_addr"], hostname)
    
# ##
# Class representing a sync folder between host and guest
# ##
class SyncedFolder(yaml.YAMLObject):
    yaml_tag = "!SyncedFolder"
    _hostDir = None
    _guestDir = None

    # ##
    # Constructor
    # ##
    @accepts(None, str, str)
    def __init__(self, host_dir, guest_dir):
      # Path on the host must exist
      if os.path.exists(host_dir):
        self._hostDir = host_dir
      else:
        raise PathNotExistError(host_dir)
      if re.match("^(\/.*)$",guest_dir):
        self._guestDir = guest_dir
      else:
        raise InvalidArgumentValue("guest_dir",guest_dir)

    # ##
    # Simple getters
    # ##
    def getHostDir(self):
      return self._hostDir

    def getGuestDir(self):
      return self._guestDir

    # ##
    # ToString function
    # ##
    def __str__(self):
      return self._hostDir + " => " + self._guestDir

    # ##
    # Function to dump the object as YAML
    # ##
    @classmethod
    def to_yaml(cls, dumper, data):
      representation = {
                         "host_dir" : data.getHostDir(),
                         "guest_dir" : data.getGuestDir()
                         }
      return dumper.represent_mapping(data.yaml_tag, representation)

    # ##
    # Function to create a syncfolder from yaml
    # ##
    @classmethod
    def from_yaml(cls, loader, node):
      representation = loader.construct_mapping(node, deep=True)
      # A Synced folder shall have a host_dir and a guest_dir
      if not "host_dir" in representation.keys():
          raise InvalidYAMLException("Invalid Synced folder: missing host directory")

      if not "guest_dir" in representation.keys():
          raise InvalidYAMLException("Invalid Synced folder: missing guest directory")

      return SyncedFolder(representation["host_dir"],
                          representation["guest_dir"])

# ##
# Class representing a machine template
# ##
class MachineTemplate(yaml.YAMLObject):
    yaml_tag = '!MachineTemplate'
    _path = None
    _provisioners = []
    _providers = []
    _osVersions = []
    _archs = []
    _guestInterfaces = []
    _version = None

    # ##
    # Constructor
    # ##
    @accepts(None, str,str, list, list, list, list)
    def __init__(self, path,version, archs, osVersions , providers, provisioners, guestInterfaces):
      # Checking the arguments

      if not os.path.exists(path):
        raise InvalidArgumentValue("Template path",path)

      if len(archs) == 0:
        raise InvalidMachineTemplateException("Invalid number of architectures")
      else:
        for arch in archs:
          if type(arch) is not Architecture:
            raise InvalidMachineTemplateException("Invalid architecture")

      if len(providers) == 0:
        raise InvalidMachineTemplateException("Invalid number of providers")
      else:
        for p in providers:
          if type(p) is not Provider:
            raise InvalidMachineTemplateException("Invalid provider")

      if len(provisioners) == 0:
        raise InvalidMachineTemplateException("Invalid number of provisioners")
      else:
        for p in provisioners:
          if type(p) is not Provisioner:
            raise InvalidMachineTemplateException("Invalid provisioner")

      if len(osVersions) == 0:
        raise InvalidMachineTemplateException("Invalid number of os versions")

      for i in guestInterfaces:
        if type(i) is not NetworkInterfaceTemplate:
          raise InvalidMachineTemplateException("Invalid guest interface")

      self._path = path
      self._version = version
      self._archs = archs
      self._osVersions = osVersions
      self._providers = providers
      self._provisioners = provisioners
      self._guestInterfaces = guestInterfaces

    # ##
    # Simple getters
    # ##
    def getName(self):
      fileName = os.path.basename(self._path)
      return os.path.splitext(fileName)[0]

    def getPath(self):
      return self._path

    def getArchs(self):
      return self._archs

    def getProviders(self):
      return self._providers

    def getProvisioners(self):
      return self._provisioners

    def getOsVersions(self):
      return self._osVersions

    def getGuestInterfaces(self):
      return self._guestInterfaces

    def getVersion(self):
      return self._version

    # ##
    # Function to dump the object into YAML
    # ##
    @classmethod
    def to_yaml(cls, dumper, data):
      representation = {
                          "path" : data.getPath(),
                          "archs" : data.getArchs(),
                          "os_versions" : str(data.getOsVersions()),
                          "version" : str(data.getVersion()),
                          "providers" : str(data.getProviders()),
                          "provisioners" : str(data.getProvisioners()),
                          "guest_interfaces" : data.getGuestInterfaces(),
                          }
      node = dumper.represent_mapping(data.yaml_tag, representation)
      return node

    # ##
    # Function to create a template from YAML
    # ##
    @classmethod
    def from_yaml(cls, loader, node):
      representation = loader.construct_mapping(node, deep=True)
      archs = []
      # Check if architectures are present in the template
      if "archs" in representation.keys() and type(representation["archs"]) is list:
          for p in representation["archs"]:
              archs.append(Architecture.fromString(p))

      providers = []
      # Check if providers are present in the template
      if "providers" in representation.keys() and type(representation["providers"]) is list:
          for p in representation["providers"]:
              providers.append(Provider.fromString(p))

      version = ""
      # Check if version is present in the template
      if "version" in representation.keys():
        version = str(representation["version"])

      provisioners = []
      # Check if provisioners are present in the template
      if "provisioners" in representation.keys() and type(representation["provisioners"]) is list:
          for p in representation["provisioners"]:
              provisioners.append(Provisioner.fromString(p))

      osVersions = None
      # Check if osVersions are present in the template
      if "os_versions" in representation.keys() and type(representation["os_versions"]) is list:
          osVersions = representation["os_versions"]

      guestInterfaces = []
      if "guest_interfaces" in representation.keys() and type(representation["guest_interfaces"]) is list:
          guestInterfaces = representation["guest_interfaces"]

      return MachineTemplate(loader.stream.name,
                             version,
                             archs,
                             osVersions,
                             providers,
                             provisioners,
                             guestInterfaces)

# ##
# Class representing a Machine instance
# ##
class MachineInstance(yaml.YAMLObject):
    yaml_tag = '!MachineInstance'
    _name = None
    _template = None
    _provisioner = None
    _provider = None
    _osVersion = None
    _guestInterfaces = None
    _arch = None
    _syncedFolders = None

    # ##
    # Constructor
    # ##
    @accepts(None, str, MachineTemplate, Architecture, str, Provider, Provisioner, list, list)
    def __init__(self, name, template, arch, osVersion, provider, provisioner, guestInterfaces, syncedFolders):
      # Check the arguments
      if len(osVersion) == 0:
        raise InvalidArgumentValue("osVersion",osVersion)

      if len(name) == 0:
        raise InvalidArgumentValue("name",name)
        
      # Manually check the type of list elements
      for i in guestInterfaces:
        if not type(i) is NetworkInterfaceInstance:
          raise InvalidArgumentValue("guest_interfaces",i)

      for f in syncedFolders:
        if not type(f) is SyncedFolder:
          raise InvalidArgumentValue("synced_folder",f)
      self._name = name
      self._template = template
      self._arch = arch
      self._osVersion = osVersion
      self._provider = provider
      self._provisioner = provisioner
      self._guestInterfaces = guestInterfaces
      self._syncedFolders = syncedFolders

    # ##
    # Simple getters
    # ##
    def getPath(self):
      return os.path.join(MACHINATION_USERINSTANCESDIR, self.getName())

    # ##
    # Function to generate the file attached to the instance
    # ##
    def create(self):
      # If the machine does not exist yet
      if not os.path.exists(self.getPath()):
        if os.geteuid() == 0:
          # Get the real user behind the sudo
          pw_record = pwd.getpwnam(os.getenv("SUDO_USER"))
          # Create its folder and copy the Vagrant file
          os.makedirs(self.getPath())
          shutil.copy(os.path.join(MACHINATION_INSTALLDIR, "share", "machination", "vagrant", "Vagrantfile"), os.path.join(self.getPath(), "Vagrantfile"))
          try:
            # Create the machine config file
            configFile = yaml.dump(self)
            openedFile = open(os.path.join(self.getPath(), MACHINATION_CONFIGFILE_NAME), "w+")
            openedFile.write(configFile)
            openedFile.close()
            # Generate the file related to the provisioner
            generator = Provisioner.getFileGenerator(self.getProvisioner())
            generator.create(self.getTemplate(), self.getPath())
            # Fire up the vagrant machine
            p = subprocess.Popen("vagrant up", shell=True, stderr=subprocess.PIPE, cwd=self.getPath())
            p.communicate()[0]
            if p.returncode != 0:
              shutil.rmtree(self.getPath())
              raise RuntimeError("Error while creating machine '{0}'".format(self.getName()));            
            else:
              # change the owner of the created files
              os.chown(self.getPath(), pw_record.pw_uid, pw_record.pw_gid)
              for root, dirs, files in os.walk(self.getPath()):
                for d in dirs:
                  os.lchown(os.path.join(root, d), pw_record.pw_uid, pw_record.pw_gid)
                for f in files:
                  os.lchown(os.path.join(root, f), pw_record.pw_uid, pw_record.pw_gid)

          except InvalidMachineTemplateException as e:
            shutil.rmtree(self.getPath())
            raise e
        else:
            raise RuntimeError("Only root can create a machine instance.");
      else:
        # Raise an error about the fact the machine already exists
        raise RuntimeError("Machine instance '{0}' already exists".format(self.getPath()))

    # ##
    # Simple getters
    # ##
    def getName(self):
      return self._name

    def getArch(self):
      return self._arch

    def getProvisioner(self):
      return self._provisioner

    def getProvider(self):
      return self._provider

    def getSyncedFolders(self):
      return self._syncedFolders

    def getTemplate(self):
      return self._template
    
    def getGuestInterfaces(self):
      return self._guestInterfaces

    def getOsVersion(self):
      return self._osVersion

    # ##
    # Function to start an instance
    # This function must be ran as root as some action in the the provisioner or the provider may require a root access
    # ##
    def start(self):
      if os.geteuid() == 0:
        # Get the real user behind the sudo
        pw_record = pwd.getpwnam(os.getenv("SUDO_USER"))
        # Fire up the vagrant machine
        p = subprocess.Popen("vagrant up", shell=True, stderr=subprocess.PIPE, cwd=self.getPath())
        p.communicate()[0]
        # change the owner of the created files
        os.chown(self.getPath(), pw_record.pw_uid, pw_record.pw_gid)
        for root, dirs, files in os.walk(self.getPath()):
          for d in dirs:
            os.lchown(os.path.join(root, d), pw_record.pw_uid, pw_record.pw_gid)
          for f in files:
            os.lchown(os.path.join(root, f), pw_record.pw_uid, pw_record.pw_gid)
        if p.returncode != 0:
          raise RuntimeError("Error while starting '{0}'".format(self.getName()));
      else:
          raise RuntimeError("Only root can start a machine instance");

    # ##
    # Function to destroy an instance
    # ##
    def destroy(self):
      # Destroy the vagrant machine
      p = subprocess.Popen("vagrant destroy -f", shell=True, stdout=subprocess.PIPE, cwd=self.getPath())
      p.wait()
      if p.returncode != 0:
        raise RuntimeError("Error while destroying '{0}'".format(self.getName()));
      shutil.rmtree(self.getPath())

    # ##
    # Function to stop an instance
    # ##
    def stop(self):
      if os.geteuid() == 0:
        p = subprocess.Popen("vagrant halt", shell=True, stderr=subprocess.PIPE, cwd=self.getPath())
        p.communicate()[0]
        if p.returncode != 0:
          raise RuntimeError("Error while stopping'{0}'".format(self.getName()));
      else:
        raise RuntimeError("Only root can stop a machine instance")

    # ##
    # ##
    def getInfos(self):
      i = 0
      output =  "  Name: {0}\n".format(self.getName())
      output += "  Architecture: {0}\n".format(self.getArch())
      output += "  Provisioner: {0}\n".format(self.getProvisioner())
      output += "  Provider: {0}\n".format(self.getProvider())
      p = subprocess.Popen("vagrant ssh-config", shell=True,  stderr=subprocess.PIPE, stdout=subprocess.PIPE, cwd=self.getPath())
      out = p.communicate()[0]
      if p.returncode == 0:
        ipAddrSearch = re.search("HostName (.*)",out)
        if ipAddrSearch != None :
          output += "  Primary IPAddress of the container: {0}\n".format(ipAddrSearch.group(1))
  
      p = subprocess.Popen("vagrant status", shell=True,  stderr=subprocess.PIPE, stdout=subprocess.PIPE, cwd=self.getPath())
      isStarted = False
      out = p.communicate()[0]
      isStarted = (isStarted or (re.search("(.*)machination-{0}(.*)running(.*)".format(self.getName()),out) != None)) 
      if p.returncode == 0 and isStarted:
          output += "  State: Running\n"
      else:
          output += "  State: Stopped\n"
      if len(self.getGuestInterfaces()) != 0 :
        output +="  Network interfaces:\n"
        for intf in self.getGuestInterfaces():
          output += "  - Name: eth{0}\n".format(i)
          output += "    IPAddress: {0}\n".format(intf.getIPAddr())
          output += "    MACAddress: {0}\n".format(intf.getMACAddr())
          output += "    Host interface: {0}\n".format(intf.getHostInterface())
          if intf.getHostname() != None:
            output += "    Hostname: {0}\n".format(intf.getHostname())
          i += 1
      return output

    # ##
    # Function to ssh to an instance
    # ##
    def ssh(self):
        # Start vagrant ssh to ssh into the instance
        val = subprocess.Popen("vagrant ssh", shell=True, stderr=subprocess.PIPE, cwd=self.getPath())
        # get the output of the machine
        while True:
            out = val.stderr.read(1)
            if out == '' and val.poll() != None:
                break
            if out != '':
                sys.stdout.write(out)
                sys.stdout.flush()

    # ##
    # Function to dump the object to YAML
    # ##
    @classmethod
    def to_yaml(cls, dumper, data):
        representation = {
                               "template" : "{0}|{1}".format(data.getTemplate().getName(),data.getTemplate().getVersion()),
                               "arch" : str(data.getArch()),
                               "os_version" : str(data.getOsVersion()),
                               "provider" : str(data.getProvider()),
                               "provisioner" : str(data.getProvisioner()),
                               "guest_interfaces" : data.getGuestInterfaces(),
                               "synced_folders" :  data.getSyncedFolders(),
                               }
        node = dumper.represent_mapping(data.yaml_tag, representation)
        return node

    # ##
    # Function to create an object from YAML
    # ##
    @classmethod
    def from_yaml(cls, loader, node):
        representation = loader.construct_mapping(node, deep=True)

        # Retrieve the elements to create an instance
        arch = None
        if "arch" in representation.keys():
            arch = Architecture.fromString(representation["arch"])

        provider = None
        if "provider" in representation.keys():
            provider = Provider.fromString(representation["provider"])

        provisioner = None
        if "provisioner" in representation.keys():
            provisioner = Provisioner.fromString(representation["provisioner"])

        name = os.path.basename(os.path.dirname(loader.stream.name))

        template = None
        if "template" in representation.keys():
            content = representation["template"].split("|")
            if(len(content) == 2):
              # Retrieve the template from the registry
              template = MACHINE_TEMPLATE_REGISTRY.getTemplates()[content[0]]

        osVersion = None
        if "os_version" in representation.keys():
            osVersion = representation["os_version"]

        guestInterfaces = []
        if "guest_interfaces" in representation.keys():
            guestInterfaces = representation["guest_interfaces"]

        syncedFolders = []
        if "sync_folders" in representation.keys():
            syncedFolders = representation["sync_folders"]
        
        return MachineInstance(name,
                                   template,
                                   arch,
                                   osVersion,
                                   provider,
                                   provisioner,
                                   guestInterfaces,
                                   syncedFolders)
