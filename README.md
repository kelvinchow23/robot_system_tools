# Robot System Tools

A modular robotic system toolkit with camera, robot arm, and vision capabilities.

## 🎥 Camera System

The camera system provides network-based photo capture for robotic applications.

### Quick Start

#### Option 1: Automated Pi Deployment

1. **Deploy to Pi** (from your PC):
   ```bash
   ./deploy_to_pi.sh 192.168.1.100
   ```

2. **Setup on Pi** (automatically installs everything):
   ```bash
   ssh pi@192.168.1.100
   cd /home/pi/robot_camera
   ./setup.sh
   ```

3. **Start camera server**:
   ```bash
   # Manual test
   python camera_server.py
   
   # Or as systemd service (auto-starts on boot)
   sudo systemctl start camera-server
   ```

#### Option 2: Manual Pi Setup

If you prefer manual setup on the Pi:

```bash
# On Pi - copy files manually and install
pip install -r pi_cam_server/requirements.txt
python pi_cam_server/camera_server.py --port 2222
```

## 🤖 Robot Vision Workflow

Simple robot vision workflow with separate, focused scripts:

### 1. Capture Photos
```bash
# Test camera connection
python camera_client.py 192.168.1.100 --test

# Capture a photo  
python camera_client.py 192.168.1.100
```

### 2. Calibrate Camera (First Time)
```bash
# Calibrate camera for accurate AprilTag detection
python calibrate_camera.py
```

### 3. Detect AprilTags
```bash
# Detect AprilTags in latest photo
python detect_apriltags.py --latest --show

# Or specify an image file
python detect_apriltags.py photo.jpg --show
```

### 4. Complete Workflow Test
```bash
# Run the complete workflow (like the original!)
python test_robot_vision.py 192.168.1.100

# Or run continuously
python test_robot_vision.py 192.168.1.100 --loop
```

## 📁 Project Structure

```
robot_system_tools/
├── 📄 camera_client.py      # Simple camera capture
├── 📄 detect_apriltags.py   # Simple AprilTag detection  
├── 📄 calibrate_camera.py   # Camera calibration
├── 📄 test_robot_vision.py  # Complete workflow test
├── 📄 deploy_to_pi.sh       # Pi deployment script
├── 📁 pi_cam_server/        # Pi deployment package
├── 📁 src/camera/           # Core camera library
└── 📁 docker/               # Container configs (future)
```

### Configuration

Edit `camera_config.yaml` to customize:
- Network settings (hostname, port)
- Camera settings (focus, transforms)  
- File locations

### Python API

```python
from src.camera import CameraClient, CameraServer

# Client usage
client = CameraClient()
photo_path = client.request_photo()

# Server usage (on Pi)
server = CameraServer()
server.start_server()
```

## 🗂️ Project Structure

```
robot_system_tools/
├── src/                    # Core modules
│   └── camera/            # Camera system
├── camera_server.py       # Pi camera server app
├── camera_client.py       # PC camera client app  
├── camera_config.yaml     # Configuration
├── archive/               # Archived reference code
└── README.md             # This file
```

## 🚀 Future Components

- Robot arm control
- Vision processing (AprilTags, ArUco)
- Gripper control
- Motion planning
- Safety systems

## 📚 Archive

Historical code and experiments are stored in `archive/` for reference.

---

## Original Franka Documentation (Archived)

The following sections contain the original Franka arm infrastructure documentation for reference.

