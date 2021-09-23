import subprocess
import time

def start_containers(filename = 'Names.txt'):
    create_container = 'docker run -dit --name={0} test1 {0}'
    restart_container = 'docker restart {}'
    stop_container = 'docker stop {}'

    containers_to_create = None
    with open(filename, 'r') as file:
        containers_to_create = [line.strip() for line in file]

    try:
        all_docker_containers = subprocess.run('docker ps -a --format "{{.Names}}"', capture_output=True, text=True, universal_newlines=True)
        all_containers = all_docker_containers.stdout.strip().split('\n')
        if all_docker_containers.stderr:
            raise Exception(all_docker_containers.stderr)
        running_container = subprocess.run('docker ps --format "{{.Names}}"', capture_output=True, text=True, universal_newlines=True)
        running_containers = running_container.stdout.strip().split('\n')

    except Exception as e:
        raise Exception(e)

    try:
        for name in containers_to_create:
            # if the container doesn't exist at all, create
            if name not in all_containers:
                container_creation = subprocess.run(create_container.format(name), capture_output=True, text=True) 
                if container_creation.stderr:
                    raise Exception(container_creation.stderr)
                print(f'Container "{name}" was created with id: {container_creation.stdout}')

            # if the container exists but is stopped, restart
            elif name in all_containers and name not in running_containers:
                container_restart = subprocess.run(restart_container.format(name), capture_output=True, text=True)
                print(f'Container "{name}" was restarted')
    except Exception as e:
        print(e)
        # if name not in list, stop the running container
    try:
        for container in running_containers:
            if container not in containers_to_create:
                container_stop = subprocess.run(stop_container.format(container), capture_output=True)
                if container_stop.stderr:
                    raise Exception(container_stop.stderr)
                print(f'Container {container} has been stopped')

    except Exception as e:
        print(e)

while True:
    try:
        start_containers()
    except Exception as e:
        print(e)
    print('waiting 10 seconds...')
    time.sleep(10)
