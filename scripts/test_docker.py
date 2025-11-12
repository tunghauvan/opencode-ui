#!/usr/bin/env python3
"""
Example script demonstrating how to handle environment variables in Docker containers.
Shows environment variables for regular containers.
"""

import docker
import time
import argparse

# Global variables:
VOLUME_NAME = "example-volume"
# UUID4() generated value for consistent testing
EXAMPLE_SESSION_ID = "123e4567-e89b-12d3-a456-426614174000"

def create_volume_if_not_exists(client, volume_name):
    """Create a Docker volume if it does not already exist"""
    volumes = client.volumes.list()
    if not any(v.name == volume_name for v in volumes):
        print(f"Creating volume: {volume_name}")
        client.volumes.create(name=volume_name)
    else:
        print(f"Volume {volume_name} already exists.")

def create_folder_in_volume(client, volume_name, folder_path, session_id):
    """Create a folder inside a Docker volume and add example data"""
    print(f"Creating folder and adding example data in '{folder_path}' in volume '{volume_name}'")
    temp_container = client.containers.run(
        'alpine',
        command=['sh', '-c', f'mkdir -p {folder_path} && cat > {folder_path}/auth.json << EOF\n{{\n  "github-copilot": {{\n    "type": "oauth",\n    "refresh": "{session_id}"\n  }}\n}}\nEOF'],
        volumes={volume_name: {'bind': '/root/.local/share/opencode', 'mode': 'rw'}},
        detach=True
    )
    temp_container.wait()
    temp_container.remove()
    print(f"Folder and example data added in '{folder_path}' in volume '{volume_name}'")

def main():
    parser = argparse.ArgumentParser(description='Docker environment variables example with debug waiting')
    parser.add_argument('--wait-debug', action='store_true',
                       help='Enable debug mode with waiting points for inspection')
    parser.add_argument('--session-id', default=EXAMPLE_SESSION_ID,
                       help='Session ID to use for example data')
    args = parser.parse_args()

    # Create a Docker client
    client = docker.from_env()

    # Ensure the volume exists
    create_volume_if_not_exists(client, VOLUME_NAME)
    create_folder_in_volume(client, VOLUME_NAME, f"/root/.local/share/opencode/{args.session_id}", args.session_id)

    # Regular container with environment variables
    run_with_env_vars(client, args)

def run_with_env_vars(client, args):
    """Demonstrate environment variables for regular containers"""
    ENTRYPOINT_SH = f'''
mkdir -p /root/.local/share/opencode
if [ -f /mnt/volume/{args.session_id}/auth.json ]; then
    cp /mnt/volume/{args.session_id}/auth.json /root/.local/share/opencode/auth.json
else
    cat > /root/.local/share/opencode/auth.json << EOF
{{
  "github-copilot": {{
    "type": "oauth",
    "refresh": "{args.session_id}"
  }}
}}
EOF
fi
echo "=== ENVIRONMENT VARIABLES ==="
echo "DB_PASSWORD: $DB_PASSWORD"
echo "API_KEY: $API_KEY"
echo "SECRET_TOKEN: $SECRET_TOKEN"
echo ""
echo "=== VERIFYING MOUNTED DATA ==="
cat /root/.local/share/opencode/auth.json
echo ""
sleep infinity
'''
    try:

        # Create and run container with environment variables
        print("Creating container with environment variables (alternative to secrets)...")
        try:
            existing_container = client.containers.get('example-container')
            print("Removing existing container...")
            existing_container.remove(force=True)
        except docker.errors.NotFound:
            pass

        container = client.containers.run(
            'opencode-agent:latest',
            detach=True,
            name='example-container',
            environment={
                'DB_PASSWORD': 'my-super-secret-password-12345',
                'API_KEY': 'sk-1234567890abcdef',
                'SECRET_TOKEN': 'token-xyz-987654321'
            },
            volumes={VOLUME_NAME: {'bind': '/mnt/volume', 'mode': 'rw'}},
            command=['sh', '-c', ENTRYPOINT_SH]
        )

        print(f"Container created with ID: {container.id}")
        print(f"Container status: {container.status}")

        # Wait a moment
        time.sleep(3)

        if args.wait_debug:
            try:
                input("DEBUG: Container started. Press Enter to continue...")
            except EOFError:
                print("DEBUG: Container started. Continuing...")

        # Get logs
        logs = container.logs()
        print("Container output:")
        print(logs.decode('utf-8'))

        if args.wait_debug:
            try:
                input("DEBUG: Logs retrieved. Press Enter to continue with cleanup...")
            except EOFError:
                print("DEBUG: Logs retrieved. Continuing with cleanup...")

        # Clean up
        print("Stopping container...")
        container.stop()
        print("Removing container...")
        container.remove()
        print("Container removed successfully!")

    except docker.errors.APIError as e:
        print(f"Docker API error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
