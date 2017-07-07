#!/usr/bin/env python
# -*- encoding:utf-8 -*-
import os, sys, toml
working_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
sys.path.append(working_dir)

import argparse, itertools, hashlib, shutil, datetime
from bson import json_util
from level4_data_mgt.models import get_project_id, exist_project, exist_ensembl_id
from level4_data_mgt.models import GeneExpr, TranscriptExpr, Project
from level4_data_mgt.models import expr_value_j2_file
from level4_data_mgt.models import project_info_j2_file
from level4_data_mgt.models import sample_data_j2_file
from level4_data_mgt.models import analysis_program_j2_file
from level4_data_mgt.models import clinical_data_j2_file
from level4_data_mgt.models import exist_analysis_program
from level4_data_mgt import DBDataDir

created_author = 'YJC'
created_date = datetime.datetime(2017, 5, 20, 2, 36, 54, 942880)
description = '''
数据库导入程序
'''

def md5(file_path):
    return hashlib.md5(open(file_path, 'rb').read()).hexdigest()

def project2json(file_obj, db_type, project_name = "None", file_name = "output.json", 
                 template = project_info_j2_file):
    pass

    
def analysprogram2json(file_obj, db_type, project_name = "None", file_name = "output.json"):
    import_data_program = os.path.abspath(__file__)
    md5 = md5(import_data_program)
    if exist_analysis_program(md5):
        print('程序已存在，无需再次导入')
    else:
        program_name = os.path.file_name(import_data_program)
        document_file = '%s/README' % os.path.dirname(import_data_program)
        if os.path.isfile(document_file):
            shutil.move(document_file, "%s/%s_README" % (DBDataDir, md5))
        else:
            print("未找到README文件，请准备后再次导入")
            sys.exit(1)
        path = "%s/%s" % (DBDataDir, md5)
        shutil.move(import_data_program, path)
        analysis_program = {
            "create_author": create_author,
            "created_date": created_date,
            "description": description,
            "document_file": document_file,
            "md5": md5,
            "path": path,
            "program_name": program_name
        }

        print("打开文件: %s" % file_name)
        with open(file_name, 'w') as output:
            output.write(json_util.dumps(analysis_program))

def transcript2json(*args, **kwargs):
    gene2json(*args, **kwargs)

def transcriptmean2json(*args, **kwargs):
    genemean2json(*args, **kwargs)

def clinicaldata2json():
    pass

def sampledata2json():
    pass

def gene2json(file_obj, db_type, project_name = "None", file_name = "output.json", template = None, **kwargs):
    if project_name is None:
        print("必须指定project_name")
        sys.exit(1)

    header = file_obj.readline()
    header = [i.strip('. \n\r"') for i in header.split('\t')]
    if len(header) < 5 or header[:4] != ['ensembl_id', 'project', 'subproject_name', 'species', 'source_type']:
        print('Your file must have the following four columns: ensembl_id, project, subproject_name, species, source_type')
        sys.exit(1)

    if exist_project(project_name):
        project_id = get_project_id(project_name)
    else:
        print("%s不在Project数据库，请先上传相关Project信息." % project_name)
        sys.exit(1)

    print("打开文件: %s" % file_name)
    with open(file_name, 'w') as output:
        for line in file_obj:
            gene_info = [i.strip('. \n\r') for i in line.split('\t')]
            if len(gene_info) < 6:
                print("Your file must be a tab delimited file and have five more \
                       columns: ensembl_id, project, subproject_name, species, source_type, gene_expr_value")
            else:
                ensembl_id = gene_info[0]
                subproject_name = gene_info[2]
                species = gene_info[3]
                source_type = gene_info[4]

                if project_name != gene_info[1]:
                    print("您指定的project_name与文件中不一致")
                    sys.exit(1)

                expr_value_lst = gene_info[6:]
                db_dict ={
                    "project": project_id, 
                    "species": species,
                    "source_type": source_type, 
                    "clinical_data_id_lst": None,
                    "expr_value_lst": expr_value_lst,
                    "subproject_name": subproject_name,
                    "samples_data_id_lst": None,
                    "phenotype_data_id_lst": None,
                    "project_name": project_name,
                }
                if db_type.__name__ == 'GeneExpr':
                    db_dict["gene_ensembl_id"] = ensembl_id
                elif db_type.__name__ == 'TranscriptExpr':
                    db_dict["transcript_ensembl_id"] = ensembl_id
                output.write(json_util.dumps(db_dict))

