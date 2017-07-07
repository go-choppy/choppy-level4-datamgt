import copy, json
from flask import jsonify, request
from flask_restful import Resource, reqparse, fields
from .models import get_project_info, get_expr_by_project, GeneExpr, TranscriptExpr
from .models import ExprInfo, get_exprtemp_info, get_expr_info_by_lst, render_template
from .models import write_expr_info
from .utils import url, gen_md5
from level4_data_mgt.json_loaders import call_loader
from level4_data_mgt import app

templates_conf = app.config.get("TEMPLATES")
exprtemp_info_j2_file = templates_conf.get("EXPRTEMP_INFO_J2_FILE")

def add_argument(parser, arguments):
    for arg, arg_type in arguments.items():
        parser.add_argument(arg, type=arg_type)
    return parser

# Resources
class Project(Resource):
    def get(self, project_name):
        '''
        Get project information
        '''
        # 定义argument
        parser = reqparse.RequestParser()
        arguments = {
            'project_name': str,
            'loader': str,
            'show_src_project': bool,
            'show_analysis_program': bool
        }

        parser = add_argument(parser, arguments)
        app.logger.info('获取%s数据' % project_name)
        args = parser.parse_args()
        del args['project_name']

        error, message, project_info = get_project_info(project_name, **args)
        project_info['project_name'] = project_name
        project_info['api_uri'] = url('api.project', absolute=True, project_name=project_name)
        project_info['message'] = message
        if error and not message:
            project_info['message'] = ''
        project_info = call_loader(args.get('loader'), json_obj = project_info)
        app.logger.info("project_info: %s" % project_info)
        return jsonify(project_info)

class Gene(Resource):
    def get(self, gene_ensembl_id):
        '''
        Get gene expression value
        '''
        parser = reqparse.RequestParser()
        arguments = {
            'project_name': str,
            'subproject_name': str,
            'loader': str,
            'show_gene_ensembl': bool,
            'show_clinical_data_id': bool,
            'show_samples_data_id': bool,
            'show_phenotype_data_id': bool
        }

        parser = add_argument(parser, arguments)
        app.logger.info('获取%s数据' % gene_ensembl_id)
        args = parser.parse_args()
        project_name = args.project_name
        subproject_name = args.subproject_name
        del args['project_name']
        del args['subproject_name']
        error, message, expr_info = get_expr_by_project(project_name, subproject_name, gene_ensembl_id, GeneExpr, **args)
        if not expr_info:
            expr_info = {}
        expr_info['gene_ensembl_id'] = gene_ensembl_id
        expr_info['api_uri'] = url('api.gene', absolute=True, 
                                    gene_ensembl_id=gene_ensembl_id, 
                                    project_name=project_name)
        expr_info['message'] = message
        expr_info = call_loader(args.get('loader'), json_obj = expr_info)
        app.logger.info("expr_info: %s" % expr_info)
        return jsonify(expr_info)

