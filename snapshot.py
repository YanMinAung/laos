import requests
import json
from datetime import date, timedelta, datetime

# Configuration
auth_url = "http://keystone.openstack.svc.cluster.local/v3/auth/tokens"
cinder_url = 'http://cinder.openstack.svc.cluster.local/v3/{project_id}'

volume_id = '6df30814-60b3-45d3-a667-4f469b7b8c75' # Replace with the volume id that you want to snapshot
snapshot_name = "LaoPay_NFS-VMBAK"  # Replace with your snapshot name
retention_period = 7
username = "backup-admin" # please change this
password = "(X#g?E0q>0<SA4~" # please change this
domain = "Laopay"
project_name = "Laopay1" # please change this

headers = {
    'Content-Type': 'application/json'
}
auth_data = {
    "auth": {
        "identity": {
            "methods": ["password"],
            "password": {
                "user": {
                    "name": username,
                    "domain": {"name": domain},
                    "password": password
                }
            }
        },
        "scope":{
            "project": {
                "name": project_name,
                "domain": {"name": domain}
            }
        }
    }
}

auth_headers = {
    'Content-Type': 'application/json'
}

auth_response = requests.post(auth_url, headers=auth_headers,data=json.dumps(auth_data))

if auth_response.status_code == 201:
    token = auth_response.headers['X-Subject-Token']
    project_id = auth_response.json()['token']['project']['id']
    print(f"Authenticated successfully. Token: {token}")
    cinder_headers = {
       'Content-Type': 'application/json',
       'X-Auth-Token': token
    }
    cinder_url = cinder_url.replace("{project_id}", project_id)

    date_to_delete = (datetime.now()-timedelta(days=retention_period)).strftime("%Y-%m-%d")

    snapshot_to_delete = snapshot_name + "_" + date_to_delete
    snapshot_to_create = snapshot_name + "_" + datetime.now().strftime('%Y-%m-%d')

    snapshots_url = f'{cinder_url}/snapshots/detail'
    snapshots_response = requests.get(snapshots_url, headers=cinder_headers)
    snapshots = snapshots_response.json()['snapshots']
    snapshot_id = None
    for snapshot in snapshots:
        if snapshot['name'] == snapshot_to_delete:
            snapshot_id = snapshot['id']
            break
    print(f"Old snapshot ID: {snapshot_id}")
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    snapshot_data = {
        "snapshot": {
            "volume_id": volume_id, 
            "name": snapshot_to_create,
            "description": f"Snapshot for " + snapshot_to_create,
            "force": True
        }
    }

    create_snapshot_url = f"{cinder_url}/snapshots"
    create_response = requests.post(create_snapshot_url, headers=cinder_headers, data=json.dumps(snapshot_data))

    if create_response.status_code == 202:
        snapshot = create_response.json()['snapshot']
        print(f"Snapshot created successfully. ID: {snapshot['id']}, Name: {snapshot['name']}")
    else:
        print(f"Failed to create snapshot: {create_response.status_code}")
        print(create_response.json())

    if snapshot_id:
        # Delete the old snapshot
        delete_url = f'{cinder_url}/snapshots/{snapshot_id}'
        delete_response = requests.delete(delete_url, headers = cinder_headers)
        if delete_response.status_code == 202:
            print(f"Old snapshot '{snapshot_to_delete}' deleted successfully. ID: {snapshot_id}")
        else:
            print(f"Failed to delete old snapshot '{snapshot_to_delete}': {delete_response.status_code}")
            print(delete_response.json())
    else:
        print(f"No existing snapshot with name '{snapshot_to_delete}' to delete.")
