## Description 
This repository contains scripts and off-the-shelf starter scripts for developping and running algorithms for the Franka Emika Panda arms. 
- In the [docker](docker) folder you can find the docker compose yaml and Dockerfiles to setup the docker environment for the realtime computer and workstation computer interfacing with the Franka arms. [frankapy](https://github.com/iamlab-cmu/frankapy) and [frank-interface](https://github.com/iamlab-cmu/franka-interface) are also compiled in the docker environments and you should be able to use frankapy APIs out of the box through this repo. 

- In the [calibration](calibration) folder you can find the calibration scripts to run robot camera calibration routine(currently) and multi camera calibration routine (soon), find more info [here](calibration/docs). 

- In the [franka_control_suite](franka_control_suite)(Work in Progress) folder you can find experimental feedback controllers implemented in libfranka.

- In [tests](tests) (Work in Progress) folder we will provide various unit tests and integration test scripts to ensure the software system is working as expected. Including tests for the docker environment, frankapy, robot camera calibration, etc (Work in Progress)

## Dependancies 
- docker-compose (version 1)
- docker 


Note: If using docker-compose version 2, just replace commands containing "docker-compose" with "docker compose" 
installing docker dependancies 
```
sudo apt-get install docker.io docker-compose
```
# Build Instructions

Note: Realtime Computer is the computer that sends/receives data from/to the robot realtime(1Khz). It runs the realtime linux kernel as described [here](https://frankaemika.github.io/docs/installation_linux.html#setting-up-the-real-time-kernel). Workstation computer is the computer that sends high level commands to realtime computer to control the robot, this computer can run GPUs. 

## Real time Computer 
Build docker container for the real time computer directly connected to Franka's control. 
```
sudo docker-compose -f docker/realtime_computer/docker-compose-gui.yml build \
                            --build-arg workstation_ip=<workstation_ip address>\
                            --build-arg realtime_computer_ip=<realtime_computer_ip address>\
                            --build-arg franka_firmware_version=<franka_firmware_version>
```
Note:For example if your firmware is 3.x, franka_firmware_version=3. For your robot, you can find this in Franka Desk -> Settings -> System -> Version. 

## Workstation Computer 
Build docker container for the workstation computer that has GPU/nvidia drivers 

**Note: it is important to pass the workstation IP address as seen by the realtime computer here**
```
sudo docker-compose -f docker/workstation_computer/docker-compose-gui.yml build --build-arg workstation_ip=<workstation_ip address>
```
### Build franka_control_suite in the realtime docker environment
open a bash terminal inside the realtime docker container 
```
(sudo) docker exec -it realtime_docker bash
```
go to franka_control_suite and build it
```
cd /root/git/franka_control_suite
mkdir build && cd build 
cmake ..
make
```


# Usage Instructions 
## Real time Computer 
Bring the built docker container up 
```
sudo docker-compose -f docker/realtime_computer/docker-compose-gui.yml up 
```

To open a bash terminal inside the docker container 
```
(sudo) docker exec -it realtime_docker bash
```

## Workstation Computer 
to allow GUI usage in workstation docker 
```
xhost +local:docker 
```
then in the same terminal, run, 
```
sudo docker-compose -f docker/workstation_computer/docker-compose-gui.yml up 
```

To open a bash terminal inside the docker container 
```
(sudo) docker exec -it workstation_computer_docker bash
```

## Using frankapy 
Frankapy can be used with the real time docker and optionally with workstation_computer docker(if you don't use a docker for workstation, build and use [this frankapy](https://github.com/Ruthrash/frankapy)) 

**First** In your realtime pc, start the realtime computer docker with,
```
sudo docker-compose -f docker/realtime_computer/docker-compose-gui.yml up 
```

if you are using workstation docker, **in a new terminal** start it with, 
as mentioned [here] (https://stackoverflow.com/questions/69872788/docker-could-not-connect-to-any-x-display#:~:text=The%20solution%20is%20to%20run%20the%20following%20command%20in%20your%20terminal%3A)to get GUI access first run, 

```
xhost +local:docker 
```
then in the same terminal, run,
```
sudo docker-compose -f docker/workstation_computer/docker-compose-gui.yml up 
```

To test the installation and setup of Frankapy,  

If using workstation docker, 

```
(sudo) docker exec -it workstation_computer_docker bash
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

## Setting up ssh-pass between the workstation and realtime computers (done only once)

Make sure to setup your workstation/workstation docker's ssh key to ssh into the realtime computer/docker without a password(this is required for frankapy) following instructions [here](https://github.com/iamlab-cmu/frankapy#setting-up-ssh-key-to-control-pc), you can run the following, 

1. In a terminal in your workstation/workstation docker, 
```
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
[Press enter]
[Press enter]
[Press enter]
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_rsa
```
2. Upload your public ssh key to the realtime pc
     
    i. In a separate terminal on your workstation PC/docker, use your favorite text editor to open your id_rsa.pub file.
    ```
    vim ~/.ssh/id_rsa.pub
    ```

    ii. In a new terminal on your workstation PC/docker, ssh to the realtime PC.
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


## Using calibration

Please checkout [calibration/docs](calibration/docs) for documentations of hand-eye calibration, usage of this tool 




