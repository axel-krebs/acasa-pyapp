# MAIN. Sample Web application using Microservices design principles.
# Configure injectables from application.yaml: Arango-client, Memcache, Queuing, SQL-Database etc. There are two types:
# a) Infrastrucure components that are established through this script - like Uvicorn web server - and b) those that
# already exist in the environment, e.g. LDAP-I/F, Database backends, distributed in-memory database like Redis a.s.o.
# Optional: Install and manage SSL (certificates) (?)
# Next task is to start the modules - D/I containers -, like web application, microservices etc.
# Principally, a container has a 'profile', th.i. web servers run in an asynchronous way (ASGI), or the traditional WSGI
# Moreover, long-lasting jobs should be running in a 'decoupled' way, that is they are 'enqueued' to a 'batch' module.

from arango import ArangoClient, version as arango_version
import importlib
import logging
import os
from pathlib import Path
import yaml

os.chdir(Path(__file__).parent)

SCRIPT_PATH = Path(__name__).parent.resolve()
CONFIG_FILE = Path("{}{}application.yml".format(SCRIPT_PATH, os.sep))

config = None

asgi_containers = []
async_containers = []
wsgi_containers = []


def load_config():
    with open(CONFIG_FILE, mode="r", encoding="UTF-8") as openfile:
        cfg_text = openfile.read()
        global config
        config = yaml.safe_load(cfg_text)

# External appliances (injectables)


LOG = logging.getLogger() # TODO


def arango_client(timeout: int = 12, max_retries: int = 3) -> ArangoClient:
    arango_url = "http://{}:{}".format(
        config['arango']['host_name'], config['arango']['host_port'])  # closure
    arango_client = ArangoClient(arango_url)
    arango_client.request_timeout = timeout
    return arango_client


def install_injectables():

    if config is None:
        raise "No configuration script provided!"


# Modules (containers)

def load_web_module(config: dict = None):
    mod_py = config["module_py"]
    mod_cfg = config["module_cfg"]
    py_mod = importlib.import_module(mod_py)
    web_app = py_mod.init(mod_cfg)
    global wsgi_containers
    wsgi_containers.append(web_app)

def load_service_module(config: dict = None):
    pass

def load_async_module(config: dict = None):
    pass

def load_modules():
    micro_module_list = config["container"]["asgi"]
    for micro_module in micro_module_list or []:
        print("Micro-Module", micro_module)
        
    web_module_list = config["container"]["wsgi"]
    for web_module in web_module_list or []:
        load_web_module(web_module)

    job_module_list = config["container"]["batch"]
    for job_module in job_module_list or []:
        print("Job-Module", job_module)


# deployed (per import)
def main():
    load_config()
    install_injectables()
    load_modules()
    

def test():
    load_config()
    # TODO execute tests


# started directly
if __name__ == "__main__":
    print("Application started via main script.")
    main()
