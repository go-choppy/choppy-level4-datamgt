# -*- encoding:utf-8 -*-
import os, json, bson
from mongoengine.queryset import DoesNotExist
from jinja2 import Environment, PackageLoader
from level4_data_mgt import app, db, JSON_TEMPLATES_DIR
from .utils import merge_expr_obj, merge_dicts

templates_conf = app.config.get("TEMPLATES")
expr_value_j2_file = templates_conf.get("EXPR_VALUE_J2_FILE")
project_info_j2_file = templates_conf.get("PROJECT_INFO_J2_FILE")
analysis_program_j2_file = templates_conf.get("ANALYSIS_PROGRAM_J2_FILE")
sample_data_j2_file = templates_conf.get("SAMPLE_DATA_J2_FILE")
clinical_data_j2_file = templates_conf.get("CLINICAL_DATA_J2_FILE")
exprtemp_info_j2_file = templates_conf.get("EXPRTEMP_INFO_J2_FILE")

env = Environment(loader=PackageLoader('level4_data_mgt', 'json_templates'), trim_blocks = True, lstrip_blocks = True)

def render_template(template, **kwargs):
    '''
    render模板，模板所需value由kwargs传入
    '''
    template = env.get_template(template)
    return template.render(**kwargs)

class AnalysisProgram(db.Document):
    created_author = db.StringField(max_length = 20, required = True)
    created_date = db.DateTimeField(required = True)
    description = db.StringField(max_length = 500, required = False)
    document_file = db.StringField(max_length = 255, required = True)
    md5 = db.StringField(max_length = 32, required = True)
    path = db.StringField(max_length = 255, required = True)
    program_name = db.StringField(max_length = 100, required = True)

def exist_analysis_program(md5):
    if AnalysisProgram.objects(md5 = md5):
        return True
    else:
        return False

class Project(db.Document):
    '''
    data_file_md5: 可能有多个原始数据文件需要导入，因此设置为List类别
    src_project_id: 当前project的数据可能来源于多个原project，因此设置为List类别
    src_project对应subproject，用于将多个project聚合成一个project的场景，每次聚合都意味着数据经过了某种处理
    '''
    analysis_pipeline_ref = db.ReferenceField(AnalysisProgram, required = True)
    created_date = db.DateTimeField(required = True)
    data_file_md5_lst = db.ListField(db.StringField(max_length = 32, required = True), required = True)
    data_file_name_lst = db.ListField(db.StringField(max_length = 255, required = True), required = True)
    data_type = db.StringField(max_length=10, required = True)
    description = db.StringField(max_length = 512)
    import_data_program_ref = db.ReferenceField(AnalysisProgram, required = True)
    normalized = db.BooleanField()
    normalized_method = db.StringField(max_length = 10, required = True)
    num_of_samples = db.IntField(required = True)
    project_name = db.StringField(max_length = 30, required = True)
    src_project_id_ref_lst = db.ListField(db.ReferenceField('Project', required = True), required = True)
    src_project_name_lst = db.ListField(db.StringField(max_length = 30, required = True), required = True)
    url = db.StringField(max_length = 100)
    version = db.StringField(max_length = 10, required = True)


def get_project_info(project_name, **kwargs):
    '''
    kwargs指定field是否显示在最终的结果中，可以接受N个field
    '''
    try:
        project = Project.objects.get(project_name = project_name)
        app.logger.info(project)
        if project:
            return False, 'success', json.loads(render_template(project_info_j2_file, project = project, **kwargs))
    except DoesNotExist as e:
        app.logger.warning("未找到%s" % project_name)
        return True, str(e), False


def exist_project(project_name):
    '''
    Func: Whether the id exist and have expression value in this collection
    '''
    if Project.objects(project_name = project_name):
        return True
    else:
        return False

def exist_subproject(project_name, subproject_name):
    if Project.objects(project_name = project_name, src_project_name_lst__exists = subproject_name):
        return True
    else:
        return False

def get_project_id(project_name):
    if project_name is not None:
        project = Project.objects.get(project_name = project_name)
        if project:
            return project.id
        else:
            app.logger.warning("未找到%s" % project_name)
            return None
    else:
        app.logger.error("输入的project_name为空")
        return None

class GeneExpr(db.Document):
    '''
    索引方式：project-->subproject-->gene，通过subproject限定检索范围，一个subproject可以唯一确定一个gene
    性能陷阱：sample_id和clinical_data_id等只可用于索引表达值，不可用于检索确定基因，否则将带来性能问题，换而言之，
            基因或转录本的唯一确定是由project-subproject决定的，而非样本或患者
    '''
    clinical_data_id_lst = db.ListField(db.ReferenceField('ClinicalData', required = True), required = True)
    expr_value_lst = db.ListField(db.FloatField(), required = True)
    gene_ensembl_id = db.StringField(max_length = 50, required = True)
    project_ref = db.ReferenceField(Project, required = True)
    project_name = db.StringField(max_length = 30, required = True)
    subproject_name = db.StringField(max_length = 30, required = True)
    samples_data_id_lst = db.ListField(db.ReferenceField('SampleData', required = True), required = True)
    species = db.StringField(max_length = 10, required = True)
    source_type = db.StringField(max_length = 50, required = True)
    phenotype_data_id_lst = db.ListField(db.ReferenceField('PhenotypeData', required = True), required = True)