class Transcript(Resource):
    def get(self, transcript_ensembl_id):
        '''
        Get trascript expression value
        '''
        parser = reqparse.RequestParser()
        arguments = {
            'project_name': str,
            'subproject_name': str,
            'loader': str,
            'show_transcript_ensembl': bool,
            'show_clinical_data_id': bool,
            'show_samples_data_id': bool,
            'show_phenotype_data_id': bool            
        }
        parser = add_argument(parser, arguments)
        app.logger.info('获取%s数据' % transcript_ensembl_id)
        args = parser.parse_args()
        project_name = args.project_name
        subproject_name = args.subproject_name
        # 去除重复args
        del args['project_name']
        del args['subproject_name']
        error, message, expr_info = get_expr_by_project(project_name, subproject_name, transcript_ensembl_id, TranscriptExpr, **args)
        if not expr_info:
            expr_info = {}
        expr_info['transcript_ensembl_id'] = transcript_ensembl_id
        expr_info['api_uri'] = url('api.transcript', absolute=True, 
                                    transcript_ensembl_id=transcript_ensembl_id,
                                    project_name=project_name)
        expr_info['message'] = message
        expr_info = call_loader(args.get('loader'), json_obj = expr_info)
        app.logger.info("expr_info: %s" % expr_info)
        return jsonify(expr_info)

    def post(self):
        '''
        传入多个transcript ID，生成临时资源ExprTemp
        '''
        request_json = request.json
        app.logger.debug("request_json: %s" % str(request.json))
        project_name = request_json.get('project_name')
        subproject_name = request_json.get('subproject_name')
        id_lst = request_json.get('transcript_ensembl_id_lst')
        gene_ensembl_id = request_json.get('gene_ensembl_id')

        # 日志
        app.logger.debug("project_name: %s" % project_name)
        app.logger.debug("subproject_name: %s" % subproject_name)
        app.logger.debug("id_lst: %s" % str(id_lst))
        app.logger.debug("gene_ensembl_id: %s" % gene_ensembl_id)

        query_condition = str([project_name, subproject_name, gene_ensembl_id] + sorted(id_lst))
        query_condition_md5 = gen_md5(query_condition.encode("utf8"))
        app.logger.debug("query_condition: %s" % query_condition)
        app.logger.debug("query_condition_md5: %s" % query_condition_md5)
        error, message, expr_info = get_exprtemp_info(query_condition_md5=query_condition_md5)
        if not error and expr_info:
            return jsonify({
                    "data": {
                        "id": str(expr_info.id)
                    },
                    "error_code": 0,
                    "msg": "success"
                })
        else:
            del request_json['project_name']
            del request_json['subproject_name']
            del request_json['gene_ensembl_id']
            del request_json['transcript_ensembl_id_lst']
            errors, messages, expr_info = get_expr_info_by_lst(project_name, subproject_name, id_lst, TranscriptExpr, **request_json)
            if not expr_info:
                return jsonify({
                    'error_code': 1,
                    'message': message,
                    'transcript_ensembl_id_lst': id_lst,
                    'gene_ensembl_id': gene_ensembl_id,
                    'project_name': project_name,
                    'subproject_name': subproject_name
                })
            else:
                expr_info['gene_ensembl_id_lst'] = [gene_ensembl_id]
                expr_info['query_condition_md5'] = query_condition_md5
                # TODO: 增加字段记录查询失败的ID
                expr_info['message'] = 'success'
                # TODO: 增加更多error code
                expr_info['error_code'] = 0
                template_str = render_template(exprtemp_info_j2_file, expr_value = expr_info, show_id = False)
                expr_info = json.loads(template_str.strip("'<>() ").replace('\'', '\"'))
                app.logger.debug("Jinja2 expr_info: %s" % template_str)
                app.logger.debug("expr_info: %s" % expr_info)
                app.logger.debug("expr_info keys: %s" % expr_info.get('data').keys())
                # TODO: 将数据先保存到ExprTemp，再返回给用户
                document_id = write_expr_info(**expr_info.get("data"))
                return jsonify({
                    "data": {
                        "id": str(document_id)
                    },
                    "error_code": 0,
                    "msg": "success"
                })


class ExprTemp(Resource):
    def get(self, expr_info_id = None, query_condition_md5 = None):
        parser = reqparse.RequestParser()
        arguments = {
            'loader': str
        }
        parser = add_argument(parser, arguments)
        args = parser.parse_args()
        if expr_info_id:
            error, message, expr_info = get_exprtemp_info(id = expr_info_id)
        else:
            error, message, expr_info = get_exprtemp_info(query_condition_md5 = query_condition_md5)
        app.logger.debug("expr_info<ExprTemp>: %s" % expr_info.source_type_lst)

        if error:
            app.logger.debug("error: %s" % error)
            expr_info = {}
        error_code = '0'
        message = 'success'
        template_str = render_template(exprtemp_info_j2_file, expr_value = expr_info, 
                                       show_id = True, error_code = error_code, message = message)
        app.logger.debug("Jinja2 Template: %s" % template_str)
        expr_info = json.loads(template_str.strip("'<>() ").replace('\'', '\"'))
        app.logger.debug("loader: %s" % args.get('loader'))
        expr_info = call_loader(args.get('loader'), json_obj = expr_info)
        app.logger.debug("expr_info: %s" % expr_info)
        return jsonify(expr_info)


class Test(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        app.logger.info('获取测试数据')
        args = parser.parse_args()
        welcome_page = {
            "name": "YJC",
            "version": '1.0',
            "tagline": "You Know, for Gene Data"
        }
        welcome_page = call_loader(args.get('loader'), json_obj = welcome_page)
        app.logger.info(welcome_page)
        return jsonify(welcome_page)