def genemean2json(file_obj, db_type, project_name = "None", file_name = "output.json", template = None, **kwargs):
    '''
    genemean文件header:
    ID  Colon   Kidney  Uterus
    ENSG00000242268 -9.69974005681818   -5.86667663096397   -5.43895263157895
    '''
    if project_name is None:
        print("必须指定project_name")
        sys.exit(1)

    header = file_obj.readline()
    header = [i.strip('. \n\r"') for i in header.split('\t')]

    if exist_project(project_name):
        project_id = get_project_id(project_name)
    else:
        print("%s不在Project数据库，请先上传相关Project信息." % project_name)
        sys.exit(1)

    print("打开文件: %s" % file_name)
    with open(file_name, 'w') as output:
        for line in file_obj:
            gene_info = [i.strip('. \n\r') for i in line.split('\t')]
            if len(gene_info) != len(header):
                print("列数不相等")
                sys.exit(1)
            else:
                ensembl_id = gene_info[0]
                subproject_name = kwargs.get('subproject_name')
                species = 'human'
                for item, value in zip(header[1:], gene_info[1:]):
                    source_type = item
                    expr_value_lst = value
                    db_dict ={
                        "project_ref": project_id, 
                        "species": species,
                        "source_type": source_type, 
                        "clinical_data_id_lst": None,
                        "expr_value_lst": expr_value_lst,
                        "subproject_name": subproject_name,
                        "samples_data_id_lst": None,
                        "phenotype_data_id_lst": None,
                        "project_name": project_name,
                    }
                    if db_type.__name__ == 'GeneExpr':
                        db_dict["gene_ensembl_id"] = ensembl_id
                    elif db_type.__name__ == 'TranscriptExpr':
                        db_dict["transcript_ensembl_id"] = ensembl_id
                    output.write(json_util.dumps(db_dict))

db_class_dict = {'gene_expr': GeneExpr, 'transcript_expr': TranscriptExpr, 'project': Project}
template_file_dict = {'expr_value_j2': expr_value_j2_file, 'project_info_j2': project_info_j2_file, 
                      'analysis_program_j2_file': analysis_program_j2_file, 'sample_data_j2': sample_data_j2_file,
                      'clinical_data_j2': clinical_data_j2_file}

store_func_dict = {'project_info': project2json, 'gene_exprs': gene2json, 'transcript_exprs': transcript2json,
                   'clinical_data': clinicaldata2json, 'sample_data': sampledata2json, 'gene_exprs_mean': genemean2json,
                   'transcript_exprs_mean': transcriptmean2json}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Import specified file content into database.')
    parser.add_argument('--dbtype', required=True, 
                        choices=['gene_expr', 'transcript_expr', 'project'],
                        help='data type, the program support three kind of files')
    parser.add_argument('--jsontype', required=True, 
                        choices=['gene_exprs', 'transcript_exprs', 'project_info', 'gene_exprs_mean', "transcript_exprs_mean"],
                        help='data type, the program support three kind of files')
    parser.add_argument('--project-name', default=None, help="Project name")
    parser.add_argument('--subproject-name', default=None, help="Subproject name")
    parser.add_argument('--output-file', default="output.json", help="Output file name")
    parser.add_argument('file_name', help='A file that match type')
    args = parser.parse_args()

    project_name = args.project_name
    subproject_name = args.subproject_name
    output_file = args.output_file

    file_name = args.file_name
    db_type = db_class_dict.get(args.dbtype)
    func_type = args.jsontype
    if db_type:
        with open(os.path.abspath(file_name.strip()), 'r') as f:
            if project_name:
                store_data = store_func_dict.get(func_type)
            if store_data:
                store_data(f, db_type, project_name = project_name, file_name=output_file, subproject_name=subproject_name)
            else:
                print("Can't find a suitable function for your data")
                sys.exit(2)