class TranscriptExpr(db.Document):
    '''
    索引方式：project-->subproject-->transcript，通过subproject限定检索范围，一个subproject可以唯一确定一个transcript
    '''
    clinical_data_id_lst = db.ListField(db.ReferenceField('ClinicalData', required = True), required = True)
    expr_value_lst = db.ListField(db.FloatField(), required = True)
    transcript_ensembl_id = db.StringField(max_length = 50, required = True)
    project_ref = db.ReferenceField(Project, required = True)
    subproject_name = db.StringField(max_length = 30, required = True)
    project_name = db.StringField(max_length = 30, required = True)
    samples_data_id_lst = db.ListField(db.ReferenceField('SampleData', required = True), required = True)
    species = db.StringField(max_length = 10, required = True)
    source_type = db.StringField(max_length = 50, required = True)
    phenotype_data_id_lst = db.ListField(db.ReferenceField('PhenotypeData', required = True), required = True)

def exist_ensembl_id(project_name, subproject_name, ensembl_id, expr_cls):
    kargs = {}
    if expr_cls.__name__ == "TranscriptExpr":
        kargs['transcript_ensembl_id'] = ensembl_id
    elif expr_cls.__name__ == "GeneExpr":
        kargs['gene_ensembl_id'] = ensembl_id

    projects = Project.objects(project_name=project_name)
    if expr_cls.objects(**kargs, project__in=projects, subproject_name = subproject_name):
        return True
    else:
        app.logger.warning("未找到%s, %s, %s, %s" % (project_name, subproject_name, ensembl_id))
        return False

def get_expr_by_project(project_name, subproject_name, ensembl_id, expr_cls, **kwargs):
    query_args = {}
    if expr_cls.__name__ == 'TranscriptExpr':
        query_args['transcript_ensembl_id'] = ensembl_id
        kwargs['show_transcript_ensembl'] = True
        kwargs['show_gene_ensembl'] = False
    elif expr_cls.__name__ == 'GeneExpr':
        query_args['gene_ensembl_id'] = ensembl_id
        kwargs['show_transcript_ensembl'] = False
        kwargs['show_gene_ensembl'] = True

    projects = Project.objects(project_name=project_name)
    app.logger.debug("project_id: %s" % projects[0].id)
    if subproject_name:
        query_args['subproject_name'] = subproject_name

    app.logger.debug("查询: %s" % query_args)
    try:
        # 不指定subproject_name时，可能找到多个gene/transcript document
        expr_value_rest_lst = expr_cls.objects(**query_args, project_ref__in=projects)
        app.logger.debug("expr_value_rest_lst: %s" % expr_value_rest_lst)
        if expr_value_rest_lst:
            app.logger.debug("检索结果: %s" % len(expr_value_rest_lst))
            results = [json.loads(render_template(expr_value_j2_file, expr_value = expr_value, **kwargs))\
                       for expr_value in expr_value_rest_lst]
            return False, 'success', merge_dicts(merge_expr_obj, *results)
        else:
            query_args.update({"project_name": project_name})
            raise DoesNotExist("Can't find %s" % query_args)
    except DoesNotExist as e:
        app.logger.warning("未找到%s, %s" % (project_name, ensembl_id))
        return True, str(e), False   

def get_exprs(project_name, ensembl_id, expr_cls, **kwargs):
    pass

def get_expr_info_by_lst(project_name, subproject_name, id_lst, expr_cls, **args):
    '''
    返回表达数据，多个ID同时查询
    '''
    errors = []
    messages = []
    expr_info_lst = []
    for transcript_id in id_lst:
        error, message, expr_info = get_expr_by_project(project_name, subproject_name, transcript_id, expr_cls, **args)
        app.logger.debug("expr_info: %s" % expr_info)
        if error:
            errors.append(error)
            messages.append(message)
        else:
            expr_info_lst.append(expr_info)
            app.logger.debug("expr_info_lst: %s" % expr_info_lst)
    return errors, messages, merge_dicts(merge_expr_obj, *expr_info_lst)


class ExprInfo(db.Document):
    '''
    临时资源，用于多ID查询的场景
    '''
    clinical_data_id_lst = db.ListField(db.ReferenceField('ClinicalData', required = True))
    expr_value_lst = db.ListField(db.FloatField(), required = True)
    transcript_ensembl_id_lst = db.ListField(db.StringField(max_length = 50, required = True))
    gene_ensembl_id_lst = db.ListField(db.StringField(max_length = 50, required = True))
    project_ref = db.ReferenceField(Project, required = True)
    subproject_name_lst = db.ListField(db.StringField(max_length = 30, required = True))
    project_name = db.StringField(max_length = 30, required = True)
    samples_data_id_lst = db.ListField(db.ReferenceField('SampleData', required = True))
    species_lst = db.ListField(db.StringField(max_length = 10, required = True))
    source_type_lst = db.ListField(db.StringField(max_length = 50, required = True), required = True)
    phenotype_data_id_lst = db.ListField(db.ReferenceField('PhenotypeData', required = True))
    query_condition_md5 = db.StringField(max_length = 128, required = True)