## Dependancies 
- docker-compose (version 1 or version 2, use "docker-compose .." or "docker compose .." respectively)
- docker 
- git 
- openssh-server
- nvidia-container-toolkit (look at [robot_toolkit/docs/nvidia-container-toolkit.md](robot_toolkit/docs/nvidia-container-toolkit.md) )
- GPU with necessary Nvidia drivers (if using workstation docker)
```
sudo apt-get install docker.io docker-compose git 
```
install openssh-server, following instructions [here](https://www.cyberciti.biz/faq/ubuntu-linux-install-openssh-server/)

# Build Instructions

Before building the docker environments, you need to add your user to the docker group as mentioned [here](https://askubuntu.com/questions/477551/how-can-i-use-docker-without-sudo), so that you can run the docker commands without sudo preveileges and therefore need not type in your password everytime. 

```
sudo usermod -aG docker $USER
```
Note: If using docker-compose version 2, just replace commands containing "docker-compose" with "docker compose" 
installing docker dependancies 

**Note:** <u>**Realtime Computer**</u><a id='realtime'></a> is the computer that sends/receives data from/to the robot realtime(1Khz). It runs the realtime linux kernel as described [here](https://frankaemika.github.io/docs/installation_linux.html#setting-up-the-real-time-kernel). <u>**Workstation computer**</u><a id='workstation'></a> is the computer that sends high level commands to realtime computer to control the robot, this computer can run GPUs.

## [Real time Computer](#realtime)
Build docker container for the real time computer directly connected to Franka's control. 
```
docker-compose -f docker/realtime_computer/docker-compose-gui.yml build \
                            --build-arg workstation_ip=<workstation_ip address>\
                            --build-arg realtime_computer_ip=<realtime_computer_ip address>\
                            --build-arg robot_server_version=<robot_server_version>
docker-compose -f docker/realtime_computer/docker-compose-gui.yml create             
```
Note: To find your robot server version, first find your robot systems version in Franka Desk -> Settings -> System -> Version. Next find your robot server version corresponding to your system version [here](https://frankaemika.github.io/docs/compatibility.html#compatibility-with-libfranka). eg. for robot system version >=4.2.1, robot server version is 5. 

Note: While building the docker container, the above command might print warnings in red color, don't be alarmed and let the process run. If it stops building, that's when there is an error. 

### Build franka_control_suite in the realtime docker environment **(optional and not required to use frankapy)**
open a bash terminal inside the realtime docker container 
```
docker exec -it realtime_docker bash
```
go to franka_control_suite and build it
```
cd /root/git/franka_control_suite
mkdir build && cd build 
cmake ..
make
```

## [Workstation Computer](#workstation)
Build, create, and start the docker container for the workstation computer that has GPU/nvidia drivers 

**Note: it is important to pass the workstation IP address as seen by the Realtime computer here**
```
docker-compose -f docker/workstation_computer/docker-compose-gui.yml build \
                            --build-arg workstation_ip=<workstation_ip address> \ 
                            --build-arg use_robotiq=1 \
                            --build-arg build_dope=1 \
                            --build-arg build_contactgraspnet=1 \ 
                            --build-arg build_megapose=1
                                        
docker-compose -f docker/workstation_computer/docker-compose-gui.yml create
docker-compose -f docker/workstation_computer/docker-compose-gui.yml start
                                                        
```
**Note:** The default CUDA version is 11.3 and Ubuntu version is 20.04, if you would like to change these, please aquire an appropriate docker image and use `--build-arg image=<your image>`.
**Note:** if you want to use [roboiq gripper](https://robotiq.com/products), please set `--build-arg use_robotiq=1` in the previous command for building workstation docker.

Note: While building the docker container, the above command might print warnings in red color, don't be alarmed and let the process run. If it stops building, that's when there is an error. 

## Setting up ssh-key between the workstation and realtime computers (done only once)<a id='ssh-key'></a>

Make sure to setup your workstation/workstation docker's ssh key to ssh into the realtime computer/docker without a password(this is required for frankapy) following instructions [here](https://github.com/iamlab-cmu/frankapy#setting-up-ssh-key-to-control-pc), you can run the following, 

1. In a terminal in your **<u>workstation/workstation docker</u>**, 
```
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
[Press enter]
[Press enter]
[Press enter]
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_rsa
```
2. Upload your public ssh key to the **<u>realtime pc</u>**
     
    i. In a separate terminal on your **<u>workstation PC/docker</u>**, use your favorite text editor to open your id_rsa.pub file.
    ```
    vim ~/.ssh/id_rsa.pub
    ```

    ii. In a new terminal on your **<u>workstation PC/docker</u>**, ssh to the realtime PC.
    ```
    ssh [realtime -pc-username]@[realtime -pc-name]
    Input password to realtime -pc.
    ```

    iii. Inside terminal in your realtime computer **(not realtime computer docker)**, 
    ```
    vim ~/.ssh/authorized_keys
    ```
    
    iv. Copy the contents from your id_rsa.pub file to a new line on the authorized_keys file on the real time. Then save

    v. Open a new terminal in the workstation docker and try sshing to the realtime PC and it should no longer require a password.

# Usage Instructions 

Note: docker-compose provides several commands to use the docker containers that we built in previous steps. They are ["up, start and run"](https://docs.docker.com/compose/faq/#whats-the-difference-between-up-run-and-start). In our docker containers we have not yet defined explicit services, so we will use "run". "up" creates or recreates the container(if you made changes to dockerfile or .yml files), therefore you might lose changes you made in the container, like [adding ssh-key](#ssh-key). As shown below we use the "start" command to run the container we built in the previous step, make sure to "stop" the container when done
## [Real time Computer](#realtime)
In the realtime host computer terminal, bring the built docker container up 
```
docker-compose -f docker/realtime_computer/docker-compose-gui.yml start
```
and when you are done with the container, run 
```
docker-compose -f docker/realtime_computer/docker-compose-gui.yml stop
```
this would get the container running. Then in a new terminal in the realtime host machine, run, 

To open a bash terminal inside the docker container 
```
docker exec -it realtime_docker bash
```

## [Workstation Computer](#workstation) 
In a terminal in the workstation computer
```
docker-compose -f docker/workstation_computer/docker-compose-gui.yml start
```
and when you are done with the container, run 
```
docker-compose -f docker/workstation_computer/docker-compose-gui.yml stop
```
In a new terminal in the workstation host machine, to allow GUI usage, first run, 
```
xhost +local:docker 
```

then to open a bash terminal inside the workstation docker container that we started running above, run
```
docker exec -it workstation_computer_docker bash
```

## Using frankapy 
Frankapy can be used with the real time docker and optionally with workstation_computer docker(if you don't use a docker for workstation, build and use [this frankapy](https://github.com/Ruthrash/frankapy)) 

**First** In your realtime pc, start the realtime computer docker with,
```
docker-compose -f docker/realtime_computer/docker-compose-gui.yml start
```
and when you are done with the container, run 
```
docker-compose -f docker/realtime_computer/docker-compose-gui.yml stop
```

if you are using workstation docker, **in a new terminal** start it with, 
as mentioned [here](https://stackoverflow.com/questions/69872788/docker-could-not-connect-to-any-x-display#:~:text=The%20solution%20is%20to%20run%20the%20following%20command%20in%20your%20terminal%3A) to get GUI access first run, 


```
xhost +local:docker 
```
then in the same terminal, run,
```
docker-compose -f docker/workstation_computer/docker-compose-gui.yml start
```
and when you are done with the container, run 
```
docker-compose -f docker/workstation_computer/docker-compose-gui.yml stop
```


To test the installation and setup of Frankapy,  

If using workstation docker, 

```
docker exec -it workstation_computer_docker bash
cd /root/git/frankapy 
bash ./bash_scripts/start_control_pc.sh -i (realtime computer ip) -u (realtimecomputer username) -d /root/git/franka-interface -a (robot_ip) -w (workstation IP)
```
to test, run
```
cd /root/git/tests/frankapy_control_test_scripts
python3 docker_frankapy_test.py
```
If directly using host workstation and not docker, 
```
cd <path to frankapy>/frankapy 
source catkin_ws/devel/setup.bash 
bash ./bash_scripts/start_control_pc.sh -i (realtime computer ip) -u (realtimecomputer username) -d /root/git/franka-interface -a (robot_ip) -w (workstation IP)
```
to test,
go to franka_arm_infra/tests directory in your workstation machine
```
cd <path to franka_arm_infra>/tests/frankapy_control_test_scripts
```
then run
```
python3 docker_frankapy_test.py
```

## Using calibration

Please checkout [robot_toolkit/docs](robot_toolkit/docs) for documentations of robot camera extrinsic calibration, usage of this tool. We also have a video showing how to use our tool [here](https://drive.google.com/file/d/1VMregvZZmWaFMxj7J3FgXDaWfS2ae4tQ/view?usp=sharing)

## Using Deeplearning based prediciton models 

Please checkout [robot_toolkit/docs/deep_learning_models.md](robot_toolkit/docs/deep_learning_models.md) and [robot_toolkit/docs/nvidia-container-toolkit.md](robot_toolkit/docs/nvidia-container-toolkit.md) for running Neural network models with GPUs.

## Test robotiq gripper
To run the robotiq device, first in a terminal do
```sh
docker exec -it workstation_computer_docker bash
source ~/git/catkin_ws/devel/setup.bash
rosrun robotiq_2f_gripper_control Robotiq2FGripperRtuNode.py /dev/ttyUSB0
```
**Note** when connecting the robotiq gripper to the workstation pc, it may open different file descriptor. In our case it was: `/dev/ttyUSB0`. You may check the following command to see which usb port the robotiq is connected to:  `ls /dev/ttyUSB*`

In another terminal do
```sh
docker exec -it workstation_computer_docker bash
source ~/git/catkin_ws/devel/setup.bash
rosrun robotiq_2f_gripper_control Robotiq2FGripperSimpleController.py
```
then you can try first reset the gripper by passing `r` and then activate the gripper by passing `a`.

## Acknowledgements
- We thank [Reinhard Grasmann](https://reinhardgrassmann.github.io/) for providing CAD files that were super useful to run robot camera calibration routine, provided in this repo at [calibration/models_4_3d_printing](calibration/models_4_3d_printing)
