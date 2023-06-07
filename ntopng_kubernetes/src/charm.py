
import json
import subprocess
import time
from ntopng.ntopng import Ntopng

from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus
import time
import subprocess
import psutil



class ntopng_server():#CharmBase

    def __init__(self) -> None: #, *args
        # Defaults
        self.username     = "admin"
        self.password     = "admin"
        self.ntopng_url   = "http://localhost:3000"
        self.iface_id     = 0
        self.auth_token   = None
        self.enable_debug = False
        self.epoch_end    = int(time.time()-1)
        self.epoch_begin  = self.epoch_end - 3600
        self.maxhits      = 10

        process_hostname = subprocess.run(["hostname", "-I"], capture_output=True, text=True)
        
        self.host_ip     = process_hostname.stdout.splitlines()[0]
        try:
            self.my_ntopng   = Ntopng(self.username, self.password, self.auth_token, self.ntopng_url)
        except Exception as e:
            self._on_start_service_action()

        """Initialize charm and configure states and events to observe.
        super().__init__(*args)
        self.framework.observe(self.on.start_service_action, self._on_start_service_action) #0
        self.framework.observe(self.on.get_interfaces_action,self._on_get_interfaces_action) #1
        self.framework.observe(self.on.get_active_host_from_interface, self._on_get_active_host_from_interface_action) #2
        self.framework.observe(self.on.get_alerts_stats_from_interface_action, self._on_get_alerts_stats_from_interface_action) #3
        self.framework.observe(self.on.get_flow_alerts_stats_action, self._on_get_flow_alerts_stats_action) #4
        self.framework.observe(self.on.get_alerts_action, self._on_get_alerts_action) #5
        self.framework.observe(self.on.get_alerts_per_type_action, self._on_get_alerts_per_type_action) #6
        self.framework.observe(self.on.get_alerts_per_serverity_action, self.on_get_alerts_per_serverity_action) #7
        self.framework.observe(self.on.stop_service_action, self._on_stop_service_action) #8
        self.framework.observe(self.on.health_check_action, self._on_health_check_action) #9
        self.framework.observe(self.on.config_changed, self.configure_pod) #10
        """

    #### 0. Iniciar el servicio con services
    def _on_start_service_action(self): #event
        try:

            ps_process = subprocess.Popen(["ps", "aux"],stdout=subprocess.PIPE)
            grep_process = subprocess.run(["grep", "ntopng -e"],stdin=ps_process.stdout, capture_output=True,text=True)
            aux = grep_process.stdout.splitlines()
            if len(aux) > 0:
                line = aux[0].split()
                user_process = line[0]

            if len(aux) == 0 or user_process != "ntopng":
                reset = subprocess.Popen(["redis-cli", "del", "ntopng.user.admin.password"], stdout=subprocess.PIPE)
                reset.communicate()
                start = subprocess.Popen(["ntopng", "-e"])
                start.communicate()
                time.sleep(6)
                self.my_ntopng = Ntopng(self.username, self.password, self.auth_token, self.ntopng_url)
            
            print("Server started successfully")
            '''event.set_results({
                    "output": f"Server started successfully"
                })'''
        except Exception as e:
            #event.fail(f"Server initiation failed due an unespected exception named: {e}")
            print(f"Server initiation failed due an unespected exception named: {e}")
    
    #### 1. Listar interfaces disponibles
    def _on_get_interfaces_action(self): #event
        try:
            interfaces = self.my_ntopng.get_interfaces_list()
            interface_output = ""

            for interface in interfaces:
                interface_output = interface_output + "Interface: " + interface.get("name") + "\n\t" + "With ID: " + str(interface.get("ifid")) + "\n"

            print(interface_output)
            '''event.set_results({
                    "output": interface_output
                })'''
        except Exception as e:
            #event.fail(f"Get interfaces failed due an unespected exception named: {e}")
            print({e}) 
    
    #### 2. Proporcionar la lista de hosts de una interfaz
    def _on_get_active_host_from_interface_action(self, id_interface): #event
        try:
            #interface = event.params["id-interface"]
            interface_instance = self.my_ntopng.get_interface(id_interface)
            host_list = interface_instance.get_active_hosts()

            for host in host_list:
                host_country = host.get("country")
                if host_country == "":
                    host_country = "Unknown"
                host_bytes = host.get("bytes")
                data_output = host.get("ip") + " - " + host_country + "\n"
                data_output += "Connection: " + "received " + str(host_bytes.get("recvd")) + ", " + "sent " + str(host_bytes.get("sent")) + ", " + "total " + str(host_bytes.get("total")) 
                print(data_output)
                '''event.set_results({
                    "output": data_output
                })'''

        except Exception as e:
            #event.fail(f"Get active host failed due an unespected exception named: {e}")  
            print({e})


    #### 3. Most seen alerts & Alerts with higher severity
    def _on_get_alerts_stats_from_interface_action(self, id_interface): #event 

        try:
            #interface = event.params["id-interface"]
            #epoch_begin = event.params["epoch-begin"]
            #epoch_end = event.params["epoch-end"]
            epoch_begin = ""
            epoch_end = ""

            if epoch_begin == '':
                epoch_begin = self.epoch_begin
            if epoch_end == '':
                epoch_end = self.epoch_end

            historial_interface = self.my_ntopng.get_historical_interface(id_interface)
            data = historial_interface.get_alerts_stats(epoch_begin, epoch_end)
            pretty = json.dumps(data, indent=4, sort_keys=True)
            print(pretty)

            '''event.set_results({
                "output": pretty
            })'''

        except Exception as e:
            #event.fail(f"Get alerts stats failed due an unespected exception named: {e}")
            parameters_info = "Parameters:\n \tid-interface (int): Number of the interface \n \tepoch_begin (int): Start of the time interval (epoch)\n \tepoch_end (int): End of the time interval (epoch)\n"
            #event.fail(parameters_info)
            print({e})
            print("Check the parameters\n\n" + parameters_info)


    #### 4. Return flow alerts stats (premium function, but when reset the password we have 10 minutos of free premium license :D )
    def _on_get_flow_alerts_stats_action(self, id_interface):

        try:

            '''stop = subprocess.Popen(["service", "ntopng", "stop"])
            stop.communicate()
            '''
            for process in psutil.process_iter():
                if "ntopng" in process.name() and "zombie" not in process.status():
                    process.kill()

            reset = subprocess.Popen(["redis-cli", "del", "ntopng.user.admin.password"],stdout=subprocess.PIPE)
            reset.communicate()
            start = subprocess.Popen(["ntopng","-e"])
            start.communicate()
            time.sleep(6) #Minimum 5 seconds to start the services
            
            #interface = event.params["id-interface"]
            #epoch_begin = event.params["epoch-begin"]
            #epoch_end = event.params["epoch-end"]
            epoch_begin = ""
            epoch_end = ""

            if epoch_begin == '':
                epoch_begin = self.epoch_begin
            if epoch_end == '':
                epoch_end = self.epoch_end

            interface_instance = self.my_ntopng.get_interface(id_interface)
            historial_interface = interface_instance.get_historical()

            data = historial_interface.get_flow_alerts_stats(epoch_begin, epoch_end)
            pretty = json.dumps(data, indent=4, sort_keys=True)
            print(pretty)
            
            '''event.set_results({
                "output": pretty
            })'''

        except Exception as e:
            #event.fail(f"Get flow alerts stats failed due an unespected exception named: {e}")
            parameters_info = "Parameters:\n \tid-interface (int): Number of the interface\n \tepoch_begin (int): Start of the time interval (epoch)\n \tepoch_end (int): End of the time interval (epoch)\n"
            #event.fail(parameters_info)
            print({e})
            print("Check the parameters\n\n" + parameters_info)

    #### 5. Run queries on the alert database
    def _on_get_alerts_action(self,id_interface):

        try:
            #interface = event.params["id-interface"]
            #alert_family = event.params["alert-family"]
            #epoch_begin = event.params["epoch-begin"]
            #epoch_end = event.params["epoch-end"]
            #maxhits = event.params["maxhits"]
            epoch_begin = ""
            epoch_end = ""
            maxhits = ""
            alert_family = ""

            if epoch_begin == '':
                epoch_begin = self.epoch_begin
            if epoch_end == '':
                epoch_end = self.epoch_end
            if maxhits == '':
                maxhits = self.maxhits
            if alert_family == '':
                alert_family  = "flow" #flow, host, interface, mac, system and user
                
            select_clause = '*'
            where_clause  = ""
            group_by = ""
            order_by = ""

            historial_interface = self.my_ntopng.get_historical_interface(id_interface)
            data = historial_interface.get_alerts(alert_family, epoch_begin, epoch_end, select_clause, where_clause, maxhits, group_by, order_by)
            pretty = json.dumps(data, indent=4, sort_keys=True)
            print(pretty)

            '''event.set_results({
                "output": pretty
            })'''

        except Exception as e: #FIXME Meter el alert_family en la variable parameters_info
            parameters_info = "Parameters:\n \tid-interface (int): Number of the interface\n \tmaxhits(int): Max number of results (limit)\n \tepoch_begin (int): Start of the time interval (epoch)\n \tepoch_end (int): End of the time interval (epoch)\n \tmaxhits (int): Max number of results (limit)\n"
            print({e})
            print("Check the parameters\n\n" + parameters_info)

    #### 6. Statistics about the number of alerts per alert type
    def _on_get_alerts_per_type_action(self,id_interface): #event
        try:
            #interface = event.params["id-interface"]
            #epoch_begin = event.params["epoch-begin"]
            #epoch_end = event.params["epoch-end"]
            epoch_begin = ""
            epoch_end = ""

            if epoch_begin == '':
                epoch_begin = self.epoch_begin
            if epoch_end == '':
                epoch_end = self.epoch_end

            interface_instance = self.my_ntopng.get_interface(id_interface)
            historial_interface = interface_instance.get_historical()
            data = historial_interface.get_alert_type_counters(epoch_begin, epoch_end)
            pretty = json.dumps(data, indent=4, sort_keys=True)
            print(pretty)

            '''event.set_results({
                "output": pretty
            })'''

        except Exception as e:
            #event.fail(f"Get alerts per type failed due an unespected exception named: {e}")
            parameters_info = "Parameters:\n \tid-interface (int): Number of the interface\n \tepoch_begin (int): Start of the time interval (epoch)\n \tepoch_end (int): End of the time interval (epoch)\n"
            #event.fail(parameters_info)
            print({e})
            print("Check the parameters\n\n" + parameters_info)

    #### 7. Statistics about the number of alerts per alert severity
    def on_get_alerts_per_serverity_action(self,id_interface):
        try:
            #interface = event.params["id-interface"]
            #epoch_begin = event.params["epoch-begin"]
            #epoch_end = event.params["epoch-end"]
            epoch_begin = ""
            epoch_end = ""

            if epoch_begin == '':
                epoch_begin = self.epoch_begin
            if epoch_end == '':
                epoch_end = self.epoch_end

            interface_instance = self.my_ntopng.get_interface(id_interface)
            historial_interface = interface_instance.get_historical()
            data = historial_interface.get_alert_severity_counters(epoch_begin, epoch_end)
            pretty = json.dumps(data, indent=4, sort_keys=True)
            print(pretty)

            '''event.set_results({
                "output": pretty
            })'''

        except Exception as e:
            #event.fail(f"Get alerts per severity failed due an unespected exception named: {e}")
            parameters_info = "Parameters:\n \tid-interface (int): Number of the interface\n \tepoch_begin (int): Start of the time interval (epoch)\n \tepoch_end (int): End of the time interval (epoch)\n"
            #event.fail(parameters_info)
            print({e})
            print("Check the parameters\n\n" + parameters_info)

    #### 8. Apagar el servicio con services
    def _on_stop_service_action(self): #event
        try:
            #subprocess.Popen(["service", "ntopng", "stop"])
            for process in psutil.process_iter():
                if "ntopng" in process.name() and "zombie" not in process.status():
                    process.kill()
            
            print("Server stoped successfully")
            '''event.set_results({
                    "output": f"Server stoped successfully"
                })'''
        except Exception as e:
            #event.fail(f"Server stop failed due an unespected exception named: {e}")
            print({e})

    #### 9. Health-check
    def _on_health_check_action(self): #event
        """Health-check service"""
        try:
            listOfProcObjects = []
            for process in psutil.process_iter():
                if "ntopng-main" in process.name() and "zombie" not in process.status():
                    pinfo = process.as_dict(attrs=['name'])
                    
                    ps_process = subprocess.Popen(["ps", "aux"],stdout=subprocess.PIPE)
                    grep_process = subprocess.run(["grep", "ntopng -e"],stdin=ps_process.stdout, capture_output=True,text=True)
                    aux = grep_process.stdout.splitlines()[0]
                    cpu_percent = aux.split()
                    pinfo['cpu_percent'] = cpu_percent[2]
                    
                    pinfo['ram_usage'] = self.get_size(process.memory_info().vms)

                    listOfProcObjects.append(pinfo)
                    io = psutil.net_io_counters()
                    net_usage = {"bytes_sent": self.get_size(io.bytes_sent), "bytes_recv": self.get_size(io.bytes_recv)}
                    print(listOfProcObjects)
                    print(str(net_usage))
                    '''
                    event.set_results({
                        "output": f"Status: Ntopng is running",
                        "service-usage": listOfProcObjects,
                        "network-usage": str(net_usage)
                    })
                    '''
                    return
            '''
            event.set_results({
                "output": f"Health-check: Ntopng is not running"
            })
            '''
        except Exception as e:
            print(f"Health-check: Health-check status failed with the following exception: {e}")
            #event.fail(f"Health-check: Health-check status failed with the following exception: {e}")

    #### 10. configure pod
    def configure_pod(self): #event
        if not self.unit.is_leader():
            self.unit.status = ActiveStatus()
            return
        self.unit.status = MaintenanceStatus("Applying pod spec")
        containers = [
            {
                "name": self.framework.model.app.name,
                "image": "jeffreysilver/ntopng_server:kubernetes",
                "ports": [
                    {
                        "name": "ntopng-service",
                        "containerPort": 3000,
                        "protocol": "UDP",
                    }
                    ,
                    {   
                        "name": "ntopng",
                        "containerPort": 22,
                        "protocol": "UDP",
                    }
                ],
                "command": ["/bin/bash","-ce","tail -f /dev/null"],
                "kubernetes": { "securityContext": { "privileged": True}}
            }            
        ]

        kubernetesResources = {"pod": {"hostNetwork": True}}

        self.model.pod.set_spec({"version": 3, "containers": containers, "kubernetesResources": kubernetesResources})

        self.unit.status = ActiveStatus()
        self.app.status = ActiveStatus()

    def get_size(self, bytes):
        """
        Returns size of bytes in a nice format
        """
        for unit in ['', 'K', 'M', 'G', 'T', 'P']:
            if bytes < 1024:
                return f"{bytes:.2f}{unit}B"
            bytes /= 1024


class charm:

    def main():
        ntopng = ntopng_server()
        '''
        ntopng._on_start_service_action()
        ntopng._on_get_interfaces_action()
        ntopng._on_get_active_host_from_interface_action(2)
        ntopng._on_get_alerts_stats_from_interface_action(2)
        ntopng._on_get_flow_alerts_stats_action(2)
        ntopng._on_get_alerts_action(2)
        ntopng._on_get_alerts_per_type_action(2)
        ntopng.on_get_alerts_per_serverity_action(2)
        '''
        ntopng._on_health_check_action()
        ntopng._on_stop_service_action()

    if __name__ == "__main__":
        main()
