# Shared web objects
from abc import ABC, abstractmethod
import os
from pathlib import Path
from quart import Quart, session, render_template
import uvicorn
import yaml

SCRIPT_PATH = Path(__name__).parent.resolve()

DEFAULT_CONFIG = { # Defaults taken from Quart API
    "import_name": "DEFAULT",
    "static_url_path": "/",
    "static_folder": "static",
    "static_host": "localhost",
    "host_matching":  False,
    "subdomain_matching": False,
    "template_folder": "templates",
    "instance_path": None,
    "instance_relative_config": False,
    "root_path": None
}

class Deployment(ABC):
    
    @abstractmethod
    def apply(rt: Quart, render_func):
        raise NotImplementedError("Should not happen..")

class Deployer():
    """_summary_
        Basically a wrapper around the Quart web app, with some convenience methods, e.g. 'start' 
        or 'stop' the server resp. debug..
    Args:
        ABC (_type_): _description_
    """
    def __init__(self, web_app: Quart, host: str, port: int):
        self._quart_inst = web_app
        self._host_name = host
        self._port_number = port

        #@quart_inst.before_request
        #def make_session_permanent():
        #    session.permanent = True

    def debug(self):
        self._quart_inst.run()

    def start_server(self):
        uvicorn.run(self._quart_inst, host=self._host_name, port=self._port_number, log_level="info")

    def stop_server(self):
        pass

    def deploy(self, d: Deployment):
        """_summary_
        Principally, a variant of "inversion of control" 
        Args:
            d (Deployment): _description_
        """
        d.apply(self._quart_inst, render_template)

def create_instance(root: Path = SCRIPT_PATH) -> Deployer:
    """_summary_
    A deployment must have a predefined structure, e.g. the config file 
    must be named 'config.yaml' and must have an entry 'quart' etc.

    Args:
        folder (Path, optional): _description_. Defaults to script path
    """
    CONFIG_PATH = "{}{}{}".format(root.resolve(), os.sep, "config.yml")
    config = DEFAULT_CONFIG # !!!
    with open(CONFIG_PATH, mode = "r", encoding = "UTF-8") as openfile:
        cfg_text = openfile.read()
        config = yaml.safe_load(cfg_text)
        quart_config = config["quart"]
        # TODO test config values..
        config = quart_config
    root_resolved = root.resolve()
    template_path = "{}{}{}".format(root_resolved, str(os.sep), config["template_folder"]) # need abs. path for jinja2
    static_path = "{}{}{}".format(root_resolved, str(os.sep), config["static_folder"]) # 
    web_app = Quart(
        import_name = config["import_name"],
        #root_path = config["root_path"],
        root_path = root_resolved, # assume correct
        static_folder = static_path,
        static_url_path = config["static_url_path"],
        template_folder = template_path
    )
    return Deployer(web_app, host = config["host_name"], port=config["host_port"])

# everything executed when module is imported (initialization)

if __name__ == "__main__":
    print("This is a library and cannot be invoked directly; pls. use 'import'.")