def get_exprtemp_info(id = None, query_condition_md5 = None, **kwargs):
    '''
    kwargs指定field是否显示在最终的结果中，可以接受N个field
    '''
    try:
        if query_condition_md5:
            expr_info = ExprInfo.objects.get(query_condition_md5 = query_condition_md5)
        else:
            id = bson.ObjectId(id)
            expr_info = ExprInfo.objects.get(id = id)
        if expr_info:
            return False, 'success', expr_info
        else:
            raise DoesNotExist
    except (DoesNotExist, bson.errors.InvalidId) as e:
        # id不能完全匹配ObjectId时将导致InvalidId异常
        app.logger.info(str(e))
        return True, str(e), False

def write_expr_info(**kwargs):
    '''
    保存用户查询获得的ExprInfo信息
    '''
    expr_temp = ExprInfo(**kwargs)
    expr_temp.save()
    app.logger.info("Document ID: %s" % expr_temp.id)
    return expr_temp.id

class ClinicalData(db.Document):
    '''
    索引方式：project-->subproject-->patient，不可能同一个患者两次出现在同一个subproject
    '''
    age = db.FloatField(min_value = 0.001, max_value = 1200)  # 单位: 月
    age_began_smoking_in_years = db.IntField(min_value = 1900, max_value = 2999)    # 单位: 年
    alcohol_history_documented = db.BooleanField()  # 0: 无饮酒史，1: 有饮酒史
    amount_of_alcohol_comsumption_per_day = db.FloatField(min_value = 0.01, max_value = 100)    # 单位: kg
    frequency_of_alcohol_consumption = db.IntField(min_value = 1, max = 7)  # 单位: 周
    gender = db.BooleanField()  # 0: 女性 1: 男性
    height = db.FloatField(min_value = 30, max_value = 300) # 单位: 厘米
    lymph_node_examined_count = db.FloatField(min_value = 0.1, max_value = 100) # 单位: 个数
    number_of_lymphnodes_position_by_he = db.FloatField(min_value = 0.1, max_value = 100) # 单位: 个数
    number_of_lymphnodes_position_by_ihc = db.FloatField(min_value = 0.1, max_value = 100) # 单位: 个数
    number_pack_years_smoked = db.FloatField(min_value = 0.01, max_value = 100) # 单位: 包
    OS = db.FloatField(min_value = 0.01, max_value = 1200)  # 单位: 月
    OS_IND = db.BooleanField()  # 0: 未死亡 1: 死亡
    patient_id = db.StringField(max_length = 50, required = True)
    project_ref = db.ReferenceField(Project, required = True)
    project_name = db.StringField(max_length = 30, required = True)
    subproject_name = db.StringField(max_length = 30, required = True)
    RFS = db.FloatField(min_value = 0.01, max_value = 1200)  # 单位: 月
    RFS_IND = db.BooleanField() # 0: 未复发 1: 复发
    stopped_smoking_year = db.IntField(min_value = 1900, max_value = 2999)  # 单位: 年
    tobacco_smoking_history = db.BooleanField() # 0: 无吸烟史，1: 有吸烟史
    weight = db.FloatField(min_value = 1, max_value = 500) # 单位: kg


class SampleData(db.Document):
    '''
    索引方式：project-->subproject-->sample，不可能同一个样本两次出现在同一个subproject
    '''
    clinical_data_id_ref = db.ReferenceField(ClinicalData, required = True)
    concentration = db.FloatField(min_value = 0.001, max_value = 1000)
    ERCC = db.StringField(max_length = 10)
    FFPE = db.BooleanField()
    histological_type = db.StringField(max_length = 30, required = True)
    od260_280 = db.FloatField(min_value = 0.001, max_value = 1000)
    primary_site = db.StringField(max_length = 30, required = True)
    project_ref = db.ReferenceField(Project, required = True)
    project_name = db.StringField(max_length = 30, required = True)
    subproject_name = db.StringField(max_length = 30, required = True)
    reads = db.FloatField(min_value = 0.01, max_value = 1000)
    rin = db.FloatField(min_value = 0.001, max_value = 1000)
    sample_id = db.StringField(max_length = 50, required = True)
    source = db.StringField(max_length = 30, required = True)
    species = db.StringField(max_length = 10, required = True)
    tissue_histological_subtype = db.StringField(max_length = 30, required = False)
    tissue_molecular_subtype = db.StringField(max_length = 30, required = False)
    volume = db.FloatField(min_value = 0.001, max_value = 1000)
    weight = db.FloatField(min_value = 0.001, max_value = 1000)
    yields = db.FloatField(min_value = 0.01, max_value = 1000)


class PhenotypeData(db.Document):
    pass


class ExperimentMetaData(db.Document):
    pass


class PDXModel(db.Document):
    pass


class CellLine(db.Document):
    pass


class DrugPerturbation(db.Document):
    pass


class DrugSensitivity(db.Document):
    pass


class MgtMetaData(db.Document):
    pass
