import logging
import traceback
import json

from bson import json_util
from flask.views import MethodView
from flask import request
from flask_smorest import Blueprint, Api, abort

from ext_requests.cluster_requests import cluster_request_to_delete_job, cluster_request_to_delete_job_by_ip
from services.service_management import delete_service
from ext_requests.apps_db import mongo_update_job_status
from ext_requests.cluster_db import mongo_get_all_clusters, mongo_find_all_active_clusters, \
    mongo_update_cluster_information, mongo_find_cluster_by_id
from services.instance_management import instance_scale_up_scheduled_handler

clustersbp = Blueprint(
    'Clusters', 'cluster management', url_prefix='/api/clusters'
)

clusterinfo = Blueprint(
    'Clusterinfo', 'cluster informations', url_prefix='/api/information'
)

clusterop = Blueprint(
    'Cluster operations', url_prefix='/api/cluster/add'
)

cluster_info_schema = {
    "type": "object",
    "properties": {
        "cpu_percent": {"type": "string"},
        "cpu_cores": {"type": "string"},
        "gpu_cores": {"type": "string"},
        "gpu_percent": {"type": "string"},
        "cumulative_memory_in_mb": {"type": "string"},
        "number_of_nodes": {"type": "string"},
        "virtualization": {"type": "array", "items": {"type": "string"}},
        "more": {"type": "object"},
        "worker_groups": {"type": "string"},
        "jobs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "system_job_id": {"type": "string"},
                    "status": {"type": "string"},
                    "instance_list": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "instance_number": {"type": "string"},
                                "status": {"type": "string"},
                                "publicip": {"type": "string"}
                            }
                        }
                    },
                }
            }
        },
    }
}

clusterop_schema = {
    "type": "object",
    "properties": {
        "cluster_name": {"type": "string"},
        "cluster_location": {"type": "string"},
    }
}


@clustersbp.route('/')
class ClustersController(MethodView):

    def get(self, *args, **kwargs):
        return json_util.dumps(mongo_get_all_clusters())


@clustersbp.route('/active')
class ActiveClustersController(MethodView):

    def get(self, *args, **kwargs):
        return json_util.dumps(mongo_find_all_active_clusters())


@clusterinfo.route('/<clusterid>')
class ClusterController(MethodView):

    @clusterinfo.arguments(schema=cluster_info_schema, location="json", validate=False, unknown=True)
    def post(self, *args, **kwargs):
        data = request.json
        mongo_update_cluster_information(kwargs['clusterid'], data)
        jobs = data.get('jobs')
        for j in jobs:
            result = mongo_update_job_status(
                job_id=j.get('system_job_id'),
                status=j.get('status'),
                instances=j.get('instance_list'))
            if result is None:
                # cluster has outdated jobs, ask to undeploy
                cluster_request_to_delete_job_by_ip(j.get('system_job_id'), -1, request.remote_addr)

        return 'ok'


@clusterop.route('/cluster/add')
class ClusterController(MethodView):

    @clusterinfo.arguments(schema=clusterop_schema, location="json", validate=False, unknown=True)
    @clusterinfo.response(200, content_type="application/json")
    @jwt_auth_required()
    def post(self, args, *kwargs):
          data = request.get_json()
          current_user = get_jwt_identity()
          result, code = register_cluster(data, current_user)
          if code != 200:
              abort(code, result)
          return json_util.dumps(result)