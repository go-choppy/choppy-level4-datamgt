import sys, os, json
BASEDIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_TEMPLATES_DIR = BASEDIR + 'level4_data_mgt' + '/json_templates'
sys.path.append(BASEDIR)
print(sys.path)
from level4_data_mgt import JSON_TEMPLATES_DIR
from jinja2 import Environment, PackageLoader
env = Environment(loader=PackageLoader('level4_data_mgt', 'json_templates'), trim_blocks = True, lstrip_blocks = True)
template = env.get_template('expr_value.json.j2')

expr_value1 = {
    'gene_ensembl_id': "ENSG0000022333",
    'subproject_name': ["GTEx"],
    'expr_value_lst': [999],
    'source_type': ["Liver"]
}

expr_value2 = {
    'gene_ensembl_id': "ENSG0000022333",
    'subproject_name': ["TCGA"],
    'expr_value_lst': [1.2],
    'source_type': ["Kidney"]
}

expr_value3 = {
    'gene_ensembl_id': "ENSG0000022333",
    'subproject_name': ["TCGA"],
    'expr_value_lst': [555],
    'source_type': ["Lung"]
}

expr_value4 = {
    'gene_ensembl_id': "ENSG0000022333",
    'subproject_name': ["TCGA"],
    'expr_value_lst': [666],
    'source_type': ["Bone"]
}

def test_get_expr_value():
    return json.loads(template.render(expr_value = None, clinical_data_id_lst = True,
                                      samples_data_id_lst = True, phenotype_data_id_lst = False))

def merge_dict(dict1, dict2):
    result = {}
    keys = dict1.keys()
    for key in keys:
        if isinstance(dict1.get(key), list):
            result[key] = dict2.get(key)
            result[key][0:0] = dict1.get(key)
        elif isinstance(dict1.get(key), str):
            result[key] = dict1.get(key)
    return result

def merge_results(func, *args):
    if len(args) == 1:
        return args[0]
    else:
        return func(args[0], merge_results(func, *args[1:]))

if __name__ == '__main__':
    print(merge_results(merge_dict, expr_value1, expr_value2, expr_value3, expr_value4))