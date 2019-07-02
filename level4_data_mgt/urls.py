# -*- encoding:utf-8 -*-
# import libraries
from flask import Blueprint, request, render_template
from flask_restful import Api
from level4_data_mgt import app
from .views import (Project, Gene, Transcript, Test, ExprTemp, Mutation,
                    ProjectList)

ctx = app.test_request_context()
ctx.push()
errors = {
    'ResourceDoesNotExist': {
        'message': "资源不存在",
        'status': 404,
        'url': request.path
    }
}
ctx.pop()

level4_data_mgt_bp = Blueprint('api', __name__)
api_prefix = app.config.get("API")
# api_prefix：/level4data/api/v1，末尾不能添加/，否则将导致URL无法匹配
api = Api(level4_data_mgt_bp, prefix=api_prefix, errors=errors)

# Routes RESTful API
api.add_resource(Test, '/', endpoint="test")
api.add_resource(Project, '/project/<project_name>', endpoint="project")
api.add_resource(ProjectList, '/projects', endpoint="project_list")
api.add_resource(Gene, '/gene/<gene_ensembl_id>', endpoint="gene")
api.add_resource(Transcript, '/transcript/<transcript_ensembl_id>', endpoint="transcript")
# POST 同时请求多个Transcript ID
api.add_resource(Transcript, '/transcripts/queries', endpoint="transcripts_queries")
# GET 获取多个Transcript ID对应的表达信息, expr_info_id是相应Document的_id
api.add_resource(ExprTemp, '/exprinfo/<expr_info_id>', endpoint="transcripts_expr_info")
# 从ExprTemp获取表达信息，query_condition_md5查询条件组成的字符串对应的md5值
# api.add_resource(ExprTemp, '/exprinfo/<query_condition_md5>', endpoint="transcripts_expr_info_query")
api.add_resource(Mutation, '/mutations/<gene_ensembl_id>', endpoint="mutation")

# Routes Test URLs
@app.route('/test_gene')
def gene_exprs():
    return render_template("gene_expression.html", api_prefix=api_prefix + '/gene')

@app.route('/test_transcript')
def transcript_exprs():
    return render_template("gene_expression.html", api_prefix=api_prefix + '/transcript')

@app.route('/test_transcripts')
def transcripts():
    return render_template("transcript_expr.html")

@app.route('/test_mutation')
def mutation():
    return render_template("mutation.html", api_prefix=api_prefix + '/mutation')
